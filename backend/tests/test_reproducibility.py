import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.main import download_reproducibility_bundle
from app.models import UserRole
from app.services.runs import create_research_run, execute_research_run
from tools.verify_reproducibility_export import verify_export


class ReproducibilityTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_success_bundle_contains_fixed_inputs_results_and_checksums(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d", "groups": 5}, created_by_id="owner")
            run = execute_research_run(session, run.id)
            response = download_reproducibility_bundle(run.id, SimpleNamespace(role=UserRole.RESEARCHER, id="owner"), session)
            bundle = json.loads(response.body)

            self.assertEqual(response.media_type, "application/json; charset=utf-8")
            self.assertIn("attachment", response.headers["content-disposition"])
            self.assertEqual(bundle["schema_version"], 1)
            self.assertEqual(bundle["task"]["id"], run.id)
            self.assertEqual(bundle["task"]["code_version"], run.experiment.code_version)
            self.assertEqual(bundle["dataset"]["checksum_sha256"], run.experiment.dataset_version.checksum)
            self.assertEqual(bundle["factor"]["formula"], run.experiment.factor_version.formula)
            self.assertEqual(bundle["task"]["parameters"]["groups"], 5)
            self.assertEqual(bundle["result"]["coverage"], run.artifacts[0].content["coverage"])
            canonical = json.dumps(bundle["result"], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
            self.assertEqual(bundle["result_sha256"], hashlib.sha256(canonical.encode("utf-8")).hexdigest())
            self.assertEqual(len(bundle["report_sha256"]), 64)
            self.assertTrue(any(item["event"] == "completed" for item in bundle["logs"]))
            self.assertNotIn("storage_uri", response.body.decode("utf-8"))

            with tempfile.TemporaryDirectory() as directory:
                bundle_path = Path(directory) / "reproducibility.json"
                bundle_path.write_bytes(response.body)
                self.assertEqual(verify_export(bundle_path), {"result_verified": True})
                damaged = dict(bundle)
                damaged["result"] = {**bundle["result"], "coverage": -1}
                bundle_path.write_text(json.dumps(damaged), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "result checksum mismatch"):
                    verify_export(bundle_path)

    def test_offline_verifier_checks_optional_report_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle_path = Path(directory) / "reproducibility.json"
            report_path = Path(directory) / "report.html"
            result = {"ic_mean": 0.1}
            report_path.write_bytes(b"<html>research report</html>")
            canonical = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            bundle_path.write_text(json.dumps({
                "schema_version": 1, "result": result,
                "result_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
            }), encoding="utf-8")
            self.assertEqual(verify_export(bundle_path, report_path),
                             {"result_verified": True, "report_verified": True})
            report_path.write_bytes(b"<html>changed</html>")
            with self.assertRaisesRegex(ValueError, "report checksum mismatch"):
                verify_export(bundle_path, report_path)

    def test_pending_bundle_has_no_result_and_respects_owner(self):
        with Session(self.engine, expire_on_commit=False) as session:
            run = create_research_run(session, {"factor": "momentum_20d"}, created_by_id="owner")
            with self.assertRaises(HTTPException) as raised:
                download_reproducibility_bundle(run.id, SimpleNamespace(role=UserRole.RESEARCHER, id="other"), session)
            self.assertEqual(raised.exception.status_code, 403)

            response = download_reproducibility_bundle(run.id, SimpleNamespace(role=UserRole.VIEWER, id="viewer"), session)
            bundle = json.loads(response.body)
            self.assertIsNone(bundle["result"])
            self.assertIsNone(bundle["result_sha256"])
            self.assertIsNone(bundle["report_sha256"])


if __name__ == "__main__":
    unittest.main()
