"""Write-enabled historical API/Worker acceptance test for an isolated stack.

This registers/publishes a private bundle when needed and creates a research run.
Never point it at a database whose test records must remain unchanged.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from verify_historical_audit_exports import verify_exports
from verify_reproducibility_export import load_verified_export


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, *, token: str | None = None, payload: dict | None = None) -> tuple[bytes, dict[str, str]]:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        body = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")
        request = Request(self.base_url + path, data=body, headers=headers,
                          method="POST" if payload is not None else "GET")
        try:
            with urlopen(request, timeout=30) as response:
                return response.read(), dict(response.headers)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"{path}: HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"{path}: connection failed: {exc.reason}") from exc

    def json(self, path: str, *, token: str | None = None, payload: dict | None = None):
        return json.loads(self.request(path, token=token, payload=payload)[0])


def verify_journey_binding(export: dict, *, run_id: str, dataset_id: str, bundle_id: str) -> None:
    task = export.get("task")
    dataset = export.get("dataset")
    result = export.get("result")
    sample = result.get("sample") if isinstance(result, dict) else None
    if not all(isinstance(item, dict) for item in (task, dataset, sample)):
        raise ValueError("downloaded reproducibility export does not match the requested historical journey")
    parameters = task.get("parameters")
    if (task.get("id") != run_id or task.get("status") != "success" or
            task.get("dataset_version_id") != dataset_id or dataset.get("id") != dataset_id or
            sample.get("historical_bundle_id") != bundle_id or
            not isinstance(parameters, dict) or type(parameters.get("groups")) is not int or
            parameters["groups"] != 5):
        raise ValueError("downloaded reproducibility export does not match the requested historical journey")


def run_journey(client: ApiClient, *, bundle_id: str, admin_password: str, researcher_password: str,
                output_dir: Path, timeout_seconds: int = 120) -> dict:
    if output_dir.exists():
        raise ValueError(f"output path already exists; refusing to overwrite: {output_dir}")
    admin = client.json("/auth/login", payload={"username": "admin", "password": admin_password})["access_token"]
    researcher = client.json("/auth/login", payload={"username": "researcher", "password": researcher_password})["access_token"]
    datasets = client.json("/datasets", token=admin)
    matches = [item for item in datasets if (item.get("quality_report") or {}).get("bundle_id") == bundle_id]
    if len(matches) > 1:
        raise ValueError("multiple catalog entries have the requested bundle ID")
    dataset = matches[0] if matches else client.json(
        "/datasets/register-hs300-bundle", token=admin, payload={"bundle_id": bundle_id},
    )
    if dataset["status"] == "draft":
        dataset = client.json(f"/datasets/{dataset['id']}/publish", token=admin, payload={})
    if dataset["status"] != "published":
        raise ValueError(f"historical bundle is not published: {dataset['status']}")
    run = client.json("/research/historical-tasks", token=researcher,
                      payload={"dataset_version_id": dataset["id"], "groups": 5})
    deadline = time.monotonic() + timeout_seconds
    while run["status"] in {"pending", "running"}:
        if time.monotonic() >= deadline:
            raise TimeoutError(f"historical task {run['id']} did not finish within {timeout_seconds}s")
        time.sleep(1)
        run = client.json(f"/research/tasks/{run['id']}", token=researcher)
    if run["status"] != "success":
        raise RuntimeError(f"historical task {run['id']} ended as {run['status']}: {run.get('error_summary')}")

    output_dir.mkdir(parents=True, exist_ok=False)
    exports = {
        f"/research/tasks/{run['id']}/reproducibility.json": "reproducibility.json",
        f"/research/tasks/{run['id']}/historical-audit/daily.csv": "daily.csv",
        f"/research/tasks/{run['id']}/historical-audit/unlabeled.csv": "unlabeled.csv",
        f"/reports/{run['id']}/download": "report.html",
    }
    for route, name in exports.items():
        content, headers = client.request(route, token=researcher)
        disposition = next((value for key, value in headers.items() if key.lower() == "content-disposition"), "")
        if "attachment" not in disposition.lower():
            raise ValueError(f"{route}: missing attachment disposition")
        (output_dir / name).write_bytes(content)
    counts = verify_exports(output_dir / "reproducibility.json", output_dir / "daily.csv",
                            output_dir / "unlabeled.csv", output_dir / "report.html")
    verify_journey_binding(load_verified_export(output_dir / "reproducibility.json"),
                           run_id=run["id"], dataset_id=dataset["id"], bundle_id=bundle_id)
    return {"dataset_id": dataset["id"], "run_id": run["id"], "status": run["status"], **counts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", required=True, help="API v1 URL of the isolated stack")
    parser.add_argument("--bundle-id", required=True, help="Locally available sealed CSI 300 bundle ID")
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for the four HTTP exports")
    parser.add_argument("--acknowledge-isolated-writes", action="store_true",
                        help="Confirm this may create dataset and task records in the target stack")
    args = parser.parse_args(argv)
    if not args.acknowledge_isolated_writes:
        parser.error("this creates records; use only an isolated stack and pass --acknowledge-isolated-writes")
    admin_password = os.getenv("FACTORLAB_HISTORICAL_ADMIN_PASSWORD")
    researcher_password = os.getenv("FACTORLAB_HISTORICAL_RESEARCHER_PASSWORD")
    if not admin_password or not researcher_password:
        parser.error("set FACTORLAB_HISTORICAL_ADMIN_PASSWORD and FACTORLAB_HISTORICAL_RESEARCHER_PASSWORD")
    try:
        result = run_journey(ApiClient(args.api_url), bundle_id=args.bundle_id,
                             admin_password=admin_password, researcher_password=researcher_password,
                             output_dir=args.output_dir)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, TimeoutError) as exc:
        print(f"FAIL historical API journey: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
