"""Read-only latency check for ordinary FactorLab views on a local stack.

Set FACTORLAB_DEMO_VIEWER_PASSWORD. Authentication issues one token; all timed
business requests are GETs and do not create datasets, research runs or reports.
The result measures response + JSON decoding, not browser rendering.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import urlsplit

from check_demo_readiness import ApiClient, check_web_page


ENDPOINTS = (
    ("overview", "/dashboard", dict),
    ("datasets", "/datasets", list),
    ("factors", "/factors", list),
    ("tasks", "/research/tasks", list),
    ("reports", "/reports", list),
)


def require_loopback_url(value: str, *, api: bool) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("benchmark URLs must use a local loopback HTTP(S) host without credentials or query")
    if api and not parsed.path.rstrip("/").endswith("/api/v1"):
        raise ValueError("API URL must end with /api/v1")
    return value


def measure(label: str, request, *, samples: int, limit_seconds: float, timer=perf_counter) -> dict:
    elapsed = []
    for _ in range(samples + 1):
        started = timer()
        request()
        elapsed.append(timer() - started)
    first, repeats = elapsed[0], elapsed[1:]
    return {
        "view": label,
        "first_read_seconds": round(first, 4),
        "repeat_seconds": [round(value, 4) for value in repeats],
        "repeat_median_seconds": round(statistics.median(repeats), 4),
        "max_seconds": round(max(elapsed), 4),
        "passed": max(elapsed) <= limit_seconds,
    }


def measure_views(client: ApiClient, token: str, web_url: str, *, samples: int, limit_seconds: float,
                  timer=perf_counter) -> list[dict]:
    results = [measure("web_entry", lambda: check_web_page(web_url), samples=samples,
                       limit_seconds=limit_seconds, timer=timer)]
    for label, path, expected_type in ENDPOINTS:
        item_count = None

        def read_view(path=path, expected_type=expected_type):
            nonlocal item_count
            response = client.request(path, token=token)
            if not isinstance(response, expected_type):
                raise ValueError(f"{path}: unexpected response shape")
            if isinstance(response, list):
                item_count = len(response)

        result = measure(label, read_view, samples=samples, limit_seconds=limit_seconds, timer=timer)
        if item_count is not None:
            result["item_count"] = item_count
        results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--web-url", default="http://127.0.0.1:5173/")
    parser.add_argument("--samples", type=int, default=5, help="Repeat reads per view, plus one first read (not server cold start)")
    parser.add_argument("--limit-seconds", type=float, default=2.0)
    args = parser.parse_args(argv)
    if args.samples < 3 or args.limit_seconds <= 0:
        parser.error("samples must be >= 3 and limit-seconds must be positive")
    try:
        api_url = require_loopback_url(args.api_url, api=True)
        web_url = require_loopback_url(args.web_url, api=False)
    except ValueError as exc:
        parser.error(str(exc))
    password = os.getenv("FACTORLAB_DEMO_VIEWER_PASSWORD")
    if not password:
        parser.error("set FACTORLAB_DEMO_VIEWER_PASSWORD (never put it in the output file)")

    client = ApiClient(api_url)
    try:
        login = client.request("/auth/login", payload={"username": "viewer", "password": password})
        token = login["access_token"]
        identity = client.request("/auth/me", token=token)
        if identity["role"] != "viewer" or not identity["is_active"]:
            raise ValueError("viewer account is not active with the expected role")
        results = measure_views(client, token, web_url, samples=args.samples, limit_seconds=args.limit_seconds)
    except (RuntimeError, ValueError, KeyError, TypeError, OSError) as exc:
        print(f"Latency benchmark failed: {ascii(str(exc))}", file=sys.stderr)
        return 1
    report = {
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "scope": "local HTTP response and JSON decoding; excludes browser rendering, downloads, and writes",
        "api_url": api_url,
        "web_url": web_url,
        "repeat_samples_per_view": args.samples,
        "limit_seconds": args.limit_seconds,
        "views": results,
        "passed": all(item["passed"] for item in results),
    }
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
