import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.models import RunStatus
from app.services.historical_audit import historical_audit_csv
from tools.verify_historical_audit_exports import verify_exports


class HistoricalAuditExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.bundle_path = root / "run.json"
        self.daily_path = root / "daily.csv"
        self.unlabeled_path = root / "unlabeled.csv"
        self.audit = {"momentum_20d": {
            "totals": {"candidate_count": 600, "factor_signal": 2, "valid_return": 1,
                       "label_suspended": 1},
            "daily": [
                {"date": "2024-01-02", "candidate_count": 300, "factor_signal": 1,
                 "valid_return": 1},
                {"date": "2024-01-03", "candidate_count": 300, "factor_signal": 1,
                 "label_suspended": 1},
            ],
            "unlabeled_signals": [{"date": "2024-01-03", "symbol": "sh.600000", "factor": 0.1,
                                   "next_market_date": "2024-01-04", "reason": "label_suspended"}],
        }}
        self._write_exports()

    def tearDown(self):
        self.temp.cleanup()

    def _write_exports(self):
        self._write_bundle({"historical_audit": self.audit, "ic_mean": 0.1})
        run = SimpleNamespace(status=RunStatus.SUCCESS, artifacts=[
            SimpleNamespace(artifact_type="metrics", content={"historical_audit": self.audit}),
        ])
        self.daily_path.write_bytes(historical_audit_csv(run, "daily"))
        self.unlabeled_path.write_bytes(historical_audit_csv(run, "unlabeled"))

    def _write_bundle(self, result):
        digest = hashlib.sha256(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                           separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
        self.bundle_path.write_text(json.dumps({"result": result, "result_sha256": digest}), encoding="utf-8")

    def test_valid_exports_match_bundle_and_counts(self):
        self.assertEqual(verify_exports(self.bundle_path, self.daily_path, self.unlabeled_path),
                         {"factors": 1, "daily_rows": 2, "unlabeled_rows": 1})

    def test_modified_csv_and_inconsistent_bundle_are_rejected(self):
        self.daily_path.write_bytes(self.daily_path.read_bytes().replace(b"2024-01-03,300", b"2024-01-03,301"))
        with self.assertRaisesRegex(ValueError, "daily CSV does not match"):
            verify_exports(self.bundle_path, self.daily_path, self.unlabeled_path)
        self._write_exports()
        self.audit["momentum_20d"]["totals"]["valid_return"] = 2
        self._write_bundle({"historical_audit": self.audit, "ic_mean": 0.1})
        with self.assertRaisesRegex(ValueError, "daily totals disagree"):
            verify_exports(self.bundle_path, self.daily_path, self.unlabeled_path)

    def test_changed_non_audit_metric_and_missing_checksum_are_rejected(self):
        bundle = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        bundle["result"]["ic_mean"] = 0.2
        self.bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "result checksum mismatch"):
            verify_exports(self.bundle_path, self.daily_path, self.unlabeled_path)
        bundle.pop("result_sha256")
        self.bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "no valid result checksum"):
            verify_exports(self.bundle_path, self.daily_path, self.unlabeled_path)

    def test_missing_historical_audit_is_rejected(self):
        self._write_bundle({})
        with self.assertRaisesRegex(ValueError, "no historical audit"):
            verify_exports(self.bundle_path, self.daily_path, self.unlabeled_path)


if __name__ == "__main__":
    unittest.main()
