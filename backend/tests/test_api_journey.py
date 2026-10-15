"""Full HTTP journey using isolated SQLite and uploaded CSV, without Docker or network."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from kombu.exceptions import OperationalError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import get_db
from app.main import app
from app.models import Artifact, DatasetVersion, Run, RunStatus, User
from app.services.runs import claim_pending_run, create_historical_run


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

    def test_default_loopback_frontends_can_preflight_login(self):
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            with self.subTest(origin=origin):
                response = self.client.options(
                    "/api/v1/auth/login",
                    headers={"Origin": origin, "Access-Control-Request-Method": "POST",
                             "Access-Control-Request-Headers": "content-type"},
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.headers.get("access-control-allow-origin"), origin)

        rejected = self.client.options(
            "/api/v1/auth/login",
            headers={"Origin": "http://localhost.evil.example:5173", "Access-Control-Request-Method": "POST"},
        )
        self.assertNotEqual(rejected.headers.get("access-control-allow-origin"), "http://localhost.evil.example:5173")

    def test_publish_blocks_tampered_or_missing_draft(self):
        admin = self.auth("admin", "admin12345")
        original = b"trade_date,symbol,close\n2025-01-02,000001.SZ,10\n"
        response = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "tamper_test", "name": "完整性测试"},
            files={"file": ("daily.csv", original, "text/csv")},
        )
        self.assertEqual(response.status_code, 201, response.text)
        dataset_id = response.json()["id"]
        with Session(self.engine) as session:
            path = Path(session.get(DatasetVersion, dataset_id).storage_uri)

        path.write_bytes(original.replace(b",10\n", b",11\n"))
        publish_url = f"/api/v1/datasets/{dataset_id}/publish"
        self.assertEqual(self.client.post(publish_url, headers=admin).status_code, 409)
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}", headers=admin).json()["status"], "draft")

        path.unlink()
        self.assertEqual(self.client.post(publish_url, headers=admin).status_code, 410)
        self.assertEqual(self.client.get(f"/api/v1/datasets/{dataset_id}", headers=admin).json()["status"], "draft")

        path.write_bytes(original)
        self.assertEqual(self.client.post(publish_url, headers=admin).status_code, 200)

    def test_selected_symbols_keep_full_dataset_market_calendar(self):
        admin = self.auth("admin", "admin12345")
        researcher = self.auth("researcher", "research12345")
        lines = ["trade_date,symbol,close,pe"]
        for index in range(7):
            for symbol in ("A", "B", "C"):
                if index == 2 and symbol in {"A", "B"}:
                    continue
                lines.append(f"2025-01-{index + 1:02d},{symbol},{10 + index},{8 + index}")
        imported = self.client.post(
            "/api/v1/datasets/import", headers=admin,
            data={"dataset_key": "calendar_gap", "name": "日历缺行样本"},
            files={"file": ("prices.csv", ("\n".join(lines) + "\n").encode(), "text/csv")},
        )
        self.assertEqual(imported.status_code, 201, imported.text)
        dataset_id = imported.json()["id"]
        self.assertEqual(imported.json()["quality_report"]["internal_calendar_gap_count"], 2)
        published = self.client.post(f"/api/v1/datasets/{dataset_id}/publish", headers=admin)
        self.assertEqual(published.status_code, 200, published.text)
        created = self.client.post(
            "/api/v1/research/tasks", headers=researcher,
            json={"dataset_version_id": dataset_id, "factor": "pe", "groups": 2, "symbols": ["A", "B"]},
        )
        self.assertEqual(created.status_code, 201, created.text)
        self.assertEqual(created.json()["status"], "success")
        self.assertEqual(created.json()["result"]["coverage"], 8)

    def test_comparison_api_and_exports_include_actual_group_dates(self):
        researcher = self.auth("researcher", "research12345")
        run_ids = []
        for factor in ("momentum_20d", "reversal_5d"):
            created = self.client.post("/api/v1/research/tasks", headers=researcher,
                                       json={"factor": factor, "groups": 5, "start_date": "2025-02-03"})
            self.assertEqual(created.status_code, 201, created.text)
            self.assertEqual(created.json()["status"], "success")
            run_ids.append(created.json()["id"])

        payload = {"run_ids": run_ids}
        compared = self.client.post("/api/v1/research/comparisons", headers=researcher, json=payload)
        self.assertEqual(compared.status_code, 200, compared.text)
        result = compared.json()
        self.assertEqual(result["common_group_date_count"], result["common_ic_date_count"])
        self.assertTrue(all(item["group_date_count"] > 0 for item in result["items"]))

        csv_export = self.client.post("/api/v1/research/comparisons/export.csv", headers=researcher, json=payload)
        self.assertEqual(csv_export.status_code, 200, csv_export.text)
        self.assertIn("共同多空分组日期数", csv_export.content.decode("utf-8-sig"))
        html_export = self.client.post("/api/v1/research/comparisons/export.html", headers=researcher, json=payload)
        self.assertEqual(html_export.status_code, 200, html_export.text)
        self.assertIn("共同多空分组日期", html_export.text)

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

    def test_failed_historical_task_retries_in_historical_mode(self):
        researcher = self.auth("researcher", "research12345")
        viewer = self.auth("viewer", "viewer12345")
        with Session(self.engine) as session:
            owner = session.query(User).filter_by(username="researcher").one()
            dataset = DatasetVersion(
                dataset_key="hs300_2024", name="retry fixture", version="retry-fixture",
                checksum="0" * 64, storage_uri="/unused/manifest.json", source_filename="manifest.json",
                quality_report={"dataset_kind": "hs300_bundle_v1"}, status="published",
            )
            session.add(dataset)
            session.commit()
            source = create_historical_run(session, {"dataset_version_id": dataset.id, "groups": 3},
                                           created_by_id=owner.id)
            source.status = RunStatus.FAILED
            source.error_summary = "isolated fixture failure"
            session.commit()
            source_id, dataset_id = source.id, dataset.id

        url = f"/api/v1/research/tasks/{source_id}/retry"
        self.assertEqual(self.client.post(url, headers=viewer).status_code, 403)
        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async") as enqueue:
            response = self.client.post(url, headers=researcher)
        self.assertEqual(response.status_code, 201, response.text)
        retried = response.json()
        self.assertNotEqual(retried["id"], source_id)
        self.assertEqual(retried["status"], "pending")
        self.assertEqual(retried["dataset_version_id"], dataset_id)
        self.assertEqual(retried["parameters"]["mode"], "historical_hs300_2024")
        self.assertEqual(retried["parameters"]["groups"], 3)
        self.assertEqual(len(retried["parameters"]["components"]), 4)
        enqueue.assert_called_once_with(args=[retried["id"]], task_id=retried["id"])
        self.assertEqual(self.client.get(f"/api/v1/research/tasks/{source_id}", headers=researcher).json()["status"],
                         "failed")
        with Session(self.engine) as session:
            session.get(DatasetVersion, dataset_id).status = "draft"
            session.commit()
        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async") as enqueue:
            unavailable = self.client.post(url, headers=researcher)
        self.assertEqual(unavailable.status_code, 400, unavailable.text)
        enqueue.assert_not_called()

    def test_broker_connection_failure_records_failed_run_and_allows_retry(self):
        researcher = self.auth("researcher", "research12345")
        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async", side_effect=OperationalError("redis unavailable")):
            response = self.client.post("/api/v1/research/tasks", headers=researcher,
                                        json={"factor": "momentum_20d", "groups": 5})
        self.assertEqual(response.status_code, 503, response.text)
        self.assertNotIn("redis unavailable", response.text)
        tasks = self.client.get("/api/v1/research/tasks", headers=researcher).json()
        self.assertEqual(len(tasks), 1)
        failed = tasks[0]
        self.assertEqual(failed["status"], "failed")
        self.assertIn("消息队列连接失败", failed["error_summary"])
        logs = self.client.get(f"/api/v1/research/tasks/{failed['id']}/logs", headers=researcher).json()
        self.assertTrue(any(item["event"] == "failed" for item in logs))
        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async") as enqueue:
            retried = self.client.post(f"/api/v1/research/tasks/{failed['id']}/retry", headers=researcher)
        self.assertEqual(retried.status_code, 201, retried.text)
        self.assertEqual(retried.json()["status"], "pending")
        enqueue.assert_called_once()

    def test_broker_error_does_not_overwrite_already_claimed_run(self):
        researcher = self.auth("researcher", "research12345")

        def claimed_then_error(*, args, task_id):
            with Session(self.engine) as session:
                _, claimed = claim_pending_run(session, task_id)
                self.assertTrue(claimed)
            raise OperationalError("redis ack unavailable")

        with patch.dict(os.environ, {"TASK_EXECUTION_MODE": "celery"}), \
             patch("app.main.execute_research_run_task.apply_async", side_effect=claimed_then_error):
            response = self.client.post("/api/v1/research/tasks", headers=researcher,
                                        json={"factor": "momentum_20d", "groups": 5})
        self.assertEqual(response.status_code, 503, response.text)
        self.assertIn("请先检查任务状态", response.json()["detail"])
        task = self.client.get("/api/v1/research/tasks", headers=researcher).json()[0]
        self.assertEqual(task["status"], "running")
        events = [item["event"] for item in self.client.get(
            f"/api/v1/research/tasks/{task['id']}/logs", headers=researcher,
        ).json()]
        self.assertEqual(events, ["queued", "started"])

    def test_historical_audit_csv_requires_owner_and_completed_historical_run(self):
        researcher = self.auth("researcher", "research12345")
        viewer = self.auth("viewer", "viewer12345")
        with Session(self.engine) as session:
            owner = session.query(User).filter_by(username="researcher").one()
            dataset = DatasetVersion(
                dataset_key="hs300_2024", name="audit fixture", version="fixture",
                checksum="0" * 64, storage_uri="/unused/manifest.json", source_filename="manifest.json",
                quality_report={"dataset_kind": "hs300_bundle_v1"}, status="published",
            )
            session.add(dataset)
            session.commit()
            run = create_historical_run(session, {"dataset_version_id": dataset.id}, created_by_id=owner.id)
            task_id = run.id
        daily_url = f"/api/v1/research/tasks/{task_id}/historical-audit/daily.csv"
        self.assertEqual(self.client.get(daily_url).status_code, 401)
        self.assertEqual(self.client.get(daily_url, headers=researcher).status_code, 409)

        with Session(self.engine) as session:
            run = session.get(Run, task_id)
            run.status = RunStatus.SUCCESS
            run.artifacts.append(Artifact(artifact_type="metrics", name="result.json", content={
                "historical_audit": {
                    "momentum_20d": {
                        "daily": [{"date": "2024-01-02", "candidate_count": 300, "valid_return": 299},
                                  {"date": "2024-01-03", "candidate_count": 300}],
                        "unlabeled_signals": [{"date": "2024-01-02", "symbol": "sh.600000", "factor": 0.1,
                                               "next_market_date": "2024-01-03", "reason": "label_suspended"}],
                    },
                },
            }))
            session.commit()

        daily = self.client.get(daily_url, headers=researcher)
        self.assertEqual(daily.status_code, 200, daily.text)
        self.assertTrue(daily.content.startswith(b"\xef\xbb\xbf"))
        self.assertIn("momentum_20d,2024-01-02,300,299", daily.content.decode("utf-8-sig"))
        self.assertIn("momentum_20d,2024-01-03,300,0", daily.content.decode("utf-8-sig"))
        self.assertIn("attachment", daily.headers["content-disposition"])
        unlabeled = self.client.get(
            f"/api/v1/research/tasks/{task_id}/historical-audit/unlabeled.csv", headers=viewer,
        )
        self.assertEqual(unlabeled.status_code, 200, unlabeled.text)
        self.assertIn("sh.600000,0.1,2024-01-03,label_suspended", unlabeled.content.decode("utf-8-sig"))
        self.assertEqual(self.client.get(
            f"/api/v1/research/tasks/{task_id}/historical-audit/unknown.csv", headers=researcher,
        ).status_code, 409)

        self.client.post("/api/v1/users", headers=self.auth("admin", "admin12345"), json={
            "username": "other_audit", "display_name": "其他研究员", "password": "second-pass123", "role": "researcher",
        })
        other = self.auth("other_audit", "second-pass123")
        self.assertEqual(self.client.get(daily_url, headers=other).status_code, 403)


if __name__ == "__main__":
    unittest.main()
