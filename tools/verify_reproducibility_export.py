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


def load_verified_export(bundle_path: Path, report_path: Path | None = None, *, require_v2: bool = False) -> dict:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(bundle, dict) or type(bundle.get("schema_version")) is not int or bundle["schema_version"] not in {1, 2}:
        raise ValueError("unsupported reproducibility bundle schema")
    if require_v2 and bundle["schema_version"] != 2:
        raise ValueError("reproducibility bundle is not schema v2")
    result = bundle.get("result")
    digest = bundle.get("result_sha256")
    if result is None and bundle["schema_version"] == 2:
        task = bundle.get("task")
        if (not isinstance(task, dict) or not isinstance(task.get("status"), str)
                or task["status"] not in {"pending", "running", "failed", "cancelled"}
                or digest is not None or bundle.get("report_sha256") is not None):
            raise ValueError("incomplete reproducibility bundle has inconsistent task status or checksums")
    else:
        if not isinstance(result, dict) or not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError("reproducibility bundle has no valid result checksum")
        canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != digest:
            raise ValueError("reproducibility result checksum mismatch")
    if bundle["schema_version"] == 2:
        bundle_digest = bundle.get("bundle_sha256")
        if not isinstance(bundle_digest, str) or not SHA256.fullmatch(bundle_digest):
            raise ValueError("reproducibility bundle has no valid bundle checksum")
        unsigned = {key: value for key, value in bundle.items() if key != "bundle_sha256"}
        canonical_bundle = json.dumps(unsigned, ensure_ascii=False, sort_keys=True,
                                      separators=(",", ":"), allow_nan=False)
        if hashlib.sha256(canonical_bundle.encode("utf-8")).hexdigest() != bundle_digest:
            raise ValueError("reproducibility bundle checksum mismatch")
    if report_path is not None:
        report_digest = bundle.get("report_sha256")
        if not isinstance(report_digest, str) or not SHA256.fullmatch(report_digest):
            raise ValueError("reproducibility bundle has no valid report checksum")
        if hashlib.sha256(report_path.read_bytes()).hexdigest() != report_digest:
            raise ValueError("report checksum mismatch")
    return bundle


def verify_export(bundle_path: Path, report_path: Path | None = None, *, require_v2: bool = False) -> dict[str, str | bool]:
    bundle = load_verified_export(bundle_path, report_path, require_v2=require_v2)
    summary: dict[str, str | bool] = {"result_verified": bundle["result"] is not None}
    if bundle["schema_version"] == 2:
        summary["bundle_verified"] = True
    if report_path is not None:
        summary["report_verified"] = True
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reproducibility_json", type=Path)
    parser.add_argument("--report-html", type=Path, help="Downloaded HTML report to check against report_sha256")
    parser.add_argument("--require-v2", action="store_true", help="Reject legacy v1 bundles without whole-bundle checksum")
    args = parser.parse_args()
    try:
        print(json.dumps(verify_export(args.reproducibility_json, args.report_html,
                                       require_v2=args.require_v2), ensure_ascii=False))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"verification failed: {exc}\n")


if __name__ == "__main__":
    main()
