from __future__ import annotations

import hashlib
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DatasetVersion, FactorVersion, utc_now
from app.domain.factors import FACTOR_REGISTRY
from app.services.sample_data import sample_file
from app.services.datasets import validate_csv


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_factor_catalog(session: Session) -> list[FactorVersion]:
    factors: list[FactorVersion] = []
    for definition in FACTOR_REGISTRY.values():
        factor = session.scalar(
            select(FactorVersion).where(
                FactorVersion.factor_key == definition.key,
                FactorVersion.version == definition.version,
            )
        )
        if factor is None:
            factor = FactorVersion(
                factor_key=definition.key,
                name=definition.name,
                category=definition.category,
                version=definition.version,
                formula=definition.formula,
                description=definition.description,
                parameter_schema={
                    "lookback": {
                        "type": "integer",
                        "default": definition.default_lookback,
                        "minimum": 2,
                        "maximum": 120,
                    }
                } if definition.default_lookback is not None else {},
            )
            session.add(factor)
        factors.append(factor)
    session.commit()
    for factor in factors:
        session.refresh(factor)
    return factors


def ensure_composite_factor(session: Session) -> FactorVersion:
    factor = session.scalar(
        select(FactorVersion).where(
            FactorVersion.factor_key == "equal_weight_composite",
            FactorVersion.version == "1.0.0",
        )
    )
    if factor is None:
        factor = FactorVersion(
            factor_key="equal_weight_composite",
            name="等权多因子组合",
            category="composite",
            version="1.0.0",
            formula="sum(zscore(component_i) * weight_i)",
            description="各成分因子按日预处理后，在共同样本上使用归一化权重合成。",
            parameter_schema={"factors": {"type": "array", "minItems": 2, "maxItems": 6}},
        )
        session.add(factor)
        session.commit()
        session.refresh(factor)
    return factor


def ensure_demo_catalog(session: Session) -> tuple[DatasetVersion, FactorVersion]:
    dataset = session.scalar(
        select(DatasetVersion).where(
            DatasetVersion.dataset_key == "demo_daily",
            DatasetVersion.version == "0.2.0",
        )
    )
    if dataset is None:
        path = sample_file()
        parsed = validate_csv(path.read_bytes())
        dataset = DatasetVersion(
            dataset_key="demo_daily",
            name="A股全字段演示快照",
            version="0.2.0",
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            row_count=parsed.row_count,
            symbol_count=parsed.symbol_count,
            checksum=_checksum(path),
            storage_uri=str(path),
            source_filename=path.name,
            quality_report={**parsed.report, "source": "bundled_demo"},
            published_at=utc_now(),
        )
        session.add(dataset)

    factors = ensure_factor_catalog(session)
    factor = next(item for item in factors if item.factor_key == "momentum_20d")
    session.commit()
    session.refresh(dataset)
    session.refresh(factor)
    return dataset, factor
