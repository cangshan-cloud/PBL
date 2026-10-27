"""Validate a locally acquired real A-share snapshot and run supported factors."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from statistics import fmean
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import Base  # noqa: E402
from app.services.comparisons import compare_runs, comparison_csv, comparison_html  # noqa: E402
from app.services.datasets import import_csv, publish_dataset_version, validate_csv  # noqa: E402
from app.services.runs import create_research_run, execute_research_run  # noqa: E402
from verify_research_result_consistency import verify_time_split_consistency  # noqa: E402


FACTORS = ("momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d", "pe")
VALIDATION_START = "2024-04-01"


def _raw_pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean, right_mean = fmean(left), fmean(right)
    x = [value - left_mean for value in left]
    y = [value - right_mean for value in right]
    denominator = math.sqrt(math.fsum(value * value for value in x) * math.fsum(value * value for value in y))
    return math.fsum(a * b for a, b in zip(x, y, strict=True)) / denominator if denominator else None


def independent_momentum_ic_audit(content: bytes, ic_series: list[dict], *, lookback: int = 20,
                                   validation_start: str = VALIDATION_START) -> dict:
    """Compute raw close momentum and next-market-date IC without research-engine helpers."""
    if lookback < 1:
        raise ValueError("lookback must be positive")
    prices: dict[tuple[str, str], float] = {}
    dates: set[str] = set()
    symbols: set[str] = set()
    for row in csv.DictReader(io.StringIO(content.decode("utf-8-sig"))):
        day, symbol = row["trade_date"], row["symbol"]
        key = (day, symbol)
        if key in prices:
            raise ValueError("real sample has repeated stock-date row")
        close = float(row["close"])
        if not math.isfinite(close) or close <= 0:
            raise ValueError("real sample has invalid close")
        prices[key] = close
        dates.add(day)
        symbols.add(symbol)
    calendar = sorted(dates)
    positions = {day: index for index, day in enumerate(calendar)}
    audited = []
    for point in ic_series:
        day = point["date"]
        index = positions.get(day)
        if index is None or index < lookback or index + 1 >= len(calendar):
            raise ValueError(f"IC date has no raw momentum or next date: {day}")
        previous, next_day = calendar[index - lookback], calendar[index + 1]
        factors, forward_returns = [], []
        for symbol in sorted(symbols):
            if any((calendar[position], symbol) not in prices for position in range(index - lookback, index + 2)):
                continue
            past = prices.get((previous, symbol))
            current = prices.get((day, symbol))
            future = prices.get((next_day, symbol))
            if past is None or current is None or future is None:
                continue
            factors.append(current / past - 1)
            forward_returns.append(future / current - 1)
        computed = _raw_pearson(factors, forward_returns)
        saved = point["ic"]
        if computed is None or not isinstance(saved, (int, float)) or not math.isclose(computed, saved, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError(f"independent raw momentum IC differs on {day}")
        audited.append({"date": day, "next_date": next_day, "stock_count": len(factors),
                        "independent_ic": computed, "saved_ic": saved})
    if not audited:
        raise ValueError("real sample has no IC dates to audit")
    validation = next((item for item in audited if item["date"] >= validation_start), None)
    if validation is None:
        raise ValueError("real sample has no validation-period IC date")
    return {"audited_ic_dates": len(audited), "research_spot": audited[0], "validation_spot": validation,
            "max_abs_error": max(abs(item["independent_ic"] - item["saved_ic"]) for item in audited),
            "preprocessing": "winsorize=false, standardize=false; separate diagnostic run"}


def observed_coverage_audit(content: bytes) -> dict:
    """Count observed records, without claiming a complete exchange calendar."""
    by_date: Counter[str] = Counter()
    by_symbol: Counter[str] = Counter()
    for row in csv.DictReader(io.StringIO(content.decode("utf-8-sig"))):
        by_date[row["trade_date"]] += 1
        by_symbol[row["symbol"]] += 1
    if not by_date or not by_symbol:
        raise ValueError("real sample has no observed dates or symbols")
    return {"observed_dates": len(by_date), "min_rows_per_observed_date": min(by_date.values()),
            "max_rows_per_observed_date": max(by_date.values()),
            "min_rows_per_symbol": min(by_symbol.values()), "max_rows_per_symbol": max(by_symbol.values())}


def group_date_audit(result: dict, factor: str) -> dict:
    group_dates = [item["date"] for item in result["long_short_series"]]
    for group in result["group_nav"]:
        if [point["date"] for point in group["points"]] != group_dates:
            raise ValueError(f"group NAV dates differ from long-short dates: {factor}")
    if not set(group_dates).issubset({item["date"] for item in result["ic_series"]}):
        raise ValueError(f"group dates are absent from IC calendar: {factor}")
    return {
        "coverage": result["coverage"],
        "ic_dates": len(result["ic_series"]),
        "group_dates": len(group_dates),
        "skipped_constant_factor_days": result["group_skipped_constant_factor_days"],
        "skipped_insufficient_sample_days": result["group_skipped_insufficient_sample_days"],
    }


def validation_comparison_audit(session: Session, dataset_id: str, expected_checksum: str) -> dict:
    runs = [execute_research_run(session, create_research_run(session, {
        "factor": factor,
        "dataset_version_id": dataset_id,
        "groups": 5,
        "price_basis": "source_close",
        "validation_start_date": VALIDATION_START,
    }).id) for factor in ("momentum_20d", "reversal_5d")]
    split_checks = {
        run.experiment.factor_version.factor_key: verify_time_split_consistency(
            next(item.content for item in run.artifacts if item.artifact_type == "metrics"))
        for run in runs
    }
    result = compare_runs(runs)
    full = result["matched_sample"]
    validation = result["matched_validation_sample"]
    if not full["available"] or not validation["available"]:
        raise ValueError("real sample did not produce full and validation matched IC summaries")
    if validation["validation_start_date"] != VALIDATION_START:
        raise ValueError("real sample validation split differs from the predeclared date")
    if result["common_validation_ic_date_count"] != validation["date_count"]:
        raise ValueError("real sample validation IC dates differ from matched sample dates")
    if full["label_mismatch_count"] or validation["label_mismatch_count"]:
        raise ValueError("real sample next-day labels differ across factors")
    if not 0 < validation["observation_count"] < full["observation_count"]:
        raise ValueError("real sample validation intersection is not a strict subset")
    for item in result["items"]:
        if item["dataset_checksum_sha256"] != expected_checksum:
            raise ValueError("real sample comparison checksum differs from acquisition manifest")
        if item["observation_artifact_count"] != item["metrics"]["coverage"]:
            raise ValueError("real sample full metrics and observation artifact counts differ")
        if item["validation_artifact_count"] != item["validation_observation_count"]:
            raise ValueError("real sample validation metrics and observation artifact counts differ")
    for summary in (full, validation):
        if any(not 0 < item["retention_ratio"] <= 1 for item in summary["items"]):
            raise ValueError("real sample matched observation retention is out of bounds")
    csv_text = comparison_csv(result).decode("utf-8-sig")
    html_text = comparison_html(result)
    if "验证期严格样本IC摘要" not in csv_text or "验证期严格样本 IC 摘要" not in html_text:
        raise ValueError("real sample comparison exports omit the validation matched summary")
    if any(run.id not in csv_text for run in runs):
        raise ValueError("real sample comparison CSV omits a selected run")
    exported_rows = list(csv.DictReader(io.StringIO(csv_text)))[:len(result["items"])]
    for item, exported in zip(result["items"], exported_rows, strict=True):
        if exported["run_id"] != item["run_id"] or int(exported["coverage"]) != item["metrics"]["coverage"]:
            raise ValueError("real sample comparison CSV differs from saved run coverage")
        for key in ("dataset_version_id", "dataset_checksum_sha256", "code_version"):
            if exported[key] != item[key] or item[key] not in html_text:
                raise ValueError(f"real sample comparison export differs from saved {key}")
        for key, expected in (("ic_mean", item["metrics"]["ic_mean"]),
                              ("common_date_ic_mean", item["common_date_ic"]["ic_mean"])):
            if expected is None or float(exported[key]) != expected:
                raise ValueError(f"real sample comparison CSV differs from saved {key}")
        if item["run_id"] not in html_text or f"{item['metrics']['ic_mean']:.4f}" not in html_text:
            raise ValueError("real sample comparison HTML differs from saved run identity or IC")
        if int(exported["validation_valid_ic_dates"]) != item["validation_ic"]["valid_ic_dates"]:
            raise ValueError("real sample comparison CSV differs from validation IC days")
    for warning in result["warnings"]:
        if warning not in csv_text or html.escape(warning) not in html_text:
            raise ValueError("real sample comparison export omits a risk warning")
    if f"共同证券日期观测 {validation['observation_count']} 条" not in html_text:
        raise ValueError("real sample comparison HTML omits validation matched observation count")
    return {
        "validation_start_date": VALIDATION_START,
        "common_ic_dates": result["common_ic_date_count"],
        "common_validation_ic_dates": result["common_validation_ic_date_count"],
        "matched_observations": full["observation_count"],
        "matched_validation_observations": validation["observation_count"],
        "validation_min_valid_ic_dates": validation["min_valid_ic_dates"],
        "validation_evidence_level": validation["evidence"]["level"],
        "full_label_mismatches": full["label_mismatch_count"],
        "validation_label_mismatches": validation["label_mismatch_count"],
        "factors": {item["factor"]: {
            "full_observations": item["metrics"]["coverage"],
            "validation_observations": item["validation_observation_count"],
            "full_retention_ratio": next(point["retention_ratio"] for point in full["items"] if point["run_id"] == item["run_id"]),
            "validation_retention_ratio": next(point["retention_ratio"] for point in validation["items"] if point["run_id"] == item["run_id"]),
        } for item in result["items"]},
        "split_internal_consistency": split_checks,
        "exports": "CSV/HTML full identities, IC values, warnings, and validation matched count verified",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "real")
    args = parser.parse_args()
    source_dir = args.input_dir.resolve()
    csv_path = source_dir / "baostock_2024h1_daily.csv"
    manifest_path = source_dir / "baostock_2024h1_manifest.json"
    content = csv_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(content).hexdigest()
    if digest != manifest["csv_sha256"]:
        raise ValueError("real sample checksum differs from its acquisition manifest")
    parsed = validate_csv(content)
    if parsed.row_count != manifest["row_count"] or parsed.symbol_count != manifest["symbol_count"]:
        raise ValueError("real sample dimensions differ from its acquisition manifest")

    with tempfile.TemporaryDirectory(prefix="fbl-real-check-") as temporary:
        root = Path(temporary)
        with patch.dict(os.environ, {"DATA_ROOT": str(root / "data"), "TASK_EXECUTION_MODE": "inline"}):
            engine = create_engine("sqlite:///:memory:")
            try:
                Base.metadata.create_all(engine)
                with Session(engine, expire_on_commit=False) as session:
                    dataset = import_csv(
                        session, content=content, source_filename=csv_path.name,
                        dataset_key="real_baostock", name="BaoStock 2024 H1 A股样本", data_root=root / "data",
                    )
                    publish_dataset_version(session, dataset)
                    results = {}
                    for factor in FACTORS:
                        run = create_research_run(session, {
                            "factor": factor,
                            "dataset_version_id": dataset.id,
                            "groups": 5,
                            "price_basis": "source_close",
                        })
                        run = execute_research_run(session, run.id)
                        result = next(item.content for item in run.artifacts if item.artifact_type == "metrics")
                        if run.status.value != "success" or result["coverage"] <= 0:
                            raise ValueError(f"factor did not produce valid observations: {factor}")
                        results[factor] = group_date_audit(result, factor)
                    comparison_check = validation_comparison_audit(session, dataset.id, digest)
                    raw_run = create_research_run(session, {
                        "factor": "momentum_20d", "dataset_version_id": dataset.id,
                        "groups": 5, "price_basis": "source_close",
                        "winsorize": False, "standardize": False,
                        "validation_start_date": VALIDATION_START,
                    })
                    raw_run = execute_research_run(session, raw_run.id)
                    raw_result = next(item.content for item in raw_run.artifacts if item.artifact_type == "metrics")
                    raw_ic_check = independent_momentum_ic_audit(content, raw_result["ic_series"])
            finally:
                engine.dispose()

    print(json.dumps({
        "csv_sha256": digest,
        "rows": parsed.row_count,
        "stocks": parsed.symbol_count,
        "start_date": parsed.start_date.isoformat(),
        "end_date": parsed.end_date.isoformat(),
        "observed_coverage": observed_coverage_audit(content),
        "calendar_quality": {key: parsed.report[key] for key in (
            "weekend_date_count", "weekend_row_count", "announced_closure_calendar_version",
            "announced_weekday_closure_date_count", "announced_weekday_closure_row_count",
            "announced_weekday_closure_dates", "calendar_uncovered_years")},
        "factor_checks": results,
        "validation_comparison": comparison_check,
        "independent_raw_momentum_ic": raw_ic_check,
        "note": "Software validation only; metrics are not investment conclusions.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
