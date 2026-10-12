"""Full HTTP journey using isolated SQLite and uploaded CSV, without Docker or network."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app


SAMPLE_CSV = Path(__file__).resolve().parents[2] / "data" / "sample" / "daily_prices.csv"


class ApiJourneyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )

        def isolated_db():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_db] = isolated_db
        self.env = patch.dict(os.environ, {
            "DATA_ROOT": self.temp_dir.name,
            "TASK_EXECUTION_MODE": "inline",
            "JWT_SECRET": "isolated-api-journey-test-secret",
        })
        self.env.start()
        self.engine_patch = patch("app.main.engine", self.engine)
        self.engine_patch.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        app.dependency_overrides.clear()
        self.engine_patch.stop()
        self.env.stop()
        self.engine.dispose()
        self.temp_dir.cleanup()

    def auth(self, username: str, password: str) -> dict[str, str]:
        response = self.client.post("/api/v1/auth/login", json={"username": username, "password": password})
        self.assertEqual(response.status_code, 200, response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_upload_publish_research_report_and_role_boundaries(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        viewer = self.auth("viewer", "viewer12345")
        csv_content = SAMPLE_CSV.read_bytes()

        unauthenticated = self.client.get("/api/v1/datasets")
        self.assertEqual(unauthenticated.status_code, 401)
        denied_import = self.client.post(
            "/api/v1/datasets/import", headers=viewer,
            data={"dataset_key": "journey_data", "name": "课程验收样本"},
            files={"file": ("daily_prices.csv", csv_content, "text/csv")},
        )
        self.assertEqual(denied_import.status_code, 403)

        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "journey_data", "name": "课程验收样本"},
            files={"file": ("daily_prices.csv", csv_content, "text/csv")},
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset = imported.json()
        self.assertEqual(dataset["status"], "draft")
        self.assertEqual(dataset["row_count"], 2400)
        dataset_id = dataset["id"]

        preview = self.client.get(f"/api/v1/datasets/{dataset_id}/preview", headers=researcher)
        self.assertEqual(preview.status_code, 200, preview.text)
        self.assertEqual(preview.json()["preview_count"], 20)
        self.assertEqual(self.client.post(f"/api/v1/datasets/{dataset_id}/publish", headers=viewer).status_code, 403)
        unpublished_run = self.client.post(
            "/api/v1/research/tasks", headers=researcher,
            json={"dataset_version_id": dataset_id, "factor": "momentum_20d"},
        )
        self.assertEqual(unpublished_run.status_code, 400)

        published = self.client.post(f"/api/v1/datasets/{dataset_id}/publish", headers=admin)
        self.assertEqual(published.status_code, 200, published.text)
        self.assertEqual(published.json()["status"], "published")
        self.assertEqual(self.client.post(
            "/api/v1/research/tasks", headers=viewer,
            json={"dataset_version_id": dataset_id},
        ).status_code, 403)

        created = self.client.post(
            "/api/v1/research/tasks", headers=researcher,
            json={"dataset_version_id": dataset_id, "factor": "momentum_20d", "groups": 5},
        )
        self.assertEqual(created.status_code, 201, created.text)
        task = created.json()
        self.assertEqual(task["status"], "success")
        self.assertEqual(task["dataset_version_id"], dataset_id)
        self.assertGreater(task["result"]["coverage"], 0)
        task_id = task["id"]

        logs = self.client.get(f"/api/v1/research/tasks/{task_id}/logs", headers=researcher)
        self.assertEqual(logs.status_code, 200, logs.text)
        self.assertTrue(any(item["event"] == "completed" for item in logs.json()))
        bundle = self.client.get(f"/api/v1/research/tasks/{task_id}/reproducibility.json", headers=researcher)
        self.assertEqual(bundle.status_code, 200, bundle.text)
        self.assertEqual(bundle.json()["dataset"]["checksum_sha256"], dataset["checksum"])
        self.assertEqual(bundle.json()["result"]["coverage"], task["result"]["coverage"])

        report = self.client.get(f"/api/v1/reports/{task_id}/download", headers=researcher)
        self.assertEqual(report.status_code, 200, report.text)
        self.assertIn("因子研究报告", report.text)
        self.assertIn("attachment", report.headers["content-disposition"])
        self.assertEqual(self.client.get(f"/api/v1/reports/{task_id}/html", headers=viewer).status_code, 200)

        second = self.client.post(
            "/api/v1/users", headers=admin,
            json={"username": "second_researcher", "display_name": "第二研究员", "password": "second-pass123", "role": "researcher"},
        )
        self.assertEqual(second.status_code, 201, second.text)
        other_researcher = self.auth("second_researcher", "second-pass123")
        self.assertFalse(any(item["id"] == task_id for item in self.client.get("/api/v1/research/tasks", headers=other_researcher).json()))
        for path in (
            f"/api/v1/research/tasks/{task_id}",
            f"/api/v1/research/tasks/{task_id}/logs",
            f"/api/v1/research/tasks/{task_id}/reproducibility.json",
            f"/api/v1/reports/{task_id}/download",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=other_researcher).status_code, 403)


if __name__ == "__main__":
    unittest.main()
