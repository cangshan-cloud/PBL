import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.services.comparisons import compare_runs, comparison_csv, comparison_html
from app.services.runs import create_research_run, execute_research_run


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_compares_successful_runs_with_baseline_deltas_and_rankings(self):
        with Session(self.engine, expire_on_commit=False) as session:
            momentum = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            reversal = create_research_run(session, {"factor": "reversal_5d", "groups": 5})
            momentum = execute_research_run(session, momentum.id)
            reversal = execute_research_run(session, reversal.id)

            result = compare_runs([momentum, reversal])

            self.assertEqual(result["baseline_run_id"], momentum.id)
            self.assertEqual(result["common_ic_date_count"], 99)
            self.assertFalse(result["comparable"])
            self.assertTrue(any("日期集合不同" in message for message in result["warnings"]))
            self.assertEqual(result["items"][0]["delta_from_baseline"]["ic_mean"], 0)
            self.assertEqual(set(result["rankings"]["icir"]), {momentum.id, reversal.id})

            csv_content = comparison_csv(result)
            self.assertTrue(csv_content.startswith(b"\xef\xbb\xbf"))
            self.assertIn("ic_mean_delta_from_baseline", csv_content.decode("utf-8-sig"))
            html_content = comparison_html(result)
            self.assertIn("<!doctype html>", html_content)
            self.assertIn("实验对比报告", html_content)
            self.assertIn(momentum.experiment.name, html_content)

    def test_rejects_duplicate_or_unfinished_runs(self):
        with Session(self.engine, expire_on_commit=False) as session:
            pending = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            with self.assertRaisesRegex(ValueError, "distinct"):
                compare_runs([pending, pending])
            other = create_research_run(session, {"factor": "reversal_5d", "groups": 5})
            with self.assertRaisesRegex(ValueError, "successful"):
                compare_runs([pending, other])

    def test_matching_effective_dates_are_comparable_despite_different_lookbacks(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, {
                "factor": factor, "groups": 5, "start_date": "2025-02-03",
            }).id) for factor in ("momentum_20d", "reversal_5d")]
            result = compare_runs(runs)
            self.assertTrue(result["comparable"])
            self.assertEqual(result["items"][0]["ic_start_date"], "2025-02-03")

    def test_different_stock_pool_and_preprocessing_are_disclosed(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, parameters).id) for parameters in (
                {"factor": "momentum_20d", "groups": 2},
                {"factor": "momentum_20d", "groups": 2, "symbols": ["DEMO01", "DEMO02"], "winsorize": False},
            )]
            result = compare_runs(runs)
            self.assertFalse(result["comparable"])
            self.assertTrue(any("证券筛选" in message for message in result["warnings"]))
            self.assertTrue(any("标准化参数" in message for message in result["warnings"]))

    def test_marks_different_group_counts_as_not_directly_comparable(self):
        with Session(self.engine, expire_on_commit=False) as session:
            first = execute_research_run(
                session,
                create_research_run(session, {"factor": "momentum_20d", "groups": 5}).id,
            )
            second = execute_research_run(
                session,
                create_research_run(session, {"factor": "reversal_5d", "groups": 4}).id,
            )
            result = compare_runs([first, second])
            self.assertFalse(result["comparable"])
            self.assertIn("分组数不同", result["warnings"][0])


if __name__ == "__main__":
    unittest.main()
