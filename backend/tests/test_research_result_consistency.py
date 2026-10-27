import copy
import hashlib
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from app.domain.research import Observation, evaluate
from app.domain.time_split import evaluate_time_split
from app.services.coverage import enrich_daily_coverage
from tools.verify_research_result_consistency import verify_result_consistency


class ResearchResultConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "reproducibility.json"
        self.result = {
            "daily_coverage": [
                {"date": "2024-01-02", "candidate_symbols": 3, "eligible_symbols": 2,
                 "excluded_symbols": 1, "coverage_ratio": 2 / 3,
                 "ic_status": "valid", "group_status": "valid"},
                {"date": "2024-01-03", "candidate_symbols": 3, "eligible_symbols": 2,
                 "excluded_symbols": 1, "coverage_ratio": 2 / 3,
                 "ic_status": "constant_factor_or_return", "group_status": "constant_factor"},
                {"date": "2024-01-04", "candidate_symbols": 3, "eligible_symbols": 1,
                 "excluded_symbols": 2, "coverage_ratio": 1 / 3,
                 "ic_status": "insufficient_sample", "group_status": "insufficient_sample"},
                {"date": "2024-01-05", "candidate_symbols": 0, "eligible_symbols": 0,
                 "excluded_symbols": 0, "coverage_ratio": None,
                 "ic_status": "no_observation", "group_status": "no_observation"},
            ],
            "ic_series": [{"date": "2024-01-02", "ic": 1.0, "rank_ic": 1.0},
                          {"date": "2024-01-03", "ic": None, "rank_ic": None}],
            "long_short_series": [{"date": "2024-01-02", "return": 0.03, "nav": 1.03,
                                   "turnover": 2.0, "cost": 0.002, "net_return": 0.028,
                                   "net_nav": 1.028}],
            "group_nav": [{"group": 1, "points": [{"date": "2024-01-02", "nav": 0.99}]},
                          {"group": 2, "points": [{"date": "2024-01-02", "nav": 1.02}]}],
            "coverage": 5, "candidate_coverage": 9, "coverage_ratio": 5 / 9,
            "zero_observation_days": 1, "group_skipped_constant_factor_days": 1,
            "group_skipped_insufficient_sample_days": 1, "transaction_cost_bps": 10,
        }
        self._write()

    def tearDown(self):
        self.temp.cleanup()

    def _write(self):
        canonical = json.dumps(self.result, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        declared_cutoff = self.result.get("time_split", {}).get("validation_start_date")
        self.path.write_text(json.dumps({"schema_version": 1, "result_sha256": digest,
                                         "task": {"parameters": {"validation_start_date": declared_cutoff}},
                                         "result": self.result}), encoding="utf-8")

    def _reject(self, change, pattern):
        original = copy.deepcopy(self.result)
        change(self.result)
        self._write()
        with self.assertRaisesRegex(ValueError, pattern):
            verify_result_consistency(self.path)
        self.result = original
        self._write()

    def test_consistent_result(self):
        self.assertEqual(verify_result_consistency(self.path),
                         {"daily_dates": 4, "ic_dates": 2, "group_dates": 1,
                          "eligible_observations": 5})

    def test_counts_ratios_and_aggregate_tampering_with_valid_checksum(self):
        self._reject(lambda r: r["daily_coverage"][0].update(excluded_symbols=0), "counts differ")
        self._reject(lambda r: r["daily_coverage"][0].update(coverage_ratio=0.5), "coverage_ratio")
        self._reject(lambda r: r.update(coverage=6), "coverage: aggregate differs")
        self._reject(lambda r: r.update(zero_observation_days=0), "zero_observation_days")
        self._reject(lambda r: r.update(candidate_coverage=8), "candidate_coverage")

    def test_status_and_series_dates_tampering_with_valid_checksum(self):
        self._reject(lambda r: r["daily_coverage"][1].update(ic_status="valid"), "status conflicts")
        self._reject(lambda r: r["daily_coverage"][2].update(group_status="valid"), "status conflicts")
        self._reject(lambda r: r["ic_series"].pop(), "missing IC point")
        self._reject(lambda r: r["long_short_series"].clear(), "dates differ")
        self._reject(lambda r: r["group_nav"][0]["points"].clear(), "dates differ")
        self._reject(lambda r: r["daily_coverage"].reverse(), "not unique and ordered")

    def test_cost_net_return_and_nav_tampering_with_valid_checksum(self):
        self._reject(lambda r: r["long_short_series"][0].update(cost=0.003), "cost: arithmetic mismatch")
        self._reject(lambda r: r["long_short_series"][0].update(net_return=0.029), "net_return: arithmetic mismatch")
        self._reject(lambda r: r["long_short_series"][0].update(nav=1.04), "nav: arithmetic mismatch")
        self._reject(lambda r: r["long_short_series"][0].update(net_nav=1.03), "net_nav: arithmetic mismatch")
        self._reject(lambda r: r.update(transaction_cost_bps=-1), "negative turnover or transaction cost")

    def test_checksum_still_required(self):
        text = self.path.read_text(encoding="utf-8")
        self.path.write_text(text.replace('"coverage": 5', '"coverage": 6'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            verify_result_consistency(self.path)

    def test_real_evaluator_split_and_embargo_tampering(self):
        start = date(2025, 1, 1)
        observations = [Observation(start + timedelta(days=day), symbol, factor,
                                    0.01 * (day + index))
                        for day in range(7)
                        for index, (symbol, factor) in enumerate((("A", 1.0), ("B", 2.0)))]
        result = evaluate(observations, groups=2, winsorize=False, standardize=False,
                          mad_scale=3, transaction_cost_bps=10)
        days = [start + timedelta(days=day) for day in range(7)]
        enrich_daily_coverage(result, days, {day: 2 for day in days})
        result["time_split"] = evaluate_time_split(observations, "2025-01-05", groups=2,
                                                   winsorize=False, standardize=False,
                                                   mad_scale=3)
        self.result = result
        self._write()
        summary = verify_result_consistency(self.path)
        self.assertEqual(summary["research_signal_dates"], 3)
        self.assertEqual(summary["validation_signal_dates"], 3)
        self.assertEqual(summary["validation_valid_ic_dates"], 3)
        self._reject(lambda r: r["time_split"].update(embargo_signal_date="2025-01-03"),
                     "embargo date differs")
        self._reject(lambda r: r["time_split"]["validation"].update(observation_count=5),
                     "observation_count: count differs")
        self._reject(lambda r: r["time_split"]["research"].update(ic_mean=0.25),
                     "ic_mean: arithmetic mismatch")
        self._reject(lambda r: r["time_split"]["validation"].update(rank_ic_mean=0.25),
                     "rank_ic_mean: arithmetic mismatch")
        self._reject(lambda r: r["time_split"]["validation"].update(ic_positive_ratio=0.5),
                     "ic_positive_ratio: arithmetic mismatch")
        self._reject(lambda r: r["time_split"]["validation"].update(valid_ic_dates=2),
                     "valid_ic_dates: count differs")
        body = json.loads(self.path.read_text(encoding="utf-8"))
        body["task"]["parameters"]["validation_start_date"] = "2025-01-06"
        self.path.write_text(json.dumps(body), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cutoff differs from declared task parameter"):
            verify_result_consistency(self.path)


if __name__ == "__main__":
    unittest.main()
