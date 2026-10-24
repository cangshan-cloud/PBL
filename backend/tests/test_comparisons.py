import sys
import csv
import io
import json
import math
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.db import Base
from app.services.comparisons import _dataset_source_kind, _export_number, _ic_evidence, compare_runs, comparison_csv, comparison_html
from app.services.observation_artifact import create_observation_artifact, read_observation_artifact
from app.services.runs import create_research_run, execute_research_run


class ComparisonTests(unittest.TestCase):
    def test_dataset_source_kind_does_not_claim_imported_csv_is_real_market_data(self):
        self.assertEqual(_dataset_source_kind(SimpleNamespace(dataset_key="demo_daily", quality_report={"source": "bundled_demo"})), "bundled_demo")
        self.assertEqual(_dataset_source_kind(SimpleNamespace(dataset_key="hs300_2024", quality_report={"dataset_kind": "hs300_bundle_v1"})), "historical_bundle")
        self.assertEqual(_dataset_source_kind(SimpleNamespace(dataset_key="user_data", quality_report={})), "imported_csv")
        self.assertEqual(_dataset_source_kind(SimpleNamespace(dataset_key="user_data", quality_report={"source": "bundled_demo"})), "imported_csv")

    def test_csv_summary_rows_quote_and_disarm_free_text(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, {
                "factor": factor, "groups": 5,
            }).id) for factor in ("momentum_20d", "reversal_5d")]
            result = compare_runs(runs)
            result["matched_sample"]["evidence"]["note"] = "=HYPERLINK(\"bad,url\"),\n说明"
            result["matched_validation_sample"]["reason"] = "\t=1+1,\n缺少切分"
            rows = list(csv.reader(io.StringIO(comparison_csv(result).decode("utf-8-sig"))))
            self.assertIn(["证据提示", "'=HYPERLINK(\"bad,url\"),\n说明"], rows)
            self.assertIn(["验证期严格样本IC摘要", "'\t=1+1,\n缺少切分"], rows)

    def test_html_numbers_keep_ic_precision_and_count_units(self):
        self.assertEqual(_export_number(0.24512, "ic_mean"), "0.2451")
        self.assertEqual(_export_number(0.00123, "ic_mean", signed=True), "+0.0012")
        self.assertEqual(_export_number(0.58123, "long_short_total_return"), "58.12%")
        self.assertEqual(_export_number(0.125, "ic_positive_ratio", signed=True), "+12.50%")
        self.assertEqual(_export_number(-300, "coverage", signed=True), "-300")

    def test_ic_evidence_uses_minimum_valid_days_without_claiming_significance(self):
        self.assertEqual(_ic_evidence(1)["level"], "insufficient")
        self.assertEqual(_ic_evidence(19)["level"], "insufficient")
        self.assertEqual(_ic_evidence(20)["level"], "limited")
        self.assertEqual(_ic_evidence(59)["level"], "limited")
        self.assertEqual(_ic_evidence(60)["level"], "descriptive")
        self.assertIn("不代表显著性", _ic_evidence(60)["note"])

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_validation_split_comparison_discloses_mixed_and_different_cutoffs(self):
        with Session(self.engine, expire_on_commit=False) as session:
            common = {"factor": "momentum_20d", "groups": 5, "start_date": "2025-02-03"}
            runs = [execute_research_run(session, create_research_run(session, {
                **common, **options,
            }).id) for options in (
                {"validation_start_date": "2025-04-01"},
                {},
                {"validation_start_date": "2025-04-08"},
            )]
            mixed = compare_runs(runs[:2])
            self.assertFalse(mixed["comparable"])
            self.assertIsNone(mixed["common_validation_ic_date_count"])
            self.assertTrue(any("有时间切分和无时间切分" in warning for warning in mixed["warnings"]))
            self.assertIsNotNone(mixed["items"][0]["validation_ic"]["ic_mean"])
            self.assertIsNone(mixed["items"][1]["validation_ic"])
            self.assertFalse(mixed["matched_validation_sample"]["available"])
            csv_rows = list(csv.DictReader(io.StringIO(comparison_csv(mixed).decode("utf-8-sig"))))
            self.assertEqual(csv_rows[0]["validation_start_date"], "2025-04-01")
            self.assertEqual(csv_rows[1]["validation_ic_mean"], "")
            self.assertIn("验证期 IC 摘要", comparison_html(mixed))
            json.dumps(jsonable_encoder(mixed), allow_nan=False)

            different = compare_runs([runs[0], runs[2]])
            self.assertFalse(different["comparable"])
            self.assertIsNone(different["common_validation_ic_date_count"])
            self.assertTrue(any("验证期起始日不同" in warning for warning in different["warnings"]))
            self.assertFalse(different["matched_validation_sample"]["available"])

            matching = execute_research_run(session, create_research_run(session, {
                **common, "validation_start_date": "2025-04-01",
            }).id)
            same = compare_runs([runs[0], matching])
            self.assertGreater(same["common_validation_ic_date_count"], 0)
            self.assertEqual(same["items"][0]["validation_start_date"], "2025-04-01")
            self.assertEqual(same["items"][0]["observation_artifact_count"],
                             same["items"][0]["metrics"]["coverage"])
            self.assertEqual(same["items"][0]["validation_artifact_count"],
                             same["items"][0]["validation_observation_count"])
            strict = same["matched_validation_sample"]
            self.assertTrue(strict["available"])
            self.assertEqual(strict["validation_start_date"], "2025-04-01")
            self.assertGreater(strict["observation_count"], 0)
            self.assertLess(strict["observation_count"], same["matched_sample"]["observation_count"])
            self.assertAlmostEqual(strict["items"][0]["retention_ratio"],
                                   strict["observation_count"] / strict["items"][0]["source_observation_count"])
            self.assertEqual(strict["label_mismatch_count"], 0)
            self.assertEqual(len(strict["items"]), 2)
            self.assertGreater(strict["items"][0]["valid_ic_dates"], 0)
            self.assertEqual(strict["min_valid_ic_dates"], min(item["valid_ic_dates"] for item in strict["items"]))
            self.assertEqual(strict["evidence"]["level"], _ic_evidence(strict["min_valid_ic_dates"])["level"])
            self.assertIn("证据提示", comparison_csv(same).decode("utf-8-sig"))
            self.assertIn("最少有效 IC 日", comparison_html(same))
            self.assertIn("验证期严格样本IC摘要", comparison_csv(same).decode("utf-8-sig"))
            self.assertIn("验证期严格样本 IC 摘要", comparison_html(same))

            matching.experiment.parameters = {**matching.experiment.parameters,
                                              "validation_start_date": "2025-04-02"}
            inconsistent = compare_runs([runs[0], matching])
            self.assertFalse(inconsistent["matched_validation_sample"]["available"])
            self.assertIn("参数与已保存", inconsistent["matched_validation_sample"]["reason"])
            matching.experiment.parameters = {**matching.experiment.parameters,
                                              "validation_start_date": "2025-04-01"}

            matching.artifacts[:] = [item for item in matching.artifacts if item.artifact_type != "observations"]
            legacy = compare_runs([runs[0], matching])
            self.assertFalse(legacy["matched_validation_sample"]["available"])
            self.assertFalse(legacy["matched_sample"]["available"])
            self.assertFalse(legacy["comparable"])
            self.assertTrue(any("缺少逐股观测产物" in warning for warning in legacy["warnings"]))
            self.assertTrue(legacy["items"][0]["validation_ic"])
            self.assertIsNotNone(legacy["items"][0]["common_date_ic"]["ic_mean"])
            self.assertIn("可比性,谨慎解释", comparison_csv(legacy).decode("utf-8-sig"))
            self.assertIn("缺少逐股观测产物", comparison_html(legacy))

    def test_validation_matched_sample_requires_shared_symbol_dates(self):
        with Session(self.engine, expire_on_commit=False) as session:
            common = {"factor": "momentum_20d", "groups": 2,
                      "start_date": "2025-02-03", "validation_start_date": "2025-04-01"}
            runs = [execute_research_run(session, create_research_run(session, {
                **common, "symbols": symbols,
            }).id) for symbols in (["DEMO01", "DEMO02"], ["DEMO03", "DEMO04"])]
            result = compare_runs(runs)
            self.assertFalse(result["matched_sample"]["available"])
            self.assertIn("没有共同证券日期观测", result["matched_sample"]["reason"])
            self.assertFalse(result["matched_validation_sample"]["available"])
            self.assertIn("没有共同证券日期观测", result["matched_validation_sample"]["reason"])
            self.assertIn("没有共同证券日期观测", comparison_html(result))

    def test_matched_sample_requires_valid_ic_cross_sections(self):
        with Session(self.engine, expire_on_commit=False) as session:
            params = {"factor": "momentum_20d", "groups": 2, "symbols": ["DEMO01", "DEMO02"],
                      "start_date": "2025-02-03", "validation_start_date": "2025-04-01"}
            runs = [execute_research_run(session, create_research_run(session, params).id)
                    for _ in range(2)]
            for run in runs:
                artifact = next(item for item in run.artifacts if item.artifact_type == "observations")
                constant = [replace(item, factor=1.0) for item in read_observation_artifact(artifact).values()]
                replacement = create_observation_artifact(run.id, constant,
                                                          Path(artifact.storage_uri).parents[2])
                artifact.checksum = replacement.checksum
            result = compare_runs(runs)
            self.assertGreater(result["matched_sample"]["observation_count"], 0)
            self.assertFalse(result["matched_sample"]["available"])
            self.assertFalse(result["matched_validation_sample"]["available"])
            self.assertTrue(any("有效 IC 截面" in warning for warning in result["warnings"]))
            self.assertIn("没有有效 IC 截面", comparison_html(result))
            self.assertIn("严格样本IC摘要", comparison_csv(result).decode("utf-8-sig"))

    def test_retention_over_one_warns_about_inconsistent_saved_counts(self):
        with Session(self.engine, expire_on_commit=False) as session:
            params = {"factor": "momentum_20d", "groups": 5, "start_date": "2025-02-03",
                      "validation_start_date": "2025-04-01"}
            runs = [execute_research_run(session, create_research_run(session, params).id)
                    for _ in range(2)]
            artifact = next(item for item in runs[0].artifacts if item.artifact_type == "metrics")
            split = artifact.content["time_split"]
            artifact.content = {
                **artifact.content, "coverage": 1,
                "time_split": {**split, "validation": {**split["validation"], "observation_count": 1}},
            }
            result = compare_runs(runs)
            self.assertGreater(result["matched_sample"]["items"][0]["retention_ratio"], 1)
            self.assertGreater(result["matched_validation_sample"]["items"][0]["retention_ratio"], 1)
            self.assertTrue(any("超过某个任务保存的原观测数" in warning for warning in result["warnings"]))
            self.assertTrue(any("超过某个任务保存的验证期原观测数" in warning for warning in result["warnings"]))
            self.assertTrue(any("指标有效观测数与逐股产物条数不一致" in warning for warning in result["warnings"]))
            self.assertTrue(any("验证期观测数与逐股产物条数不一致" in warning for warning in result["warnings"]))

            artifact.content = {
                **artifact.content, "coverage": 10_000,
                "time_split": {**split, "validation": {**split["validation"], "observation_count": 10_000}},
            }
            larger_denominator = compare_runs(runs)
            self.assertLess(larger_denominator["matched_sample"]["items"][0]["retention_ratio"], 1)
            self.assertEqual(larger_denominator["items"][0]["observation_artifact_count"],
                             len(read_observation_artifact(next(item for item in runs[0].artifacts if item.artifact_type == "observations"))))
            self.assertTrue(any("指标有效观测数与逐股产物条数不一致" in warning for warning in larger_denominator["warnings"]))
            self.assertTrue(any("验证期观测数与逐股产物条数不一致" in warning for warning in larger_denominator["warnings"]))
            self.assertIn("observation_artifact_count", comparison_csv(larger_denominator).decode("utf-8-sig"))
            self.assertIn("逐股产物观测", comparison_html(larger_denominator))

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
            self.assertIsNotNone(result["items"][0]["common_date_ic"]["ic_mean"])
            self.assertTrue(result["matched_sample"]["available"])
            self.assertGreater(result["matched_sample"]["observation_count"], 0)
            self.assertIn("common_date_ic_mean", comparison_csv(result).decode("utf-8-sig"))
            self.assertIn("共同日期 IC 摘要", comparison_html(result))
            self.assertIn("严格样本 IC 摘要", comparison_html(result))
            self.assertFalse(result["comparable"])
            self.assertTrue(any("日期集合不同" in message for message in result["warnings"]))
            self.assertEqual(result["items"][0]["delta_from_baseline"]["ic_mean"], 0)
            self.assertEqual(set(result["rankings"]["icir"]), {momentum.id, reversal.id})

            csv_content = comparison_csv(result)
            self.assertTrue(csv_content.startswith(b"\xef\xbb\xbf"))
            self.assertIn("ic_mean_delta_from_baseline", csv_content.decode("utf-8-sig"))
            csv_rows = list(csv.DictReader(io.StringIO(csv_content.decode("utf-8-sig"))))
            self.assertEqual(csv_rows[0]["dataset_version_id"], result["items"][0]["dataset_version_id"])
            self.assertEqual(csv_rows[1]["dataset_version_id"], result["items"][1]["dataset_version_id"])
            self.assertEqual(csv_rows[0]["dataset_checksum_sha256"], result["items"][0]["dataset_checksum_sha256"])
            self.assertEqual(result["items"][0]["dataset_checksum_sha256"], momentum.experiment.dataset_version.checksum)
            self.assertEqual(result["items"][0]["dataset_source_kind"], "bundled_demo")
            self.assertEqual(csv_rows[0]["dataset_source_kind"], "bundled_demo")
            html_content = comparison_html(result)
            self.assertIn("<!doctype html>", html_content)
            self.assertIn("实验对比报告", html_content)
            self.assertIn(momentum.experiment.name, html_content)
            self.assertIn(f"<td><code>{momentum.id}</code></td>", html_content)
            self.assertIn(f"<td><code>{reversal.id}</code></td>", html_content)
            self.assertIn(f"<td><code>{result['items'][0]['dataset_version_id']}</code></td>", html_content)
            self.assertIn("<th>数据版本 ID</th>", html_content)
            self.assertIn("<th>数据版本 SHA-256</th>", html_content)
            self.assertIn(result["items"][0]["dataset_checksum_sha256"], html_content)
            self.assertIn("内置演示数据", html_content)
            self.assertLess(html_content.index(momentum.id), html_content.index(reversal.id))
            self.assertIn("<td>基准</td>", html_content)
            self.assertIn("<td>候选 1</td>", html_content)
            formatted_ic = _export_number(result["items"][0]["metrics"]["ic_mean"], "ic_mean")
            self.assertIn(f"<td><b>{formatted_ic}</b>", html_content)

            result["items"][0]["experiment_name"] = "<script>alert(1)</script>"
            escaped_html = comparison_html(result)
            self.assertNotIn("<script>alert(1)</script>", escaped_html)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", escaped_html)

    def test_matched_sample_uses_only_shared_symbol_dates_and_legacy_falls_back(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, params).id) for params in (
                {"factor": "momentum_20d", "groups": 2},
                {"factor": "reversal_5d", "groups": 2, "symbols": ["DEMO01", "DEMO02"]},
            )]
            result = compare_runs(runs)
            matched = result["matched_sample"]
            self.assertTrue(matched["available"])
            self.assertGreater(matched["observation_count"], 0)
            self.assertLess(matched["observation_count"], min(item["metrics"]["coverage"] for item in result["items"]))
            self.assertEqual(
                [item["retention_ratio"] for item in matched["items"]],
                [matched["observation_count"] / item["metrics"]["coverage"] for item in result["items"]],
            )
            self.assertEqual(matched["label_mismatch_count"], 0)
            self.assertEqual(len(matched["items"]), 2)
            self.assertNotEqual(matched["items"][0]["ic_mean"], result["items"][0]["metrics"]["ic_mean"])

            runs[1].artifacts[:] = [item for item in runs[1].artifacts if item.artifact_type != "observations"]
            legacy = compare_runs(runs)
            self.assertFalse(legacy["matched_sample"]["available"])
            self.assertIsNotNone(legacy["items"][0]["common_date_ic"]["ic_mean"])

    def test_matched_sample_warns_when_forward_return_labels_differ(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, {
                "factor": factor, "groups": 5, "start_date": "2025-02-03",
            }).id) for factor in ("momentum_20d", "reversal_5d")]
            artifact = next(item for item in runs[1].artifacts if item.artifact_type == "observations")
            observations = list(read_observation_artifact(artifact).values())
            observations[0] = replace(observations[0], forward_return=observations[0].forward_return + .01)
            replacement = create_observation_artifact(runs[1].id, observations,
                                                       Path(artifact.storage_uri).parents[2])
            artifact.checksum = replacement.checksum
            result = compare_runs(runs)
            self.assertEqual(result["matched_sample"]["label_mismatch_count"], 1)
            self.assertTrue(any("收益标签存在差异" in warning for warning in result["warnings"]))

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

            runs[1].artifacts[:] = [item for item in runs[1].artifacts if item.artifact_type != "observations"]
            legacy = compare_runs(runs)
            self.assertFalse(legacy["comparable"])
            self.assertFalse(legacy["matched_sample"]["available"])
            self.assertEqual(legacy["common_ic_date_count"], result["common_ic_date_count"])
            self.assertTrue(any("缺少逐股观测产物" in warning for warning in legacy["warnings"]))

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
            common_days = {point["date"] for point in artifact.content["ic_series"] if point["ic"] is not None}
            expected = sum(point["ic"] for point in next(a for a in runs[0].artifacts if a.artifact_type == "metrics").content["ic_series"] if point["date"] in common_days) / len(common_days)
            self.assertAlmostEqual(result["items"][0]["common_date_ic"]["ic_mean"], expected)
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
            self.assertIsNone(result["matched_sample"]["items"][1]["retention_ratio"])
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
