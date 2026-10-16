"""Exercise the running Compose API/Worker with the local, undistributed BaoStock CSV."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from verify_compose_stack import request, require_explicit_write_target


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get("FACTORLAB_SMOKE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
DATASET_KEY = "real_baostock_2024h1"
FACTORS = ("momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d", "pe")


def upload_csv(content: bytes, token: str) -> dict:
    boundary = f"factorlab-{uuid4().hex}"
    fields = {"dataset_key": DATASET_KEY, "name": "BaoStock 2024 H1 A股样本"}
    parts = []
    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode("utf-8")
        )
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        "filename=\"baostock_2024h1_daily.csv\"\r\nContent-Type: text/csv\r\n\r\n".encode("utf-8")
        + content + b"\r\n"
    )
    body = b"".join(parts) + f"--{boundary}--\r\n".encode("ascii")
    upload = Request(
        f"{BASE_URL}/datasets/import", data=body, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urlopen(upload, timeout=30) as response:
            return json.loads(response.read())
    except HTTPError as exc:
        raise RuntimeError(f"dataset upload failed: HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc
    except URLError as exc:
        raise RuntimeError(f"dataset upload failed: {exc.reason}") from exc


def main(argv: list[str] | None = None) -> int:
    require_explicit_write_target(argv)
    admin_password = os.environ.get("FACTORLAB_REAL_ADMIN_PASSWORD")
    researcher_password = os.environ.get("FACTORLAB_REAL_RESEARCHER_PASSWORD")
    if not admin_password or not researcher_password:
        print("Set FACTORLAB_REAL_ADMIN_PASSWORD and FACTORLAB_REAL_RESEARCHER_PASSWORD.", file=sys.stderr)
        return 2

    source = ROOT / "data" / "real"
    content = (source / "baostock_2024h1_daily.csv").read_bytes()
    manifest = json.loads((source / "baostock_2024h1_manifest.json").read_text(encoding="utf-8"))
    checksum = hashlib.sha256(content).hexdigest()
    if checksum != manifest["csv_sha256"]:
        raise RuntimeError("local CSV differs from the acquisition manifest")

    admin = request("/auth/login", method="POST", payload={"username": "admin", "password": admin_password})["access_token"]
    researcher = request("/auth/login", method="POST", payload={"username": "researcher", "password": researcher_password})["access_token"]
    versions = request("/datasets", token=admin)
    matching = [item for item in versions if item["dataset_key"] == DATASET_KEY]
    if any(item["checksum"] != checksum for item in matching):
        raise RuntimeError("dataset key already has a different snapshot; choose a new key after review")
    dataset = next((item for item in matching if item["status"] == "published"), None)
    if dataset is None:
        dataset = next((item for item in matching if item["status"] == "draft"), None)
        if dataset is None:
            dataset = upload_csv(content, admin)
        dataset = request(f"/datasets/{dataset['id']}/publish", method="POST", token=admin)
    if dataset["row_count"] != manifest["row_count"] or dataset["symbol_count"] != manifest["symbol_count"]:
        raise RuntimeError("published dataset dimensions differ from the acquisition manifest")
    try:
        request(
            "/research/tasks", method="POST", token=researcher,
            payload={"dataset_version_id": dataset["id"], "factor": "market_cap", "price_basis": "source_close"},
        )
    except RuntimeError as exc:
        if "HTTP 400" not in str(exc) or "total_mv" not in str(exc):
            raise RuntimeError("missing market-cap field was not rejected with a clear reason") from exc
    else:
        raise RuntimeError("market-cap factor unexpectedly accepted a dataset without total_mv")

    summary = {}
    for factor in FACTORS:
        run = request(
            "/research/tasks", method="POST", token=researcher,
            payload={"dataset_version_id": dataset["id"], "factor": factor, "groups": 5, "price_basis": "source_close"},
        )
        deadline = time.monotonic() + 90
        while run["status"] in {"pending", "running"} and time.monotonic() < deadline:
            time.sleep(1)
            run = request(f"/research/tasks/{run['id']}", token=researcher)
        if run["status"] != "success":
            raise RuntimeError(f"{factor} run {run['id']} ended as {run['status']}: {run.get('error_summary')}")
        if not run.get("code_version", "").startswith("src-sha256:"):
            raise RuntimeError(f"{factor} run has no source fingerprint")
        result = run.get("result") or {}
        if result.get("coverage", 0) <= 0 or not result.get("ic_series"):
            raise RuntimeError(f"{factor} produced no usable observations")
        report = request(f"/reports/{run['id']}/html", token=researcher)
        if "SINGLE FACTOR REPORT" not in report or "<svg " not in report:
            raise RuntimeError(f"{factor} report is incomplete")
        reports = request("/reports", token=researcher)
        report_record = next((item for item in reports if item["run_id"] == run["id"]), None)
        if report_record is None or hashlib.sha256(report.encode("utf-8")).hexdigest() != report_record["checksum"]:
            raise RuntimeError(f"{factor} report checksum does not match its catalog record")
        events = {item["event"] for item in request(f"/research/tasks/{run['id']}/logs", token=researcher)}
        if not {"started", "completed"}.issubset(events):
            raise RuntimeError(f"{factor} is missing Worker execution logs")
        bundle = request(f"/research/tasks/{run['id']}/reproducibility.json", token=researcher)
        if bundle["dataset"]["checksum_sha256"] != checksum:
            raise RuntimeError(f"{factor} reproducibility bundle has the wrong dataset checksum")
        summary[factor] = {"run_id": run["id"], "coverage": result["coverage"], "ic_dates": len(result["ic_series"])}

    composite = request(
        "/research/composite-tasks", method="POST", token=researcher,
        payload={
            "dataset_version_id": dataset["id"],
            "factors": ["momentum_20d", "volatility_20d", "turnover_20d"],
            "groups": 5, "price_basis": "source_close",
        },
    )
    deadline = time.monotonic() + 90
    while composite["status"] in {"pending", "running"} and time.monotonic() < deadline:
        time.sleep(1)
        composite = request(f"/research/tasks/{composite['id']}", token=researcher)
    if composite["status"] != "success":
        raise RuntimeError(f"composite run {composite['id']} ended as {composite['status']}: {composite.get('error_summary')}")
    composite_result = composite.get("result") or {}
    if composite_result.get("coverage", 0) <= 0 or not composite_result.get("composite"):
        raise RuntimeError("composite run has no common sample or component record")
    composite_report = request(f"/reports/{composite['id']}/html", token=researcher)
    if "MULTI FACTOR REPORT" not in composite_report or "<svg " not in composite_report:
        raise RuntimeError("composite report is incomplete")
    reports = request("/reports", token=researcher)
    composite_record = next((item for item in reports if item["run_id"] == composite["id"]), None)
    if composite_record is None or hashlib.sha256(composite_report.encode("utf-8")).hexdigest() != composite_record["checksum"]:
        raise RuntimeError("composite report checksum does not match its catalog record")
    events = {item["event"] for item in request(f"/research/tasks/{composite['id']}/logs", token=researcher)}
    if not {"started", "completed"}.issubset(events):
        raise RuntimeError("composite run is missing Worker execution logs")
    composite_bundle = request(f"/research/tasks/{composite['id']}/reproducibility.json", token=researcher)
    if composite_bundle["dataset"]["checksum_sha256"] != checksum:
        raise RuntimeError("composite reproducibility bundle has the wrong dataset checksum")

    print(json.dumps({
        "dataset_id": dataset["id"], "dataset_checksum": checksum,
        "rows": dataset["row_count"], "stocks": dataset["symbol_count"],
        "missing_market_cap_rejected": True,
        "factor_runs": summary,
        "composite_run": {"run_id": composite["id"], "coverage": composite_result["coverage"]},
        "note": "Software acceptance only; not an investment conclusion.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, OSError, TypeError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
