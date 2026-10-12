"""Fetch raw daily price and tradability fields for historical CSI 300 symbols.

Keeps source suspension/ST rows and missing values untouched. The result is
private source evidence, not yet a published research dataset.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import socket
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from fetch_hs300_members import write_atomic
from probe_hs300_history import SOURCE_URL, query_rows, render_csv, validate_calendar
from verify_hs300_members import verify_snapshot

ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "date", "code", "open", "high", "low", "close", "volume", "turn",
    "tradestatus", "isST", "adjustflag",
)


def finite_number(raw: str) -> Decimal | None:
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() else None


def empty_audit() -> dict[str, int]:
    return {
        "member_pairs": 0, "missing_row": 0, "normal": 0, "suspended": 0,
        "st": 0, "unknown_status": 0, "zero_volume": 0,
        "invalid_volume": 0, "missing_price": 0, "missing_turn": 0,
    }


def audit_member_days(rows: list[dict[str, str]], required: set[str], audit: dict[str, int]) -> None:
    by_day = {row["date"]: row for row in rows}
    audit["member_pairs"] += len(required)
    for day in required:
        row = by_day.get(day)
        if row is None:
            audit["missing_row"] += 1
        elif row["tradestatus"] == "" or row["isST"] == "":
            audit["unknown_status"] += 1
        elif row["tradestatus"] == "0":
            audit["suspended"] += 1
        elif row["isST"] == "1":
            audit["st"] += 1
        elif finite_number(row["volume"]) is None:
            audit["invalid_volume"] += 1
        elif finite_number(row["volume"]) <= 0:
            audit["zero_volume"] += 1
        elif finite_number(row["close"]) is None or finite_number(row["close"]) <= 0:
            audit["missing_price"] += 1
        elif finite_number(row["turn"]) is None:
            audit["missing_turn"] += 1
        else:
            audit["normal"] += 1


def normalize_rows(rows: list[dict[str, str]], code: str, allowed_days: set[str]) -> list[dict[str, str]]:
    normalized = []
    seen = set()
    for row in rows:
        if set(row) != set(FIELDS) or row["code"] != code:
            raise ValueError(f"{code}: unexpected source fields or security code")
        day = row["date"]
        if day not in allowed_days or day in seen:
            raise ValueError(f"{code}: out-of-calendar or duplicate date {day}")
        if row["adjustflag"] != "1":
            raise ValueError(f"{code} {day}: unexpected adjustment flag")
        if row["tradestatus"] not in {"0", "1", ""} or row["isST"] not in {"0", "1", ""}:
            raise ValueError(f"{code} {day}: invalid tradestatus/isST flag")
        seen.add(day)
        normalized.append({field: row[field] for field in FIELDS})
    return sorted(normalized, key=lambda row: row["date"])


def fetch_one(bs: object, code: str, start: str, end: str, allowed_days: set[str]) -> list[dict[str, str]]:
    result = bs.query_history_k_data_plus(
        code, ",".join(FIELDS), start_date=start, end_date=end, frequency="d", adjustflag="1"
    )
    if result.error_code != "0" or tuple(result.fields) != FIELDS:
        raise RuntimeError(f"{code}: BaoStock error/field mismatch: {result.error_code} {result.error_msg} {result.fields}")
    return normalize_rows(query_rows(result, set(FIELDS)), code, allowed_days)


def read_saved(content: bytes, code: str, allowed_days: set[str]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError(f"{code}: checkpoint field mismatch")
    rows = list(reader)
    if rows != normalize_rows(rows, code, allowed_days):
        raise ValueError(f"{code}: checkpoint order/content mismatch")
    return rows


def load_member_codes(snapshot: Path) -> tuple[list[str], dict[str, set[str]], str]:
    verify_snapshot(snapshot)
    membership_bytes = (snapshot / "hs300_members_queries.csv").read_bytes()
    by_code: dict[str, set[str]] = {}
    for row in csv.DictReader(io.StringIO(membership_bytes.decode("utf-8"))):
        by_code.setdefault(row["code"], set()).add(row["query_date"])
    return sorted(by_code), by_code, hashlib.sha256(membership_bytes).hexdigest()


def collect_prices(
    bs: object, member_snapshot: Path, target: Path, start: str, end: str,
    selected_codes: list[str] | None = None,
) -> dict[str, object]:
    all_codes, member_days, member_hash = load_member_codes(member_snapshot)
    codes = sorted(set(selected_codes)) if selected_codes is not None else all_codes
    if not codes or set(codes) - set(all_codes):
        raise ValueError("selected codes must be nonempty historical CSI 300 members")
    request = {
        "start": start, "end": end, "member_csv_sha256": member_hash,
        "codes": codes, "fields": list(FIELDS), "adjustflag": "1", "frequency": "d",
    }
    request_content = (json.dumps(request, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if (target / "manifest.json").exists():
        raise ValueError("price snapshot already finalized; choose a new output directory")
    target.mkdir(parents=True, exist_ok=True)
    request_path = target / "request.json"
    if request_path.exists():
        if request_path.read_bytes() != request_content:
            raise ValueError("checkpoint parameters do not match this request")
    elif any(target.iterdir()):
        raise ValueError("nonempty output directory has no compatible request")
    else:
        write_atomic(request_path, request_content)

    calendar_path = target / "trade_calendar.csv"
    if calendar_path.exists():
        calendar_content = calendar_path.read_bytes()
        calendar = list(csv.DictReader(io.StringIO(calendar_content.decode("utf-8"))))
    else:
        calendar = query_rows(bs.query_trade_dates(start_date=start, end_date=end), {"calendar_date", "is_trading_day"})
        calendar_content = render_csv(calendar, ("calendar_date", "is_trading_day"))
    trading_days = set(validate_calendar(calendar, start, end))
    if not calendar_path.exists():
        write_atomic(calendar_path, calendar_content)

    raw_dir = target / "symbols"
    raw_dir.mkdir(exist_ok=True)
    if {path.stem.replace("_", ".", 1) for path in raw_dir.glob("*.csv")} - set(codes):
        raise ValueError("checkpoint contains an unrequested symbol")
    hashes = {}
    row_count = 0
    audit = empty_audit()
    for code in codes:
        path = raw_dir / f"{code.replace('.', '_', 1)}.csv"
        if path.exists():
            content = path.read_bytes()
            rows = read_saved(content, code, trading_days)
        else:
            rows = fetch_one(bs, code, start, end, trading_days)
            content = render_csv(rows, FIELDS)
            write_atomic(path, content)
        hashes[code] = hashlib.sha256(content).hexdigest()
        row_count += len(rows)
        required = member_days[code] & trading_days
        audit_member_days(rows, required, audit)
        print(f"{code}: {len(rows)} rows", flush=True)

    manifest = {
        "purpose": "raw historical price/status evidence; not a published research bundle",
        "source": "BaoStock", "source_url": SOURCE_URL,
        "package_version": importlib.metadata.version("baostock"),
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "request": request,
        "request_sha256": hashlib.sha256(request_content).hexdigest(),
        "calendar_sha256": hashlib.sha256(calendar_content).hexdigest(),
        "symbol_sha256": hashes,
        "symbol_count": len(codes), "row_count": row_count,
        "member_day_audit": audit,
        "limitations": [
            "Missing rows/status are retained as unknown and must fail closed in research.",
            "BaoStock backward-adjusted prices may be revised; source_close only, no second adjustment.",
            "Market-data redistribution rights have not been established.",
        ],
    }
    write_atomic(target / "manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--members-dir", type=Path, default=ROOT / "data" / "real" / "hs300_members_2024")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "real" / "hs300_prices_2024")
    parser.add_argument("--start", default="2023-11-01")
    parser.add_argument("--end", default="2025-01-10")
    parser.add_argument("--codes", help="comma-separated historical members for a pilot; omit for full union")
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end < start or (end - start).days > 500:
        parser.error("date range must be ordered and at most 500 days")
    codes = args.codes.split(",") if args.codes else None
    try:
        import baostock as bs
    except ImportError as exc:
        raise SystemExit("Install optional dependency: python -m pip install baostock==0.9.4") from exc
    socket.setdefaulttimeout(15)
    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(f"BaoStock login failed: {login.error_code} {login.error_msg}")
    try:
        manifest = collect_prices(bs, args.members_dir.resolve(), args.output_dir.resolve(), args.start, args.end, codes)
    finally:
        bs.logout()
    print(json.dumps({"output_dir": str(args.output_dir.resolve()), "symbol_count": manifest["symbol_count"], "row_count": manifest["row_count"], "member_day_audit": manifest["member_day_audit"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
