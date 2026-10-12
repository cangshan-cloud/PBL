"""Read-only audit of dataset records against DATA_ROOT; exit 1 when issues are found."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.storage_audit import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
