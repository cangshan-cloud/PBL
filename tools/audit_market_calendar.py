"""Read-only calendar audit for already published ordinary CSV versions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.market_calendar_audit import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
