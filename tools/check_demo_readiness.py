"""Read-only preflight for the course demo: accounts, catalog, and API views.

Set FACTORLAB_DEMO_ADMIN_PASSWORD, FACTORLAB_DEMO_RESEARCHER_PASSWORD, and
FACTORLAB_DEMO_VIEWER_PASSWORD before use. This script creates no research run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


FACTORS = {"momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d", "market_cap", "pe"}
ROLES = ("admin", "researcher", "viewer")


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, *, token: str | None = None, payload: dict | None = None) -> object:
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
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            raise RuntimeError(f"{path}: HTTP {exc.code}") from exc
        except URLError as exc:
            raise RuntimeError(f"{path}: connection failed: {exc.reason}") from exc


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


def check_readiness(client: ApiClient, passwords: dict[str, str], *, require_historical: bool = False) -> list[str]:
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
    catalog = client.request("/factors", token=tokens["researcher"])
    if not FACTORS.issubset({item["id"] for item in catalog}):
        raise ValueError("six required built-in factors are unavailable")
    tasks = client.request("/research/tasks", token=tokens["viewer"])
    reports = client.request("/reports", token=tokens["viewer"])
    if not isinstance(tasks, list) or not isinstance(reports, list):
        raise ValueError("viewer task or report listing is unavailable")

    checks = ["three demo accounts and roles", "published demo_daily 0.2.0 (2400 rows / 20 symbols)",
              "six built-in factors", "viewer task and report listings"]
    if require_historical:
        historical = next((item for item in datasets if item["dataset_key"] == "hs300_2024" and
                           item["status"] == "published" and
                           (item.get("quality_report") or {}).get("dataset_kind") == "hs300_bundle_v1"), None)
        if historical is None:
            raise ValueError("no published historical CSI 300 bundle in the platform catalog")
        checks.append(f"published historical bundle {historical['version']} (catalog only)")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default=os.getenv("FACTORLAB_DEMO_API_URL", "http://127.0.0.1:8000/api/v1"))
    parser.add_argument("--web-url", default=os.getenv("FACTORLAB_DEMO_WEB_URL", "http://127.0.0.1:5173/"))
    parser.add_argument("--require-historical", action="store_true", help="Require a published CSI 300 bundle catalog entry")
    args = parser.parse_args()
    passwords = {role: os.getenv(f"FACTORLAB_DEMO_{role.upper()}_PASSWORD", "") for role in ROLES}
    try:
        check_web_page(args.web_url)
        checks = check_readiness(ApiClient(args.api_url), passwords, require_historical=args.require_historical)
    except (RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(f"FAIL 演示就绪检查：{exc}", file=sys.stderr)
        return 1
    print("PASS FactorLab web entry reachable from this host")
    for check in checks:
        print(f"PASS {check}")
    print("只读预检通过；尚未验证新任务执行、报告内容、浏览器和 Worker。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
