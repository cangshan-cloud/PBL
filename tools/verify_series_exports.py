"""Reconcile browser-downloaded daily series and coverage CSVs with one reproducibility JSON.

This is a read-only export check, not an independent factor or market-data audit.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_reproducibility_export import load_verified_export


IC_FIELDS = ("run_id", "date", "ic", "rank_ic")
LONG_SHORT_FIELDS = (
    "run_id", "date", "gross_return", "gross_nav", "two_side_turnover", "cost",
    "net_return", "net_nav", "transaction_cost_bps",
)
GROUP_NAV_FIELDS = ("run_id", "group", "date", "nav")
DAILY_COVERAGE_FIELDS = (
    "run_id", "date", "candidate_symbols", "eligible_symbols", "coverage_ratio",
    "excluded_symbols", "ic_status", "group_status",
)


def _rows(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(fields):
            raise ValueError(f"{path.name}: unexpected CSV columns")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{path.name}: malformed CSV row")
    return rows


def _same_cell(actual: str, expected: object) -> bool:
    if expected is None:
        return actual == ""
    if isinstance(expected, str):
        return actual == expected
    if isinstance(expected, bool) or not isinstance(expected, (int, float)):
        return False
    try:
        value = float(actual)
    except ValueError:
        return False
    return math.isfinite(value) and value == float(expected)


def _verify(path: Path, fields: tuple[str, ...], expected: list[dict[str, object]]) -> int:
    actual = _rows(path, fields)
    if len(actual) != len(expected):
        raise ValueError(f"{path.name}: row count differs from reproducibility result")
    for index, (row, source) in enumerate(zip(actual, expected, strict=True), start=2):
        for field in fields:
            if field not in source or not _same_cell(row[field], source[field]):
                raise ValueError(f"{path.name}:{index}: {field} differs from reproducibility result")
    return len(actual)


def verify_series_exports(bundle_path: Path, ic_path: Path | None = None,
                          long_short_path: Path | None = None,
                          group_nav_path: Path | None = None,
                          daily_coverage_path: Path | None = None) -> dict[str, int]:
    if all(path is None for path in (ic_path, long_short_path, group_nav_path, daily_coverage_path)):
        raise ValueError("provide at least one series CSV")
    bundle = load_verified_export(bundle_path)
    task = bundle.get("task")
    run_id = task.get("id") if isinstance(task, dict) else None
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("reproducibility bundle has no Run ID")
    result = bundle["result"]
    summary = {}
    if ic_path is not None:
        series = result.get("ic_series")
        if not isinstance(series, list) or any(not isinstance(row, dict) for row in series):
            raise ValueError("reproducibility result has no valid IC series")
        expected = [dict(run_id=run_id, date=row["date"], ic=row["ic"],
                         rank_ic=row["rank_ic"]) for row in series]
        summary["ic_rows"] = _verify(ic_path, IC_FIELDS, expected)
    if long_short_path is not None:
        series = result.get("long_short_series")
        cost_bps = result.get("transaction_cost_bps")
        if not isinstance(series, list) or any(not isinstance(row, dict) for row in series):
            raise ValueError("reproducibility result has no valid long-short series")
        if isinstance(cost_bps, bool) or not isinstance(cost_bps, (int, float)):
            raise ValueError("reproducibility result has no transaction cost parameter")
        expected = [dict(run_id=run_id, date=row["date"], gross_return=row["return"],
                         gross_nav=row["nav"], two_side_turnover=row["turnover"],
                         cost=row["cost"], net_return=row["net_return"],
                         net_nav=row["net_nav"], transaction_cost_bps=cost_bps) for row in series]
        summary["long_short_rows"] = _verify(long_short_path, LONG_SHORT_FIELDS, expected)
    if group_nav_path is not None:
        groups = result.get("group_nav")
        if not isinstance(groups, list) or any(not isinstance(item, dict) or
                                              not isinstance(item.get("points"), list) or
                                              any(not isinstance(point, dict) for point in item["points"])
                                              for item in groups):
            raise ValueError("reproducibility result has no valid group NAV series")
        expected = [dict(run_id=run_id, group=item["group"], date=point["date"], nav=point["nav"])
                    for item in groups for point in item["points"]]
        summary["group_nav_rows"] = _verify(group_nav_path, GROUP_NAV_FIELDS, expected)
    if daily_coverage_path is not None:
        series = result.get("daily_coverage")
        if not isinstance(series, list) or any(not isinstance(row, dict) for row in series):
            raise ValueError("reproducibility result has no valid daily coverage series")
        expected = [dict(run_id=run_id, date=row["date"],
                         candidate_symbols=row.get("candidate_symbols"),
                         eligible_symbols=row["eligible_symbols"],
                         coverage_ratio=row.get("coverage_ratio"),
                         excluded_symbols=row.get("excluded_symbols"),
                         ic_status=row["ic_status"], group_status=row["group_status"])
                    for row in series]
        summary["daily_coverage_rows"] = _verify(daily_coverage_path, DAILY_COVERAGE_FIELDS, expected)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reproducibility_json", type=Path)
    parser.add_argument("--ic-csv", type=Path)
    parser.add_argument("--long-short-csv", type=Path)
    parser.add_argument("--group-nav-csv", type=Path)
    parser.add_argument("--daily-coverage-csv", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify_series_exports(args.reproducibility_json, args.ic_csv,
                                               args.long_short_csv, args.group_nav_csv,
                                               args.daily_coverage_csv), ensure_ascii=False))
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.exit(1, f"series export verification failed: {exc}\n")


if __name__ == "__main__":
    main()
