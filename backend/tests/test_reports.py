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
from app.main import download_report, preview_report
from app.models import Artifact, UserRole
from app.services.reports import _svg_chart, build_report_html, get_report, list_reports, read_verified_report
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
            self.assertIn("多空累计收益", content)
            self.assertIn("截面Z-score标准化", content)
            self.assertIn("每日 IC 与 Rank IC", content)
            self.assertIn("IC 分布（固定 0.2 宽度分箱）", content)
            self.assertIn("各组净值（初值 1）", content)
            self.assertIn("多空组合净值（初值 1）", content)
            self.assertEqual(content.count("<svg "), 3)
            self.assertIn("<polyline ", content)
            self.assertNotIn("<script", content)
            self.assertIn(completed.id, content)
            self.assertEqual(len(artifact.checksum), 64)
            self.assertEqual(list_reports(session)[0]["run_id"], completed.id)

    def test_dynamic_text_is_html_escaped(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "lookback": 20, "groups": 5})
            run.experiment.name = "<script>alert(1)</script>"
            rendered = build_report_html(run, {"coverage": 0, "group_returns": []})
            self.assertNotIn("<script>alert(1)</script>", rendered)
            self.assertIn("&lt;script&gt;", rendered)

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


if __name__ == "__main__":
    unittest.main()
