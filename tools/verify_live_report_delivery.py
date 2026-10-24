"""Verify one existing report's archived and disclosed HTTP responses locally.

Credentials are read from environment or a hidden prompt; no report bytes are
persisted beyond a temporary directory. This does not validate browser saving.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from verify_report_delivery import verify_delivery


def _request(base: str, path: str, token: str | None = None, payload: dict | None = None) -> tuple[bytes, object]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(base + path, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read(), response.headers


def _json(body: bytes, label: str) -> object:
    try:
        return json.loads(body)
    except (UnicodeError, ValueError) as exc:
        raise ValueError(f"{label} is not JSON") from exc


def verify_live(base: str, username: str, password: str, run_prefix: str, browser_file: Path | None = None) -> dict:
    parsed = urllib.parse.urlparse(base)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.path.rstrip("/") != "/api/v1":
        raise ValueError("base URL must be local http://127.0.0.1:8000/api/v1 or localhost equivalent")
    if not run_prefix or any(char not in "0123456789abcdef-" for char in run_prefix.lower()):
        raise ValueError("run prefix must contain only hex digits or hyphens")
    login, _ = _request(base, "/auth/login", payload={"username": username, "password": password})
    token = _json(login, "login response").get("access_token")
    if not isinstance(token, str) or not token:
        raise ValueError("login response has no access token")
    listed, _ = _request(base, "/reports", token)
    reports = _json(listed, "report list")
    if not isinstance(reports, list):
        raise ValueError("report list is not an array")
    matches = [item for item in reports if isinstance(item, dict) and isinstance(item.get("run_id"), str)
               and item["run_id"].startswith(run_prefix)]
    if len(matches) != 1:
        raise ValueError(f"run prefix matches {len(matches)} reports; require exactly one")
    summary = matches[0]
    run_id = summary["run_id"]
    dataset_id = summary.get("dataset_version_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("report summary has no dataset version ID")
    dataset_bytes, _ = _request(base, f"/datasets/{urllib.parse.quote(dataset_id, safe='')}", token)
    dataset = _json(dataset_bytes, "dataset metadata")
    original, original_headers = _request(base, f"/reports/{run_id}/download", token)
    delivered, delivery_headers = _request(base, f"/reports/{run_id}/delivery", token)
    for label, headers in (("archive", original_headers), ("delivery", delivery_headers)):
        if not headers.get("Content-Type", "").lower().startswith("text/html"):
            raise ValueError(f"{label} response is not HTML")
    if delivery_headers.get("X-Archived-Report-SHA256") != summary.get("checksum"):
        raise ValueError("delivery HTTP checksum header differs from report summary")
    with tempfile.TemporaryDirectory(prefix="factorlab-delivery-qa-") as directory:
        root = Path(directory)
        archive_path, delivery_path = root / "archive.html", root / "delivery.html"
        dataset_path, summary_path = root / "dataset.json", root / "summary.json"
        archive_path.write_bytes(original)
        delivery_path.write_bytes(delivered)
        dataset_path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")
        summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
        result = verify_delivery(archive_path, delivery_path, dataset_path, summary_path)
    browser_file_verified = None
    if browser_file is not None:
        saved = browser_file.read_bytes()
        if saved != delivered:
            raise ValueError("browser-saved file differs from delivery HTTP bytes")
        browser_file_verified = True
    return {**result, "archive_bytes": len(original), "delivery_bytes": len(delivered),
            "delivery_sha256": hashlib.sha256(delivered).hexdigest(), "http_checked": True,
            "browser_file_verified": browser_file_verified}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_prefix", help="Unique prefix of an existing report Run ID")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--browser-file", type=Path, help="Optional browser-downloaded HTML to compare byte for byte")
    args = parser.parse_args()
    password = os.environ.get("FACTORLAB_QA_PASSWORD") or getpass.getpass("Local account password: ")
    try:
        print(json.dumps(verify_live(args.base_url.rstrip("/"), args.username, password, args.run_prefix, args.browser_file), ensure_ascii=False))
    except (OSError, urllib.error.URLError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f"verification failed: {exc}\n")


if __name__ == "__main__":
    main()
