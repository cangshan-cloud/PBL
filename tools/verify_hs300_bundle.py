"""Verify every file and source invariant in a sealed CSI 300 research bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_hs300_bundle import RESEARCH_END, RESEARCH_START, SCHEMA_VERSION, sha256_file, validate_sources


def verify_bundle(bundle_dir: Path) -> dict[str, object]:
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported bundle schema version")
    if (manifest.get("research_start"), manifest.get("research_end")) != (RESEARCH_START, RESEARCH_END):
        raise ValueError("unsupported research date range")
    if manifest.get("price_basis") != "source_close" or manifest.get("price_adjustflag") != "1":
        raise ValueError("unexpected price basis/adjustment")
    expected_windows = {"momentum": 20, "reversal": 5, "volatility": 20, "turnover": 20}
    if manifest.get("factor_windows") != expected_windows:
        raise ValueError("unexpected factor windows")
    file_hashes = manifest["file_sha256"]
    if not file_hashes or any(Path(name).is_absolute() or ".." in Path(name).parts for name in file_hashes):
        raise ValueError("unsafe or empty bundle file list")
    actual_files = set()
    for path in bundle_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"bundle contains symlink: {path}")
        if path.is_file() and path != bundle_dir / "manifest.json":
            actual_files.add(path.relative_to(bundle_dir).as_posix())
    if actual_files != set(file_hashes):
        raise ValueError("bundle file set does not match manifest")
    for name, expected in file_hashes.items():
        if sha256_file(bundle_dir / name) != expected:
            raise ValueError(f"bundle hash mismatch: {name}")
    identity = {
        key: manifest[key] for key in (
            "schema_version", "research_start", "research_end", "price_basis",
            "price_adjustflag", "factor_windows", "file_sha256",
        )
    }
    version = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if manifest.get("version_sha256") != version or manifest.get("bundle_id") != f"hs300_2024_{version[:16]}":
        raise ValueError("bundle content identity mismatch")
    if bundle_dir.name != manifest["bundle_id"]:
        raise ValueError("bundle directory name does not match content identity")
    members, prices, _ = validate_sources(bundle_dir / "members_source", bundle_dir / "prices_source")
    if (
        manifest.get("member_trading_days") != members["trading_day_count"]
        or manifest.get("member_rows") != members["member_row_count"]
        or manifest.get("price_symbols") != prices["symbol_count"]
        or manifest.get("price_rows") != prices["row_count"]
        or manifest.get("member_day_audit") != prices["member_day_audit"]
    ):
        raise ValueError("bundle summary does not match source components")
    return {
        "bundle_id": manifest["bundle_id"],
        "verified_files": len(file_hashes),
        "member_trading_days": members["trading_day_count"],
        "member_rows": members["member_row_count"],
        "price_symbols": prices["symbol_count"],
        "price_rows": prices["row_count"],
        "member_day_audit": prices["member_day_audit"],
        "publication_status": manifest["publication_status"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_bundle(args.bundle_dir.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
