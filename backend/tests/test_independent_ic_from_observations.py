import gzip
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.verify_independent_ic_from_observations import verify


class IndependentIcFromObservationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifact = self.root / "observations.jsonl.gz"
        self.repro = self.root / "reproducibility.json"
        self.rows = [
            {"date": day, "symbol": f"sh.60000{index}", "factor": float(index),
             "forward_return": float(forward)}
            for day, returns in (("2024-01-02", (2, 1, 3)), ("2024-01-03", (3, 2, 1)))
            for index, forward in enumerate(returns, 1)
        ]
        self.result = {"coverage": 6, "ic_series": [
            {"date": "2024-01-02", "ic": 0.5, "rank_ic": 0.5},
            {"date": "2024-01-03", "ic": -1.0, "rank_ic": -1.0},
        ], "ic_mean": -0.25, "ic_std": 0.75, "rank_ic_mean": -0.25,
            "icir": -1 / 3, "ic_positive_ratio": 0.5}
        self.write()

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        self.artifact.write_bytes(gzip.compress(("\n".join(json.dumps(row) for row in self.rows) + "\n").encode()))
        self.repro.write_text(json.dumps({"schema_version": 2, "task": {"id": "run-1"},
                                         "result": self.result}))

    def test_hand_calculated_two_day_ic_and_summary(self):
        digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        report = verify(self.artifact, self.repro, digest)
        self.assertEqual((report["observation_count"], report["date_count"], report["valid_ic_dates"]), (6, 2, 2))
        self.assertLess(report["max_absolute_error"], 1e-12)
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            verify(self.artifact, self.repro, "0" * 64)

    def test_daily_and_summary_tampering_fail(self):
        self.result["ic_series"][0]["rank_ic"] = 0.4
        self.write()
        with self.assertRaisesRegex(ValueError, "Rank IC mismatch"):
            verify(self.artifact, self.repro)
        self.result["ic_series"][0]["rank_ic"] = 0.5
        self.result["ic_mean"] = 0.0
        self.write()
        with self.assertRaisesRegex(ValueError, "ic_mean mismatch"):
            verify(self.artifact, self.repro)

    def test_missing_or_duplicate_observation_fails(self):
        self.rows.pop()
        self.write()
        with self.assertRaisesRegex(ValueError, "observation count"):
            verify(self.artifact, self.repro)
        self.rows.append(self.rows[0].copy())
        self.write()
        with self.assertRaisesRegex(ValueError, "duplicate observation"):
            verify(self.artifact, self.repro)


if __name__ == "__main__":
    unittest.main()
