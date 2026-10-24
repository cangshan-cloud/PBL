import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.coverage import enrich_daily_coverage


class CoverageTests(unittest.TestCase):
    def test_includes_zero_observation_and_zero_candidate_market_days(self):
        days = [date(2025, 1, day) for day in (2, 3, 4)]
        result = {"coverage": 1, "daily_coverage": [
            {"date": days[0].isoformat(), "eligible_symbols": 1,
             "ic_status": "insufficient_sample", "group_status": "insufficient_sample"},
        ]}
        enrich_daily_coverage(result, days, {days[0]: 2, days[1]: 3})
        self.assertEqual(result["candidate_coverage"], 5)
        self.assertEqual(result["coverage_ratio"], .2)
        self.assertEqual(result["zero_observation_days"], 2)
        self.assertEqual(result["daily_coverage"][1]["excluded_symbols"], 3)
        self.assertEqual(result["daily_coverage"][1]["coverage_ratio"], 0)
        self.assertIsNone(result["daily_coverage"][2]["coverage_ratio"])
        self.assertEqual(result["daily_coverage"][2]["ic_status"], "no_observation")

    def test_rejects_eligible_count_above_candidate_count(self):
        day = date(2025, 1, 2)
        result = {"coverage": 2, "daily_coverage": [{"date": day.isoformat(), "eligible_symbols": 2}]}
        with self.assertRaisesRegex(ValueError, "exceed candidates"):
            enrich_daily_coverage(result, [day], {day: 1})
