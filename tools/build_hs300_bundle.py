"""Seal verified CSI 300 source components into a private, hash-addressed bundle.

This is an offline research-input bundle. Platform dataset registration and
historical-universe factor execution are separate later steps.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from verify_hs300_members import verify_snapshot
from verify_hs300_prices import verify_prices

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
RESEARCH_START = "2024-01-01"
RESEARCH_END = "2024-12-31"


def sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def validate_sources(members_dir: Path, prices_dir: Path) -> tuple[dict, dict, dict]:
    member_result = verify_snapshot(members_dir)
    price_result = verify_prices(members_dir, prices_dir)
    member_manifest = json.loads((members_dir / "manifest.json").read_text(encoding="utf-8"))
    price_manifest = json.loads((prices_dir / "manifest.json").read_text(encoding="utf-8"))
    if (member_manifest["requested_start"], member_manifest["requested_end"]) != (RESEARCH_START, RESEARCH_END):
        raise ValueError("membership source must cover exactly calendar year 2024")
    if price_manifest["symbol_count"] != len(price_manifest["request"]["codes"]):
        raise ValueError("price source symbol count mismatch")
    if price_manifest["member_day_audit"]["member_pairs"] != member_result["member_row_count"]:
        raise ValueError("price snapshot is a pilot or has incomplete member-day coverage")
    if price_manifest["member_day_audit"]["missing_row"] or price_manifest["member_day_audit"]["unknown_status"]:
        raise ValueError("missing member row or unknown trading/ST status")
    if price_result["member_day_audit"] != price_manifest["member_day_audit"]:
        raise ValueError("price audit mismatch")
    with (prices_dir / "trade_calendar.csv").open(newline="", encoding="utf-8") as source:
        trading_days = [row["calendar_date"] for row in csv.DictReader(source) if row["is_trading_day"] == "1"]
    with (members_dir / "trade_calendar.csv").open(newline="", encoding="utf-8") as source:
        member_trading_days = [row["calendar_date"] for row in csv.DictReader(source) if row["is_trading_day"] == "1"]
    if [day for day in trading_days if RESEARCH_START <= day <= RESEARCH_END] != member_trading_days:
        raise ValueError("price and member trading calendars disagree in 2024")
    pre_days = [day for day in trading_days if day < RESEARCH_START]
    post_days = [day for day in trading_days if day > RESEARCH_END]
    if len(pre_days) < 20 or not post_days:
        raise ValueError("price calendar lacks 20 warm-up days or first post-2024 label day")
    if price_manifest["request"]["start"] > pre_days[0] or price_manifest["request"]["end"] < post_days[0]:
        raise ValueError("price request does not span warm-up/label dates")
    return member_result, price_result, price_manifest


def copy_component(source: Path, destination: Path, staged: Path, hashes: dict[str, str]) -> None:
    target = staged / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    hashes[destination.as_posix()] = sha256_file(target)


def build_bundle(members_dir: Path, prices_dir: Path, output_root: Path) -> tuple[Path, dict]:
    member_result, price_result, price_manifest = validate_sources(members_dir, prices_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".hs300_stage_", dir=output_root) as stage_name:
        staged = Path(stage_name)
        hashes: dict[str, str] = {}
        components = (
            (members_dir / "manifest.json", Path("members_source/manifest.json")),
            (members_dir / "trade_calendar.csv", Path("members_source/trade_calendar.csv")),
            (members_dir / "hs300_members_queries.csv", Path("members_source/hs300_members_queries.csv")),
            (prices_dir / "manifest.json", Path("prices_source/manifest.json")),
            (prices_dir / "request.json", Path("prices_source/request.json")),
            (prices_dir / "trade_calendar.csv", Path("prices_source/trade_calendar.csv")),
        )
        for source, destination in components:
            copy_component(source, destination, staged, hashes)
        member_manifest = json.loads((members_dir / "manifest.json").read_text(encoding="utf-8"))
        for day in member_manifest["daily_roster_sha256"]:
            filename = f"{day}.csv"
            copy_component(members_dir / "daily_rosters" / filename, Path("members_source/daily_rosters") / filename, staged, hashes)
        for code in price_manifest["request"]["codes"]:
            filename = f"{code.replace('.', '_', 1)}.csv"
            copy_component(prices_dir / "symbols" / filename, Path("prices_source/symbols") / filename, staged, hashes)

        identity = {
            "schema_version": SCHEMA_VERSION,
            "research_start": RESEARCH_START,
            "research_end": RESEARCH_END,
            "price_basis": "source_close",
            "price_adjustflag": "1",
            "factor_windows": {"momentum": 20, "reversal": 5, "volatility": 20, "turnover": 20},
            "file_sha256": hashes,
        }
        version = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        manifest = {
            **identity,
            "bundle_id": f"hs300_2024_{version[:16]}",
            "version_sha256": version,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "member_trading_days": member_result["trading_day_count"],
            "member_rows": member_result["member_row_count"],
            "price_symbols": price_result["symbol_count"],
            "price_rows": price_result["row_count"],
            "member_day_audit": price_result["member_day_audit"],
            "publication_status": "offline_sealed_not_registered",
            "limitations": [
                "One official constituent adjustment was independently checked; not every maintenance event.",
                "ST historical source status was not independently checked.",
                "Backward-adjusted source prices may be revised after acquisition.",
                "Not an executable trading return or a claim of fully eliminated bias.",
            ],
        }
        (staged / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        target = output_root / manifest["bundle_id"]
        if target.exists():
            raise FileExistsError(f"bundle already exists: {target}")
        os.rename(staged, target)
    return target, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--members-dir", type=Path, default=ROOT / "data" / "real" / "hs300_members_2024")
    parser.add_argument("--prices-dir", type=Path, default=ROOT / "data" / "real" / "hs300_prices_2024")
    parser.add_argument("--output-root", type=Path, default=ROOT / "data" / "real" / "bundles")
    args = parser.parse_args()
    path, manifest = build_bundle(args.members_dir.resolve(), args.prices_dir.resolve(), args.output_root.resolve())
    print(json.dumps({"bundle_dir": str(path), "bundle_id": manifest["bundle_id"], "file_count": len(manifest["file_sha256"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
