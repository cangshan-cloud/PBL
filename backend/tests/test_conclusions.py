import sys
import math
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.services.conclusions import build_run_conclusion
from app.services.runs import create_research_run, execute_research_run


class ConclusionTests(unittest.TestCase):
    def test_time_split_grade_uses_validation_not_full_range(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            result = {
                "ic_mean": .15, "rank_ic_mean": .14, "icir": 2,
                "ic_series": [{"date": f"day-{day}", "ic": .15} for day in range(80)],
                "time_split": {"validation_start_date": "2025-04-01",
                               "research": {"ic_mean": .15},
                               "validation": {"ic_mean": .06, "rank_ic_mean": .05,
                                              "icir": 1.2, "ic_positive_ratio": .7,
                                              "valid_ic_dates": 10}},
            }
            conclusion = build_run_conclusion(run, result)
            self.assertEqual(conclusion["grade"], "insufficient")
            self.assertIn("验证期有效 IC 截面不足", conclusion["headline"])
            self.assertIn("验证期IC均值为0.0600", conclusion["evidence"][0])
            self.assertIn("全区间 IC 均值0.1500仅作背景", conclusion["evidence"][-1])
            self.assertEqual(conclusion["method"]["grade_basis"], "validation_ic")
            self.assertEqual(conclusion["method"]["version"], "1.0.3")

            result["time_split"]["research"]["ic_mean"] = -.04
            thin_reversal = build_run_conclusion(run, result)
            self.assertEqual(thin_reversal["grade"], "insufficient")
            self.assertIn("方向相反", thin_reversal["headline"])
            result["time_split"]["research"]["ic_mean"] = .15

            result["time_split"]["validation"]["valid_ic_dates"] = 65
            sufficient = build_run_conclusion(run, result)
            self.assertEqual(sufficient["grade"], "promising")
            result["time_split"]["validation"]["valid_ic_dates"] = 30
            limited = build_run_conclusion(run, result)
            self.assertEqual(limited["grade"], "mixed")
            result["time_split"]["validation"]["valid_ic_dates"] = 65
            result["time_split"]["research"]["ic_mean"] = -.04
            reversal = build_run_conclusion(run, result)
            self.assertEqual(reversal["grade"], "mixed")
            self.assertIn("方向相反", reversal["headline"])
            self.assertTrue(any("不能用全区间均值掩盖" in item for item in reversal["limitations"]))

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_generates_auditable_conclusion_for_successful_run(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = execute_research_run(
                session,
                create_research_run(session, {"factor": "momentum_20d", "groups": 5}).id,
            )
            conclusion = build_run_conclusion(run)
            self.assertEqual(conclusion["run_id"], run.id)
            self.assertEqual(conclusion["method"]["type"], "deterministic_rule_template")
            self.assertEqual(len(conclusion["evidence"]), 5)
            self.assertTrue(any("合成演示数据" in item for item in conclusion["limitations"]))
            self.assertIn("必须由研究人员复核", conclusion["disclaimer"])

            report = next(item for item in run.artifacts if item.artifact_type == "report_html")
            report_text = Path(report.storage_uri).read_text(encoding="utf-8")
            self.assertIn("结构化结论草稿", report_text)
            self.assertIn(conclusion["headline"], report_text)

    def test_rejects_conclusion_for_unfinished_run(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            with self.assertRaisesRegex(ValueError, "successful"):
                build_run_conclusion(run)

    def test_missing_ic_dates_do_not_inflate_effective_sample(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            result = {
                "ic_mean": 0.04, "rank_ic_mean": 0.03, "icir": 1.2,
                "ic_series": ([{"date": f"day-{day}", "ic": None} for day in range(97)] +
                              [{"date": "valid", "ic": 0.04},
                               {"date": "nan", "ic": math.nan}, {"date": "boolean", "ic": True}]),
            }
            conclusion = build_run_conclusion(run, result)
            self.assertEqual(conclusion["grade"], "insufficient")
            self.assertEqual(conclusion["method"]["version"], "1.0.2")
            self.assertIn("覆盖1个有效截面", conclusion["evidence"][0])
            self.assertTrue(any("99个交易日无法计算" in item for item in conclusion["limitations"]))
            self.assertTrue(any("有效截面少于60" in item for item in conclusion["limitations"]))

    def test_constant_factor_skips_are_disclosed_without_changing_old_results(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            result = {"ic_series": [{"date": "2025-01-01", "ic": None}],
                      "group_skipped_constant_factor_days": 1}
            conclusion = build_run_conclusion(run, result)
            self.assertTrue(any("1个交易日全截面因子同值" in item for item in conclusion["limitations"]))
            self.assertFalse(any("全截面因子同值" in item for item in
                                 build_run_conclusion(run, {"ic_series": []})["limitations"]))

    def test_insufficient_daily_group_sample_is_disclosed(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            conclusion = build_run_conclusion(run, {"ic_series": [],
                                                     "group_skipped_insufficient_sample_days": 2})
            self.assertTrue(any("2个交易日有效证券数少于目标分组数" in item
                                for item in conclusion["limitations"]))

    def test_no_group_result_is_not_described_as_zero_or_performance(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "groups": 5})
            conclusion = build_run_conclusion(run, {"ic_series": [], "long_short_series": [],
                                                     "long_short_total_return": None,
                                                     "long_short_net_total_return": None})
            self.assertIn("不能评价多空表现", conclusion["evidence"][2])
            self.assertIn("没有可计算的成本后多空收益", conclusion["evidence"][3])
            self.assertTrue(any("不得把缺失值解释为零收益" in item for item in conclusion["limitations"]))


if __name__ == "__main__":
    unittest.main()
