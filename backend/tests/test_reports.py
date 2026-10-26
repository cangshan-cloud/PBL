import sys
import tempfile
import unittest
import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db import Base
from app.main import download_report, download_report_delivery_copy, preview_report
from app.models import Artifact, UserRole
from app.services.reports import _align_dated_chart_series, _daily_series_detail, _svg_chart, build_report_html, get_report, list_reports, read_verified_report, report_delivery_copy
from app.services.runs import create_research_run, execute_research_run


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_successful_run_creates_report_artifact(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            completed = execute_research_run(session, run.id)
            pair = get_report(session, completed.id)
            self.assertIsNotNone(pair)
            _, artifact = pair
            content = Path(artifact.storage_uri).read_text(encoding="utf-8")
            self.assertIn("因子研究报告", content)
            self.assertIn("不构成投资建议", content)
            self.assertIn("若使用当前成分股回溯历史", content)
            self.assertIn("多空累计收益", content)
            self.assertIn("截面Z-score标准化", content)
            self.assertIn("每日 IC 与 Rank IC", content)
            self.assertIn("IC 分布（固定 0.2 宽度分箱）", content)
            self.assertIn("逐日样本诊断", content)
            self.assertIn("<th>候选</th><th>有效</th><th>覆盖率</th>", content)
            self.assertIn("各组净值（初值 1）", content)
            self.assertIn("多空组合净值（初值 1）", content)
            self.assertEqual(content.count("<svg "), 3)
            self.assertIn("<polyline ", content)
            self.assertNotIn("<script", content)
            self.assertIn(completed.id, content)
            self.assertEqual(len(artifact.checksum), 64)
            self.assertEqual(list_reports(session)[0]["run_id"], completed.id)
            self.assertEqual(list_reports(session)[0]["dataset_version_id"], completed.experiment.dataset_version.id)
            self.assertEqual(list_reports(session)[0]["dataset_checksum_sha256"], completed.experiment.dataset_version.checksum)

    def test_new_demo_report_discloses_synthetic_calendar(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            dataset = run.experiment.dataset_version
            dataset.dataset_key = "demo_daily"
            dataset.quality_report = {"source": "bundled_demo"}
            rendered = build_report_html(run, {"coverage": 0, "group_returns": []})
            self.assertIn("数据质量与来源限制", rendered)
            self.assertIn("不能作为真实市场证据", rendered)
            dataset.quality_report = {"source": "imported_csv"}
            dataset.checksum = "other"
            self.assertNotIn("数据质量与来源限制", build_report_html(run, {"coverage": 0, "group_returns": []}))

    def test_new_report_discloses_calendar_quality_findings(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            dataset = run.experiment.dataset_version
            dataset.dataset_key = "imported_2026"
            dataset.quality_report = {
                "weekend_row_count": 2,
                "announced_weekday_closure_row_count": 1,
                "announced_weekday_closure_dates": ["2026-10-07"],
                "announced_closure_calendar_version": "sse-szse-announced-closures-2024-2026-v2",
                "calendar_uncovered_years": [2027],
            }
            rendered = build_report_html(run, {"coverage": 0, "group_returns": []})
            self.assertIn("2 行周末日期行情", rendered)
            self.assertIn("2026-10-07", rendered)
            self.assertIn("2027 年", rendered)
            self.assertIn("sse-szse-announced-closures-2024-2026-v2", rendered)

    def test_imported_csv_report_discloses_unverified_provenance_even_without_known_calendar_issue(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "pe", "groups": 2})
            dataset = run.experiment.dataset_version
            dataset.dataset_key = "private_daily"
            dataset.quality_report = {"valid": True, "columns": ["trade_date", "symbol", "close", "pe"]}
            rendered = build_report_html(run, {"coverage": 0, "group_returns": []})
            self.assertIn("CSV 导入数据", rendered)
            self.assertIn("不认证数据真实性、使用授权或完整交易日历", rendered)
            delivered = report_delivery_copy(rendered.encode("utf-8"), run, "archived-sha").decode("utf-8")
            self.assertEqual(delivered.count("不认证数据真实性、使用授权或完整交易日历"), 2)
            dataset.quality_report = {"dataset_kind": "hs300_bundle_v1", "columns": ["close"]}
            self.assertNotIn("CSV 导入数据", build_report_html(run, {"coverage": 0, "group_returns": []}))

    def test_adjusted_report_discloses_dataset_wide_missing_multiplier(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "pe", "groups": 2})
            run.experiment.dataset_version.quality_report = {"missing_counts": {"adj_factor": 1}}
            run.experiment.parameters = {"price_basis": "factor_adjusted", "symbols": ["000001.SZ", "000003.SZ"]}
            rendered = build_report_html(run, {"coverage": 0, "group_returns": []})
            self.assertIn("全量质量报告有 1 行缺失 adj_factor", rendered)
            self.assertIn("不代表版本内其他证券可用于调整价研究", rendered)
            delivered = report_delivery_copy(rendered.encode("utf-8"), run, "archived-sha").decode("utf-8")
            self.assertEqual(delivered.count("全量质量报告有 1 行缺失 adj_factor"), 2)
            run.experiment.parameters = {"price_basis": "source_close"}
            self.assertNotIn("全量质量报告有 1 行缺失 adj_factor",
                             build_report_html(run, {"coverage": 0, "group_returns": []}))

    def test_adapter_adjustment_status_is_disclosed_without_reapplying_factor(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            dataset = run.experiment.dataset_version
            dataset.dataset_key = "imported_baostock"
            dataset.quality_report = {"adapter_report": {"source_adjustment_flags": ["2"]}}
            rendered = build_report_html(run, {"coverage": 0, "group_returns": []})
            self.assertIn("adjustflag=2（来源声明的前复权状态）", rendered)
            self.assertIn("不是数值复权因子", rendered)
            self.assertIn("价格口径：导入的 close", rendered)
            delivered = report_delivery_copy(rendered.encode("utf-8"), run, "archived-sha").decode("utf-8")
            self.assertEqual(delivered.count("adjustflag=2"), 2)
            for flag, label in (("1", "后复权"), ("3", "不复权")):
                dataset.quality_report = {"adapter_report": {"source_adjustment_flags": [flag]}}
                self.assertIn(f"adjustflag={flag}（来源声明的{label}状态）",
                              build_report_html(run, {"coverage": 0, "group_returns": []}))
            dataset.quality_report = {"adapter_report": {"source_adjustment_flags": []}}
            self.assertNotIn("adjustflag=", build_report_html(run, {"coverage": 0, "group_returns": []}))
            dataset.quality_report = {"adapter_report": {"source_adjustment_flags": [["2"]]}}
            self.assertNotIn("adjustflag=", build_report_html(run, {"coverage": 0, "group_returns": []}))

    def test_dynamic_text_is_html_escaped(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            run.experiment.name = "<script>alert(1)</script>"
            rendered = build_report_html(run, {"coverage": 0, "group_returns": []})
            self.assertNotIn("<script>alert(1)</script>", rendered)
            self.assertIn("&lt;script&gt;", rendered)

    def test_report_discloses_constant_factor_skip_count(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            rendered = build_report_html(run, {"coverage": 2, "group_returns": [],
                                               "group_skipped_constant_factor_days": 1,
                                               "group_skipped_insufficient_sample_days": 2})
            self.assertIn("全截面因子同值而跳过分组的日期：1 天", rendered)
            self.assertIn("有效证券数少于目标分组数而跳过的日期：2 天", rendered)
            self.assertIn("暂无可计算的分组收益；不以零收益填补。", rendered)

    def test_correlation_matrix_labels_are_html_escaped(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            run.experiment.parameters = {"components": [
                {"key": "<script>x</script>", "version": "1", "weight": 0.5},
                {"key": "safe", "version": "1", "weight": 0.5},
            ]}
            rendered = build_report_html(run, {"coverage": 2, "group_returns": [], "composite": {
                "common_coverage": 2,
                "correlation_matrix": [{"left": "<script>x</script>", "right": "safe", "correlation": None}],
            }})
            self.assertIn("&lt;script&gt;x&lt;/script&gt;", rendered)
            self.assertNotIn("<script>x</script>", rendered)
            self.assertIn("<td>—</td>", rendered)

    def test_report_preview_and_download_verify_checksum(self):
        path = Path(self.temp_dir.name) / "report.html"
        original = b"<html><body>verified report</body></html>"
        path.write_bytes(original)
        artifact = Artifact(
            artifact_type="report_html",
            name="report.html",
            storage_uri=str(path),
            checksum=hashlib.sha256(original).hexdigest(),
        )
        user = SimpleNamespace(role=UserRole.VIEWER)
        run = SimpleNamespace(experiment=SimpleNamespace(created_by_id="other"))
        with patch("app.main.get_report", return_value=(run, artifact)):
            self.assertEqual(read_verified_report(artifact), original)
            self.assertEqual(preview_report("run-12345678", user, None).body, original)
            download = download_report("run-12345678", user, None)
            self.assertEqual(download.body, original)
            self.assertIn("attachment", download.headers["content-disposition"])

            path.write_bytes(b"<html>changed</html>")
            for endpoint in (preview_report, download_report):
                with self.assertRaises(HTTPException) as raised:
                    endpoint("run-12345678", user, None)
                self.assertEqual(raised.exception.status_code, 409)

            path.unlink()
            with self.assertRaises(HTTPException) as raised:
                preview_report("run-12345678", user, None)
            self.assertEqual(raised.exception.status_code, 410)

    def test_report_without_checksum_is_rejected(self):
        path = Path(self.temp_dir.name) / "report.html"
        path.write_text("<html>old report</html>", encoding="utf-8")
        artifact = Artifact(artifact_type="report_html", name="report.html", storage_uri=str(path), checksum=None)
        with self.assertRaisesRegex(ValueError, "校验和不匹配"):
            read_verified_report(artifact)

    def test_delivery_copy_discloses_demo_and_preserves_archive(self):
        original = b"<html><body><main><h1>Original</h1></main></body></html>"
        dataset = SimpleNamespace(id="dataset-v1", dataset_key="demo_daily", version="0.2.0",
            checksum="c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e",
            quality_report={"source": "bundled_demo"})
        run = SimpleNamespace(experiment=SimpleNamespace(dataset_version=dataset, created_by_id="other"))
        path = Path(self.temp_dir.name) / "report.html"
        path.write_bytes(original)
        digest = hashlib.sha256(original).hexdigest()
        artifact = Artifact(artifact_type="report_html", name="report.html", storage_uri=str(path), checksum=digest)
        user = SimpleNamespace(role=UserRole.VIEWER)
        with patch("app.main.get_report", return_value=(run, artifact)):
            delivered = download_report_delivery_copy("run-12345678", user, None)
            self.assertIn("合成演示数据", delivered.body.decode())
            self.assertIn(digest, delivered.body.decode())
            self.assertEqual(delivered.headers["x-archived-report-sha256"], digest)
            self.assertEqual(download_report("run-12345678", user, None).body, original)
            self.assertEqual(path.read_bytes(), original)

    def test_delivery_endpoint_rejects_missing_tampered_and_invalid_archive(self):
        original = b"<html><main>verified report</main></html>"
        path = Path(self.temp_dir.name) / "report.html"
        path.write_bytes(original)
        digest = hashlib.sha256(original).hexdigest()
        artifact = Artifact(artifact_type="report_html", name="report.html", storage_uri=str(path), checksum=digest)
        dataset = SimpleNamespace(id="dataset-v1", dataset_key="imported", version="v1", checksum="data-sha", quality_report={})
        run = SimpleNamespace(experiment=SimpleNamespace(dataset_version=dataset, created_by_id="other"))
        user = SimpleNamespace(role=UserRole.VIEWER)
        with patch("app.main.get_report", return_value=(run, artifact)):
            path.write_bytes(b"<html><main>tampered</main></html>")
            with self.assertRaises(HTTPException) as tampered:
                download_report_delivery_copy("run-12345678", user, None)
            self.assertEqual(tampered.exception.status_code, 409)

            path.unlink()
            with self.assertRaises(HTTPException) as missing:
                download_report_delivery_copy("run-12345678", user, None)
            self.assertEqual(missing.exception.status_code, 410)

            malformed = b"<html>verified but missing main</html>"
            path.write_bytes(malformed)
            artifact.checksum = hashlib.sha256(malformed).hexdigest()
            with self.assertRaises(HTTPException) as invalid_structure:
                download_report_delivery_copy("run-12345678", user, None)
            self.assertEqual(invalid_structure.exception.status_code, 409)

            invalid_encoding = b"<html><main>\xff</main></html>"
            path.write_bytes(invalid_encoding)
            artifact.checksum = hashlib.sha256(invalid_encoding).hexdigest()
            with self.assertRaises(HTTPException) as invalid_text:
                download_report_delivery_copy("run-12345678", user, None)
            self.assertEqual(invalid_text.exception.status_code, 409)

    def test_delivery_copy_escapes_provenance_and_handles_invalid_html(self):
        dataset = SimpleNamespace(id="<script>", dataset_key="imported", version="v1", checksum="sha<&", quality_report={"weekend_row_count": 2})
        run = SimpleNamespace(experiment=SimpleNamespace(dataset_version=dataset))
        delivered = report_delivery_copy(b"<html><main>report</main></html>", run, "original")
        self.assertIn(b"&lt;script&gt;", delivered)
        self.assertIn(b"sha&lt;&amp;", delivered)
        self.assertIn("周末日期行情", delivered.decode())
        self.assertNotIn(b"<script>", delivered)
        with self.assertRaisesRegex(ValueError, "页面结构"):
            report_delivery_copy(b"<html>missing main</html>", run, "original")

    def test_delivery_copy_carries_calendar_findings_and_escapes_dates(self):
        dataset = SimpleNamespace(id="dataset-v1", dataset_key="imported", version="v1", checksum="sha",
            quality_report={"announced_weekday_closure_row_count": 1,
                            "announced_weekday_closure_dates": ["2026-10-07<script>"],
                            "announced_closure_calendar_version": "calendar-v2",
                            "calendar_uncovered_years": [2027]})
        run = SimpleNamespace(experiment=SimpleNamespace(dataset_version=dataset))
        delivered = report_delivery_copy(b"<html><main>report</main></html>", run, "original").decode()
        self.assertIn("2026-10-07&lt;script&gt;", delivered)
        self.assertIn("规则版本：calendar-v2", delivered)
        self.assertIn("未覆盖 2027 年", delivered)
        self.assertNotIn("<script>", delivered)

    def test_chart_gaps_do_not_become_zero_and_labels_are_escaped(self):
        chart = _svg_chart(
            "IC <test>", ["2025-01-02", "2025-01-03", "2025-01-06"],
            [("factor <A>", [0.2, None, 0.4], "#176548")], baseline=0,
        )
        self.assertIn("IC &lt;test&gt;", chart)
        self.assertIn("factor &lt;A&gt;", chart)
        self.assertNotIn("<polyline", chart)
        self.assertEqual(chart.count("<circle "), 2)
        self.assertNotIn("nan", chart.lower())

    def test_group_nav_report_aligns_dates_and_breaks_missing_day(self):
        dates, series = _align_dated_chart_series([
            ("Q1", [{"date": "2025-01-02", "nav": 1.01},
                    {"date": "2025-01-06", "nav": 1.03}], "#277a5b"),
            ("Q2", [{"date": "2025-01-03", "nav": 0.99},
                    {"date": "2025-01-06", "nav": 1.02}], "#65a563"),
        ], "nav")
        self.assertEqual(dates, ["2025-01-02", "2025-01-03", "2025-01-06"])
        self.assertEqual(series[0][1], [1.01, None, 1.03])
        self.assertEqual(series[1][1], [None, 0.99, 1.02])
        chart = _svg_chart("各组净值", dates, series, baseline=1)
        self.assertEqual(chart.count("<circle "), 2)
        self.assertEqual(chart.count("<polyline "), 1)
        self.assertIn("2025-01-02", chart)
        self.assertIn("2025-01-06", chart)
        self.assertIn("非自然日间隔", chart)

        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "pe", "groups": 2})
            rendered = build_report_html(run, {"coverage": 0, "group_returns": [], "group_nav": [
                {"group": 1, "points": [{"date": "2025-01-02", "nav": 1.01},
                                         {"date": "2025-01-06", "nav": 1.03}]},
                {"group": 2, "points": [{"date": "2025-01-03", "nav": 0.99},
                                         {"date": "2025-01-06", "nav": 1.02}]},
            ]})
            group_chart = rendered.split("<figcaption>各组净值（初值 1）</figcaption>", 1)[1].split("</figure>", 1)[0]
            self.assertEqual(group_chart.count("<circle "), 2)
            self.assertEqual(group_chart.count("<polyline "), 1)

    def test_report_daily_series_table_joins_dates_without_filling_values(self):
        result = {
            "ic_series": [{"date": "2025-01-02", "ic": 0.123456, "rank_ic": None},
                          {"date": "2025-01-03", "ic": None, "rank_ic": -0.2}],
            "long_short_series": [{"date": "2025-01-03", "nav": 1.02, "net_nav": 1.01}],
            "group_nav": [{"group": 1, "points": [{"date": "2025-01-02", "nav": 1.03}]},
                          {"group": 2, "points": [{"date": "2025-01-06", "nav": 0.98}]}],
        }
        detail = _daily_series_detail(result)
        self.assertIn("3 个结果日期", detail)
        self.assertIn("<th>Q1 净值</th><th>Q2 净值</th>", detail)
        self.assertIn("<tr><td>2025-01-02</td><td>0.1235</td><td>—</td><td>—</td><td>—</td><td>1.0300</td><td>—</td></tr>", detail)
        self.assertIn("<tr><td>2025-01-03</td><td>—</td><td>-0.2000</td><td>1.0200</td><td>1.0100</td><td>—</td><td>—</td></tr>", detail)
        self.assertIn("<tr><td>2025-01-06</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>0.9800</td></tr>", detail)
        self.assertEqual(_daily_series_detail({}), "")
        hostile_date = _daily_series_detail({"ic_series": [
            {"date": "<script>x</script>", "ic": 0.1, "rank_ic": None},
        ]})
        self.assertIn("&lt;script&gt;x&lt;/script&gt;", hostile_date)
        self.assertNotIn("<script>", hostile_date)

        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "pe", "groups": 2})
            rendered = build_report_html(run, {"coverage": 0, "group_returns": [], **result})
            self.assertIn('<details class="series-detail">', rendered)
            self.assertIn("<tr><td>2025-01-03</td><td>—</td><td>-0.2000</td>", rendered)


if __name__ == "__main__":
    unittest.main()
