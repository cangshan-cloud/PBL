import hashlib
import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.check_demo_readiness import ApiClient, FACTORS, check_readiness, check_web_page, check_worker


class FakeClient:
    def __init__(self, *, historical=True, factors=None, bad_preview=None, report_bytes=None,
                 report_checksum=None, report_available=True):
        self.calls = []
        self.historical = historical
        self.factors = factors if factors is not None else FACTORS
        self.bad_preview = bad_preview
        self.report_bytes = report_bytes if report_bytes is not None else b"<!doctype html><title>Demo report</title>"
        self.report_checksum = report_checksum or hashlib.sha256(self.report_bytes).hexdigest()
        self.report_available = report_available
        self.downloads = []

    def download_report(self, run_id, *, token, timeout=10):
        self.downloads.append((run_id, token, timeout))
        return self.report_bytes

    def request(self, path, *, token=None, payload=None, timeout=10):
        self.calls.append((path, token, payload, timeout))
        if path == "/auth/login":
            return {"access_token": payload["username"]}
        if path == "/auth/me":
            return {"role": token, "is_active": True}
        if path == "/datasets":
            datasets = [{"id": "demo-id", "dataset_key": "demo_daily", "version": "0.2.0", "status": "published",
                         "row_count": 2400, "symbol_count": 20}]
            if self.historical:
                datasets.append({"id": "historical-id", "dataset_key": "hs300_2024", "version": "0375298bd2c8ac52",
                                 "status": "published", "quality_report": {"dataset_kind": "hs300_bundle_v1",
                                 "bundle_id": "hs300_2024_0375298bd2c8ac52"}})
            return datasets
        if path == "/datasets/demo-id/preview":
            if self.bad_preview == "demo_missing":
                raise RuntimeError("HTTP 410")
            return {"dataset_id": "demo-id", "total_rows": 2400}
        if path == "/datasets/historical-id/preview":
            if self.bad_preview == "historical_tampered":
                raise RuntimeError("HTTP 409")
            return {"dataset_id": "historical-id", "rows": [
                {"item": "bundle_id", "value": "hs300_2024_0375298bd2c8ac52"},
                {"item": "verified_files", "value": "576"},
            ]}
        if path == "/factors":
            return [{"id": key} for key in self.factors]
        if path == "/research/tasks":
            return ([{"id": "demo-run", "dataset_version_id": "demo-id", "status": "success"}]
                    if self.report_available else [])
        if path == "/reports":
            return ([{"run_id": "demo-run", "checksum": self.report_checksum}]
                    if self.report_available else [])
        raise AssertionError(f"unexpected API call: {path}")


class DemoReadinessTests(unittest.TestCase):
    passwords = {"admin": "admin-secret", "researcher": "research-secret", "viewer": "view-secret"}

    def test_preflight_is_read_only_and_checks_historical_catalog_when_requested(self):
        client = FakeClient()
        checks = check_readiness(client, self.passwords, require_historical=True)
        self.assertEqual(len(checks), 5)
        self.assertTrue(any("verified historical bundle" in item for item in checks))
        self.assertEqual(sum(path == "/auth/login" for path, _, _, _ in client.calls), 3)
        self.assertTrue(all(payload is None for path, _, payload, _ in client.calls if path != "/auth/login"))
        self.assertIn(("/datasets/historical-id/preview", "admin", None, 30), client.calls)
        self.assertFalse(any(path in {"/research/historical-tasks", "/research/tasks"} and payload
                             for path, _, payload, _ in client.calls))

    def test_missing_factor_and_historical_catalog_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "six required"):
            check_readiness(FakeClient(factors={"momentum_20d"}), self.passwords)
        with self.assertRaisesRegex(ValueError, "no published historical"):
            check_readiness(FakeClient(historical=False), self.passwords, require_historical=True)

    def test_optional_report_fallback_is_read_only_and_verifies_download_checksum(self):
        client = FakeClient()
        checks = check_readiness(client, self.passwords, require_report_fallback=True)
        self.assertTrue(any("verified demo report fallback demo-run" in item for item in checks))
        self.assertEqual(client.downloads, [("demo-run", "viewer", 10)])
        self.assertTrue(all(payload is None for path, _, payload, _ in client.calls if path != "/auth/login"))

    def test_optional_report_fallback_rejects_missing_and_tampered_report(self):
        with self.assertRaisesRegex(ValueError, "no successful demo_daily"):
            check_readiness(FakeClient(report_available=False), self.passwords, require_report_fallback=True)
        with self.assertRaisesRegex(ValueError, "no demo report fallback passed download verification"):
            check_readiness(FakeClient(report_checksum="0" * 64), self.passwords, require_report_fallback=True)

    def test_report_download_requires_html_and_has_size_limit(self):
        class Response:
            def __init__(self, content_type, content):
                self.headers = {"Content-Type": content_type}
                self.content = content

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, limit):
                return self.content[:limit]

        client = ApiClient("http://127.0.0.1:8000/api/v1")
        with patch("tools.check_demo_readiness.urlopen", return_value=Response("text/html", b"<html>ok</html>")) as get:
            self.assertEqual(client.download_report("run-id", token="viewer"), b"<html>ok</html>")
        self.assertEqual(get.call_args.args[0].get_header("Authorization"), "Bearer viewer")
        with patch("tools.check_demo_readiness.urlopen", return_value=Response("application/json", b"{}")):
            with self.assertRaisesRegex(ValueError, "not HTML"):
                client.download_report("run-id", token="viewer")
        with patch("tools.check_demo_readiness.urlopen", return_value=Response("text/html", b"x" * (10 * 1024 * 1024 + 1))):
            with self.assertRaisesRegex(ValueError, "exceeds 10 MiB"):
                client.download_report("run-id", token="viewer")

    def test_missing_demo_file_or_tampered_historical_bundle_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "HTTP 410"):
            check_readiness(FakeClient(bad_preview="demo_missing"), self.passwords)
        with self.assertRaisesRegex(ValueError, "no published historical CSI 300 bundle passed file verification"):
            check_readiness(FakeClient(bad_preview="historical_tampered"), self.passwords, require_historical=True)

    def test_passwords_are_required_before_any_http_call(self):
        client = FakeClient()
        with self.assertRaisesRegex(ValueError, "missing admin password"):
            check_readiness(client, {})
        self.assertEqual(client.calls, [])

    def test_web_entry_must_be_reachable_and_match_app(self):
        class Response:
            headers = {"Content-Type": "text/html; charset=utf-8"}

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, _limit):
                return b'<title>FactorLab Demo</title><div id="root"></div>'

        with patch("tools.check_demo_readiness.urlopen", return_value=Response()):
            check_web_page("http://127.0.0.1:5173/")
        with patch("tools.check_demo_readiness.urlopen", side_effect=OSError("connection refused")):
            with self.assertRaisesRegex(RuntimeError, "web entry is unavailable"):
                check_web_page("http://127.0.0.1:5173/")

        class WrongPage(Response):
            def read(self, _limit):
                return b'<title>Other</title><div id="root"></div>'

        with patch("tools.check_demo_readiness.urlopen", return_value=WrongPage()):
            with self.assertRaisesRegex(ValueError, "not the FactorLab"):
                check_web_page("http://127.0.0.1:5173/")

    def test_optional_worker_ping_is_read_only_and_project_scoped(self):
        response = subprocess.CompletedProcess(args=[], returncode=0, stdout="-> celery@worker: OK\n    pong\n", stderr="")
        with patch("tools.check_demo_readiness.subprocess.run", return_value=response) as run:
            check_worker(compose_project="factorlab-hs300-qa")
        command = run.call_args.args[0]
        self.assertEqual(command[:4], ["docker", "compose", "-p", "factorlab-hs300-qa"])
        self.assertEqual(command[4:7], ["exec", "-T", "worker"])
        self.assertEqual(command[-3:], ["inspect", "ping", "--timeout=5"])
        self.assertNotIn("apply_async", command)
        self.assertFalse(run.call_args.kwargs["check"])

    def test_worker_ping_failure_and_missing_docker_fail_closed(self):
        with patch("tools.check_demo_readiness.subprocess.run", return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout="1 node online, but no pong", stderr="",
        )):
            with self.assertRaisesRegex(RuntimeError, "did not answer"):
                check_worker()
        with patch("tools.check_demo_readiness.subprocess.run", side_effect=FileNotFoundError("docker")):
            with self.assertRaisesRegex(RuntimeError, "could not run"):
                check_worker()


if __name__ == "__main__":
    unittest.main()
