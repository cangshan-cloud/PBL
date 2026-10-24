"""Hand-derived oracle for the matched stock-date IC comparison."""

import math
import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.research import Observation
from app.services.comparisons import _matched_ic_summary


class MatchedComparisonGoldenTests(unittest.TestCase):
    def test_three_date_intersection_matches_hand_derived_ic(self):
        dates = (date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 6))
        symbols = ("A", "B", "C")
        returns = (0.00, 0.01, 0.02)
        factors = (
            ((0, 1, 2), (2, 1, 0), (1, 0, 2)),
            ((2, 1, 0), (0, 1, 2), (1, 2, 0)),
        )
        maps = []
        for run_factors in factors:
            points = {}
            for day, daily_factors in zip(dates, run_factors):
                for symbol, factor, forward_return in zip(symbols, daily_factors, returns):
                    points[(day, symbol)] = Observation(day, symbol, factor, forward_return)
            maps.append(points)
        # This extreme observation exists only in run 1 and must not affect the intersection.
        maps[0][(dates[0], "X")] = Observation(dates[0], "X", 99.0, 0.99)
        keys = set(maps[0]) & set(maps[1])
        params = {"groups": 2, "winsorize": False, "standardize": False,
                  "mad_scale": 3.0, "transaction_cost_bps": 0.0}
        runs = [SimpleNamespace(experiment=SimpleNamespace(parameters=params)) for _ in range(2)]
        items = [{"run_id": "run-a"}, {"run_id": "run-b"}]

        result = _matched_ic_summary(runs, items, maps, keys, [10, 9])

        self.assertTrue(result["available"])
        self.assertEqual(result["observation_count"], 9)
        self.assertEqual(result["date_count"], 3)
        self.assertEqual(result["label_mismatch_count"], 0)
        self.assertEqual(result["min_valid_ic_dates"], 3)
        self.assertEqual(result["evidence"]["level"], "insufficient")
        self.assertAlmostEqual(result["min_retention_ratio"], 0.9)
        self.assertEqual([item["source_observation_count"] for item in result["items"]], [10, 9])
        self.assertEqual([item["retention_ratio"] for item in result["items"]], [0.9, 1.0])
        for actual, sign, positive_ratio in zip(result["items"], (1, -1), (2 / 3, 1 / 3)):
            self.assertEqual(actual["valid_ic_dates"], 3)
            self.assertAlmostEqual(actual["ic_mean"], sign / 6)
            self.assertAlmostEqual(actual["rank_ic_mean"], sign / 6)
            self.assertAlmostEqual(actual["icir"], sign / math.sqrt(26))
            self.assertAlmostEqual(actual["ic_positive_ratio"], positive_ratio)


if __name__ == "__main__":
    unittest.main()
