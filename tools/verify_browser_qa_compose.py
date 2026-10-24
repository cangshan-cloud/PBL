"""Preflight the isolated browser-QA Compose contract without starting services."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = (PROJECT_ROOT / "data" / "sample").resolve()
MAIN_RUNTIME = (PROJECT_ROOT / "data" / "runtime").resolve()


def validate_config(config: dict, project: str, runtime: Path) -> None:
    if not project.startswith("factorlab-browser-qa-") or project == "factorlab-browser-qa-":
        raise ValueError("project name must start with factorlab-browser-qa- and have a unique suffix")
    if config.get("name") != project:
        raise ValueError("Compose project name differs from requested isolated project")
    resolved_runtime = runtime.resolve()
    if not runtime.is_dir() or not runtime.is_absolute() or resolved_runtime == MAIN_RUNTIME:
        raise ValueError("runtime must be an existing absolute directory outside the main runtime")
    if PROJECT_ROOT == resolved_runtime or PROJECT_ROOT in resolved_runtime.parents:
        raise ValueError("runtime must not be inside the repository")
    temp_roots = {Path(tempfile.gettempdir()).resolve(), Path("/private/tmp").resolve()}
    if resolved_runtime.parent not in temp_roots or not resolved_runtime.name.startswith("factorlab-browser-qa-"):
        raise ValueError("runtime must be a dedicated factorlab-browser-qa-* directory in the system temp folder")
    services = config["services"]
    if set(services) != {"web", "api", "worker", "db", "redis"}:
        raise ValueError("isolated Compose service set differs from five-service contract")
    if not services["web"].get("healthcheck"):
        raise ValueError("isolated Web is missing a healthcheck")
    expected_ports = {"web": (15121, 5173), "api": (18021, 8000)}
    for name, (published, target) in expected_ports.items():
        ports = services[name].get("ports", [])
        if len(ports) != 1 or ports[0].get("host_ip") != "127.0.0.1" or int(ports[0].get("published", -1)) != published or int(ports[0].get("target", -1)) != target:
            raise ValueError(f"{name} must publish only isolated loopback port {published}:{target}")
    if any(services[name].get("ports") for name in ("worker", "db", "redis")):
        raise ValueError("worker, db, and redis must not publish host ports")
    if services["web"]["environment"].get("VITE_API_BASE_URL") != "http://127.0.0.1:18021/api/v1":
        raise ValueError("Web API URL differs from isolated API port")
    if set(services["api"]["environment"].get("CORS_ORIGINS", "").split(",")) != {"http://127.0.0.1:15121", "http://localhost:15121"}:
        raise ValueError("API CORS origins differ from isolated Web port")
    for name in ("api", "worker"):
        mounts = services[name].get("volumes", [])
        if len(mounts) != 2:
            raise ValueError(f"{name} must have only sample and isolated runtime mounts")
        by_target = {mount.get("target"): mount for mount in mounts}
        sample = by_target.get("/data/sample", {})
        data = by_target.get("/data/runtime", {})
        if sample.get("type") != "bind" or Path(sample.get("source", "")).resolve() != SAMPLE_ROOT or sample.get("read_only") is not True:
            raise ValueError(f"{name} sample mount must be read-only repository sample data")
        if data.get("type") != "bind" or Path(data.get("source", "")).resolve() != resolved_runtime or data.get("read_only") is True:
            raise ValueError(f"{name} runtime mount differs from requested isolated directory")
        database_url = services[name]["environment"].get("DATABASE_URL", "")
        if "@db:5432/" not in database_url or services[name]["environment"].get("REDIS_URL") != "redis://redis:6379/0":
            raise ValueError(f"{name} must use Compose-local database and queue")
    db_mounts = services["db"].get("volumes", [])
    if len(db_mounts) != 1 or db_mounts[0].get("type") != "volume" or db_mounts[0].get("source") != "postgres_data" or db_mounts[0].get("target") != "/var/lib/postgresql/data":
        raise ValueError("PostgreSQL container must use only its project-scoped volume")
    volume = config.get("volumes", {}).get("postgres_data", {})
    if volume.get("name") != f"{project}_postgres_data":
        raise ValueError("PostgreSQL volume is not scoped to isolated project")
    if config.get("networks", {}).get("default", {}).get("name") != f"{project}_default":
        raise ValueError("network is not scoped to isolated project")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--runtime-dir", required=True, type=Path)
    args = parser.parse_args()
    env = {**os.environ, "FACTORLAB_QA_RUNTIME_DIR": str(args.runtime_dir)}
    command = ["docker", "compose", "-p", args.project_name, "-f", "docker-compose.yml",
               "-f", "docker-compose.browser-qa.yml", "config", "--format", "json"]
    try:
        result = subprocess.run(command, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, check=True)
        validate_config(json.loads(result.stdout), args.project_name, args.runtime_dir)
    except (OSError, subprocess.CalledProcessError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL isolated browser-QA Compose preflight: {exc}", file=sys.stderr)
        return 1
    print(f"PASS isolated browser-QA Compose project={args.project_name} ports=15121/18021 runtime={args.runtime_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
