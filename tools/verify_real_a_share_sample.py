"""Validate a locally acquired real A-share snapshot and run supported factors."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.db import Base  # noqa: E402
from app.services.datasets import import_csv, publish_dataset_version, validate_csv  # noqa: E402
from app.services.runs import create_research_run, execute_research_run  # noqa: E402


FACTORS = ("momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d", "pe")


def group_date_audit(result: dict, factor: str) -> dict:
    group_dates = [item["date"] for item in result["long_short_series"]]
    for group in result["group_nav"]:
        if [point["date"] for point in group["points"]] != group_dates:
            raise ValueError(f"group NAV dates differ from long-short dates: {factor}")
    if not set(group_dates).issubset({item["date"] for item in result["ic_series"]}):
        raise ValueError(f"group dates are absent from IC calendar: {factor}")
    return {
        "coverage": result["coverage"],
        "ic_dates": len(result["ic_series"]),
        "group_dates": len(group_dates),
        "skipped_constant_factor_days": result["group_skipped_constant_factor_days"],
        "skipped_insufficient_sample_days": result["group_skipped_insufficient_sample_days"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "real")
    args = parser.parse_args()
    source_dir = args.input_dir.resolve()
    csv_path = source_dir / "baostock_2024h1_daily.csv"
    manifest_path = source_dir / "baostock_2024h1_manifest.json"
    content = csv_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(content).hexdigest()
    if digest != manifest["csv_sha256"]:
        raise ValueError("real sample checksum differs from its acquisition manifest")
    parsed = validate_csv(content)
    if parsed.row_count != manifest["row_count"] or parsed.symbol_count != manifest["symbol_count"]:
        raise ValueError("real sample dimensions differ from its acquisition manifest")

    with tempfile.TemporaryDirectory(prefix="fbl-real-check-") as temporary:
        root = Path(temporary)
        with patch.dict(os.environ, {"DATA_ROOT": str(root / "data"), "TASK_EXECUTION_MODE": "inline"}):
            engine = create_engine("sqlite:///:memory:")
            try:
                Base.metadata.create_all(engine)
                with Session(engine, expire_on_commit=False) as session:
                    dataset = import_csv(
                        session, content=content, source_filename=csv_path.name,
                        dataset_key="real_baostock", name="BaoStock 2024 H1 A股样本", data_root=root / "data",
                    )
                    publish_dataset_version(session, dataset)
                    results = {}
                    for factor in FACTORS:
                        run = create_research_run(session, {
                            "factor": factor,
                            "dataset_version_id": dataset.id,
                            "groups": 5,
                            "price_basis": "source_close",
                        })
                        run = execute_research_run(session, run.id)
                        result = next(item.content for item in run.artifacts if item.artifact_type == "metrics")
                        if run.status.value != "success" or result["coverage"] <= 0:
                            raise ValueError(f"factor did not produce valid observations: {factor}")
                        results[factor] = group_date_audit(result, factor)
            finally:
                engine.dispose()

    print(json.dumps({
        "csv_sha256": digest,
        "rows": parsed.row_count,
        "stocks": parsed.symbol_count,
        "start_date": parsed.start_date.isoformat(),
        "end_date": parsed.end_date.isoformat(),
        "factor_checks": results,
        "note": "Software validation only; metrics are not investment conclusions.",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
