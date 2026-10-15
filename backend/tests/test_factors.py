import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.factors import FACTOR_REGISTRY, calculate_factor, get_factor
from app.domain.research import PriceRow, calendar_positions
from app.services.sample_data import load_sample_prices


def rows(days: int = 8) -> list[PriceRow]:
    start = date(2025, 1, 1)
    output = []
    for symbol_index, symbol in enumerate(("A", "B", "C"), start=1):
        for day in range(days):
            output.append(
                PriceRow(
                    start + timedelta(days=day),
                    symbol,
                    10 + symbol_index * day + day * day / 10,
                    turnover_rate=symbol_index + day / 10,
                    total_mv=1000 * symbol_index + day,
                    pe=8 * symbol_index + day / 10,
                )
            )
    return output


class FactorTests(unittest.TestCase):
    def test_registry_contains_six_published_factors(self):
        self.assertEqual(
            set(FACTOR_REGISTRY),
            {"momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d", "market_cap", "pe"},
        )
        self.assertTrue(all(item.public_dict()["status"] == "available" for item in FACTOR_REGISTRY.values()))

    def test_price_factor_formulas(self):
        data = rows()
        momentum = calculate_factor("momentum_20d", data, 2)
        reversal = calculate_factor("reversal_5d", data, 2)
        volatility = calculate_factor("volatility_20d", data, 2)
        self.assertGreater(len(momentum), 0)
        self.assertAlmostEqual(reversal[0].factor, -momentum[0].factor)
        self.assertGreater(volatility[0].factor, 0)
        self.assertEqual(momentum[0].forward_return, reversal[0].forward_return)

    def test_field_factor_formulas(self):
        data = rows()
        turnover = calculate_factor("turnover_20d", data, 2)
        market_cap = calculate_factor("market_cap", data)
        pe = calculate_factor("pe", data)
        self.assertAlmostEqual(turnover[0].factor, 1.05)
        self.assertEqual(market_cap[0].factor, 1000)
        self.assertEqual(pe[0].factor, 8)

    def test_missing_market_day_does_not_compress_window_or_forward_label(self):
        data = [item for item in rows(7) if not (item.symbol == "A" and item.trade_date == date(2025, 1, 3))]
        for factor_key in FACTOR_REGISTRY:
            with self.subTest(factor=factor_key):
                observations = calculate_factor(factor_key, data, 2 if factor_key in {
                    "momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d"
                } else None)
                a_dates = {item.trade_date for item in observations if item.symbol == "A"}
                self.assertNotIn(date(2025, 1, 2), a_dates)  # Next A row is Jan 4, not the next market day.
                if factor_key in {"momentum_20d", "reversal_5d", "volatility_20d"}:
                    self.assertNotIn(date(2025, 1, 4), a_dates)  # Window crosses the missing Jan 3.
                    self.assertNotIn(date(2025, 1, 5), a_dates)
                    self.assertIn(date(2025, 1, 6), a_dates)
                self.assertTrue(any(item.symbol == "B" for item in observations))

    def test_full_dataset_calendar_detects_gaps_after_symbol_selection(self):
        data = [item for item in rows(7) if not (item.symbol == "A" and item.trade_date == date(2025, 1, 3))]
        selected = [item for item in data if item.symbol == "A"]
        without_full_calendar = calculate_factor("pe", selected)
        with_full_calendar = calculate_factor("pe", selected, market_positions=calendar_positions(data))
        self.assertIn(date(2025, 1, 2), {item.trade_date for item in without_full_calendar})
        self.assertNotIn(date(2025, 1, 2), {item.trade_date for item in with_full_calendar})
        momentum = calculate_factor("momentum_20d", selected, 2, market_positions=calendar_positions(data))
        self.assertEqual([item.trade_date for item in momentum], [date(2025, 1, 6)])

    def test_missing_field_and_unknown_factor_are_rejected(self):
        minimal = [PriceRow(item.trade_date, item.symbol, item.close) for item in rows()]
        with self.assertRaisesRegex(ValueError, "turnover_rate"):
            calculate_factor("turnover_20d", minimal, 2)
        with self.assertRaisesRegex(ValueError, "unsupported factor"):
            get_factor("future_factor")

    def test_bundled_demo_dataset_supports_all_published_factors(self):
        data = load_sample_prices()
        self.assertEqual(len(data), 2400)
        self.assertEqual(len({item.symbol for item in data}), 20)
        for factor_key, definition in FACTOR_REGISTRY.items():
            with self.subTest(factor=factor_key):
                observations = calculate_factor(factor_key, data, definition.default_lookback)
                self.assertGreater(len(observations), 0)


if __name__ == "__main__":
    unittest.main()
