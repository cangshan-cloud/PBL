import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.check_demo_readiness import FACTORS, check_readiness


class FakeClient:
    def __init__(self, *, historical=True, factors=None):
        self.calls = []
        self.historical = historical
        self.factors = factors if factors is not None else FACTORS

    def request(self, path, *, token=None, payload=None):
        self.calls.append((path, token, payload))
        if path == "/auth/login":
            return {"access_token": payload["username"]}
        if path == "/auth/me":
            return {"role": token, "is_active": True}
        if path == "/datasets":
            datasets = [{"dataset_key": "demo_daily", "version": "0.2.0", "status": "published",
                         "row_count": 2400, "symbol_count": 20}]
            if self.historical:
                datasets.append({"dataset_key": "hs300_2024", "version": "0375298bd2c8ac52",
                                 "status": "published", "quality_report": {"dataset_kind": "hs300_bundle_v1"}})
            return datasets
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
        self.assertTrue(any("historical bundle" in item for item in checks))
        self.assertEqual(sum(path == "/auth/login" for path, _, _ in client.calls), 3)
        self.assertTrue(all(payload is None for path, _, payload in client.calls if path != "/auth/login"))
        self.assertFalse(any(path in {"/research/historical-tasks", "/research/tasks"} and payload
                             for path, _, payload in client.calls))

    def test_missing_factor_and_historical_catalog_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "six required"):
            check_readiness(FakeClient(factors={"momentum_20d"}), self.passwords)
        with self.assertRaisesRegex(ValueError, "no published historical"):
            check_readiness(FakeClient(historical=False), self.passwords, require_historical=True)

    def test_passwords_are_required_before_any_http_call(self):
        client = FakeClient()
        with self.assertRaisesRegex(ValueError, "missing admin password"):
            check_readiness(client, {})
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
