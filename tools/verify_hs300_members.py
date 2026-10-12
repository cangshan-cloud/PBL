"""Verify a finalized local CSI 300 membership snapshot and summarize roster changes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from fetch_hs300_members import read_members
from probe_hs300_history import validate_calendar


def verify_snapshot(target: Path) -> dict[str, object]:
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("purpose") != "dated source-query evidence; constituent effective timing unverified":
        raise ValueError("unsupported snapshot purpose")
    expected_hashes = manifest["file_sha256"]
    expected_files = {"trade_calendar.csv", "hs300_members_queries.csv"}
    if set(expected_hashes) != expected_files:
        raise ValueError("unexpected top-level file hash set")
    contents = {}
    for name in sorted(expected_files):
        content = (target / name).read_bytes()
        if hashlib.sha256(content).hexdigest() != expected_hashes[name]:
            raise ValueError(f"hash mismatch: {name}")
        contents[name] = content

    calendar = list(csv.DictReader(io.StringIO(contents["trade_calendar.csv"].decode("utf-8"))))
    days = validate_calendar(calendar, manifest["requested_start"], manifest["requested_end"])
    if len(days) != manifest["trading_day_count"] or set(manifest["daily_roster_sha256"]) != set(days):
        raise ValueError("trading-day count or daily hash coverage mismatch")

    all_rows = []
    previous = None
    changes = []
    for day in days:
        content = (target / "daily_rosters" / f"{day}.csv").read_bytes()
        if hashlib.sha256(content).hexdigest() != manifest["daily_roster_sha256"][day]:
            raise ValueError(f"daily roster hash mismatch: {day}")
        rows = read_members(content, day)
        codes = {row["code"] for row in rows}
        if previous is not None and codes != previous:
            changes.append({"query_date": day, "removed_count": len(previous - codes), "added_count": len(codes - previous)})
        previous = codes
        all_rows.extend(rows)
    final_rows = list(csv.DictReader(io.StringIO(contents["hs300_members_queries.csv"].decode("utf-8"))))
    if final_rows != all_rows or len(all_rows) != manifest["member_row_count"]:
        raise ValueError("aggregate membership does not match daily checkpoints")
    return {
        "trading_day_count": len(days),
        "member_row_count": len(all_rows),
        "changed_query_days": changes,
        "caution": "Query-day changes do not independently prove index effective dates.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_snapshot(args.snapshot_dir.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
