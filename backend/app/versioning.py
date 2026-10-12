"""Stable fingerprint of the backend source used to create and execute runs."""

from __future__ import annotations

import hashlib
from pathlib import Path


def source_fingerprint(app_root: Path | None = None) -> str:
    root = app_root or Path(__file__).resolve().parent
    files = sorted(root.rglob("*.py"), key=lambda path: path.relative_to(root).as_posix())
    if not files:
        raise ValueError("backend source files not found")
    digest = hashlib.sha256()
    manifest = root.parent / "pyproject.toml"
    entries = [("pyproject.toml", manifest)] if manifest.is_file() else []
    entries.extend((f"app/{path.relative_to(root).as_posix()}", path) for path in files)
    for name, path in entries:
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return f"src-sha256:{digest.hexdigest()}"
