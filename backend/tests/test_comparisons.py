import sys
import csv
import io
import json
import math
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.db import Base
from app.services.comparisons import compare_runs, comparison_csv, comparison_html
from app.services.runs import create_research_run, execute_research_run


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_csv_neutralizes_formula_like_saved_metadata(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, {
                "factor": factor, "groups": 5,
            }).id) for factor in ("momentum_20d", "reversal_5d")]
            result = compare_runs(runs)
            result["items"][0]["experiment_name"] = "  =HYPERLINK(\"https://example.invalid\")"
            result["items"][1]["factor"] = "\t@SUM(1)"
            result["warnings"].append("+SUM(1)")
            rows = list(csv.DictReader(io.StringIO(comparison_csv(result).decode("utf-8-sig"))))
            self.assertEqual(rows[0]["experiment_name"], "'  =HYPERLINK(\"https://example.invalid\")")
            self.assertEqual(rows[1]["factor"], "'\t@SUM(1)")
            self.assertTrue(any(row["experiment_name"] == "'+SUM(1)" for row in rows))
            self.assertEqual(result["items"][0]["experiment_name"], "  =HYPERLINK(\"https://example.invalid\")")

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

    def test_same_ic_dates_but_different_group_dates_are_not_fully_comparable(self):
        with Session(self.engine, expire_on_commit=False) as session:
            first = execute_research_run(session, create_research_run(session, {
                "factor": "momentum_20d", "groups": 5, "start_date": "2025-02-03",
            }).id)
            second = execute_research_run(session, create_research_run(session, {
                "factor": "reversal_5d", "groups": 5, "start_date": "2025-02-03",
            }).id)
            artifact = next(item for item in second.artifacts if item.artifact_type == "metrics")
            artifact.content = {**artifact.content,
                                "long_short_series": artifact.content["long_short_series"][1:]}
            result = compare_runs([first, second])
            self.assertEqual(result["items"][0]["ic_date_count"], result["items"][1]["ic_date_count"])
            self.assertNotEqual(result["items"][0]["group_date_count"], result["items"][1]["group_date_count"])
            self.assertFalse(result["comparable"])
            self.assertTrue(any("多空分组日期集合不同" in item for item in result["warnings"]))
            self.assertIn("共同多空分组日期数", comparison_csv(result).decode("utf-8-sig"))
            self.assertIn("共同多空分组日期", comparison_html(result))

    def test_null_ic_date_is_not_counted_as_common_effective_ic(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, {
                "factor": factor, "groups": 5, "start_date": "2025-02-03",
            }).id) for factor in ("momentum_20d", "reversal_5d")]
            baseline = compare_runs(runs)
            artifact = next(item for item in runs[1].artifacts if item.artifact_type == "metrics")
            series = [dict(item) for item in artifact.content["ic_series"]]
            series[0]["ic"] = None
            artifact.content = {**artifact.content, "ic_series": series}
            result = compare_runs(runs)
            self.assertEqual(result["common_ic_date_count"], baseline["common_ic_date_count"] - 1)
            self.assertEqual(result["items"][1]["ic_date_count"], baseline["items"][1]["ic_date_count"] - 1)
            self.assertFalse(result["comparable"])
            self.assertTrue(any("实际有效 IC 日期集合不同" in item for item in result["warnings"]))
            self.assertIn("共同有效IC日期数", comparison_csv(result).decode("utf-8-sig"))
            self.assertIn("共同有效 IC 交易日", comparison_html(result))

    def test_missing_metric_is_not_ranked_as_last_place(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, {
                "factor": factor, "groups": 5, "start_date": "2025-02-03",
            }).id) for factor in ("momentum_20d", "reversal_5d")]
            artifact = next(item for item in runs[1].artifacts if item.artifact_type == "metrics")
            artifact.content = {**artifact.content, "long_short_net_total_return": None}
            result = compare_runs(runs)
            self.assertEqual(result["rankings"]["long_short_net_total_return"], [runs[0].id])
            self.assertTrue(any("成本后收益缺失" in item for item in result["warnings"]))

    def test_legacy_nonfinite_metrics_are_missing_in_all_exports(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, {
                "factor": factor, "groups": 5, "start_date": "2025-02-03",
            }).id) for factor in ("momentum_20d", "reversal_5d")]
            artifact = next(item for item in runs[1].artifacts if item.artifact_type == "metrics")
            artifact.content = {**artifact.content, "ic_mean": math.nan,
                                "long_short_net_total_return": math.inf,
                                "coverage": 10 ** 1000}
            result = compare_runs(runs)
            self.assertIsNone(result["items"][1]["metrics"]["ic_mean"])
            self.assertIsNone(result["items"][1]["metrics"]["long_short_net_total_return"])
            self.assertIsNone(result["items"][1]["metrics"]["coverage"])
            self.assertIsNone(result["items"][1]["delta_from_baseline"]["ic_mean"])
            self.assertEqual(result["rankings"]["ic_mean"], [runs[0].id])
            self.assertTrue(any("成本后收益缺失" in item for item in result["warnings"]))
            json.dumps(jsonable_encoder(result), allow_nan=False)
            self.assertNotIn("nan", comparison_csv(result).decode("utf-8-sig").lower())
            self.assertIn("—", comparison_html(result))

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
