"""Verify a private raw CSI 300 price/status snapshot against its member source."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from fetch_hs300_prices import FIELDS, audit_member_days, empty_audit, load_member_codes, read_saved
from probe_hs300_history import validate_calendar


def verify_prices(member_snapshot: Path, target: Path) -> dict[str, object]:
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("purpose") != "raw historical price/status evidence; not a published research bundle":
        raise ValueError("unsupported price snapshot purpose")
    request_content = (target / "request.json").read_bytes()
    if hashlib.sha256(request_content).hexdigest() != manifest["request_sha256"]:
        raise ValueError("request hash mismatch")
    request = json.loads(request_content)
    if request != manifest["request"] or tuple(request["fields"]) != FIELDS:
        raise ValueError("request content/fields mismatch")
    all_codes, member_days, member_hash = load_member_codes(member_snapshot)
    codes = request["codes"]
    if codes != sorted(set(codes)) or set(codes) - set(all_codes) or request["member_csv_sha256"] != member_hash:
        raise ValueError("source member version or selected codes mismatch")
    calendar_content = (target / "trade_calendar.csv").read_bytes()
    if hashlib.sha256(calendar_content).hexdigest() != manifest["calendar_sha256"]:
        raise ValueError("calendar hash mismatch")
    calendar = list(csv.DictReader(io.StringIO(calendar_content.decode("utf-8"))))
    trading_days = set(validate_calendar(calendar, request["start"], request["end"]))
    if set(manifest["symbol_sha256"]) != set(codes):
        raise ValueError("symbol hash coverage mismatch")
    expected_paths = {f"{code.replace('.', '_', 1)}.csv" for code in codes}
    observed_paths = {path.name for path in (target / "symbols").glob("*.csv")}
    if observed_paths != expected_paths:
        raise ValueError("symbol file set does not match request")
    audit = empty_audit()
    count = 0
    for code in codes:
        content = (target / "symbols" / f"{code.replace('.', '_', 1)}.csv").read_bytes()
        if hashlib.sha256(content).hexdigest() != manifest["symbol_sha256"][code]:
            raise ValueError(f"symbol hash mismatch: {code}")
        rows = read_saved(content, code, trading_days)
        count += len(rows)
        audit_member_days(rows, member_days[code] & trading_days, audit)
    if count != manifest["row_count"] or len(codes) != manifest["symbol_count"] or audit != manifest["member_day_audit"]:
        raise ValueError("row count, symbol count, or member-day audit mismatch")
    if sum(value for key, value in audit.items() if key != "member_pairs") != audit["member_pairs"]:
        raise ValueError("member-day audit does not reconcile")
    return {"symbol_count": len(codes), "row_count": count, "member_day_audit": audit}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("price_dir", type=Path)
    parser.add_argument("--members-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify_prices(args.members_dir.resolve(), args.price_dir.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
