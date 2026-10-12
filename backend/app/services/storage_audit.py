from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DatasetVersion
from app.services.datasets import verify_dataset_file


def audit_dataset_storage(session: Session, data_root: Path) -> dict:
    """Read-only comparison of dataset records and files managed under DATA_ROOT."""
    records = list(session.scalars(select(DatasetVersion).order_by(DatasetVersion.id)))
    referenced = {Path(record.storage_uri).resolve() for record in records}
    issues: list[dict[str, str]] = []

    for record in records:
        try:
            verify_dataset_file(record)
        except FileNotFoundError:
            kind = "missing"
        except ValueError:
            kind = "checksum_mismatch"
        except OSError:
            kind = "unreadable"
        else:
            continue
        issues.append({"kind": kind, "dataset_id": record.id, "path": record.storage_uri})

    root = data_root.resolve()
    if root.is_dir():
        for path in sorted(root.glob("*/*/*.csv")):
            if path.resolve() not in referenced:
                issues.append({"kind": "unreferenced_file", "path": str(path)})

    return {
        "dataset_count": len(records),
        "issue_count": len(issues),
        "issues": issues,
    }


def main() -> int:
    from app.config import get_settings
    from app.db import engine

    if engine.url.get_backend_name() == "sqlite" and engine.url.database not in (None, ":memory:"):
        if not Path(engine.url.database).is_file():
            print(f"database file not found: {engine.url.database}")
            return 2
    with Session(engine) as session:
        result = audit_dataset_storage(session, get_settings().data_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
