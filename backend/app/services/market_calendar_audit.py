"""Read-only recheck of stored CSV versions against the current closure rules."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DatasetVersion
from app.services.datasets import DatasetValidationError, _read_verified_csv, validate_csv
from app.services.market_calendar import CALENDAR_SOURCES, CALENDAR_VERSION


REPORT_FIELDS = (
    "weekend_date_count", "weekend_row_count",
    "announced_weekday_closure_date_count", "announced_weekday_closure_row_count",
    "announced_weekday_closure_dates", "calendar_uncovered_years", "calendar_uncovered_row_count",
)


def audit_existing_dataset_calendars(session: Session, dataset_id: str | None = None) -> dict:
    query = select(DatasetVersion).where(DatasetVersion.status == "published").order_by(DatasetVersion.id)
    if dataset_id is not None:
        query = query.where(DatasetVersion.id == dataset_id)
    records = list(session.scalars(query))
    items: list[dict] = []
    for dataset in records:
        item = {
            "dataset_id": dataset.id,
            "dataset_key": dataset.dataset_key,
            "version": dataset.version,
            "checksum_sha256": dataset.checksum,
        }
        if (dataset.quality_report or {}).get("dataset_kind") == "hs300_bundle_v1":
            item.update(status="skipped_historical_bundle", reason="封存历史包不是普通单文件 CSV")
        else:
            try:
                content = _read_verified_csv(dataset)
                parsed = validate_csv(content)
                if parsed.row_count != dataset.row_count or parsed.symbol_count != dataset.symbol_count:
                    raise ValueError("数据库行数或证券数与已校验文件不一致")
            except (FileNotFoundError, OSError, ValueError, DatasetValidationError) as exc:
                item.update(status="error", reason=str(exc))
            else:
                item.update(status="audited", **{key: parsed.report[key] for key in REPORT_FIELDS})
        items.append(item)
    return {
        "calendar_version": CALENDAR_VERSION,
        "covered_years": sorted(CALENDAR_SOURCES),
        "published_dataset_count": len(items),
        "audited_count": sum(item["status"] == "audited" for item in items),
        "skipped_count": sum(item["status"] == "skipped_historical_bundle" for item in items),
        "error_count": sum(item["status"] == "error" for item in items),
        "items": items,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="只读复核已发布普通 CSV 的公告休市日期；不更新质量报告")
    parser.add_argument("--dataset-id", help="仅复核指定的已发布数据版本 ID")
    args = parser.parse_args(argv)

    from app.db import engine

    if engine.url.get_backend_name() == "sqlite" and engine.url.database not in (None, ":memory:"):
        if not Path(engine.url.database).is_file():
            print(json.dumps({"error": "database file not found"}, ensure_ascii=False))
            return 2
    with Session(engine) as session:
        result = audit_existing_dataset_calendars(session, args.dataset_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.dataset_id and not result["published_dataset_count"]:
        return 2
    return 1 if result["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
