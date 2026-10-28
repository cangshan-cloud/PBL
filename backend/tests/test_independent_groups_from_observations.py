import gzip
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.verify_independent_groups_from_observations import verify


class IndependentGroupsFromObservationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifact = self.root / "observations.jsonl.gz"
        self.repro = self.root / "reproducibility.json"
        self.days = ("2024-01-02", "2024-01-03")
        self.rows = [{"date": day, "symbol": f"sh.60000{index}",
                      "factor": float(index if day == self.days[0] else 5 - index),
                      "forward_return": index / 10}
                     for day in self.days for index in range(1, 5)]
        self.result = {
            "coverage": 8, "transaction_cost_bps": 10.0,
            "cost_model": "equal_weight_target_traded_notional_v1",
            "group_returns": [{"group": 1, "mean_return": 0.25},
                              {"group": 2, "mean_return": 0.25}],
            "group_nav": [
                {"group": 1, "points": [{"date": self.days[0], "nav": 1.15},
                                         {"date": self.days[1], "nav": 1.5525}]},
                {"group": 2, "points": [{"date": self.days[0], "nav": 1.35},
                                         {"date": self.days[1], "nav": 1.5525}]},
            ],
            "long_short_series": [
                {"date": self.days[0], "return": 0.2, "nav": 1.2, "turnover": 2.0,
                 "cost": 0.002, "net_return": 0.198, "net_nav": 1.198},
                {"date": self.days[1], "return": -0.2, "nav": 0.96, "turnover": 4.0,
                 "cost": 0.004, "net_return": -0.204, "net_nav": 0.953608},
            ],
            "long_short_mean": 0.0, "long_short_total_return": -0.04,
            "long_short_net_mean": -0.003, "long_short_net_total_return": -0.046392,
            "long_short_turnover": 3.0, "top_group_turnover": 1.0,
        }
        self.write()

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        self.artifact.write_bytes(gzip.compress(("\n".join(json.dumps(row) for row in self.rows) + "\n").encode()))
        self.repro.write_text(json.dumps({"schema_version": 2, "task": {"id": "run-1"},
                                         "result": self.result}))

    def test_hand_calculated_groups_turnover_and_cost(self):
        digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        report = verify(self.artifact, self.repro, digest, groups=2)
        self.assertEqual((report["observation_count"], report["date_count"], report["groups"]), (8, 2, 2))
        self.assertLess(report["max_absolute_error"], 1e-12)
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            verify(self.artifact, self.repro, "0" * 64, groups=2)

    def test_daily_cost_nav_and_summary_tampering_fail(self):
        self.result["long_short_series"][1]["cost"] = 0.0
        self.write()
        with self.assertRaisesRegex(ValueError, "long-short cost mismatch"):
            verify(self.artifact, self.repro, groups=2)
        self.result["long_short_series"][1]["cost"] = 0.004
        self.result["group_nav"][0]["points"][0]["nav"] = 1.0
        self.write()
        with self.assertRaisesRegex(ValueError, "group 1 NAV mismatch"):
            verify(self.artifact, self.repro, groups=2)
        self.result["group_nav"][0]["points"][0]["nav"] = 1.15
        self.result["long_short_net_total_return"] = 0.0
        self.write()
        with self.assertRaisesRegex(ValueError, "long_short_net_total_return mismatch"):
            verify(self.artifact, self.repro, groups=2)

    def test_missing_day_and_wrong_cost_model_fail(self):
        self.result["long_short_series"].pop()
        self.write()
        with self.assertRaisesRegex(ValueError, "missing long-short day"):
            verify(self.artifact, self.repro, groups=2)
        self.result["cost_model"] = "unknown"
        self.write()
        with self.assertRaisesRegex(ValueError, "historical cost model"):
            verify(self.artifact, self.repro, groups=2)


if __name__ == "__main__":
    unittest.main()
