"""Smoke-test the running Compose API, Celery task, and generated report."""

from __future__ import annotations

import json
import hashlib
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = os.environ.get("FACTORLAB_SMOKE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")


def verify_snapshot(bundle: dict, run: dict, report: str) -> None:
    task = bundle.get("task")
    if bundle.get("schema_version") != 1 or not isinstance(task, dict) or task.get("id") != run["id"]:
        raise RuntimeError("reproducibility bundle does not match the completed run")
    result = bundle.get("result")
    if not isinstance(result, dict) or result != run.get("result"):
        raise RuntimeError("reproducibility result differs from the task response")
    canonical = json.dumps(result, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != bundle.get("result_sha256"):
        raise RuntimeError("reproducibility result checksum mismatch")
    if hashlib.sha256(report.encode("utf-8")).hexdigest() != bundle.get("report_sha256"):
        raise RuntimeError("reproducibility report checksum mismatch")


def request(path: str, *, method: str = "GET", payload: dict | None = None, token: str | None = None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if "application/json" in response.headers.get("Content-Type", "") else body
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"{method} {path}: {exc.reason}") from exc


def main() -> int:
    password = os.environ.get("FACTORLAB_SMOKE_PASSWORD")
    if not password:
        print("Set FACTORLAB_SMOKE_PASSWORD to the researcher account password.", file=sys.stderr)
        return 2

    login = request("/auth/login", method="POST", payload={"username": "researcher", "password": password})
    token = login["access_token"]
    datasets = request("/datasets", token=token)
    demo = next((item for item in datasets if item["dataset_key"] == "demo_daily" and item["status"] == "published"), None)
    if demo is None:
        raise RuntimeError("Published demo_daily dataset not found")

    run = request(
        "/research/tasks",
        method="POST",
        payload={"dataset_version_id": demo["id"], "factor": "momentum_20d", "groups": 5},
        token=token,
    )
    run_id = run["id"]
    deadline = time.monotonic() + 90
    while run["status"] in {"pending", "running"} and time.monotonic() < deadline:
        time.sleep(1)
        run = request(f"/research/tasks/{run_id}", token=token)
    if run["status"] != "success":
        raise RuntimeError(f"Run {run_id} ended with {run['status']}: {run.get('error_summary')}")
    code_version = run.get("code_version", "")
    if not code_version.startswith("src-sha256:") or len(code_version) != 75:
        raise RuntimeError(f"Run {run_id} has no backend source fingerprint")
    result = run.get("result") or {}
    histogram = result.get("ic_histogram") or []
    valid_days = sum(item["ic"] is not None for item in result.get("ic_series", []))
    if len(histogram) != 10 or sum(item["count"] for item in histogram) != valid_days:
        raise RuntimeError(f"Run {run_id} IC distribution does not match valid IC days")
    groups = result.get("group_nav") or []
    if len(groups) != 5 or not all(item.get("points") for item in groups):
        raise RuntimeError(f"Run {run_id} is missing the five quantile NAV series")

    logs = request(f"/research/tasks/{run_id}/logs", token=token)
    events = {item["event"] for item in logs}
    if not {"started", "completed"}.issubset(events):
        raise RuntimeError(f"Run {run_id} missing execution log events: {sorted(events)}")
    report = request(f"/reports/{run_id}/html", token=token)
    if report.count("<svg ") != 3 or "SINGLE FACTOR REPORT" not in report or "IC 分布（固定 0.2 宽度分箱）" not in report or "各组净值（初值 1）" not in report:
        raise RuntimeError(f"Run {run_id} report content is incomplete")
    if code_version not in report:
        raise RuntimeError(f"Run {run_id} report is missing the recorded code fingerprint")
    summaries = request("/reports", token=token)
    summary = next((item for item in summaries if item["run_id"] == run_id), None)
    if summary is None or hashlib.sha256(report.encode("utf-8")).hexdigest() != summary["checksum"]:
        raise RuntimeError(f"Run {run_id} report checksum does not match its catalog record")
    bundle = request(f"/research/tasks/{run_id}/reproducibility.json", token=token)
    verify_snapshot(bundle, run, report)

    print(f"PASS run_id={run_id} status={run['status']} progress={run['progress']}")
    print(f"PASS dataset={demo['dataset_key']} version={demo['version']} events={','.join(sorted(events))}")
    print(f"PASS ic_distribution_bins={len(histogram)} valid_days={valid_days}")
    print(f"PASS group_nav_series={len(groups)} points_per_group={len(groups[0]['points'])}")
    print(f"PASS backend_source_fingerprint={code_version[:23]}…")
    print(f"PASS report_html_chars={len(report)} svg=present checksum=verified")
    print("PASS reproducibility_result_and_report_sha256=verified")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, KeyError, TypeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
