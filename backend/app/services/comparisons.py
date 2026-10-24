from __future__ import annotations

import csv
import html
import io
import math
from collections.abc import Iterable
from datetime import date
from statistics import fmean, pstdev

from app.domain.research import evaluate
from app.models import Run, RunStatus
from app.services.observation_artifact import read_observation_artifact


METRICS = (
    "coverage",
    "ic_mean",
    "rank_ic_mean",
    "icir",
    "ic_positive_ratio",
    "long_short_total_return",
    "long_short_net_total_return",
    "top_group_turnover",
)
METRIC_LABELS = {
    "coverage": "有效观测",
    "ic_mean": "IC均值",
    "rank_ic_mean": "Rank IC",
    "icir": "ICIR",
    "ic_positive_ratio": "IC为正比例",
    "long_short_total_return": "多空累计收益",
    "long_short_net_total_return": "成本后多空累计收益",
    "top_group_turnover": "头部组换手率",
}
DATASET_SOURCE_LABELS = {
    "bundled_demo": "内置演示数据",
    "historical_bundle": "历史研究数据包（来源另核）",
    "imported_csv": "导入 CSV（来源另核）",
}


def _dataset_source_kind(dataset: DatasetVersion) -> str:
    report = dataset.quality_report or {}
    if dataset.dataset_key == "demo_daily" and report.get("source") == "bundled_demo":
        return "bundled_demo"
    if dataset.dataset_key == "hs300_2024" and report.get("dataset_kind") == "hs300_bundle_v1":
        return "historical_bundle"
    return "imported_csv"


def compare_runs(runs: Iterable[Run]) -> dict:
    selected = list(runs)
    if not 2 <= len(selected) <= 6:
        raise ValueError("select between two and six runs")
    if len({run.id for run in selected}) != len(selected):
        raise ValueError("run_ids must be distinct")

    items: list[dict] = []
    date_sets: list[set[str]] = []
    group_date_sets: list[set[str]] = []
    ic_maps: list[dict[str, dict]] = []
    observation_maps: list[dict | None] = []
    validation_date_sets: list[set[str] | None] = []
    for run in selected:
        if run.status != RunStatus.SUCCESS:
            raise ValueError("only successful runs can be compared")
        artifact = next((item for item in run.artifacts if item.artifact_type == "metrics"), None)
        if artifact is None or artifact.content is None:
            raise ValueError("successful run is missing metrics artifact")
        result = artifact.content
        observations_artifact = next((item for item in run.artifacts if item.artifact_type == "observations"), None)
        observation_points = read_observation_artifact(observations_artifact) if observations_artifact else None
        observation_maps.append(observation_points)
        ic_maps.append({str(point["date"]): point for point in result.get("ic_series", []) if point.get("date")})
        dates = {str(item["date"]) for item in result.get("ic_series", [])
                 if item.get("date") and _finite_metric(item.get("ic")) is not None}
        date_sets.append(dates)
        group_dates = {str(item["date"]) for item in result.get("long_short_series", []) if item.get("date")}
        group_date_sets.append(group_dates)
        parameters = run.experiment.parameters
        split = result.get("time_split")
        split = split if isinstance(split, dict) else None
        validation = split.get("validation") if split else None
        validation = validation if isinstance(validation, dict) else None
        cutoff = split.get("validation_start_date") if validation else None
        cutoff = cutoff if isinstance(cutoff, str) and cutoff else None
        validation_date_sets.append({day for day in dates if day >= cutoff} if cutoff else None)
        items.append(
            {
                "run_id": run.id,
                "experiment_name": run.experiment.name,
                "factor": parameters.get("factor"),
                "dataset_version_id": run.experiment.dataset_version_id,
                "dataset_checksum_sha256": run.experiment.dataset_version.checksum,
                "dataset_source_kind": _dataset_source_kind(run.experiment.dataset_version),
                "dataset_version": run.experiment.dataset_version.version,
                "groups": parameters.get("groups"),
                "transaction_cost_bps": result.get("transaction_cost_bps"),
                "finished_at": run.finished_at,
                "metrics": {key: _finite_metric(result.get(key)) for key in METRICS},
                "ic_date_count": len(dates),
                "group_date_count": len(group_dates),
                "ic_start_date": min(dates) if dates else None,
                "ic_end_date": max(dates) if dates else None,
                "sample_symbols": sorted(set(parameters.get("symbols") or [])),
                "preprocessing": {
                    "winsorize": bool(parameters.get("winsorize", True)),
                    "standardize": bool(parameters.get("standardize", True)),
                    "mad_scale": float(parameters.get("mad_scale", 3)) if parameters.get("winsorize", True) else None,
                },
                "code_version": run.experiment.code_version,
                "price_basis": parameters.get("price_basis", "source_close"),
                "validation_start_date": cutoff,
                "validation_ic": {
                    key: _finite_metric(validation.get(key))
                    for key in ("valid_ic_dates", "ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio")
                } if cutoff else None,
                "validation_observation_count": _finite_metric(validation.get("observation_count")) if cutoff else None,
                "observation_artifact_count": len(observation_points) if observation_points is not None else None,
                "validation_artifact_count": sum(day.isoformat() >= cutoff for day, _ in observation_points)
                if observation_points is not None and cutoff else None,
                "requested_validation_start_date": parameters.get("validation_start_date"),
            }
        )

    baseline = items[0]
    for item in items:
        item["delta_from_baseline"] = {
            key: _difference(item["metrics"].get(key), baseline["metrics"].get(key))
            for key in METRICS
        }

    warnings: list[str] = []
    for item in items:
        if item["observation_artifact_count"] is not None and item["metrics"]["coverage"] is not None:
            if item["observation_artifact_count"] != item["metrics"]["coverage"]:
                warnings.append(f"任务 {item['run_id']} 的指标有效观测数与逐股产物条数不一致，需核对产物来源。")
        if item["validation_artifact_count"] is not None and item["validation_observation_count"] is not None:
            if item["validation_artifact_count"] != item["validation_observation_count"]:
                warnings.append(f"任务 {item['run_id']} 的验证期观测数与逐股产物条数不一致，需核对分段结果。")
    cutoffs = [item["validation_start_date"] for item in items]
    if any(item["requested_validation_start_date"] != item["validation_start_date"] for item in items):
        warnings.append("部分任务的验证期参数与已保存分段结果不一致，验证期摘要不可直接比较。")
    if any(cutoffs) and not all(cutoffs):
        warnings.append("同时选择了有时间切分和无时间切分的任务；原始全区间排名不能当作验证期排名。")
    elif len(set(cutoffs)) > 1:
        warnings.append("所选任务的验证期起始日不同，验证期 IC 摘要不可直接横向归因。")
    common_validation_dates = None
    if all(cutoffs) and len(set(cutoffs)) == 1:
        common_validation_dates = set.intersection(*(dates for dates in validation_date_sets if dates is not None))
        if not common_validation_dates:
            warnings.append("所选任务没有共同的验证期有效 IC 日期。")
        elif any(dates != validation_date_sets[0] for dates in validation_date_sets[1:]):
            warnings.append("验证期实际有效 IC 日期集合不同；下表仍为各任务保存的验证期摘要。")
    if any(item["price_basis"] != baseline["price_basis"] for item in items[1:]):
        warnings.append("所选任务的研究价格口径不同，请核对复权处理。")
    if len({item["dataset_version_id"] for item in items}) > 1:
        warnings.append("所选任务使用了不同数据版本，指标差异可能来自样本变化。")
    if len({item["groups"] for item in items}) > 1:
        warnings.append("所选任务的分组数不同，多空收益和换手率不宜直接横向比较。")
    common_dates = set.intersection(*date_sets) if date_sets else set()
    common_group_dates = set.intersection(*group_date_sets) if group_date_sets else set()
    for item, points in zip(items, ic_maps):
        ic_values = [float(points[day]["ic"]) for day in sorted(common_dates)]
        rank_values = [_finite_metric(points[day].get("rank_ic")) for day in sorted(common_dates)]
        rank_values = [float(value) for value in rank_values if value is not None]
        mean = fmean(ic_values) if ic_values else None
        deviation = (0.0 if max(ic_values) - min(ic_values) <= 1e-12 else pstdev(ic_values)) if len(ic_values) > 1 else None
        item["common_date_ic"] = {
            "ic_mean": mean,
            "rank_ic_mean": fmean(rank_values) if rank_values else None,
            "icir": mean / deviation if mean is not None and deviation else None,
            "ic_positive_ratio": sum(value > 0 for value in ic_values) / len(ic_values) if ic_values else None,
            "rank_ic_valid_dates": len(rank_values),
        }
    if len({item["transaction_cost_bps"] for item in items}) > 1:
        warnings.append("所选任务的成本假设不同，成本后收益不能直接归因于因子差异。")
    if any(item["metrics"].get("long_short_net_total_return") is None for item in items):
        warnings.append("部分任务的成本后收益缺失或不是有限数，无法比较该指标。")
    if not common_dates:
        warnings.append("所选任务没有共同的有效 IC 交易日。")
    elif any(dates != date_sets[0] for dates in date_sets[1:]):
        warnings.append("实际有效 IC 日期集合不同；原始指标仍为各任务全区间结果，下方另列共同日期 IC 摘要。")
    if not common_group_dates:
        warnings.append("所选任务没有共同的多空分组日期，多空收益和换手率不可直接比较。")
    elif any(dates != group_date_sets[0] for dates in group_date_sets[1:]):
        warnings.append("实际多空分组日期集合不同；多空收益和换手率均按各任务原始可分组日期计算，未在共同日期上重新计算。")
    if any(item["sample_symbols"] != baseline["sample_symbols"] for item in items[1:]):
        warnings.append("所选任务的证券筛选条件不同，指标差异可能来自股票池变化。")
    if any(item["preprocessing"] != baseline["preprocessing"] for item in items[1:]):
        warnings.append("所选任务的去极值或标准化参数不同，请结合预处理差异解释结果。")
    if any(item["code_version"] != baseline["code_version"] for item in items[1:]):
        warnings.append("所选任务的代码版本不同，计算实现变化可能影响结果。")

    matched_sample = {"available": False, "reason": "至少一个旧任务缺少逐股观测产物；仅能提供共同日期摘要。"}
    matched_validation_sample = {"available": False, "reason": "仅当所有任务使用同一验证期起始日且保有逐股观测产物时可计算。"}
    if all(points is not None for points in observation_maps):
        keys = set.intersection(*(set(points) for points in observation_maps))
        if keys:
            matched_sample = _matched_ic_summary(
                selected, items, observation_maps, keys,
                [item["metrics"]["coverage"] for item in items],
            )
            if matched_sample["label_mismatch_count"]:
                warnings.append("共同证券日期上的次日收益标签存在差异；严格样本 IC 仍受价格或数据口径影响。")
            if any((item["retention_ratio"] or 0) > 1 for item in matched_sample["items"]):
                warnings.append("严格样本观测数超过某个任务保存的原观测数，需核对指标与观测产物一致性。")
            if not matched_sample["available"]:
                warnings.append("共同证券日期样本未使每个任务形成有效 IC 截面；严格样本 IC 不可横向比较。")
        else:
            matched_sample = {"available": False, "reason": "所选任务没有共同证券日期观测，无法重算严格样本 IC。"}
            warnings.append("所选任务没有共同证券日期观测，严格样本 IC 不可比较。")
        if all(cutoffs) and len(set(cutoffs)) == 1 and all(
            item["requested_validation_start_date"] == item["validation_start_date"] for item in items
        ):
            cutoff_date = date.fromisoformat(cutoffs[0])
            validation_keys = {key for key in keys if key[0] >= cutoff_date}
            if validation_keys:
                matched_validation_sample = _matched_ic_summary(
                    selected, items, observation_maps, validation_keys,
                    [item["validation_observation_count"] for item in items],
                )
                matched_validation_sample["validation_start_date"] = cutoffs[0]
                if matched_validation_sample["label_mismatch_count"]:
                    warnings.append("共同验证期证券日期上的次日收益标签存在差异；验证期严格样本 IC 不具备同标签口径。")
                if any((item["retention_ratio"] or 0) > 1 for item in matched_validation_sample["items"]):
                    warnings.append("验证期严格样本观测数超过某个任务保存的验证期原观测数，需核对产物一致性。")
                if not matched_validation_sample["available"]:
                    warnings.append("验证期共同证券日期样本未使每个任务形成有效 IC 截面；验证期严格样本 IC 不可横向比较。")
            else:
                matched_validation_sample = {"available": False, "reason": "同一验证期起始日之后没有共同证券日期观测。"}
                warnings.append("同一验证期起始日之后没有共同证券日期观测；验证期严格样本 IC 不可比较。")
        elif all(cutoffs) and len(set(cutoffs)) == 1:
            matched_validation_sample = {"available": False, "reason": "验证期参数与已保存分段结果不一致，不能重算验证期严格样本 IC。"}
    else:
        warnings.append("至少一个任务缺少逐股观测产物，无法核对严格同样本 IC；原始指标与共同日期摘要仍可查看，但不能据此认定样本可比。")

    return {
        "baseline_run_id": baseline["run_id"],
        "items": items,
        "rankings": {
            key: [item["run_id"] for item in sorted(
                (item for item in items if _rank_value(item["metrics"].get(key)) is not None),
                key=lambda value: _rank_value(value["metrics"].get(key)), reverse=True)]
            for key in ("ic_mean", "rank_ic_mean", "icir", "long_short_net_total_return")
        },
        "common_ic_date_count": len(common_dates),
        "common_group_date_count": len(common_group_dates),
        "common_validation_ic_date_count": len(common_validation_dates) if common_validation_dates is not None else None,
        "matched_sample": matched_sample,
        "matched_validation_sample": matched_validation_sample,
        "comparable": not warnings,
        "warnings": warnings,
    }


def _matched_ic_summary(
    selected: list[Run], items: list[dict], observation_maps: list[dict], keys: set,
    source_counts: list[int | float | None],
) -> dict:
    ordered_keys = sorted(keys)
    label_mismatch_count = sum(
        any(not math.isclose(observation_maps[0][key].forward_return,
                             points[key].forward_return, rel_tol=0, abs_tol=1e-12)
            for points in observation_maps[1:])
        for key in ordered_keys
    )
    matched_items = []
    for run, item, points, source_count in zip(selected, items, observation_maps, source_counts):
        params = run.experiment.parameters
        composite = params.get("mode") in {"composite", "historical_hs300_2024"}
        matched = evaluate(
            [points[key] for key in ordered_keys], int(params.get("groups", 5)),
            winsorize=False if composite else bool(params.get("winsorize", True)),
            standardize=False if composite else bool(params.get("standardize", True)),
            mad_scale=float(params.get("mad_scale", 3)),
            transaction_cost_bps=float(params.get("transaction_cost_bps", 0)),
        )
        matched_items.append({"run_id": item["run_id"],
                              "ic_mean": matched["ic_mean"],
                              "rank_ic_mean": matched["rank_ic_mean"],
                              "icir": matched["icir"],
                              "ic_positive_ratio": matched["ic_positive_ratio"],
                              "valid_ic_dates": sum(point["ic"] is not None for point in matched["ic_series"]),
                              "source_observation_count": source_count,
                              "retention_ratio": len(ordered_keys) / source_count if source_count and source_count > 0 else None})
    minimum_valid_days = min(item["valid_ic_dates"] for item in matched_items)
    valid_for_all = minimum_valid_days > 0
    return {"available": valid_for_all,
            **({} if valid_for_all else {"reason": "至少一个任务在共同证券日期样本上没有有效 IC 截面。"}),
            "observation_count": len(ordered_keys),
            "date_count": len({key[0] for key in ordered_keys}),
            "label_mismatch_count": label_mismatch_count, "items": matched_items,
            "min_valid_ic_dates": minimum_valid_days,
            "min_retention_ratio": min(item["retention_ratio"] for item in matched_items)
            if all(item["retention_ratio"] is not None for item in matched_items) else None,
            "evidence": _ic_evidence(minimum_valid_days)}


def _ic_evidence(valid_days: int) -> dict[str, str]:
    if valid_days < 20:
        return {"level": "insufficient", "note": "最少有效 IC 日不足 20；只能说明可计算，不能评价稳定性。"}
    if valid_days < 60:
        return {"level": "limited", "note": "最少有效 IC 日为 20—59；样本基础有限，不应据此断言稳定性。"}
    return {"level": "descriptive", "note": "最少有效 IC 日达到 60；仍是描述性回溯，不代表显著性或未来表现。"}


def _difference(value: object, baseline: object) -> float | int | None:
    if _finite_metric(value) is None or _finite_metric(baseline) is None:
        return None
    difference = value - baseline
    return difference if _finite_metric(difference) is not None else None


def _finite_metric(value: object) -> float | int | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    try:
        return value if math.isfinite(value) else None
    except OverflowError:
        return None


def _rank_value(value: object) -> float | None:
    return float(value) if _finite_metric(value) is not None else None


def _spreadsheet_safe(value: object) -> object:
    if isinstance(value, str) and value and (
        value[0] in "\t\r\n" or value.lstrip().startswith(("=", "+", "-", "@"))
    ):
        return "'" + value
    return value


def comparison_csv(result: dict) -> bytes:
    stream = io.StringIO(newline="")
    section_writer = csv.writer(stream, lineterminator="\n")

    def section_row(*values: object) -> None:
        section_writer.writerow([_spreadsheet_safe(value) for value in values])

    metadata_fields = ["run_id", "experiment_name", "factor", "dataset_version_id", "dataset_checksum_sha256", "dataset_source_kind", "dataset_version", "price_basis", "groups", "ic_date_count", "group_date_count", "transaction_cost_bps", "ic_start_date", "ic_end_date", "sample_symbols", "preprocessing", "code_version", "observation_artifact_count", "validation_artifact_count"]
    fieldnames = list(metadata_fields)
    fieldnames.extend(f"common_date_{key}" for key in ("ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio", "rank_ic_valid_dates"))
    fieldnames.append("validation_start_date")
    fieldnames.extend(f"validation_{key}" for key in ("valid_ic_dates", "ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio"))
    for key in METRICS:
        fieldnames.extend((key, f"{key}_delta_from_baseline"))
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for item in result["items"]:
        row = {key: item.get(key) for key in metadata_fields}
        row.update({f"common_date_{key}": value for key, value in item["common_date_ic"].items()})
        row["validation_start_date"] = item.get("validation_start_date")
        row.update({f"validation_{key}": value for key, value in (item.get("validation_ic") or {}).items()})
        for key in METRICS:
            row[key] = item["metrics"].get(key)
            row[f"{key}_delta_from_baseline"] = item["delta_from_baseline"].get(key)
        writer.writerow({key: _spreadsheet_safe(value) for key, value in row.items()})
    section_row()
    section_row("可比性", "通过" if result["comparable"] else "谨慎解释")
    section_row("共同有效IC日期数", result["common_ic_date_count"])
    section_row("共同多空分组日期数", result["common_group_date_count"])
    section_row("共同验证期有效IC日期数", result.get("common_validation_ic_date_count"))
    matched = result["matched_sample"]
    section_row("共同证券日期观测数", matched.get("observation_count"))
    section_row("共同证券日期收益标签差异数", matched.get("label_mismatch_count"))
    if matched["available"]:
        section_row()
        section_row("严格样本IC摘要")
        section_row("最少有效IC日", matched["min_valid_ic_dates"])
        section_row("证据提示", matched["evidence"]["note"])
        strict_writer = csv.DictWriter(stream, fieldnames=["run_id", "ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio", "valid_ic_dates", "source_observation_count", "retention_ratio"], lineterminator="\n")
        strict_writer.writeheader()
        strict_writer.writerows(matched["items"])
    else:
        section_row("严格样本IC摘要", matched["reason"])
    validation_matched = result["matched_validation_sample"]
    if validation_matched["available"]:
        section_row()
        section_row("验证期严格样本IC摘要")
        section_row("验证期起始日", validation_matched["validation_start_date"])
        section_row("共同证券日期观测数", validation_matched["observation_count"])
        section_row("共同证券日期收益标签差异数", validation_matched["label_mismatch_count"])
        section_row("最少有效IC日", validation_matched["min_valid_ic_dates"])
        section_row("证据提示", validation_matched["evidence"]["note"])
        strict_writer = csv.DictWriter(stream, fieldnames=["run_id", "ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio", "valid_ic_dates", "source_observation_count", "retention_ratio"], lineterminator="\n")
        strict_writer.writeheader()
        strict_writer.writerows(validation_matched["items"])
    else:
        section_row("验证期严格样本IC摘要", validation_matched["reason"])
    for warning in result["warnings"]:
        writer.writerow({"run_id": "风险提示", "experiment_name": _spreadsheet_safe(warning)})
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def comparison_html(result: dict) -> str:
    provenance_rows = "".join(
        "<tr>"
        f"<td>{'基准' if index == 0 else f'候选 {index}'}</td>"
        f"<td>{html.escape(str(item['experiment_name']))}</td>"
        f"<td><code>{html.escape(str(item['run_id']))}</code></td>"
        f"<td><code>{html.escape(str(item['dataset_version_id']))}</code></td>"
        f"<td><code>{html.escape(str(item['dataset_checksum_sha256']))}</code></td>"
        f"<td>{html.escape(str(item['dataset_version']))}<small>{html.escape(DATASET_SOURCE_LABELS[item['dataset_source_kind']])}</small></td>"
        f"<td><code>{html.escape(str(item['code_version']))}</code></td>"
        "</tr>"
        for index, item in enumerate(result["items"])
    )
    headers = "".join(
        f"<th>{html.escape(item['experiment_name'])}<small>{'基准' if index == 0 else html.escape(str(item['factor']))}</small></th>"
        for index, item in enumerate(result["items"])
    )
    rows = "".join(
        "<tr><th>" + html.escape(METRIC_LABELS[key]) + "</th>" + "".join(
            f"<td><b>{_export_number(item['metrics'].get(key), key)}</b>"
            + (f"<small>较基准 {_export_number(item['delta_from_baseline'].get(key), key, signed=True)}</small>" if index else "<small>基准</small>")
            + "</td>"
            for index, item in enumerate(result["items"])
        ) + "</tr>"
        for key in METRICS
    )
    warnings = "".join(f"<li>{html.escape(item)}</li>" for item in result["warnings"]) or "<li>数据版本、分组数和共同日期检查通过。</li>"
    common_rows = "".join("<tr><th>" + html.escape(METRIC_LABELS[key]) + "</th>" + "".join(
        f"<td>{_export_number(item['common_date_ic'].get(key), key)}</td>" for item in result["items"]
    ) + "</tr>" for key in ("ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio"))
    validation_rows = "<tr><th>验证期起始日</th>" + "".join(
        f"<td>{html.escape(item['validation_start_date']) if item['validation_start_date'] else '—'}</td>"
        for item in result["items"]
    ) + "</tr>" + "".join(
        "<tr><th>" + html.escape("有效 IC 日" if key == "valid_ic_dates" else METRIC_LABELS[key]) + "</th>" + "".join(
            f"<td>{_export_number((item.get('validation_ic') or {}).get(key), 'coverage' if key == 'valid_ic_dates' else key)}</td>"
            for item in result["items"]
        ) + "</tr>"
        for key in ("valid_ic_dates", "ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio")
    )
    matched = result["matched_sample"]
    matched_rows = "".join("<tr><th>" + html.escape(METRIC_LABELS[key]) + "</th>" + "".join(
        f"<td>{_export_number(item.get(key), key)}</td>" for item in matched.get("items", [])
    ) + "</tr>" for key in ("ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio"))
    matched_rows += _retention_html_rows(matched.get("items", []))
    matched_rows += "<tr><th>逐股产物观测</th>" + "".join(
        f"<td>{_export_number(item['observation_artifact_count'], 'coverage')}</td>" for item in result["items"]
    ) + "</tr>"
    matched_section = (
        f"<p>共同证券日期观测 {matched['observation_count']} 条，涉及 {matched['date_count']} 天；"
        f"次日收益标签差异 {matched['label_mismatch_count']} 条。各任务按原预处理口径重算截面 IC。"
        f"最少有效 IC 日 {matched['min_valid_ic_dates']}；{html.escape(matched['evidence']['note'])}</p>"
        f"<table><thead><tr><th>指标</th>{headers}</tr></thead><tbody>{matched_rows}</tbody></table>"
        if matched["available"] else f"<p>{html.escape(matched['reason'])}</p>"
    )
    validation_matched = result["matched_validation_sample"]
    validation_matched_rows = "".join("<tr><th>" + html.escape(METRIC_LABELS[key]) + "</th>" + "".join(
        f"<td>{_export_number(item.get(key), key)}</td>" for item in validation_matched.get("items", [])
    ) + "</tr>" for key in ("ic_mean", "rank_ic_mean", "icir", "ic_positive_ratio"))
    validation_matched_rows += _retention_html_rows(validation_matched.get("items", []))
    validation_matched_rows += "<tr><th>验证期产物观测</th>" + "".join(
        f"<td>{_export_number(item['validation_artifact_count'], 'coverage')}</td>" for item in result["items"]
    ) + "</tr>"
    validation_matched_section = (
        f"<p>验证期从 {html.escape(validation_matched['validation_start_date'])} 开始；共同证券日期观测 "
        f"{validation_matched['observation_count']} 条，涉及 {validation_matched['date_count']} 天；"
        f"次日收益标签差异 {validation_matched['label_mismatch_count']} 条。"
        f"最少有效 IC 日 {validation_matched['min_valid_ic_dates']}；{html.escape(validation_matched['evidence']['note'])}"
        f"仅重算 IC，不重算交易收益。</p>"
        f"<table><thead><tr><th>指标</th>{headers}</tr></thead><tbody>{validation_matched_rows}</tbody></table>"
        if validation_matched["available"] else f"<p>{html.escape(validation_matched['reason'])}</p>"
    )
    rankings = "".join(
        f"<section><h3>{html.escape(METRIC_LABELS[key])}</h3><ol>" + "".join(
            f"<li>{html.escape(next(item['experiment_name'] for item in result['items'] if item['run_id'] == run_id))}</li>"
            for run_id in run_ids
        ) + "</ol></section>"
        for key, run_ids in result["rankings"].items()
    )
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FactorLab实验对比报告</title><style>
body{{font-family:Inter,'PingFang SC','Microsoft YaHei',sans-serif;color:#173128;background:#f4f5ef;margin:0}}main{{max-width:1100px;margin:auto;padding:52px 36px}}header{{border-bottom:4px solid #173128;padding-bottom:22px}}h1{{font-size:38px;margin:8px 0}}.tag{{font-size:11px;letter-spacing:2px;color:#6b7c73}}table{{width:100%;border-collapse:collapse;background:white;margin-top:18px}}th,td{{padding:12px;border-bottom:1px solid #e5e9e2;text-align:left}}thead th{{background:#173128;color:white}}th small,td small{{display:block;font-weight:400;opacity:.7;margin-top:5px}}code{{overflow-wrap:anywhere}}.check{{background:{'#edf7da' if result['comparable'] else '#fff5db'};border-left:4px solid {'#89ad43' if result['comparable'] else '#d5a22f'};padding:16px;margin:25px 0}}.rankings{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}.rankings section{{background:white;padding:14px;border:1px solid #dfe5dc;border-radius:10px}}li{{margin:7px 0}}footer{{margin-top:36px;color:#78877f;font-size:12px}}@media print{{body{{background:white}}main{{padding:16px}}}}@media(max-width:800px){{.rankings{{grid-template-columns:1fr 1fr}}}}
</style></head><body><main><header><p class="tag">FACTORLAB · EXPERIMENT COMPARISON</p><h1>实验对比报告</h1><p>首个任务为差值基准；本报告基于已保存的不可变研究结果生成。</p></header><h2>任务溯源</h2><div style="overflow:auto"><table><thead><tr><th>角色</th><th>实验</th><th>完整 Run ID</th><th>数据版本 ID</th><th>数据版本 SHA-256</th><th>数据版本号</th><th>代码版本</th></tr></thead><tbody>{provenance_rows}</tbody></table></div><div class="check"><b>{'所列口径检查通过，仍属描述性回溯' if result['comparable'] else '存在口径差异，请谨慎解释'}</b><p>共同有效 IC 交易日：{result['common_ic_date_count']}；共同多空分组日期：{result['common_group_date_count']}</p><ul>{warnings}</ul></div><h2>一、核心指标（原始全区间）</h2><div style="overflow:auto"><table><thead><tr><th>指标</th>{headers}</tr></thead><tbody>{rows}</tbody></table></div><h2>二、共同日期 IC 摘要</h2><p>仅基于保存的逐日 IC 重算；没有重算逐股截面。Rank IC 的有效日数可能更少。</p><div style="overflow:auto"><table><thead><tr><th>指标</th>{headers}</tr></thead><tbody>{common_rows}</tbody></table></div><h2>三、验证期 IC 摘要</h2><p>仅展示各任务保存的分段诊断；未设置切分日的任务显示为缺失。原始全区间排名不是验证期排名；本表不代表严格同股票样本或验证期交易收益。</p><div style="overflow:auto"><table><thead><tr><th>指标</th>{headers}</tr></thead><tbody>{validation_rows}</tbody></table></div><h2>四、严格样本 IC 摘要</h2><p>共同证券×日期键重算每个任务的 IC；不重算多空或可交易收益。</p>{matched_section}<h2>五、验证期严格样本 IC 摘要</h2><p>仅当所有任务的预设切分日相同、观测产物可用且验证期存在共同证券×日期键时计算。不同价格、标签、预处理或代码口径仍需谨慎解释。</p>{validation_matched_section}<h2>六、原始指标排名</h2><div class="rankings">{rankings}</div><h2>七、解释边界</h2><p>差值和排名不代表统计显著性、因果关系或未来表现。毛多空收益未计费用；成本后多空收益仅扣固定换手成本，均未模拟冲击成本、涨跌停和实际成交约束。</p><footer>仅用于课程研究，不构成投资建议。</footer></main></body></html>"""


def _export_number(value: object, key: str, signed: bool = False) -> str:
    if not isinstance(value, (int, float)):
        return "—"
    if key == "coverage":
        return f"{value:+g}" if signed else f"{value:g}"
    suffix = "%" if key in {"ic_positive_ratio", "long_short_total_return", "long_short_net_total_return", "top_group_turnover"} else ""
    scaled = float(value) * 100 if suffix else float(value)
    precision = 2 if suffix else 4
    return f"{scaled:+.{precision}f}{suffix}" if signed else f"{scaled:.{precision}f}{suffix}"


def _retention_html_rows(items: list[dict]) -> str:
    return "".join(
        f"<tr><th>{label}</th>" + "".join(
            f"<td>{_export_number(item.get(key), format_key)}</td>" for item in items
        ) + "</tr>"
        for label, key, format_key in (
            ("原任务观测", "source_observation_count", "coverage"),
            ("共同样本保留率", "retention_ratio", "ic_positive_ratio"),
        )
    )
