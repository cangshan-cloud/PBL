"""Probe BaoStock's dated CSI 300 roster and trading calendar (private local output).

This is a source-feasibility probe, not an approved point-in-time dataset.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import socket
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://github.com/zxygithub/baostock/blob/master/docs/pythonAPI.md"


def query_rows(result: object, required: set[str]) -> list[dict[str, str]]:
    if result.error_code != "0":
        raise RuntimeError(f"BaoStock query failed: {result.error_code} {result.error_msg}")
    fields = tuple(result.fields)
    if not required.issubset(fields):
        raise ValueError(f"BaoStock fields missing {sorted(required - set(fields))}: {fields}")
    rows = []
    while result.next():
        values = result.get_row_data()
        if len(values) != len(fields):
            raise ValueError("BaoStock field/value length mismatch")
        rows.append(dict(zip(fields, values, strict=True)))
    return rows


def validate_calendar(calendar: list[dict[str, str]], start: str, end: str) -> list[str]:
    expected = [(date.fromisoformat(row["calendar_date"]), row["is_trading_day"]) for row in calendar]
    if not expected or len({day for day, _ in expected}) != len(expected):
        raise ValueError("missing or duplicate calendar dates")
    if any(flag not in {"0", "1"} for _, flag in expected):
        raise ValueError("invalid trading-day flag")
    requested = [date.fromisoformat(start) + timedelta(days=offset) for offset in range((date.fromisoformat(end) - date.fromisoformat(start)).days + 1)]
    if [day for day, _ in expected] != requested:
        raise ValueError("calendar does not cover every requested date in order")

    return [day.isoformat() for day, flag in expected if flag == "1"]


def normalize_members(rows: list[dict[str, str]], day_text: str) -> list[dict[str, str]]:
    codes = [row["code"] for row in rows]
    if len(codes) != 300 or len(set(codes)) != 300:
        raise ValueError(f"{day_text}: expected 300 unique CSI 300 members, got {len(codes)}")
    members = []
    for row in rows:
        code = row["code"]
        market, sep, number = code.partition(".")
        if sep != "." or market not in {"sh", "sz"} or len(number) != 6 or not number.isdigit():
            raise ValueError(f"{day_text}: unexpected member code {code}")
        update_date = row["updateDate"]
        if not update_date or date.fromisoformat(update_date) > date.fromisoformat(day_text):
            raise ValueError(f"{day_text}: invalid future/missing updateDate for {code}")
        members.append({"query_date": day_text, "code": code, "update_date": update_date})
    return sorted(members, key=lambda row: row["code"])


def collect(bs: object, start: str, end: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    calendar = query_rows(
        bs.query_trade_dates(start_date=start, end_date=end),
        {"calendar_date", "is_trading_day"},
    )
    trading_days = validate_calendar(calendar, start, end)
    members = []
    for day_text in trading_days:
        rows = query_rows(bs.query_hs300_stocks(day_text), {"code", "updateDate"})
        members.extend(normalize_members(rows, day_text))
    return calendar, members


def render_csv(rows: list[dict[str, str]], fields: tuple[str, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2024-06-28")
    parser.add_argument("--end", default="2024-07-01")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "real" / "hs300_probe")
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end < start or (end - start).days > 370:
        parser.error("date range must be ordered and at most 370 days")
    target = args.output_dir.resolve()
    if target.exists() and any(target.iterdir()):
        parser.error("output directory must be empty; use a new path to preserve earlier evidence")
    try:
        import baostock as bs
    except ImportError as exc:
        raise SystemExit("Install optional dependency: python -m pip install baostock==0.9.4") from exc
    socket.setdefaulttimeout(15)
    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(f"BaoStock login failed: {login.error_code} {login.error_msg}")
    try:
        calendar, members = collect(bs, args.start, args.end)
    finally:
        bs.logout()
    files = {
        "trade_calendar.csv": render_csv(calendar, ("calendar_date", "is_trading_day")),
        "hs300_members_queries.csv": render_csv(members, ("query_date", "code", "update_date")),
    }
    trading_days = [row["calendar_date"] for row in calendar if row["is_trading_day"] == "1"]
    manifest = {
        "purpose": "source-feasibility probe only; membership effective dates unverified",
        "source": "BaoStock",
        "source_url": SOURCE_URL,
        "package_version": importlib.metadata.version("baostock"),
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "queries": ["query_trade_dates", "query_hs300_stocks"],
        "requested_start": args.start,
        "requested_end": args.end,
        "trading_days": trading_days,
        "member_rows": len(members),
        "file_sha256": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
        "limitations": [
            "The query date and updateDate do not alone prove constituent effective timing.",
            "Prices, suspension, and ST status are not included in this probe.",
            "Market-data redistribution rights have not been established; keep raw files private.",
        ],
    }
    target.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (target / name).write_bytes(content)
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_dir": str(target), "trading_days": len(trading_days), "member_rows": len(members)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
