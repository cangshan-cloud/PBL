"""Read-only local HTTP delivery audit contract."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from app.services.reports import report_delivery_copy
import verify_live_report_delivery as live


class LiveReportDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.dataset = {"id": "dataset-1", "dataset_key": "imported", "version": "v1",
                        "checksum": "a" * 64, "quality_report": {}}
        self.original = b"<html><main><h1>Original</h1></main></html>"
        self.digest = hashlib.sha256(self.original).hexdigest()
        self.summary = {"run_id": "abc12345-0000", "dataset_version_id": self.dataset["id"],
                        "dataset_checksum_sha256": self.dataset["checksum"], "checksum": self.digest}
        run = SimpleNamespace(experiment=SimpleNamespace(dataset_version=SimpleNamespace(**self.dataset)))
        self.delivered = report_delivery_copy(self.original, run, self.digest)

    def responses(self, bad_header=False, duplicate=False):
        summaries = [self.summary, self.summary] if duplicate else [self.summary]
        return {
            "/auth/login": (json.dumps({"access_token": "local-token"}).encode(), {}),
            "/reports": (json.dumps(summaries).encode(), {}),
            "/datasets/dataset-1": (json.dumps(self.dataset).encode(), {}),
            "/reports/abc12345-0000/download": (self.original, {"Content-Type": "text/html; charset=utf-8"}),
            "/reports/abc12345-0000/delivery": (self.delivered, {"Content-Type": "text/html; charset=utf-8",
                                                        "X-Archived-Report-SHA256": "0" * 64 if bad_header else self.digest}),
        }

    def test_verifies_actual_http_bodies_and_header(self):
        responses = self.responses()
        with patch.object(live, "_request", side_effect=lambda _base, path, *_args, **_kwargs: responses[path]):
            result = live.verify_live("http://127.0.0.1:8000/api/v1", "admin", "secret", "abc12345")
        self.assertTrue(result["verified"])
        self.assertTrue(result["http_checked"])
        self.assertEqual(result["archive_bytes"], len(self.original))
        self.assertEqual(result["delivery_bytes"], len(self.delivered))
        self.assertIsNone(result["browser_file_verified"])

    def test_browser_saved_bytes_must_match_http_delivery(self):
        responses = self.responses()
        with tempfile.TemporaryDirectory() as directory:
            browser_file = Path(directory) / "download.html"
            browser_file.write_bytes(self.delivered)
            with patch.object(live, "_request", side_effect=lambda _base, path, *_args, **_kwargs: responses[path]):
                result = live.verify_live("http://127.0.0.1:8000/api/v1", "admin", "secret", "abc12345", browser_file)
            self.assertTrue(result["browser_file_verified"])
            browser_file.write_bytes(self.delivered + b"tampered")
            with patch.object(live, "_request", side_effect=lambda _base, path, *_args, **_kwargs: responses[path]):
                with self.assertRaisesRegex(ValueError, "browser-saved file differs"):
                    live.verify_live("http://127.0.0.1:8000/api/v1", "admin", "secret", "abc12345", browser_file)

    def test_rejects_nonlocal_url_and_ambiguous_run(self):
        with self.assertRaisesRegex(ValueError, "local"):
            live.verify_live("https://example.com/api/v1", "admin", "secret", "abc12345")
        responses = self.responses(duplicate=True)
        with patch.object(live, "_request", side_effect=lambda _base, path, *_args, **_kwargs: responses[path]):
            with self.assertRaisesRegex(ValueError, "matches 2"):
                live.verify_live("http://localhost:8000/api/v1", "admin", "secret", "abc12345")

    def test_rejects_conflicting_http_checksum(self):
        responses = self.responses(bad_header=True)
        with patch.object(live, "_request", side_effect=lambda _base, path, *_args, **_kwargs: responses[path]):
            with self.assertRaisesRegex(ValueError, "header differs"):
                live.verify_live("http://127.0.0.1:8000/api/v1", "admin", "secret", "abc12345")


if __name__ == "__main__":
    unittest.main()
