"""Read-only verification of one completed Run's live V2 JSON and HTML downloads.

Only accepts an explicit loopback API URL. Credentials come from an environment
variable; downloaded bytes are held in a temporary directory and then removed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_reproducibility_export import load_verified_export, verify_export
from tools.verify_research_result_consistency import verify_result_consistency


RUN_ID = re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\Z")


def validate_api_url(value: str) -> str:
    parsed = urlsplit(value)
    if (value != value.strip() or parsed.scheme != "http" or
            parsed.hostname not in {"127.0.0.1", "localhost"}
            or parsed.port is None or parsed.path.rstrip("/") != "/api/v1"
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("API URL must be an explicit loopback http://host:port/api/v1")
    return value.rstrip("/")


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


class LocalApiClient:
    def __init__(self, api_url: str):
        self.api_url = validate_api_url(api_url)
        self.opener = build_opener(_NoRedirect)

    def request(self, path: str, *, token: str | None = None, payload: dict | None = None) -> tuple[bytes, dict[str, str]]:
        headers = {"Accept": "application/json"}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        if payload is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.api_url + path, data=json.dumps(payload).encode() if payload is not None else None,
                          headers=headers, method="POST" if payload is not None else "GET")
        try:
            with self.opener.open(request, timeout=30) as response:
                return response.read(), {key.lower(): value for key, value in response.headers.items()}
        except HTTPError as exc:
            raise RuntimeError(f"{path}: HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"{path}: connection failed: {exc.reason}") from exc


def verify_http_run(client: LocalApiClient, *, run_id: str, username: str, password: str,
                    audit_result: bool = False) -> dict:
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run ID must be a UUID")
    login_bytes, _ = client.request("/auth/login", payload={"username": username, "password": password})
    token = json.loads(login_bytes)["access_token"]
    task_bytes, _ = client.request(f"/research/tasks/{run_id}", token=token)
    task = json.loads(task_bytes)
    bundle_bytes, bundle_headers = client.request(f"/research/tasks/{run_id}/reproducibility.json", token=token)
    report_bytes, report_headers = client.request(f"/reports/{run_id}/download", token=token)
    for label, headers in (("bundle", bundle_headers), ("report", report_headers)):
        disposition = next((value for key, value in headers.items() if key.lower() == "content-disposition"), "")
        if "attachment" not in disposition.lower():
            raise ValueError(f"{label} response has no attachment disposition")
    with tempfile.TemporaryDirectory(prefix="factorlab-http-repro-") as directory:
        bundle_path = Path(directory) / "reproducibility.json"
        report_path = Path(directory) / "report.html"
        bundle_path.write_bytes(bundle_bytes)
        report_path.write_bytes(report_bytes)
        bundle = load_verified_export(bundle_path, report_path, require_v2=True)
        checks = verify_export(bundle_path, report_path, require_v2=True)
        identity = ("id", "status", "parameters", "dataset_version_id", "factor_version_id", "code_version")
        dataset = bundle.get("dataset")
        factor = bundle.get("factor")
        if (task.get("id") != run_id or task.get("status") != "success" or
                not isinstance(bundle.get("task"), dict) or
                not isinstance(dataset, dict) or not isinstance(factor, dict) or
                any(bundle["task"].get(key) != task.get(key) for key in identity) or
                bundle.get("result") != task.get("result") or
                dataset.get("id") != task.get("dataset_version_id") or
                factor.get("id") != task.get("factor_version_id")):
            raise ValueError("downloaded bundle does not match the completed task response")
        if not checks["result_verified"] or not checks["bundle_verified"] or not checks["report_verified"]:
            raise ValueError("completed task did not pass all V2 export checks")
        audit = verify_result_consistency(bundle_path) if audit_result else None
    return {"run_id": run_id, "schema_version": 2, "result_sha256": bundle["result_sha256"],
            "bundle_sha256": bundle["bundle_sha256"], "report_sha256": bundle["report_sha256"],
            "checks": checks, **({"audit": audit} if audit is not None else {})}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", required=True, help="Explicit loopback API v1 URL")
    parser.add_argument("--run-id", required=True, help="Existing successful Run UUID; no task is created")
    parser.add_argument("--username", default="researcher", help="Account allowed to read this Run")
    parser.add_argument("--audit-result", action="store_true", help="Also audit saved daily result arithmetic")
    args = parser.parse_args()
    password = os.environ.get("FACTORLAB_HTTP_QA_PASSWORD")
    if not password:
        parser.error("set FACTORLAB_HTTP_QA_PASSWORD")
    try:
        result = verify_http_run(LocalApiClient(args.api_url), run_id=args.run_id,
                                 username=args.username, password=password, audit_result=args.audit_result)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        parser.exit(1, f"HTTP V2 verification failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
