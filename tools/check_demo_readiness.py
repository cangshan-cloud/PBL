"""Read-only preflight for the course demo: accounts, catalog, and API views.

Set FACTORLAB_DEMO_ADMIN_PASSWORD, FACTORLAB_DEMO_RESEARCHER_PASSWORD, and
FACTORLAB_DEMO_VIEWER_PASSWORD before use. This script creates no research run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


FACTORS = {"momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d", "market_cap", "pe"}
DEMO_DAILY_020_SHA256 = "c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e"
ROLES = ("admin", "researcher", "viewer")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, *, token: str | None = None, payload: dict | None = None,
                timeout: int = 10) -> object:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        request = Request(f"{self.base_url}{path}", data=data, headers=headers,
                          method="POST" if payload is not None else "GET")
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            raise RuntimeError(f"{path}: HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"{path}: connection failed: {exc.reason}") from exc

    def download_report(self, run_id: str, *, token: str, timeout: int = 10) -> bytes:
        path = f"/reports/{run_id}/download"
        request = Request(f"{self.base_url}{path}", headers={
            "Accept": "text/html", "Authorization": f"Bearer {token}",
        })
        try:
            with urlopen(request, timeout=timeout) as response:
                if "text/html" not in response.headers.get("Content-Type", ""):
                    raise ValueError(f"{path}: response is not HTML")
                content = response.read(10 * 1024 * 1024 + 1)
        except HTTPError as exc:
            raise RuntimeError(f"{path}: HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"{path}: connection failed: {exc.reason}") from exc
        if len(content) > 10 * 1024 * 1024:
            raise ValueError(f"{path}: report exceeds 10 MiB preflight limit")
        return content


def check_web_page(url: str) -> None:
    """Require the browser entry page, not merely a healthy API container."""
    try:
        with urlopen(Request(url, headers={"Accept": "text/html"}), timeout=10) as response:
            content_type = response.headers.get("Content-Type", "")
            html = response.read(128 * 1024).decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise RuntimeError(f"web entry is unavailable: {exc}") from exc
    if "text/html" not in content_type or "<title>FactorLab" not in html or 'id="root"' not in html:
        raise ValueError("web entry is not the FactorLab page")


def check_active_task_age(tasks: list[dict], max_age_minutes: int, *, now: datetime | None = None) -> str:
    if max_age_minutes <= 0:
        raise ValueError("max active task age must be a positive number of minutes")
    now = now or datetime.now(timezone.utc)
    stale = []
    for item in tasks:
        status = item.get("status")
        if status not in {"pending", "running"}:
            continue
        timestamp_key = "queued_at" if status == "pending" else "started_at"
        raw = item.get(timestamp_key)
        try:
            timestamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError(f"active task {item.get('id', '<unknown>')} has invalid {timestamp_key}") from exc
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age_minutes = (now - timestamp).total_seconds() / 60
        if age_minutes > max_age_minutes:
            stale.append(f"{item.get('id', '<unknown>')} ({status}, {age_minutes:.0f} min)")
    if stale:
        raise ValueError(f"{len(stale)} active task(s) older than {max_age_minutes} min: " + "; ".join(stale[:5]))
    return f"no pending/running task older than {max_age_minutes} min"


def check_readiness(client: ApiClient, passwords: dict[str, str], *, require_historical: bool = False,
                    require_report_fallback: bool = False, max_active_age_minutes: int | None = None) -> list[str]:
    tokens = {}
    for role in ROLES:
        password = passwords.get(role)
        if not password:
            raise ValueError(f"missing {role} password")
        login = client.request("/auth/login", payload={"username": role, "password": password})
        token = login["access_token"]
        identity = client.request("/auth/me", token=token)
        if identity["role"] != role or not identity["is_active"]:
            raise ValueError(f"{role} account has unexpected role or is inactive")
        tokens[role] = token

    datasets = client.request("/datasets", token=tokens["admin"])
    demo = next((item for item in datasets if item["dataset_key"] == "demo_daily" and
                 item["version"] == "0.2.0" and item["status"] == "published"), None)
    if not demo or demo["row_count"] != 2400 or demo["symbol_count"] != 20:
        raise ValueError("published demo_daily 0.2.0 with 2400 rows and 20 symbols is unavailable")
    if demo.get("checksum") != DEMO_DAILY_020_SHA256:
        raise ValueError("published demo_daily 0.2.0 checksum differs from the pinned course-demo snapshot")
    demo_preview = client.request(f"/datasets/{demo['id']}/preview", token=tokens["admin"])
    if demo_preview.get("dataset_id") != demo["id"] or demo_preview.get("total_rows") != 2400:
        raise ValueError("demo_daily file preview does not match the published catalog")
    catalog = client.request("/factors", token=tokens["researcher"])
    if not FACTORS.issubset({item["id"] for item in catalog}):
        raise ValueError("six required built-in factors are unavailable")
    tasks = client.request("/research/tasks", token=tokens["viewer"])
    reports = client.request("/reports", token=tokens["viewer"])
    if not isinstance(tasks, list) or not isinstance(reports, list):
        raise ValueError("viewer task or report listing is unavailable")

    checks = ["three demo accounts and roles", "verified demo_daily 0.2.0 file (2400 rows / 20 symbols)",
              "six built-in factors", "viewer task and report listings"]
    if max_active_age_minutes is not None:
        checks.append(check_active_task_age(tasks, max_active_age_minutes))
    if require_report_fallback:
        demo_runs = {item["id"] for item in tasks if item.get("dataset_version_id") == demo["id"] and
                     item.get("status") == "success"}
        candidates = [item for item in reports if item.get("run_id") in demo_runs]
        if not candidates:
            raise ValueError("no successful demo_daily 0.2.0 report is available for fallback")
        failures = []
        for item in candidates:
            run_id = item["run_id"]
            try:
                content = client.download_report(run_id, token=tokens["viewer"])
                if not content or hashlib.sha256(content).hexdigest() != item.get("checksum"):
                    raise ValueError("download checksum mismatch or empty report")
                checks.append(f"verified demo report fallback {run_id} (viewer download and SHA-256)")
                break
            except (RuntimeError, ValueError) as exc:
                failures.append(f"{run_id}: {exc}")
        else:
            raise ValueError("no demo report fallback passed download verification: " + "; ".join(failures))
    if require_historical:
        historical = [item for item in datasets if item["dataset_key"] == "hs300_2024" and
                      item["status"] == "published" and
                      (item.get("quality_report") or {}).get("dataset_kind") == "hs300_bundle_v1"]
        if not historical:
            raise ValueError("no published historical CSI 300 bundle in the platform catalog")
        failures = []
        for item in historical:
            try:
                preview = client.request(f"/datasets/{item['id']}/preview", token=tokens["admin"], timeout=30)
                rows = {row["item"]: row["value"] for row in preview["rows"]}
                if (preview.get("dataset_id") == item["id"] and
                    rows.get("bundle_id") == (item.get("quality_report") or {}).get("bundle_id") and
                    int(rows.get("verified_files", "0")) > 0):
                    checks.append(f"verified historical bundle {item['version']} (file hashes checked)")
                    break
                failures.append(f"{item['version']}: preview metadata mismatch")
            except (RuntimeError, KeyError, TypeError, ValueError) as exc:
                failures.append(f"{item['version']}: {exc}")
        else:
            raise ValueError("no published historical CSI 300 bundle passed file verification: " + "; ".join(failures))
    return checks


def check_worker(*, compose_project: str | None = None) -> None:
    """Ping Celery through the selected Compose worker without creating a task."""
    command = ["docker", "compose"]
    if compose_project:
        command.extend(["-p", compose_project])
    command.extend(["exec", "-T", "worker", "celery", "-A", "app.tasks:celery_app",
                    "inspect", "ping", "--timeout=5"])
    try:
        result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"worker ping could not run: {exc}") from exc
    if result.returncode != 0 or not re.search(r"(?m)^\s*pong\s*$", result.stdout):
        detail = (result.stderr or result.stdout).strip()[:300]
        raise RuntimeError(f"worker did not answer Celery ping (exit {result.returncode}): {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default=os.getenv("FACTORLAB_DEMO_API_URL", "http://127.0.0.1:8000/api/v1"))
    parser.add_argument("--web-url", default=os.getenv("FACTORLAB_DEMO_WEB_URL", "http://127.0.0.1:5173/"))
    parser.add_argument("--require-historical", action="store_true", help="Require a published CSI 300 bundle with intact local files")
    parser.add_argument("--require-report-fallback", action="store_true",
                        help="Require a downloadable, checksum-valid report from a successful demo_daily 0.2.0 task")
    parser.add_argument("--check-worker", action="store_true", help="Read-only Celery ping through Docker Compose")
    parser.add_argument("--max-active-age-minutes", type=int,
                        help="Fail if a pending/running task has exceeded this age; read-only stale-task warning")
    parser.add_argument("--compose-project", help="Compose project for --check-worker; defaults to the repository project")
    args = parser.parse_args()
    if args.compose_project and not args.check_worker:
        parser.error("--compose-project requires --check-worker")
    if args.max_active_age_minutes is not None and args.max_active_age_minutes <= 0:
        parser.error("--max-active-age-minutes must be positive")
    passwords = {role: os.getenv(f"FACTORLAB_DEMO_{role.upper()}_PASSWORD", "") for role in ROLES}
    try:
        check_web_page(args.web_url)
        checks = check_readiness(ApiClient(args.api_url), passwords, require_historical=args.require_historical,
                                 require_report_fallback=args.require_report_fallback,
                                 max_active_age_minutes=args.max_active_age_minutes)
        if args.check_worker:
            check_worker(compose_project=args.compose_project)
            checks.append("Celery worker answered Compose ping")
    except (RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL 演示就绪检查：{exc}", file=sys.stderr)
        return 1
    print("PASS FactorLab web entry reachable from this host")
    for check in checks:
        print(f"PASS {check}")
    unchecked = ["新任务执行", "浏览器交互"]
    if not args.require_report_fallback:
        unchecked.insert(1, "报告内容")
    if not args.check_worker:
        unchecked.append("Worker")
    print("只读预检通过；尚未验证" + "、".join(unchecked) + "。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
