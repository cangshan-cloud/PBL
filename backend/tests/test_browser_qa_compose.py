"""Pure contract tests for the isolated browser-QA Compose preflight."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from verify_browser_qa_compose import SAMPLE_ROOT, validate_config


class BrowserQaComposeTests(unittest.TestCase):
    project = "factorlab-browser-qa-unit"

    def fixture(self, runtime: Path) -> dict:
        mounts = [
            {"type": "bind", "source": str(SAMPLE_ROOT), "target": "/data/sample", "read_only": True},
            {"type": "bind", "source": str(runtime), "target": "/data/runtime", "read_only": False},
        ]
        return {
            "name": self.project,
            "networks": {"default": {"name": f"{self.project}_default"}},
            "volumes": {"postgres_data": {"name": f"{self.project}_postgres_data"}},
            "services": {
                "web": {"ports": [{"host_ip": "127.0.0.1", "published": "15121", "target": 5173}],
                        "healthcheck": {"test": ["CMD", "node", "-e", "fetch('http://127.0.0.1:5173/')"]},
                        "environment": {"VITE_API_BASE_URL": "http://127.0.0.1:18021/api/v1"}},
                "api": {"ports": [{"host_ip": "127.0.0.1", "published": "18021", "target": 8000}],
                        "environment": {"CORS_ORIGINS": "http://127.0.0.1:15121,http://localhost:15121",
                                        "DATABASE_URL": "postgresql+psycopg://user:pass@db:5432/factorlab",
                                        "REDIS_URL": "redis://redis:6379/0"},
                        "volumes": copy.deepcopy(mounts)},
                "worker": {"environment": {"DATABASE_URL": "postgresql+psycopg://user:pass@db:5432/factorlab",
                                           "REDIS_URL": "redis://redis:6379/0"},
                           "volumes": copy.deepcopy(mounts)},
                "db": {"volumes": [{"type": "volume", "source": "postgres_data",
                                      "target": "/var/lib/postgresql/data"}]}, "redis": {},
            },
        }

    def test_accepts_separate_project_ports_volume_and_runtime(self):
        with tempfile.TemporaryDirectory(prefix="factorlab-browser-qa-") as directory:
            validate_config(self.fixture(Path(directory)), self.project, Path(directory))

    def test_rejects_main_project_and_runtime_or_extra_mount(self):
        with tempfile.TemporaryDirectory(prefix="factorlab-browser-qa-") as directory:
            runtime = Path(directory)
            config = self.fixture(runtime)
            with self.assertRaisesRegex(ValueError, "project name"):
                validate_config(config, "fbl", runtime)
            with self.assertRaisesRegex(ValueError, "dedicated"):
                validate_config(config, self.project, Path(tempfile.gettempdir()))
            config["services"]["worker"]["volumes"].append({"source": "/", "target": "/host"})
            with self.assertRaisesRegex(ValueError, "only sample"):
                validate_config(config, self.project, runtime)

    def test_rejects_port_sample_cors_and_volume_regressions(self):
        with tempfile.TemporaryDirectory(prefix="factorlab-browser-qa-") as directory:
            runtime = Path(directory)
            original = self.fixture(runtime)
            cases = [
                (lambda c: c["services"]["api"]["ports"][0].update({"published": "8000"}), "isolated loopback"),
                (lambda c: c["services"]["api"]["volumes"][0].update({"read_only": False}), "read-only"),
                (lambda c: c["services"]["api"]["environment"].update({"CORS_ORIGINS": "*"}), "CORS"),
                (lambda c: c["volumes"]["postgres_data"].update({"name": "fbl_postgres_data"}), "scoped"),
                (lambda c: c["services"]["db"]["volumes"][0].update({"source": "main_data"}), "project-scoped"),
                (lambda c: c["services"]["worker"]["environment"].update({"DATABASE_URL": "postgresql://user:pass@localhost:5432/factorlab"}), "Compose-local"),
                (lambda c: c["services"]["web"].pop("healthcheck"), "Web is missing a healthcheck"),
            ]
            for mutate, error in cases:
                config = copy.deepcopy(original)
                mutate(config)
                with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                    validate_config(config, self.project, runtime)


if __name__ == "__main__":
    unittest.main()
