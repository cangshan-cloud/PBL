"""Fetch a small, fixed BaoStock A-share sample for local course research.

The output is intentionally gitignored: the package license does not establish
redistribution rights for the market data returned by the service.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import io
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.datasets import validate_csv  # noqa: E402


START_DATE = "2024-01-01"
END_DATE = "2024-06-30"
SYMBOLS = (
    "sh.600000", "sh.600276", "sh.600519", "sh.601318", "sh.601398",
    "sz.000001", "sz.000333", "sz.000858", "sz.002415", "sz.300750",
)
SOURCE_FIELDS = (
    "date", "code", "open", "high", "low", "close", "volume", "amount",
    "turn", "tradestatus", "peTTM", "adjustflag",
)
OUTPUT_FIELDS = (
    "trade_date", "symbol", "open", "high", "low", "close", "volume",
    "amount", "turnover_rate", "pe",
)
SOURCE_URL = "https://www.baostock.com/mainContent?file=pythonAPI.md"


def normalize_row(row: dict[str, str], expected_code: str) -> dict[str, str]:
    if row["code"] != expected_code:
        raise ValueError(f"unexpected security code: {row['code']}")
    if row["adjustflag"] != "1":
        raise ValueError(f"unexpected adjustment flag for {expected_code} {row['date']}")
    if row["tradestatus"] != "1":
        raise ValueError(f"suspended/non-trading row: {expected_code} {row['date']}")
    for field in ("open", "high", "low", "close", "volume", "amount"):
        if not row[field].strip():
            raise ValueError(f"missing {field}: {expected_code} {row['date']}")
    market, code = row["code"].split(".", 1)
    if market not in {"sh", "sz"} or len(code) != 6 or not code.isdigit():
        raise ValueError(f"invalid A-share code: {row['code']}")
    return {
        "trade_date": row["date"],
        "symbol": f"{code}.{'SH' if market == 'sh' else 'SZ'}",
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "volume": row["volume"],
        "amount": row["amount"],
        "turnover_rate": row["turn"],
        "pe": row["peTTM"],
    }


def fetch_rows(bs: object) -> list[dict[str, str]]:
    rows = []
    for code in SYMBOLS:
        query = bs.query_history_k_data_plus(
            code, ",".join(SOURCE_FIELDS), start_date=START_DATE, end_date=END_DATE,
            frequency="d", adjustflag="1",
        )
        if query.error_code != "0":
            raise RuntimeError(f"BaoStock query failed for {code}: {query.error_code} {query.error_msg}")
        if tuple(query.fields) != SOURCE_FIELDS:
            raise ValueError(f"BaoStock returned unexpected fields for {code}: {query.fields}")
        count = 0
        while query.next():
            rows.append(normalize_row(dict(zip(query.fields, query.get_row_data(), strict=True)), code))
            count += 1
        if not count:
            raise ValueError(f"BaoStock returned no rows for {code}")
        print(f"{code}: {count} rows")
    return sorted(rows, key=lambda row: (row["trade_date"], row["symbol"]))


def render_csv(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "real")
    parser.add_argument("--refresh", action="store_true", help="replace an existing local snapshot after re-fetching")
    args = parser.parse_args()
    target_dir = args.output_dir.resolve()
    target = target_dir / "baostock_2024h1_daily.csv"
    manifest_path = target_dir / "baostock_2024h1_manifest.json"
    if not args.refresh and (target.exists() or manifest_path.exists()):
        raise SystemExit("local snapshot already exists; pass --refresh only if you intend to replace it")
    try:
        import baostock as bs
    except ImportError as exc:
        raise SystemExit("Install the optional acquisition dependency: python -m pip install baostock==0.9.4") from exc

    socket.setdefaulttimeout(15)
    login = bs.login()
    if login.error_code != "0":
        raise RuntimeError(f"BaoStock login failed: {login.error_code} {login.error_msg}")
    try:
        rows = fetch_rows(bs)
    finally:
        bs.logout()

    content = render_csv(rows)
    parsed = validate_csv(content)
    target_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(content).hexdigest()
    manifest = {
        "source": "BaoStock historical A-share K-line API",
        "source_url": SOURCE_URL,
        "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
        "baostock_package_version": importlib.metadata.version("baostock"),
        "query_method": "query_history_k_data_plus",
        "symbols": list(SYMBOLS),
        "start_date": START_DATE,
        "end_date": END_DATE,
        "frequency": "d",
        "adjustflag": "1 (BaoStock backward adjusted, percentage-change method)",
        "source_fields": list(SOURCE_FIELDS),
        "output_fields": list(OUTPUT_FIELDS),
        "filters": "Reject non-trading/suspended rows; no forward-fill or synthetic prices",
        "row_count": parsed.row_count,
        "symbol_count": parsed.symbol_count,
        "observed_start_date": parsed.start_date.isoformat(),
        "observed_end_date": parsed.end_date.isoformat(),
        "csv_sha256": digest,
        "limitations": [
            "Fixed manually selected stocks create survivorship/selection bias.",
            "Prices use BaoStock's backward-adjustment method; do not multiply by another adjustment factor.",
            "peTTM point-in-time disclosure alignment has not been independently verified.",
            "BaoStock software license does not establish market-data redistribution rights.",
        ],
    }
    target.write_bytes(content)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"validated {parsed.row_count} rows / {parsed.symbol_count} stocks; SHA-256 {digest}")
    print(f"CSV: {target}")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
