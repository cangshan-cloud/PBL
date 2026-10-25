import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from verify_historical_api_journey import main, run_journey, verify_journey_binding


class FakeClient:
    def __init__(self, *, existing=False, task_status="success"):
        self.existing = existing
        self.task_status = task_status
        self.calls = []

    def json(self, path, *, token=None, payload=None):
        self.calls.append((path, token, payload))
        if path == "/auth/login":
            return {"access_token": payload["username"]}
        if path == "/datasets":
            return ([{"id": "dataset-1", "status": "published",
                      "quality_report": {"bundle_id": "hs300_2024_0123456789abcdef"}}] if self.existing else [])
        if path == "/datasets/register-hs300-bundle":
            return {"id": "dataset-1", "status": "draft"}
        if path == "/datasets/dataset-1/publish":
            return {"id": "dataset-1", "status": "published"}
        if path == "/research/historical-tasks":
            return {"id": "run-1", "status": "pending"}
        if path == "/research/tasks/run-1":
            return {"id": "run-1", "status": self.task_status, "error_summary": "worker failed"}
        raise AssertionError(path)

    def request(self, path, *, token=None, payload=None):
        self.calls.append((path, token, payload))
        return path.encode(), {"Content-Disposition": 'attachment; filename="evidence"'}


class HistoricalApiJourneyTests(unittest.TestCase):
    bundle_id = "hs300_2024_0123456789abcdef"

    def test_register_publish_run_and_download(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "evidence"
            client = FakeClient()
            with patch("verify_historical_api_journey.time.sleep"), patch(
                "verify_historical_api_journey.verify_exports", return_value={
                    "factors": 4, "daily_rows": 968, "unlabeled_rows": 32, "report_verified": True,
                },
            ) as verify, patch("verify_historical_api_journey.load_verified_export", return_value={
                "task": {"id": "run-1", "status": "success", "dataset_version_id": "dataset-1",
                         "parameters": {"groups": 5}},
                "dataset": {"id": "dataset-1"},
                "result": {"sample": {"historical_bundle_id": self.bundle_id}},
            }):
                result = run_journey(client, bundle_id=self.bundle_id, admin_password="a", researcher_password="r",
                                     output_dir=output)
            self.assertEqual(result["run_id"], "run-1")
            self.assertEqual(result["daily_rows"], 968)
            self.assertTrue(result["report_verified"])
            self.assertEqual((output / "daily.csv").read_bytes(), b"/research/tasks/run-1/historical-audit/daily.csv")
            self.assertEqual((output / "report.html").read_bytes(), b"/reports/run-1/download")
            self.assertEqual(len(list(output.iterdir())), 4)
            verify.assert_called_once_with(output / "reproducibility.json", output / "daily.csv",
                                           output / "unlabeled.csv", output / "report.html")
            self.assertIn(("/datasets/register-hs300-bundle", "admin", {"bundle_id": self.bundle_id}), client.calls)
            self.assertIn(("/datasets/dataset-1/publish", "admin", {}), client.calls)
            self.assertIn(("/research/historical-tasks", "researcher",
                           {"dataset_version_id": "dataset-1", "groups": 5}), client.calls)

    def test_existing_dataset_is_reused_and_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "evidence"
            client = FakeClient(existing=True)
            with patch("verify_historical_api_journey.time.sleep"), patch(
                "verify_historical_api_journey.verify_exports", return_value={},
            ), patch("verify_historical_api_journey.load_verified_export", return_value={
                "task": {"id": "run-1", "status": "success", "dataset_version_id": "dataset-1",
                         "parameters": {"groups": 5}},
                "dataset": {"id": "dataset-1"},
                "result": {"sample": {"historical_bundle_id": self.bundle_id}},
            }):
                run_journey(client, bundle_id=self.bundle_id, admin_password="a", researcher_password="r",
                            output_dir=output)
            self.assertFalse(any(path.startswith("/datasets/register") or path.endswith("/publish")
                                 for path, _, _ in client.calls))
            second = FakeClient()
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                run_journey(second, bundle_id=self.bundle_id, admin_password="a", researcher_password="r",
                            output_dir=output)
            self.assertEqual(second.calls, [])

    def test_failed_task_leaves_no_output_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "evidence"
            with patch("verify_historical_api_journey.time.sleep"):
                with self.assertRaisesRegex(RuntimeError, "worker failed"):
                    run_journey(FakeClient(task_status="failed"), bundle_id=self.bundle_id,
                                admin_password="a", researcher_password="r", output_dir=output)
            self.assertFalse(output.exists())

    def test_cli_requires_explicit_write_acknowledgment(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "evidence"
            args = ["--api-url", "http://127.0.0.1:18000/api/v1", "--bundle-id", self.bundle_id,
                    "--output-dir", str(output)]
            with self.assertRaises(SystemExit) as error:
                main(args)
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(output.exists())

    def test_rejects_exports_from_another_run_dataset_or_bundle(self):
        export = {"task": {"id": "run-1", "status": "success", "dataset_version_id": "dataset-1",
                           "parameters": {"groups": 5}}, "dataset": {"id": "dataset-1"},
                  "result": {"sample": {"historical_bundle_id": self.bundle_id}}}
        expected = {"run_id": "run-1", "dataset_id": "dataset-1", "bundle_id": self.bundle_id}
        verify_journey_binding(export, **expected)
        for changed in ({"task": {**export["task"], "id": "other"}},
                        {"dataset": {"id": "other"}},
                        {"result": {"sample": {"historical_bundle_id": "other"}}},
                        {"task": {**export["task"], "parameters": {"groups": 2}}},
                        {"task": []}, {"result": {"sample": None}}):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    verify_journey_binding({**export, **changed}, **expected)


if __name__ == "__main__":
    unittest.main()
