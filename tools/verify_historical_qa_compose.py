"""Preflight an isolated historical-bundle Compose project without starting it."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (ROOT / "data" / "sample").resolve()
BUNDLES = (ROOT / "data" / "real" / "bundles").resolve()


def validate_config(config: dict, project: str, runtime: Path) -> None:
    if not project.startswith("factorlab-historical-qa-") or project == "factorlab-historical-qa-":
        raise ValueError("project must use a unique factorlab-historical-qa-* name")
    if config.get("name") != project:
        raise ValueError("Compose project name differs from requested project")
    resolved = runtime.resolve()
    temp_roots = {Path(tempfile.gettempdir()).resolve(), Path("/private/tmp").resolve()}
    if (not runtime.is_absolute() or not runtime.is_dir() or resolved.parent not in temp_roots or
            not resolved.name.startswith("factorlab-historical-qa-")):
        raise ValueError("runtime must be a dedicated existing factorlab-historical-qa-* temp directory")
    services = config.get("services", {})
    if set(services) != {"web", "api", "worker", "db", "redis"}:
        raise ValueError("isolated service set differs from five-service contract")
    expected_ports = {"api": (18022, 8000), "web": (15122, 5173)}
    for service, (host_port, target_port) in expected_ports.items():
        ports = services[service].get("ports", [])
        if (len(ports) != 1 or ports[0].get("host_ip") != "127.0.0.1" or
                int(ports[0].get("published", -1)) != host_port or
                int(ports[0].get("target", -1)) != target_port):
            raise ValueError(f"{service} must publish only its isolated loopback port")
    if any(services[service].get("ports") for service in ("worker", "db", "redis")):
        raise ValueError("worker, db and redis must not publish host ports")
    if services["web"]["environment"].get("VITE_API_BASE_URL") != "http://127.0.0.1:18022/api/v1":
        raise ValueError("Web must use isolated API port")
    if not services["web"].get("healthcheck"):
        raise ValueError("Web must have a healthcheck")
    allowed_origins = {"http://127.0.0.1:15122", "http://localhost:15122"}
    if set(services["api"]["environment"].get("CORS_ORIGINS", "").split(",")) != allowed_origins:
        raise ValueError("API CORS origins must use isolated Web port")
    for service in ("api", "worker"):
        mounts = services[service].get("volumes", [])
        if len(mounts) != 3:
            raise ValueError(f"{service} must have exactly three isolated mounts")
        by_target = {mount.get("target"): mount for mount in mounts}
        expected = {"/data/sample": (SAMPLE, True), "/data/runtime": (resolved, False),
                    "/data/real/bundles": (BUNDLES, True)}
        if set(by_target) != set(expected):
            raise ValueError(f"{service} mount targets differ from historical QA contract")
        for target, (source, read_only) in expected.items():
            mount = by_target[target]
            if (mount.get("type") != "bind" or Path(mount.get("source", "")).resolve() != source or
                    bool(mount.get("read_only", False)) != read_only):
                raise ValueError(f"{service} {target} mount differs from historical QA contract")
        environment = services[service]["environment"]
        if "@db:5432/" not in environment.get("DATABASE_URL", "") or environment.get("REDIS_URL") != "redis://redis:6379/0":
            raise ValueError(f"{service} must use Compose-local database and queue")
    db_mounts = services["db"].get("volumes", [])
    if (len(db_mounts) != 1 or db_mounts[0].get("target") != "/var/lib/postgresql/data" or
            db_mounts[0].get("type") != "volume" or db_mounts[0].get("source") != "postgres_data"):
        raise ValueError("database must use only its project-scoped volume")
    if config.get("volumes", {}).get("postgres_data", {}).get("name") != f"{project}_postgres_data":
        raise ValueError("PostgreSQL volume is not scoped to isolated project")
    if config.get("networks", {}).get("default", {}).get("name") != f"{project}_default":
        raise ValueError("network is not scoped to isolated project")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--runtime-dir", required=True, type=Path)
    args = parser.parse_args()
    environment = {**os.environ, "FACTORLAB_HISTORICAL_QA_RUNTIME_DIR": str(args.runtime_dir)}
    command = ["docker", "compose", "-p", args.project_name, "-f", "docker-compose.yml",
               "-f", "docker-compose.historical-qa.yml", "config", "--format", "json"]
    try:
        result = subprocess.run(command, cwd=ROOT, env=environment, capture_output=True, text=True, check=True)
        validate_config(json.loads(result.stdout), args.project_name, args.runtime_dir)
    except (OSError, subprocess.CalledProcessError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL isolated historical Compose preflight: {exc}", file=sys.stderr)
        return 1
    print(f"PASS isolated historical Compose project={args.project_name} ports=15122/18022 runtime={args.runtime_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
