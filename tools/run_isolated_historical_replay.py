"""Generate and verify a current historical run in an isolated in-memory database.

Writes derived evidence only under ignored data/real; never connects to the
running API, Worker, Redis, or PostgreSQL stack.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base
from app.models import DatasetVersion, RunStatus
from app.services.historical_bundle import verify_historical_bundle
from app.services.reproducibility import build_reproducibility_bundle
from app.services.runs import create_historical_run, execute_research_run
from tools.verify_historical_recomputation import verify_recomputation
from tools.verify_reproducibility_export import verify_export


PRIVATE_ROOT = ROOT / "data" / "real"


def require_private_new_output(output_dir: Path) -> Path:
    target = output_dir.resolve()
    if not target.is_relative_to(PRIVATE_ROOT.resolve()) or target == PRIVATE_ROOT.resolve():
        raise ValueError("output must be a new directory inside ignored data/real")
    if target.exists():
        raise ValueError("output directory already exists; refusing to overwrite")
    return target


def run_isolated_replay(manifest_path: Path, output_dir: Path,
                        validation_start_date: str | None = None) -> dict[str, object]:
    target = require_private_new_output(output_dir)
    if validation_start_date not in {None, "2024-07-01"}:
        raise ValueError("historical validation_start_date must be 2024-07-01")
    verified = verify_historical_bundle(manifest_path)
    manifest = verified["manifest"]
    with tempfile.TemporaryDirectory(prefix="factorlab-historical-replay-") as temporary:
        engine = create_engine("sqlite:///:memory:")
        try:
            Base.metadata.create_all(engine)
            with Session(engine, expire_on_commit=False) as session:
                dataset = DatasetVersion(
                    dataset_key="hs300_2024", name="isolated replay", version="current",
                    checksum=verified["checksum"], storage_uri=str(manifest_path),
                    source_filename="manifest.json", row_count=manifest["price_rows"],
                    symbol_count=manifest["price_symbols"],
                    quality_report={"dataset_kind": "hs300_bundle_v1", "bundle_id": manifest["bundle_id"]},
                    status="published",
                )
                session.add(dataset)
                session.commit()
                run = create_historical_run(session, {
                    "dataset_version_id": dataset.id,
                    "validation_start_date": validation_start_date,
                })
                settings = replace(get_settings(), data_root=Path(temporary))
                with patch("app.services.runs.get_settings", return_value=settings):
                    completed = execute_research_run(session, run.id)
                if completed.status != RunStatus.SUCCESS:
                    raise RuntimeError(f"isolated historical task ended as {completed.status}")
                export = jsonable_encoder(build_reproducibility_bundle(completed))
                report = next(item for item in completed.artifacts if item.artifact_type == "report_html")
                report_bytes = Path(report.storage_uri).read_bytes()
                if hashlib.sha256(report_bytes).hexdigest() != report.checksum:
                    raise ValueError("isolated report checksum mismatch")
                run_id = completed.id
        finally:
            engine.dispose()
    target.mkdir(parents=True, exist_ok=False)
    export_path = target / "reproducibility.json"
    export_path.write_text(json.dumps(export, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    report_path = target / "report.html"
    report_path.write_bytes(report_bytes)
    verify_export(export_path, report_path, require_v2=True)
    replay = verify_recomputation(export_path, manifest_path, require_v2=True)
    return {"run_id": run_id, "result_sha256": export["result_sha256"],
            "report_sha256": export["report_sha256"],
            "time_split": export["result"].get("time_split"), **replay}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest_json", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--acknowledge-private-output", action="store_true",
                        help="Confirm this writes derived evidence under ignored data/real")
    parser.add_argument("--validation-start-date", choices=["2024-07-01"],
                        help="Optional fixed historical IC split with one embargoed signal day")
    args = parser.parse_args()
    if not args.acknowledge_private_output:
        parser.error("pass --acknowledge-private-output to create private derived evidence")
    try:
        result = run_isolated_replay(args.manifest_json, args.output_dir, args.validation_start_date)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f"隔离历史复算失败：{exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
