import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.check_demo_readiness import FACTORS, check_readiness, check_web_page


class FakeClient:
    def __init__(self, *, historical=True, factors=None, bad_preview=None):
        self.calls = []
        self.historical = historical
        self.factors = factors if factors is not None else FACTORS
        self.bad_preview = bad_preview

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
        if path in {"/research/tasks", "/reports"}:
            return []
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


if __name__ == "__main__":
    unittest.main()
