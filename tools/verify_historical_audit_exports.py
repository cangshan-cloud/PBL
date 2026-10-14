"""Reconcile downloaded historical audit CSVs against a task reproducibility JSON.

This verifies export consistency, not the source market data or factor formula.
Uses only the Python standard library so teammates can run it without the API stack.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


UNLABELED_COLUMNS = ["factor", "date", "symbol", "factor_value", "next_market_date", "reason"]


def _csv_rows(path: Path, columns: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != columns:
            raise ValueError(f"{path.name}: CSV columns do not match audit schema")
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{path.name}: malformed CSV row")
    return rows


def verify_exports(bundle_path: Path, daily_path: Path, unlabeled_path: Path) -> dict[str, int]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    audit = (bundle.get("result") or {}).get("historical_audit")
    if not isinstance(audit, dict) or not audit:
        raise ValueError("reproducibility bundle has no historical audit")

    daily_fields = sorted({key for item in audit.values() for row in item["daily"] for key in row if key != "date"})
    daily_columns = ["factor", "date", *daily_fields]
    expected_daily = []
    expected_unlabeled = []
    for factor, item in sorted(audit.items()):
        daily = item["daily"]
        totals = item["totals"]
        if len({row["date"] for row in daily}) != len(daily):
            raise ValueError(f"{factor}: duplicate audit date")
        for field in set(daily_fields) | set(totals):
            if sum(int(row.get(field, 0)) for row in daily) != int(totals.get(field, 0)):
                raise ValueError(f"{factor}: daily totals disagree for {field}")
        unlabeled = item["unlabeled_signals"]
        if int(totals.get("factor_signal", 0)) != int(totals.get("valid_return", 0)) + len(unlabeled):
            raise ValueError(f"{factor}: unlabeled signal count disagrees with totals")
        expected_daily.extend(
            {"factor": factor, "date": row["date"], **{field: str(row.get(field, 0)) for field in daily_fields}}
            for row in daily
        )
        expected_unlabeled.extend(
            {"factor": factor, "date": row["date"], "symbol": row["symbol"],
             "factor_value": str(row["factor"]), "next_market_date": row["next_market_date"] or "",
             "reason": row["reason"]}
            for row in unlabeled
        )

    if _csv_rows(daily_path, daily_columns) != expected_daily:
        raise ValueError("daily CSV does not match reproducibility audit")
    if _csv_rows(unlabeled_path, UNLABELED_COLUMNS) != expected_unlabeled:
        raise ValueError("unlabeled CSV does not match reproducibility audit")
    return {"factors": len(audit), "daily_rows": len(expected_daily), "unlabeled_rows": len(expected_unlabeled)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reproducibility_json", type=Path)
    parser.add_argument("daily_csv", type=Path)
    parser.add_argument("unlabeled_csv", type=Path)
    args = parser.parse_args()
    try:
        result = verify_exports(args.reproducibility_json, args.daily_csv, args.unlabeled_csv)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.exit(1, f"审计导出核验失败：{exc}\n")
    print(f"审计导出核验通过：{result['factors']} 个因子，{result['daily_rows']} 行逐日审计，"
          f"{result['unlabeled_rows']} 条无标签信号")


if __name__ == "__main__":
    main()
