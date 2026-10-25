"""Safety contract tests for the isolated historical-bundle Compose override."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from verify_historical_qa_compose import BUNDLES, SAMPLE, validate_config


class HistoricalQaComposeTests(unittest.TestCase):
    project = "factorlab-historical-qa-unit"

    def fixture(self, runtime: Path) -> dict:
        mounts = [
            {"type": "bind", "source": str(SAMPLE), "target": "/data/sample", "read_only": True},
            {"type": "bind", "source": str(runtime), "target": "/data/runtime", "read_only": False},
            {"type": "bind", "source": str(BUNDLES), "target": "/data/real/bundles", "read_only": True},
        ]
        return {
            "name": self.project,
            "networks": {"default": {"name": f"{self.project}_default"}},
            "volumes": {"postgres_data": {"name": f"{self.project}_postgres_data"}},
            "services": {
                "web": {"ports": [{"host_ip": "127.0.0.1", "published": "15122", "target": 5173}],
                        "healthcheck": {"test": ["CMD", "node"]},
                        "environment": {"VITE_API_BASE_URL": "http://127.0.0.1:18022/api/v1"}},
                "api": {"ports": [{"host_ip": "127.0.0.1", "published": "18022", "target": 8000}],
                        "environment": {"CORS_ORIGINS": "http://127.0.0.1:15122,http://localhost:15122",
                                        "DATABASE_URL": "postgresql+psycopg://user:pass@db:5432/factorlab",
                                        "REDIS_URL": "redis://redis:6379/0"},
                        "volumes": copy.deepcopy(mounts)},
                "worker": {"environment": {"DATABASE_URL": "postgresql+psycopg://user:pass@db:5432/factorlab",
                                           "REDIS_URL": "redis://redis:6379/0"},
                           "volumes": copy.deepcopy(mounts)},
                "db": {"volumes": [{"type": "volume", "source": "postgres_data",
                                     "target": "/var/lib/postgresql/data"}]},
                "redis": {},
            },
        }

    def test_accepts_isolated_project(self):
        with tempfile.TemporaryDirectory(prefix="factorlab-historical-qa-") as directory:
            validate_config(self.fixture(Path(directory)), self.project, Path(directory))

    def test_rejects_main_project_and_invalid_runtime(self):
        with tempfile.TemporaryDirectory(prefix="factorlab-historical-qa-") as directory:
            runtime = Path(directory)
            config = self.fixture(runtime)
            with self.assertRaisesRegex(ValueError, "unique"):
                validate_config(config, "fbl", runtime)
            with self.assertRaisesRegex(ValueError, "dedicated"):
                validate_config(config, self.project, Path(tempfile.gettempdir()))

    def test_rejects_main_stack_ports_mounts_and_queue(self):
        with tempfile.TemporaryDirectory(prefix="factorlab-historical-qa-") as directory:
            runtime = Path(directory)
            original = self.fixture(runtime)
            cases = [
                (lambda c: c["services"]["api"]["ports"][0].update({"published": "8000"}), "isolated loopback"),
                (lambda c: c["services"]["api"]["volumes"][2].update({"read_only": False}), "mount differs"),
                (lambda c: c["services"]["worker"]["volumes"].pop(0), "three isolated mounts"),
                (lambda c: c["services"]["api"]["environment"].update({"CORS_ORIGINS": "*"}), "CORS"),
                (lambda c: c["volumes"]["postgres_data"].update({"name": "fbl_postgres_data"}), "not scoped"),
                (lambda c: c["services"]["db"]["volumes"][0].update({"source": "fbl_postgres_data"}), "project-scoped"),
                (lambda c: c["services"]["worker"]["environment"].update({"REDIS_URL": "redis://localhost:6379/0"}), "Compose-local"),
            ]
            for mutate, error in cases:
                config = copy.deepcopy(original)
                mutate(config)
                with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                    validate_config(config, self.project, runtime)


if __name__ == "__main__":
    unittest.main()
