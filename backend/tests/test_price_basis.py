import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.prices import apply_price_basis
from app.domain.research import PriceRow, momentum_observations
from app.services.runs import _validate_dataset_price_basis


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

    def test_adapter_adjustment_provenance_blocks_double_adjustment(self):
        dataset = SimpleNamespace(quality_report={"columns": ["close", "adj_factor"], "adapter_report": {"source_adjustment_flags": ["2"]}})
        with self.assertRaisesRegex(ValueError, "double adjustment"):
            _validate_dataset_price_basis(dataset, "factor_adjusted")
        _validate_dataset_price_basis(dataset, "source_close")
        dataset.quality_report["adapter_report"]["source_adjustment_flags"] = ["3"]
        _validate_dataset_price_basis(dataset, "factor_adjusted")
        dataset.quality_report["adapter_report"]["source_adjustment_flags"] = "3"
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            _validate_dataset_price_basis(dataset, "factor_adjusted")

    def test_adjustment_requires_a_numeric_multiplier_column_before_queueing(self):
        dataset = SimpleNamespace(quality_report={"columns": ["trade_date", "symbol", "close"]})
        with self.assertRaisesRegex(ValueError, "missing adj_factor"):
            _validate_dataset_price_basis(dataset, "factor_adjusted")
        _validate_dataset_price_basis(dataset, "source_close")
        dataset.quality_report["adapter_report"] = {"source_adjustment_flags": ["3"]}
        with self.assertRaisesRegex(ValueError, "missing adj_factor"):
            _validate_dataset_price_basis(dataset, "factor_adjusted")
        dataset.quality_report["columns"].append("adj_factor")
        _validate_dataset_price_basis(dataset, "factor_adjusted")

    def test_missing_multiplier_values_block_only_the_full_unfiltered_sample(self):
        dataset = SimpleNamespace(quality_report={
            "columns": ["trade_date", "symbol", "close", "adj_factor"],
            "missing_counts": {"adj_factor": 1},
            "missing_adj_factor_by_symbol": {"B": 1},
        })
        with self.assertRaisesRegex(ValueError, "missing adj_factor values"):
            _validate_dataset_price_basis(dataset, "factor_adjusted")
        _validate_dataset_price_basis(dataset, "factor_adjusted", ["A", "C"])
        with self.assertRaisesRegex(ValueError, "selected symbols have missing"):
            _validate_dataset_price_basis(dataset, "factor_adjusted", ["A", "B"])
        _validate_dataset_price_basis(dataset, "source_close")
        dataset.quality_report["missing_counts"]["adj_factor"] = 0
        _validate_dataset_price_basis(dataset, "factor_adjusted")
        del dataset.quality_report["missing_adj_factor_by_symbol"]
        _validate_dataset_price_basis(dataset, "factor_adjusted", ["A", "B"])


if __name__ == "__main__":
    unittest.main()
