import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.verify_http_reproducibility import validate_api_url, verify_http_run


RUN_ID = "f424f62b-4081-400c-89ef-79bbff4a4e59"


def digest(value: dict) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


class FakeClient:
    def __init__(self):
        self.report = b"<html>report</html>"
        self.task = {
            "id": RUN_ID, "status": "success", "parameters": {"groups": 5},
            "dataset_version_id": "dataset-1", "factor_version_id": "factor-1",
            "code_version": "src-sha256:test", "result": {"coverage": 42},
        }
        self.bundle = {
            "schema_version": 2,
            "task": {key: value for key, value in self.task.items() if key != "result"},
            "dataset": {"id": "dataset-1"}, "factor": {"id": "factor-1"},
            "result": self.task["result"], "result_sha256": digest(self.task["result"]),
            "report_sha256": hashlib.sha256(self.report).hexdigest(),
        }
        self.seal()
        self.paths = []

    def seal(self):
        self.bundle["bundle_sha256"] = digest({key: value for key, value in self.bundle.items()
                                               if key != "bundle_sha256"})

    def request(self, path, *, token=None, payload=None):
        self.paths.append((path, token, payload))
        if path == "/auth/login":
            return b'{"access_token":"fake-token"}', {}
        if path == f"/research/tasks/{RUN_ID}":
            return json.dumps(self.task).encode(), {}
        if path == f"/research/tasks/{RUN_ID}/reproducibility.json":
            return json.dumps(self.bundle).encode(), {"content-disposition": "attachment; filename=run.json"}
        if path == f"/reports/{RUN_ID}/download":
            return self.report, {"Content-Disposition": "attachment; filename=report.html"}
        raise AssertionError(path)


class HttpReproducibilityTests(unittest.TestCase):
    def test_loopback_only(self):
        self.assertEqual(validate_api_url("http://127.0.0.1:18022/api/v1/"),
                         "http://127.0.0.1:18022/api/v1")
        for value in ("http://example.org:18022/api/v1", "https://localhost:18022/api/v1",
                      "http://localhost/api/v1", "http://user:pass@localhost:18022/api/v1",
                      "http://localhost:18022/api/v1?x=1", "http://localhost:18022/other",
                      " http://localhost:18022/api/v1"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "loopback"):
                validate_api_url(value)

    def test_successful_read_only_v2_binding(self):
        client = FakeClient()
        result = verify_http_run(client, run_id=RUN_ID, username="researcher", password="secret")
        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(result["bundle_sha256"], client.bundle["bundle_sha256"])
        self.assertEqual(result["checks"], {"result_verified": True, "bundle_verified": True,
                                            "report_verified": True})
        self.assertEqual(client.paths[0], ("/auth/login", None,
                                           {"username": "researcher", "password": "secret"}))
        self.assertTrue(all(payload is None and token == "fake-token" for _, token, payload in client.paths[1:]))

    def test_rejects_wrong_task_result_and_report_bytes(self):
        client = FakeClient()
        client.task["result"] = {"coverage": 43}
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_http_run(client, run_id=RUN_ID, username="researcher", password="secret")
        client = FakeClient()
        client.task["parameters"] = {"groups": 3}
        with self.assertRaisesRegex(ValueError, "does not match"):
            verify_http_run(client, run_id=RUN_ID, username="researcher", password="secret")
        client = FakeClient()
        client.report = b"<html>changed</html>"
        with self.assertRaisesRegex(ValueError, "report checksum mismatch"):
            verify_http_run(client, run_id=RUN_ID, username="researcher", password="secret")

    def test_rejects_missing_attachment_disposition(self):
        class NoAttachment(FakeClient):
            def request(self, path, *, token=None, payload=None):
                body, headers = super().request(path, token=token, payload=payload)
                if path.endswith("/download"):
                    headers = {"content-type": "text/html"}
                return body, headers

        with self.assertRaisesRegex(ValueError, "report response has no attachment"):
            verify_http_run(NoAttachment(), run_id=RUN_ID, username="researcher", password="secret")

    def test_rejects_v1_and_invalid_run_id(self):
        client = FakeClient()
        client.bundle["schema_version"] = 1
        client.bundle.pop("bundle_sha256")
        with self.assertRaisesRegex(ValueError, "not schema v2"):
            verify_http_run(client, run_id=RUN_ID, username="researcher", password="secret")
        with self.assertRaisesRegex(ValueError, "UUID"):
            verify_http_run(client, run_id="../other", username="researcher", password="secret")
        self.assertEqual(client.paths[-1][0], f"/reports/{RUN_ID}/download")


if __name__ == "__main__":
    unittest.main()
