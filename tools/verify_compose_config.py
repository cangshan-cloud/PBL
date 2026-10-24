"""Check the Compose contract without starting containers or exposing secrets."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POSTGRES = {"POSTGRES_DB": "verify_db", "POSTGRES_USER": "verify_user", "POSTGRES_PASSWORD": "verify_pass_123"}


def main() -> int:
    env = {**os.environ, **POSTGRES}
    try:
        process = subprocess.run(
            ["docker", "compose", "config", "--format", "json"],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        print("FAIL Docker Compose config could not be read; check Docker CLI and compose file.", file=sys.stderr)
        return 1

    services = json.loads(process.stdout)["services"]
    expected_url = "postgresql+psycopg://verify_user:verify_pass_123@db:5432/verify_db"
    for name in ("api", "worker"):
        if services[name]["environment"]["DATABASE_URL"] != expected_url:
            raise ValueError(f"{name} database URL differs from PostgreSQL credentials")
    if any(services["db"]["environment"][key] != value for key, value in POSTGRES.items()):
        raise ValueError("PostgreSQL container credentials differ from Compose inputs")

    for name, port in (("web", 5173), ("api", 8000)):
        ports = services[name].get("ports", [])
        if len(ports) != 1 or ports[0]["host_ip"] != "127.0.0.1" or int(ports[0]["published"]) != port:
            raise ValueError(f"{name} must publish only port {port} on 127.0.0.1")
    for name in ("db", "redis", "worker"):
        if services[name].get("ports"):
            raise ValueError(f"{name} must not publish a host port")
    for name in ("web", "api", "worker", "db", "redis"):
        if not services[name].get("healthcheck"):
            raise ValueError(f"{name} is missing a healthcheck")

    print("PASS Compose credentials, loopback ports, and service healthchecks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
