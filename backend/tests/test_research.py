import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.research import Observation, PriceRow, evaluate, ic_histogram, momentum_observations, pearson, preprocess_observations


class ResearchEngineTests(unittest.TestCase):
    def test_factor_at_t_uses_next_day_return(self):
        start = date(2025, 1, 1)
        rows = [PriceRow(start + timedelta(days=i), "A", 100 + i) for i in range(5)]
        observations = momentum_observations(rows, lookback=2)
        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0].trade_date, start + timedelta(days=2))
        self.assertAlmostEqual(observations[0].factor, 102 / 100 - 1)
        self.assertAlmostEqual(observations[0].forward_return, 103 / 102 - 1)

    def test_perfect_ic(self):
        self.assertAlmostEqual(pearson([1, 2, 3], [2, 4, 6]), 1.0)

    def test_ic_histogram_uses_fixed_bins_and_excludes_missing_days(self):
        first = date(2025, 1, 1)
        items = [
            Observation(first + timedelta(days=offset), symbol, factor, forward)
            for offset, returns in enumerate(((1, 2, 3), (3, 2, 1), (2, 2, 2)))
            for symbol, factor, forward in zip(("A", "B", "C"), (1, 2, 3), returns)
        ]
        result = evaluate(items, groups=3, winsorize=False, standardize=False)
        self.assertEqual(len(result["ic_series"]), 3)
        self.assertEqual(sum(item["count"] for item in result["ic_histogram"]), 2)
        self.assertEqual(result["ic_histogram"][0]["count"], 1)
        self.assertEqual(result["ic_histogram"][-1]["count"], 1)
        self.assertEqual(ic_histogram([])[0]["count"], 0)

    def test_nearly_constant_ic_does_not_create_unbounded_icir(self):
        first = date(2025, 1, 1)
        second = date(2025, 1, 2)
        items = [
            Observation(day, symbol, factor, forward)
            for day, returns in ((first, (0.1, 0, -0.1)), (second, (0.10000000000000002, 0, -0.1)))
            for symbol, factor, forward in zip(("A", "B", "C"), (0.1, 0, -0.1), returns)
        ]
        result = evaluate(items, groups=3, winsorize=False, standardize=False)
        self.assertEqual(result["ic_std"], 0)
        self.assertIsNone(result["icir"])

    def test_evaluate_returns_summary(self):
        items = [
            Observation(date(2025, 1, 1), "A", 1, 0.01),
            Observation(date(2025, 1, 1), "B", 2, 0.02),
            Observation(date(2025, 1, 1), "C", 3, 0.03),
        ]
        result = evaluate(items, groups=3)
        self.assertEqual(result["coverage"], 3)
        self.assertAlmostEqual(result["ic_mean"], 1.0)
        self.assertEqual(len(result["group_returns"]), 3)
        self.assertEqual(len(result["group_nav"]), 3)
        self.assertAlmostEqual(result["long_short_mean"], 0.02)
        self.assertAlmostEqual(result["long_short_total_return"], 0.02)
        self.assertEqual(result["preprocessing"]["method"], "MAD")

    def test_group_mean_averages_daily_equal_weight_returns_not_all_stock_rows(self):
        first = date(2025, 1, 1)
        second = date(2025, 1, 2)
        items = [
            Observation(first, "A", 1, 0.0), Observation(first, "B", 2, 0.10),
            Observation(second, "A", 1, 0.0), Observation(second, "B", 2, 0.0),
            Observation(second, "C", 3, 0.30), Observation(second, "D", 4, 0.50),
        ]
        result = evaluate(items, groups=2, winsorize=False, standardize=False)
        top = next(item for item in result["group_returns"] if item["group"] == 2)
        self.assertAlmostEqual(top["mean_return"], (0.10 + 0.40) / 2)
        top_nav = next(item for item in result["group_nav"] if item["group"] == 2)["points"]
        self.assertAlmostEqual(top_nav[-1]["nav"], 1.10 * 1.40)
        self.assertEqual(result["coverage"], 6)

    def test_preprocessing_winsorizes_outlier_and_standardizes_each_date(self):
        items = [
            Observation(date(2025, 1, 1), "A", 1, 0.01),
            Observation(date(2025, 1, 1), "B", 2, 0.02),
            Observation(date(2025, 1, 1), "C", 3, 0.03),
            Observation(date(2025, 1, 1), "D", 1000, 0.04),
        ]
        processed = preprocess_observations(items, mad_scale=3)
        values = [item.factor for item in processed]
        self.assertAlmostEqual(sum(values), 0.0)
        self.assertAlmostEqual(sum(value * value for value in values) / len(values), 1.0)
        self.assertLess(max(values), 2.0)

    def test_turnover_and_ic_positive_ratio(self):
        day1 = date(2025, 1, 1)
        day2 = date(2025, 1, 2)
        items = [
            Observation(day1, "A", 1, 0.01), Observation(day1, "B", 2, 0.02),
            Observation(day2, "A", 2, 0.02), Observation(day2, "B", 1, 0.01),
        ]
        result = evaluate(items, groups=2)
        self.assertEqual(result["ic_positive_ratio"], 1.0)
        self.assertEqual(result["top_group_turnover"], 1.0)
        self.assertEqual(len(result["long_short_series"]), 2)

    def test_rejects_invalid_close(self):
        rows = [PriceRow(date(2025, 1, 1), "A", 0)]
        with self.assertRaisesRegex(ValueError, "close must be positive"):
            momentum_observations(rows, 2)

    def test_costs_include_initial_entry_and_both_sides_of_replacement(self):
        items = [
            Observation(date(2025, 1, 1), "A", 1, 0.01),
            Observation(date(2025, 1, 1), "B", 2, 0.02),
            Observation(date(2025, 1, 2), "A", 2, 0.02),
            Observation(date(2025, 1, 2), "B", 1, 0.01),
        ]
        result = evaluate(items, groups=2, transaction_cost_bps=10)
        first, second = result["long_short_series"]
        self.assertAlmostEqual(first["cost"], 0.002)
        self.assertAlmostEqual(second["cost"], 0.004)
        self.assertAlmostEqual(result["long_short_net_total_return"], 1.008 * 1.006 - 1)
        zero = evaluate(items, groups=2, transaction_cost_bps=0)
        self.assertEqual(zero["long_short_net_total_return"], zero["long_short_total_return"])

    def test_unchanged_targets_do_not_incur_repeated_entry_cost(self):
        items = [
            Observation(date(2025, 1, day), symbol, factor, factor / 100)
            for day in (1, 2)
            for symbol, factor in (("A", 1), ("B", 2))
        ]
        result = evaluate(items, groups=2, transaction_cost_bps=10)
        self.assertEqual(result["long_short_series"][1]["cost"], 0)
        self.assertEqual(result["top_group_turnover"], 0)


if __name__ == "__main__":
    unittest.main()
