import hashlib
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.domain.historical_research import FACTOR_WINDOWS, HistoricalBar
from tools.verify_historical_recomputation import recompute_result, verify_recomputation


class HistoricalRecomputationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.manifest = self.root / "hs300_2024_0123456789abcdef" / "manifest.json"
        self.days = [date(2023, 12, 1) + timedelta(days=index) for index in range(29)]
        symbols = [f"sh.{index:06d}" for index in range(10)]
        self.members = {day: set(symbols) for day in self.days[21:-1]}
        self.bars = {
            symbol: {day: HistoricalBar(100 + index * (1 + rank / 10), 1 + rank / 10, 100, "1", "0")
                     for index, day in enumerate(self.days)}
            for rank, symbol in enumerate(symbols)
        }
        self.checksum = "a" * 64
        self.export = self.root / "run.json"

    def tearDown(self):
        self.temp.cleanup()

    def _write_export(self, result, *, parameters=None, checksum=None):
        params = parameters or {
            "mode": "historical_hs300_2024", "dataset_version_id": "dataset-1",
            "groups": 5, "factors": list(FACTOR_WINDOWS), "lookbacks": FACTOR_WINDOWS,
            "weighting": "equal", "price_basis": "source_close",
            "components": [{"key": key, "version": "1.0.0", "lookback": window, "weight": 0.25}
                           for key, window in FACTOR_WINDOWS.items()],
            "winsorize": True, "standardize": True, "mad_scale": 3.0,
            "transaction_cost_bps": 10.0,
        }
        digest = hashlib.sha256(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                          separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        self.export.write_text(json.dumps({
            "schema_version": 1, "task": {"status": "success", "dataset_version_id": "dataset-1",
                                            "parameters": params},
            "dataset": {"id": "dataset-1", "checksum_sha256": checksum or self.checksum},
            "result": result, "result_sha256": digest,
        }), encoding="utf-8")

    def test_recomputes_and_detects_self_consistent_result_change(self):
        with patch("tools.verify_historical_recomputation.load_historical_bundle",
                   return_value=(self.days, self.members, self.bars)) as loaded:
            result = recompute_result(self.manifest, self.checksum, 5)
            self.assertEqual(result["coverage"], 70)
            self._write_export(result)
            summary = verify_recomputation(self.export, self.manifest)
            self.assertEqual(summary["observations"], 70)
            self.assertEqual(summary["factors"], 4)
            self.assertEqual(loaded.call_args.args, (self.manifest, self.checksum))
            near_equal = {**result, "ic_mean": result["ic_mean"] + 1e-15}
            self._write_export(near_equal)
            with self.assertRaisesRegex(ValueError, "historical recomputation mismatch: ic_mean"):
                verify_recomputation(self.export, self.manifest)
            altered = {**result, "ic_mean": 0.9}
            self._write_export(altered)  # Recalculate the self-checksum too.
            with self.assertRaisesRegex(ValueError, "historical recomputation mismatch: ic_mean"):
                verify_recomputation(self.export, self.manifest)

    def test_rejects_unsupported_configuration_before_loading_bundle(self):
        self._write_export({"coverage": 0}, parameters={"mode": "historical_hs300_2024", "groups": 5})
        with patch("tools.verify_historical_recomputation.load_historical_bundle") as loaded:
            with self.assertRaisesRegex(ValueError, "unsupported historical task configuration"):
                verify_recomputation(self.export, self.manifest)
            loaded.assert_not_called()


if __name__ == "__main__":
    unittest.main()
