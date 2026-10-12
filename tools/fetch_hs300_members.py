"""Fetch dated CSI 300 membership with resumable private checkpoints.

The result is source evidence, not an independently verified effective-date universe.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import os
import socket
from datetime import date, datetime, timezone
from pathlib import Path

from probe_hs300_history import SOURCE_URL, normalize_members, query_rows, render_csv, validate_calendar

ROOT = Path(__file__).resolve().parents[1]
MEMBER_FIELDS = ("query_date", "code", "update_date")
CALENDAR_FIELDS = ("calendar_date", "is_trading_day")


def write_atomic(path: Path, content: bytes) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def read_members(content: bytes, day: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(io.StringIO(content.decode("utf-8"))))
    if not rows or set(rows[0]) != set(MEMBER_FIELDS) or any(row["query_date"] != day for row in rows):
        raise ValueError(f"{day}: invalid saved checkpoint schema/date")
    normalized = normalize_members(
        [{"code": row["code"], "updateDate": row["update_date"]} for row in rows], day
    )
    if rows != normalized:
        raise ValueError(f"{day}: checkpoint order/content is not canonical")
    return rows


def fetch_one(bs: object, day: str) -> list[dict[str, str]]:
    rows = query_rows(bs.query_hs300_stocks(day), {"code", "updateDate"})
    return normalize_members(rows, day)


def collect_with_checkpoints(bs: object, start: str, end: str, target: Path) -> dict[str, object]:
    if (target / "manifest.json").exists():
        raise ValueError("snapshot already finalized; choose a new output directory")
    target.mkdir(parents=True, exist_ok=True)
    calendar_path = target / "trade_calendar.csv"
    if calendar_path.exists():
        calendar_content = calendar_path.read_bytes()
        calendar = list(csv.DictReader(io.StringIO(calendar_content.decode("utf-8"))))
    else:
        calendar = query_rows(bs.query_trade_dates(start_date=start, end_date=end), set(CALENDAR_FIELDS))
        calendar_content = render_csv(calendar, CALENDAR_FIELDS)
    trading_days = validate_calendar(calendar, start, end)
    if not calendar_path.exists():
        write_atomic(calendar_path, calendar_content)

    roster_dir = target / "daily_rosters"
    roster_dir.mkdir(exist_ok=True)
    saved_days = {path.stem for path in roster_dir.glob("*.csv")}
    if saved_days - set(trading_days):
        raise ValueError(f"out-of-range checkpoints: {sorted(saved_days - set(trading_days))[:3]}")
    members: list[dict[str, str]] = []
    daily_hashes = {}
    for day in trading_days:
        path = roster_dir / f"{day}.csv"
        if path.exists():
            content = path.read_bytes()
            rows = read_members(content, day)
        else:
            rows = fetch_one(bs, day)
            content = render_csv(rows, MEMBER_FIELDS)
            write_atomic(path, content)
        members.extend(rows)
        daily_hashes[day] = hashlib.sha256(content).hexdigest()
        print(f"{day}: {len(rows)} members", flush=True)

    member_content = render_csv(members, MEMBER_FIELDS)
    manifest = {
        "purpose": "dated source-query evidence; constituent effective timing unverified",
        "source": "BaoStock",
        "source_url": SOURCE_URL,
        "package_version": importlib.metadata.version("baostock"),
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_start": start,
        "requested_end": end,
        "queries": ["query_trade_dates", "query_hs300_stocks"],
        "trading_day_count": len(trading_days),
        "member_row_count": len(members),
        "file_sha256": {
            "trade_calendar.csv": hashlib.sha256(calendar_content).hexdigest(),
            "hs300_members_queries.csv": hashlib.sha256(member_content).hexdigest(),
        },
        "daily_roster_sha256": daily_hashes,
        "limitations": [
            "The query date and updateDate do not alone prove index effective timing.",
            "Prices, suspension, and ST status are not included.",
            "Raw market-data redistribution rights have not been established.",
        ],
    }
    write_atomic(target / "hs300_members_queries.csv", member_content)
    write_atomic(target / "manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "real" / "hs300_members_2024")
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end < start or (end - start).days > 370:
        parser.error("date range must be ordered and at most 370 days")
    target = args.output_dir.resolve()
    if target.exists() and any(target.iterdir()) and not (target / "trade_calendar.csv").exists():
        parser.error("nonempty output directory is not a compatible checkpoint")
    try:
        import baostock as bs
    except ImportError as exc:
        raise SystemExit("Install optional dependency: python -m pip install baostock==0.9.4") from exc
    socket.setdefaulttimeout(15)
    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(f"BaoStock login failed: {login.error_code} {login.error_msg}")
    try:
        manifest = collect_with_checkpoints(bs, args.start, args.end, target)
    finally:
        bs.logout()
    print(json.dumps({"output_dir": str(target), "trading_day_count": manifest["trading_day_count"], "member_row_count": manifest["member_row_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
