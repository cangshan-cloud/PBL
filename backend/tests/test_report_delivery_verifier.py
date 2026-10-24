"""Offline report verifier against generated delivery copies and tampering."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.reports import report_delivery_copy
from tools.verify_report_delivery import verify_delivery


class ReportDeliveryVerifierTests(unittest.TestCase):
    def test_quality_disclosure_and_identity_are_verified(self):
        dataset = {"id": "dataset-v1", "dataset_key": "imported", "version": "v1",
                   "checksum": "a" * 64,
                   "quality_report": {"announced_weekday_closure_row_count": 3,
                                      "announced_weekday_closure_dates": ["2026-10-07"],
                                      "announced_closure_calendar_version": "calendar-v2",
                                      "calendar_uncovered_years": [2027]}}
        original = b"<html><main><h1>Original report</h1></main></html>"
        archive_sha = hashlib.sha256(original).hexdigest()
        summary = {"run_id": "run-v1", "dataset_version_id": dataset["id"],
                   "dataset_checksum_sha256": dataset["checksum"], "checksum": archive_sha}
        run = SimpleNamespace(experiment=SimpleNamespace(dataset_version=SimpleNamespace(**dataset)))
        delivered = report_delivery_copy(original, run, archive_sha)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path, delivery_path = root / "archive.html", root / "delivery.html"
            dataset_path, summary_path = root / "dataset.json", root / "summary.json"
            archive_path.write_bytes(original)
            delivery_path.write_bytes(delivered)
            dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
            summary_path.write_text(json.dumps(summary), encoding="utf-8")

            verified = verify_delivery(archive_path, delivery_path, dataset_path, summary_path)
            self.assertTrue(verified["verified"])
            self.assertEqual(verified["risk_count"], 2)
            self.assertEqual(verified["archived_report_sha256"], archive_sha)

            delivery_path.write_bytes(delivered.replace(b"Original report", b"Altered report"))
            with self.assertRaisesRegex(ValueError, "outside the disclosure"):
                verify_delivery(archive_path, delivery_path, dataset_path, summary_path)
            delivery_path.write_bytes(delivered)

            delivery_path.write_bytes(delivered.replace(b"2026-10-07", b"2026-10-08"))
            with self.assertRaisesRegex(ValueError, "differs from dataset quality"):
                verify_delivery(archive_path, delivery_path, dataset_path, summary_path)
            delivery_path.write_bytes(delivered)

            summary_path.write_text(json.dumps({**summary, "checksum": "0" * 64}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "archived report bytes differ"):
                verify_delivery(archive_path, delivery_path, dataset_path, summary_path)
            summary_path.write_text(json.dumps(summary), encoding="utf-8")

            dataset_path.write_text(json.dumps({**dataset, "checksum": "b" * 64}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "report summary differs"):
                verify_delivery(archive_path, delivery_path, dataset_path, summary_path)

    def test_generic_disclosure_has_no_market_certification_claim(self):
        dataset = {"id": "dataset-clean", "dataset_key": "imported", "version": "v1",
                   "checksum": "b" * 64, "quality_report": {}}
        original = b"<html><main>Original</main></html>"
        digest = hashlib.sha256(original).hexdigest()
        summary = {"run_id": "run-clean", "dataset_version_id": dataset["id"],
                   "dataset_checksum_sha256": dataset["checksum"], "checksum": digest}
        run = SimpleNamespace(experiment=SimpleNamespace(dataset_version=SimpleNamespace(**dataset)))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / name for name in ("archive.html", "delivery.html", "dataset.json", "summary.json")]
            paths[0].write_bytes(original)
            paths[1].write_bytes(report_delivery_copy(original, run, digest))
            paths[2].write_text(json.dumps(dataset), encoding="utf-8")
            paths[3].write_text(json.dumps(summary), encoding="utf-8")
            self.assertEqual(verify_delivery(*paths)["risk_count"], 1)


if __name__ == "__main__":
    unittest.main()
