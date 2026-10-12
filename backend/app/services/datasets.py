from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DatasetVersion
from app.services.historical_bundle import BUNDLE_ID, verify_historical_bundle


REQUIRED_COLUMNS = {"trade_date", "symbol", "close"}
OPTIONAL_NUMERIC_COLUMNS = {"open", "high", "low", "volume", "amount", "adj_factor", "turnover_rate", "total_mv", "pe"}
DATASET_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,49}$")


class DatasetValidationError(ValueError):
    def __init__(self, message: str, report: dict | None = None):
        super().__init__(message)
        self.report = report or {"valid": False, "errors": [message]}


@dataclass(frozen=True)
class ParsedDataset:
    row_count: int
    symbol_count: int
    start_date: date
    end_date: date
    report: dict


def _number(value: str, column: str, line: int) -> float:
    if value == "":
        raise DatasetValidationError(f"第{line}行的{column}不能为空")
    try:
        number = float(value)
    except ValueError as exc:
        raise DatasetValidationError(f"第{line}行的{column}不是有效数字") from exc
    if not math.isfinite(number):
        raise DatasetValidationError(f"第{line}行的{column}必须是有限数值")
    return number


def validate_csv(content: bytes) -> ParsedDataset:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DatasetValidationError("CSV必须使用UTF-8编码") from exc
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    if any(not item or not item.strip() for item in fieldnames):
        raise DatasetValidationError("CSV表头包含空字段名")
    if any(item != item.strip() for item in fieldnames):
        raise DatasetValidationError("标准CSV表头不能包含首尾空格，请使用字段适配功能")
    if len(fieldnames) != len(set(fieldnames)):
        raise DatasetValidationError("CSV表头包含重复字段名")
    columns = set(fieldnames)
    missing = sorted(REQUIRED_COLUMNS - columns)
    if missing:
        raise DatasetValidationError(f"缺少必填字段：{', '.join(missing)}")

    seen: set[tuple[str, date]] = set()
    symbols: set[str] = set()
    dates: list[date] = []
    errors: list[str] = []
    missing_counts = {column: 0 for column in columns}
    numeric_values: dict[str, list[float]] = {column: [] for column in ({"close"} | OPTIONAL_NUMERIC_COLUMNS) & columns}
    rows = 0
    for line, raw in enumerate(reader, start=2):
        rows += 1
        try:
            if None in raw or any(value is None for value in raw.values()):
                raise DatasetValidationError(f"第{line}行的列数与表头不一致")
            for column in columns:
                if not (raw.get(column) or "").strip():
                    missing_counts[column] += 1
            symbol = (raw.get("symbol") or "").strip()
            if not symbol:
                raise DatasetValidationError(f"第{line}行的symbol不能为空")
            try:
                trade_date = date.fromisoformat((raw.get("trade_date") or "").strip())
            except ValueError as exc:
                raise DatasetValidationError(f"第{line}行的trade_date不是YYYY-MM-DD格式") from exc
            key = (symbol, trade_date)
            if key in seen:
                raise DatasetValidationError(f"第{line}行存在重复证券日期：{symbol} {trade_date}")
            close = _number((raw.get("close") or "").strip(), "close", line)
            if close <= 0:
                raise DatasetValidationError(f"第{line}行的close必须大于0")
            numeric_values["close"].append(close)

            numeric: dict[str, float] = {}
            for column in OPTIONAL_NUMERIC_COLUMNS & columns:
                value = (raw.get(column) or "").strip()
                if value:
                    numeric[column] = _number(value, column, line)
                    numeric_values[column].append(numeric[column])
            for column in ("volume", "amount", "turnover_rate", "total_mv"):
                if column in numeric and numeric[column] < 0:
                    raise DatasetValidationError(f"第{line}行的{column}不能为负数")
            if "adj_factor" in numeric and numeric["adj_factor"] <= 0:
                raise DatasetValidationError(f"第{line}行的adj_factor必须大于0")
            if "high" in numeric and numeric["high"] < max(
                close, numeric.get("open", close), numeric.get("low", close)
            ):
                raise DatasetValidationError(f"第{line}行的high低于open、close或low")
            if "low" in numeric and numeric["low"] > min(close, numeric.get("open", close)):
                raise DatasetValidationError(f"第{line}行的low高于open或close")
            seen.add(key)
            symbols.add(symbol)
            dates.append(trade_date)
        except DatasetValidationError as exc:
            errors.append(str(exc))
            if len(errors) >= 20:
                break

    if not rows:
        raise DatasetValidationError("CSV不包含数据行")
    if errors:
        raise DatasetValidationError(
            "数据质量检查失败",
            {"valid": False, "checked_rows": rows, "error_count": len(errors), "errors": errors},
        )
    return ParsedDataset(
        row_count=rows,
        symbol_count=len(symbols),
        start_date=min(dates),
        end_date=max(dates),
        report={
            "valid": True,
            "checked_rows": rows,
            "duplicate_count": 0,
            "error_count": 0,
            "required_columns": sorted(REQUIRED_COLUMNS),
            "columns": sorted(columns),
            "missing_counts": missing_counts,
            "completeness": {
                column: (rows - missing_counts[column]) / rows for column in sorted(columns)
            },
            "numeric_summary": {
                column: {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                }
                for column, values in sorted(numeric_values.items()) if values
            },
        },
    )


def verify_dataset_file(dataset: DatasetVersion) -> Path:
    path = Path(dataset.storage_uri)
    if (dataset.quality_report or {}).get("dataset_kind") == "hs300_bundle_v1":
        verify_historical_bundle(path, dataset.checksum)
        return path
    if not path.is_file():
        raise FileNotFoundError("dataset file not found")
    with path.open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != dataset.checksum:
            raise ValueError("dataset checksum mismatch")
    return path


def preview_dataset(dataset: DatasetVersion, limit: int = 20) -> dict:
    if (dataset.quality_report or {}).get("dataset_kind") == "hs300_bundle_v1":
        verify_dataset_file(dataset)
        report = dataset.quality_report or {}
        rows = [
            {"item": "bundle_id", "value": str(report.get("bundle_id", ""))},
            {"item": "verified_files", "value": str(report.get("verified_files", ""))},
            {"item": "member_trading_days", "value": str(report.get("member_trading_days", ""))},
            {"item": "member_rows", "value": str(report.get("member_rows", ""))},
            {"item": "price_rows", "value": str(dataset.row_count)},
        ]
        return {"dataset_id": dataset.id, "columns": ["item", "value"], "rows": rows,
                "preview_count": len(rows), "total_rows": len(rows), "truncated": False}
    limit = max(1, min(limit, 100))
    path = verify_dataset_file(dataset)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = [column.strip() for column in (reader.fieldnames or [])]
        rows = []
        for index, raw in enumerate(reader):
            if index >= limit:
                break
            rows.append({column: (raw.get(column) or "")[:200] for column in columns})
    return {
        "dataset_id": dataset.id,
        "columns": columns,
        "rows": rows,
        "preview_count": len(rows),
        "total_rows": dataset.row_count,
        "truncated": dataset.row_count > len(rows),
    }


def import_csv(
    session: Session,
    *,
    content: bytes,
    source_filename: str,
    dataset_key: str,
    name: str,
    data_root: Path,
    quality_metadata: dict | None = None,
) -> DatasetVersion:
    if not DATASET_KEY_PATTERN.fullmatch(dataset_key):
        raise DatasetValidationError("数据集标识只能包含小写字母、数字和下划线，且必须以字母开头")
    if not name.strip():
        raise DatasetValidationError("数据集名称不能为空")
    if not source_filename.lower().endswith(".csv"):
        raise DatasetValidationError("当前阶段仅支持CSV文件")
    parsed = validate_csv(content)
    checksum = hashlib.sha256(content).hexdigest()
    version = datetime.now(timezone.utc).strftime("%Y%m%d.%H%M%S.%f")
    version_id = str(uuid4())
    target_dir = data_root / dataset_key / version
    target_dir.mkdir(parents=True, exist_ok=False)
    target = target_dir / f"{version_id}.csv"
    try:
        target.write_bytes(content)
        dataset = DatasetVersion(
            id=version_id,
            dataset_key=dataset_key,
            name=name.strip(),
            version=version,
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            row_count=parsed.row_count,
            symbol_count=parsed.symbol_count,
            checksum=checksum,
            storage_uri=str(target),
            source_filename=Path(source_filename).name,
            quality_report={**parsed.report, **(quality_metadata or {})},
            status="draft",
        )
        session.add(dataset)
        session.commit()
    except Exception:
        session.rollback()
        try:
            target.unlink(missing_ok=True)
            target_dir.rmdir()
        except OSError:
            pass  # Preserve the original write/commit error; a nonempty directory is not ours to remove.
        raise
    session.refresh(dataset)
    return dataset


def list_dataset_versions(session: Session) -> list[DatasetVersion]:
    return list(session.scalars(select(DatasetVersion).order_by(DatasetVersion.created_at.desc())))


def register_hs300_bundle(session: Session, *, bundle_id: str, data_root: Path) -> DatasetVersion:
    if not BUNDLE_ID.fullmatch(bundle_id):
        raise DatasetValidationError("无效的历史数据包标识")
    manifest_path = data_root.parent / "real" / "bundles" / bundle_id / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("historical bundle not found")
    verified = verify_historical_bundle(manifest_path)
    manifest = verified["manifest"]
    version = manifest["version_sha256"][:16]
    existing = session.scalar(select(DatasetVersion).where(
        DatasetVersion.dataset_key == "hs300_2024", DatasetVersion.version == version,
    ))
    if existing is not None:
        raise DatasetValidationError("历史数据包已注册")
    dataset = DatasetVersion(
        dataset_key="hs300_2024", name="沪深300历史成分与行情（2024）",
        version=version, market="CN_A", frequency="1d",
        start_date=date.fromisoformat(manifest["research_start"]),
        end_date=date.fromisoformat(manifest["research_end"]),
        row_count=manifest["price_rows"], symbol_count=manifest["price_symbols"],
        checksum=verified["checksum"], storage_uri=str(manifest_path.resolve()),
        source_filename="manifest.json", status="draft",
        quality_report={
            "valid": True, "dataset_kind": "hs300_bundle_v1",
            "bundle_id": bundle_id, "verified_files": verified["verified_files"],
            "member_trading_days": manifest["member_trading_days"],
            "member_rows": manifest["member_rows"],
            "member_day_audit": manifest.get("member_day_audit", {}),
            "verification_scope": "manifest_identity_and_all_file_hashes",
        },
    )
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset


def get_dataset_version(session: Session, dataset_id: str) -> DatasetVersion | None:
    return session.get(DatasetVersion, dataset_id)


def publish_dataset_version(session: Session, dataset: DatasetVersion) -> DatasetVersion:
    if dataset.status not in {"draft", "published"}:
        raise ValueError(f"cannot publish dataset in status {dataset.status}")
    verify_dataset_file(dataset)
    if dataset.status == "published":
        return dataset
    dataset.status = "published"
    dataset.published_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(dataset)
    return dataset
