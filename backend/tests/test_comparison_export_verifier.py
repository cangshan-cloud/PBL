import html
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.services.comparisons import compare_runs, comparison_csv, comparison_html
from app.services.runs import create_research_run, execute_research_run
from tools.verify_comparison_exports import verify_exports


class ComparisonExportVerifierTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_offline_verifier_checks_real_export_shapes_and_detects_tampering(self):
        with Session(self.engine, expire_on_commit=False) as session:
            runs = [execute_research_run(session, create_research_run(session, {
                "factor": factor, "groups": 5,
            }).id) for factor in ("momentum_20d", "reversal_5d")]
            result = compare_runs(runs)
            snapshot = {**jsonable_encoder(result), "export_format": "factorlab-comparison", "export_schema_version": 1}
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                json_path, csv_path, html_path = (root / name for name in ("comparison.json", "comparison.csv", "comparison.html"))
                json_path.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
                csv_path.write_bytes(comparison_csv(result))
                html_path.write_text(comparison_html(result), encoding="utf-8")

                summary = verify_exports(json_path, csv_path, html_path)
                self.assertEqual(summary["run_count"], 2)
                self.assertEqual(summary["baseline_run_id"], runs[0].id)
                self.assertTrue(summary["csv_verified"])
                self.assertTrue(summary["html_verified"])

                self.assertEqual(snapshot["items"][0]["dataset_checksum_sha256"],
                                 runs[0].experiment.dataset_version.checksum)
                self.assertEqual(snapshot["items"][0]["dataset_source_kind"], "bundled_demo")

                original_html = html_path.read_text(encoding="utf-8")
                checksum = snapshot["items"][0]["dataset_checksum_sha256"]
                html_path.write_text(original_html.replace(
                    f"<code>{checksum}</code>", f"<code>{'0' * 64}</code>", 1), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "HTML provenance row 1 differs"):
                    verify_exports(json_path, csv_path, html_path)
                html_path.write_text(original_html, encoding="utf-8")

                csv_path.write_text(csv_path.read_text(encoding="utf-8-sig").replace(
                    ",bundled_demo,", ",imported_csv,", 1), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "CSV differs from JSON dataset_source_kind"):
                    verify_exports(json_path, csv_path, html_path)
                csv_path.write_bytes(comparison_csv(result))

                first_id, second_id = (item["run_id"] for item in snapshot["items"])
                swapped_html = original_html.replace(first_id, "TEMP-RUN-ID", 1).replace(
                    second_id, first_id, 1).replace("TEMP-RUN-ID", second_id, 1)
                html_path.write_text(swapped_html, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "HTML provenance row 1 differs"):
                    verify_exports(json_path, csv_path, html_path)
                html_path.write_text(original_html, encoding="utf-8")

                original_ic = [f"{item['metrics']['ic_mean']:.4f}" for item in snapshot["items"]]
                swapped_original_ic = original_html.replace(
                    f"<b>{original_ic[0]}</b>", "<b>TEMP-IC</b>", 1).replace(
                    f"<b>{original_ic[1]}</b>", f"<b>{original_ic[0]}</b>", 1).replace(
                    "<b>TEMP-IC</b>", f"<b>{original_ic[1]}</b>", 1)
                self.assertNotEqual(swapped_original_ic, original_html)
                html_path.write_text(swapped_original_ic, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "HTML original IC column 1 differs"):
                    verify_exports(json_path, csv_path, html_path)
                html_path.write_text(original_html, encoding="utf-8")

                common_ic = [f"{item['common_date_ic']['ic_mean']:.4f}" for item in snapshot["items"]]
                original_row = f"<tr><th>IC均值</th><td>{common_ic[0]}</td><td>{common_ic[1]}</td></tr>"
                swapped_row = f"<tr><th>IC均值</th><td>{common_ic[1]}</td><td>{common_ic[0]}</td></tr>"
                self.assertIn(original_row, original_html)
                html_path.write_text(original_html.replace(original_row, swapped_row, 1), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "HTML common-date IC column 1 differs"):
                    verify_exports(json_path, csv_path, html_path)
                html_path.write_text(original_html, encoding="utf-8")

                warning = result["warnings"][0]
                html_path.write_text(html_path.read_text(encoding="utf-8").replace(
                    html.escape(warning), "removed-warning", 1), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "HTML omits a JSON warning"):
                    verify_exports(json_path, csv_path, html_path)
                html_path.write_text(comparison_html(result), encoding="utf-8")

                csv_path.write_text(csv_path.read_text(encoding="utf-8-sig").replace(
                    snapshot["items"][0]["dataset_version_id"], "wrong-dataset", 1), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "CSV differs from JSON dataset_version_id"):
                    verify_exports(json_path, csv_path, html_path)

                damaged_items = [{**snapshot["items"][0], "dataset_checksum_sha256": "invalid"}, *snapshot["items"][1:]]
                json_path.write_text(json.dumps({**snapshot, "items": damaged_items}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "invalid dataset checksum"):
                    verify_exports(json_path)

                json_path.write_text(json.dumps({**snapshot, "baseline_run_id": runs[1].id}), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "baseline differs"):
                    verify_exports(json_path)


if __name__ == "__main__":
    unittest.main()
