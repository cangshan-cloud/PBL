import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from benchmark_page_queries import ENDPOINTS, measure, measure_views, require_loopback_url


class FakeClient:
    def __init__(self):
        self.calls = []

    def request(self, path, *, token):
        self.calls.append((path, token))
        return {} if path == "/dashboard" else []


class PageQueryBenchmarkTests(unittest.TestCase):
    def test_rejects_nonlocal_or_credential_bearing_urls(self):
        for value in ("https://example.com/api/v1", "http://user:secret@localhost/api/v1",
                      "http://localhost/api/v1?token=secret", "file:///tmp/a"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                require_loopback_url(value, api=True)
        self.assertEqual(require_loopback_url("http://127.0.0.1:8000/api/v1", api=True),
                         "http://127.0.0.1:8000/api/v1")
        with self.assertRaisesRegex(ValueError, "end with"):
            require_loopback_url("http://localhost:8000/health", api=True)

    def test_measures_first_and_repeat_reads_and_enforces_limit(self):
        ticks = iter((0.0, 0.3, 1.0, 1.2, 2.0, 4.5, 5.0, 5.4))
        result = measure("overview", lambda: None, samples=3, limit_seconds=2, timer=lambda: next(ticks))
        self.assertEqual(result["first_read_seconds"], 0.3)
        self.assertEqual(result["repeat_seconds"], [0.2, 2.5, 0.4])
        self.assertFalse(result["passed"])

    def test_only_reads_expected_views_after_web_entry(self):
        client = FakeClient()
        with patch("benchmark_page_queries.check_web_page") as web:
            results = measure_views(client, "token", "http://localhost:5173/", samples=3, limit_seconds=2)
        self.assertEqual(web.call_count, 4)
        self.assertEqual([item["view"] for item in results], ["web_entry", *(label for label, _, _ in ENDPOINTS)])
        self.assertEqual(client.calls, [(path, "token") for _, path, _ in ENDPOINTS for _ in range(4)])
        self.assertEqual([item.get("item_count") for item in results], [None, None, 0, 0, 0, 0])
        self.assertTrue(all(item["passed"] for item in results))


if __name__ == "__main__":
    unittest.main()
