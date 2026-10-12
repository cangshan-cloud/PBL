import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.services.conclusions import build_run_conclusion
from app.services.runs import create_research_run, execute_research_run


class ConclusionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
