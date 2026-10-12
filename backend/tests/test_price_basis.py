import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.prices import apply_price_basis
from app.domain.research import PriceRow, momentum_observations


class PriceBasisTests(unittest.TestCase):
    def test_split_day_does_not_create_false_loss_after_adjustment(self):
        days = [date(2025, 1, day) for day in (2, 3, 6, 7)]
        rows = [
            PriceRow(day, "000001.SZ", close, adj_factor=factor)
            for day, close, factor in zip(days, (100, 100, 50, 55), (1, 1, 2, 2))
        ]
        raw = momentum_observations(apply_price_basis(rows, "source_close"), lookback=1)
        adjusted_rows = apply_price_basis(rows, "factor_adjusted")
        adjusted = momentum_observations(adjusted_rows, lookback=1)
        self.assertEqual([row.close for row in adjusted_rows], [100, 100, 100, 110])
        self.assertAlmostEqual(raw[0].forward_return, -0.5)
        self.assertAlmostEqual(adjusted[0].forward_return, 0)
        self.assertAlmostEqual(raw[1].factor, -0.5)
        self.assertAlmostEqual(adjusted[1].factor, 0)
        self.assertAlmostEqual(adjusted[1].forward_return, 0.1)
        self.assertEqual([row.close for row in rows], [100, 100, 50, 55])

    def test_adjusted_basis_requires_valid_factor_on_every_row(self):
        for factor in (None, 0, -1, float("nan"), float("inf")):
            with self.subTest(factor=factor), self.assertRaisesRegex(ValueError, "adj_factor"):
                apply_price_basis([PriceRow(date(2025, 1, 2), "A", 100, adj_factor=factor)], "factor_adjusted")

    def test_unknown_basis_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "price_basis"):
            apply_price_basis([], "unknown")


if __name__ == "__main__":
    unittest.main()
