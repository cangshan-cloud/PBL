"""Integrity gate for locally sealed CSI 300 research bundles."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


BUNDLE_ID = re.compile(r"hs300_2024_[0-9a-f]{16}\Z")
IDENTITY_FIELDS = (
    "schema_version", "research_start", "research_end", "price_basis",
    "price_adjustflag", "factor_windows", "file_sha256",
)


def verify_historical_bundle(manifest_path: Path, expected_checksum: str | None = None) -> dict:
    if manifest_path.name != "manifest.json" or not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError("historical bundle manifest is missing or unsafe")
    bundle_dir = manifest_path.parent
    if not BUNDLE_ID.fullmatch(bundle_dir.name) or bundle_dir.is_symlink():
        raise ValueError("invalid historical bundle directory")
    raw = manifest_path.read_bytes()
    checksum = hashlib.sha256(raw).hexdigest()
    if expected_checksum is not None and checksum != expected_checksum:
        raise ValueError("historical bundle manifest checksum mismatch")
    try:
        manifest = json.loads(raw)
        hashes = manifest["file_sha256"]
        identity = {key: manifest[key] for key in IDENTITY_FIELDS}
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("invalid historical bundle manifest") from exc
    if not isinstance(hashes, dict) or not hashes:
        raise ValueError("historical bundle file list is empty")
    if (manifest["schema_version"], manifest["research_start"], manifest["research_end"]) != (1, "2024-01-01", "2024-12-31"):
        raise ValueError("unsupported historical bundle range or schema")
    if manifest["price_basis"] != "source_close" or manifest["price_adjustflag"] != "1":
        raise ValueError("unsupported historical bundle price convention")
    if manifest["factor_windows"] != {"momentum": 20, "reversal": 5, "volatility": 20, "turnover": 20}:
        raise ValueError("unsupported historical bundle factor windows")
    actual = set()
    for path in bundle_dir.rglob("*"):
        if path.is_symlink():
            raise ValueError("historical bundle contains a symlink")
        if path.is_file() and path != manifest_path:
            actual.add(path.relative_to(bundle_dir).as_posix())
    if actual != set(hashes):
        raise ValueError("historical bundle file set mismatch")
    for name, digest in hashes.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("unsafe historical bundle file entry")
        with (bundle_dir / relative).open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != digest:
                raise ValueError(f"historical bundle file checksum mismatch: {name}")
    version = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if manifest.get("version_sha256") != version or manifest.get("bundle_id") != f"hs300_2024_{version[:16]}":
        raise ValueError("historical bundle identity mismatch")
    if bundle_dir.name != manifest["bundle_id"]:
        raise ValueError("historical bundle directory identity mismatch")
    for field in ("member_trading_days", "member_rows", "price_symbols", "price_rows"):
        if not isinstance(manifest.get(field), int) or manifest[field] <= 0:
            raise ValueError(f"historical bundle has invalid {field}")
    return {"manifest": manifest, "checksum": checksum, "verified_files": len(hashes)}
