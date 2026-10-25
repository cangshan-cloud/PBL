"""Check a downloaded research snapshot and optional HTML report without the API stack.

This checks export consistency only; it does not rerun factors or authenticate market data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_verified_export(bundle_path: Path, report_path: Path | None = None) -> dict:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(bundle, dict) or type(bundle.get("schema_version")) is not int or bundle["schema_version"] != 1:
        raise ValueError("unsupported reproducibility bundle schema")
    result = bundle.get("result")
    digest = bundle.get("result_sha256")
    if not isinstance(result, dict) or not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise ValueError("reproducibility bundle has no valid result checksum")
    canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != digest:
        raise ValueError("reproducibility result checksum mismatch")
    if report_path is not None:
        report_digest = bundle.get("report_sha256")
        if not isinstance(report_digest, str) or not SHA256.fullmatch(report_digest):
            raise ValueError("reproducibility bundle has no valid report checksum")
        if hashlib.sha256(report_path.read_bytes()).hexdigest() != report_digest:
            raise ValueError("report checksum mismatch")
    return bundle


def verify_export(bundle_path: Path, report_path: Path | None = None) -> dict[str, str | bool]:
    load_verified_export(bundle_path, report_path)
    summary: dict[str, str | bool] = {"result_verified": True}
    if report_path is not None:
        summary["report_verified"] = True
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reproducibility_json", type=Path)
    parser.add_argument("--report-html", type=Path, help="Downloaded HTML report to check against report_sha256")
    args = parser.parse_args()
    try:
        print(json.dumps(verify_export(args.reproducibility_json, args.report_html), ensure_ascii=False))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"verification failed: {exc}\n")


if __name__ == "__main__":
    main()
