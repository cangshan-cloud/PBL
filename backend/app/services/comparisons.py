from __future__ import annotations

import csv
import html
import io
import math
from collections.abc import Iterable

from app.models import Run, RunStatus


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


def compare_runs(runs: Iterable[Run]) -> dict:
    selected = list(runs)
    if not 2 <= len(selected) <= 6:
        raise ValueError("select between two and six runs")
    if len({run.id for run in selected}) != len(selected):
        raise ValueError("run_ids must be distinct")

    items: list[dict] = []
    date_sets: list[set[str]] = []
    group_date_sets: list[set[str]] = []
    for run in selected:
        if run.status != RunStatus.SUCCESS:
            raise ValueError("only successful runs can be compared")
        artifact = next((item for item in run.artifacts if item.artifact_type == "metrics"), None)
        if artifact is None or artifact.content is None:
            raise ValueError("successful run is missing metrics artifact")
        result = artifact.content
        dates = {str(item["date"]) for item in result.get("ic_series", []) if item.get("date")}
        date_sets.append(dates)
        group_dates = {str(item["date"]) for item in result.get("long_short_series", []) if item.get("date")}
        group_date_sets.append(group_dates)
        parameters = run.experiment.parameters
        items.append(
            {
                "run_id": run.id,
                "experiment_name": run.experiment.name,
                "factor": parameters.get("factor"),
                "dataset_version_id": run.experiment.dataset_version_id,
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
            }
        )

    baseline = items[0]
    for item in items:
        item["delta_from_baseline"] = {
            key: _difference(item["metrics"].get(key), baseline["metrics"].get(key))
            for key in METRICS
        }

    warnings: list[str] = []
    if any(item["price_basis"] != baseline["price_basis"] for item in items[1:]):
        warnings.append("所选任务的研究价格口径不同，请核对复权处理。")
    if len({item["dataset_version_id"] for item in items}) > 1:
        warnings.append("所选任务使用了不同数据版本，指标差异可能来自样本变化。")
    if len({item["groups"] for item in items}) > 1:
        warnings.append("所选任务的分组数不同，多空收益和换手率不宜直接横向比较。")
    common_dates = set.intersection(*date_sets) if date_sets else set()
    common_group_dates = set.intersection(*group_date_sets) if group_date_sets else set()
    if len({item["transaction_cost_bps"] for item in items}) > 1:
        warnings.append("所选任务的成本假设不同，成本后收益不能直接归因于因子差异。")
    if any(item["metrics"].get("long_short_net_total_return") is None for item in items):
        warnings.append("部分任务的成本后收益缺失或不是有限数，无法比较该指标。")
    if not common_dates:
        warnings.append("所选任务没有共同的 IC 交易日。")
    elif any(dates != date_sets[0] for dates in date_sets[1:]):
        warnings.append("实际 IC 日期集合不同；展示的是各任务原始全区间指标，未在共同日期上重新计算。")
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
        "comparable": not warnings,
        "warnings": warnings,
    }


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


def comparison_csv(result: dict) -> bytes:
    stream = io.StringIO(newline="")
    metadata_fields = ["run_id", "experiment_name", "factor", "dataset_version", "price_basis", "groups", "ic_date_count", "group_date_count", "transaction_cost_bps", "ic_start_date", "ic_end_date", "sample_symbols", "preprocessing", "code_version"]
    fieldnames = list(metadata_fields)
    for key in METRICS:
        fieldnames.extend((key, f"{key}_delta_from_baseline"))
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for item in result["items"]:
        row = {key: item.get(key) for key in metadata_fields}
        for key in METRICS:
            row[key] = item["metrics"].get(key)
            row[f"{key}_delta_from_baseline"] = item["delta_from_baseline"].get(key)
        writer.writerow(row)
    stream.write("\n可比性," + ("通过" if result["comparable"] else "谨慎解释") + "\n")
    stream.write(f"共同IC日期数,{result['common_ic_date_count']}\n")
    stream.write(f"共同多空分组日期数,{result['common_group_date_count']}\n")
    for warning in result["warnings"]:
        writer.writerow({"run_id": "风险提示", "experiment_name": warning})
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def comparison_html(result: dict) -> str:
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
    rankings = "".join(
        f"<section><h3>{html.escape(METRIC_LABELS[key])}</h3><ol>" + "".join(
            f"<li>{html.escape(next(item['experiment_name'] for item in result['items'] if item['run_id'] == run_id))}</li>"
            for run_id in run_ids
        ) + "</ol></section>"
        for key, run_ids in result["rankings"].items()
    )
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FactorLab实验对比报告</title><style>
body{{font-family:Inter,'PingFang SC','Microsoft YaHei',sans-serif;color:#173128;background:#f4f5ef;margin:0}}main{{max-width:1100px;margin:auto;padding:52px 36px}}header{{border-bottom:4px solid #173128;padding-bottom:22px}}h1{{font-size:38px;margin:8px 0}}.tag{{font-size:11px;letter-spacing:2px;color:#6b7c73}}table{{width:100%;border-collapse:collapse;background:white;margin-top:18px}}th,td{{padding:12px;border-bottom:1px solid #e5e9e2;text-align:left}}thead th{{background:#173128;color:white}}th small,td small{{display:block;font-weight:400;opacity:.7;margin-top:5px}}.check{{background:{'#edf7da' if result['comparable'] else '#fff5db'};border-left:4px solid {'#89ad43' if result['comparable'] else '#d5a22f'};padding:16px;margin:25px 0}}.rankings{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}.rankings section{{background:white;padding:14px;border:1px solid #dfe5dc;border-radius:10px}}li{{margin:7px 0}}footer{{margin-top:36px;color:#78877f;font-size:12px}}@media print{{body{{background:white}}main{{padding:16px}}}}@media(max-width:800px){{.rankings{{grid-template-columns:1fr 1fr}}}}
</style></head><body><main><header><p class="tag">FACTORLAB · EXPERIMENT COMPARISON</p><h1>实验对比报告</h1><p>首个任务为差值基准；本报告基于已保存的不可变研究结果生成。</p></header><div class="check"><b>{'口径一致，可以直接比较' if result['comparable'] else '存在口径差异，请谨慎解释'}</b><p>共同 IC 交易日：{result['common_ic_date_count']}；共同多空分组日期：{result['common_group_date_count']}</p><ul>{warnings}</ul></div><h2>一、核心指标</h2><div style="overflow:auto"><table><thead><tr><th>指标</th>{headers}</tr></thead><tbody>{rows}</tbody></table></div><h2>二、指标排名</h2><div class="rankings">{rankings}</div><h2>三、解释边界</h2><p>差值和排名不代表统计显著性、因果关系或未来表现。毛多空收益未计费用；成本后多空收益仅扣固定换手成本，均未模拟冲击成本、涨跌停和实际成交约束。</p><footer>仅用于课程研究，不构成投资建议。</footer></main></body></html>"""


def _export_number(value: object, key: str, signed: bool = False) -> str:
    if not isinstance(value, (int, float)):
        return "—"
    if key == "coverage":
        return f"{value:+g}" if signed else f"{value:g}"
    suffix = "%" if key in {"ic_positive_ratio", "long_short_total_return", "long_short_net_total_return", "top_group_turnover"} else ""
    scaled = float(value) * 100 if suffix else float(value)
    return f"{scaled:+.2f}{suffix}" if signed else f"{scaled:.2f}{suffix}"
