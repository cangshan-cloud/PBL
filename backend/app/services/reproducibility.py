from __future__ import annotations

import hashlib
import json

from fastapi.encoders import jsonable_encoder

from app.models import Run
from app.services.runs import serialize_run


def build_reproducibility_bundle(run: Run) -> dict:
    """Export a self-describing research snapshot without host-specific file paths."""
    task = serialize_run(run)
    dataset = run.experiment.dataset_version
    factor = run.experiment.factor_version
    result = task.pop("result")
    result_digest = None
    if result is not None:
        canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        result_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    report = next((item for item in run.artifacts if item.artifact_type == "report_html"), None)
    bundle = jsonable_encoder({
        "schema_version": 2,
        "task": task,
        "dataset": {
            "id": dataset.id,
            "key": dataset.dataset_key,
            "name": dataset.name,
            "version": dataset.version,
            "checksum_sha256": dataset.checksum,
            "source_filename": dataset.source_filename,
            "row_count": dataset.row_count,
            "symbol_count": dataset.symbol_count,
            "start_date": dataset.start_date,
            "end_date": dataset.end_date,
        },
        "factor": {
            "id": factor.id,
            "key": factor.factor_key,
            "name": factor.name,
            "version": factor.version,
            "formula": factor.formula,
        },
        "result": result,
        "result_sha256": result_digest,
        "report_sha256": report.checksum if report else None,
        "logs": [
            {"level": item.level, "event": item.event, "message": item.message, "created_at": item.created_at}
            for item in run.logs
        ],
        "limitations": [
            "This bundle records a completed or in-progress run; it does not include the source dataset file.",
            "Checksums identify stored content but do not prove the dataset or report is still available.",
        ],
    })
    canonical = json.dumps(bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    bundle["bundle_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return bundle
