import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.domain.composite import combine_factor_observations
from app.domain.research import Observation
from app.models import RunStatus
from app.services.runs import create_composite_run, execute_research_run


class CompositeFactorTests(unittest.TestCase):
    def test_aligns_common_sample_and_normalizes_weights(self):
        trade_date = date(2025, 1, 1)
        first = [
            Observation(trade_date, "A", 1, 0.01),
            Observation(trade_date, "B", 2, 0.02),
            Observation(trade_date, "C", 3, 0.03),
        ]
        second = [
            Observation(trade_date, "A", 3, 0.01),
            Observation(trade_date, "B", 2, 0.02),
        ]
        combined, diagnostics = combine_factor_observations(
            {"first": first, "second": second},
            {"first": 1, "second": 1},
            winsorize=False,
            standardize=False,
        )
        self.assertEqual({item.symbol for item in combined}, {"A", "B"})
        self.assertEqual(diagnostics["common_coverage"], 2)
        self.assertEqual(diagnostics["weights"], {"first": 0.5, "second": 0.5})
        self.assertAlmostEqual(combined[0].factor, 2.0)

    def test_rejects_invalid_components_and_weights(self):
        item = Observation(date(2025, 1, 1), "A", 1, 0.01)
        with self.assertRaisesRegex(ValueError, "at least two"):
            combine_factor_observations({"one": [item]}, {"one": 1})
        with self.assertRaisesRegex(ValueError, "non-negative"):
            combine_factor_observations({"one": [item], "two": [item]}, {"one": 1, "two": -1})

    def test_duplicate_observation_is_rejected_instead_of_overwritten(self):
        item = Observation(date(2025, 1, 1), "A", 1, 0.01)
        with self.assertRaisesRegex(ValueError, "duplicate factor observation: one"):
            combine_factor_observations({"one": [item, item], "two": [item]},
                                        {"one": 1, "two": 1}, winsorize=False, standardize=False)

    def test_conflicting_forward_returns_are_rejected(self):
        day = date(2025, 1, 1)
        first = [Observation(day, "A", 1, 0.01), Observation(day, "B", 2, 0.02)]
        second = [Observation(day, "A", 3, 0.03), Observation(day, "B", 4, 0.02)]
        with self.assertRaisesRegex(ValueError, "component forward returns disagree"):
            combine_factor_observations({"one": first, "two": second},
                                        {"one": 1, "two": 1}, winsorize=False, standardize=False)

    def test_observation_input_order_does_not_change_combination(self):
        day = date(2025, 1, 1)
        first = [Observation(day, symbol, factor, 0.01 * factor)
                 for symbol, factor in zip("ABCD", (1, 2, 3, 4))]
        second = [Observation(day, symbol, factor, 0.01 * ordinal)
                  for symbol, factor, ordinal in zip("ABCD", (4, 1, 3, 2), (1, 2, 3, 4))]
        original = combine_factor_observations({"one": first, "two": second},
                                               {"one": 1, "two": 1}, winsorize=False, standardize=False)
        reversed_input = combine_factor_observations({"one": first[::-1], "two": second[::-1]},
                                                     {"one": 1, "two": 1}, winsorize=False, standardize=False)
        self.assertEqual(original, reversed_input)

    def test_composite_run_persists_recipe_and_result(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with Session(engine, expire_on_commit=False) as session:
                run = create_composite_run(
                    session,
                    {
                        "factors": ["momentum_20d", "reversal_5d"],
                        "lookbacks": {"momentum_20d": 20, "reversal_5d": 5},
                        "groups": 5,
                        "winsorize": True,
                        "standardize": True,
                        "mad_scale": 3,
                    },
                )
                completed = execute_research_run(session, run.id)
                self.assertEqual(completed.status, RunStatus.SUCCESS)
                self.assertTrue(completed.experiment.code_version.startswith("src-sha256:"))
                self.assertEqual(completed.experiment.factor_version.factor_key, "equal_weight_composite")
                self.assertEqual(len(completed.experiment.parameters["components"]), 2)
                metrics = next(item.content for item in completed.artifacts if item.artifact_type == "metrics")
                self.assertEqual(metrics["composite"]["common_coverage"], 1980)
                self.assertEqual(len(metrics["composite"]["correlation_matrix"]), 4)
                report = next(item for item in completed.artifacts if item.artifact_type == "report_html")
                report_text = Path(report.storage_uri).read_text(encoding="utf-8")
                self.assertIn("MULTI FACTOR REPORT", report_text)
                self.assertIn("组合成分", report_text)
                self.assertIn("因子相关矩阵", report_text)
                self.assertIn("逐日计算截面 Pearson 相关系数", report_text)
                self.assertIn("<td>1.0000</td>", report_text)
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
