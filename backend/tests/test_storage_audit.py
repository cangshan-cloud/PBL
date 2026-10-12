import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.services.datasets import import_csv
from app.services.storage_audit import audit_dataset_storage


CSV = b"trade_date,symbol,close\n2025-01-02,000001.SZ,10\n"


class StorageAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "runtime"
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_reports_changed_missing_and_unreferenced_files_without_modifying_them(self):
        with Session(self.engine) as session:
            first = import_csv(session, content=CSV, source_filename="a.csv", dataset_key="first_data", name="一", data_root=self.root)
            second = import_csv(session, content=CSV, source_filename="b.csv", dataset_key="second_data", name="二", data_root=self.root)
            self.assertEqual(audit_dataset_storage(session, self.root)["issue_count"], 0)

            first_path = Path(first.storage_uri)
            second_path = Path(second.storage_uri)
            first_path.write_bytes(CSV.replace(b",10\n", b",11\n"))
            second_path.unlink()
            orphan = self.root / "orphan_data" / "version" / "extra.csv"
            orphan.parent.mkdir(parents=True)
            orphan.write_bytes(CSV)
            result = audit_dataset_storage(session, self.root)
            self.assertEqual(result["dataset_count"], 2)
            self.assertEqual(result["issue_count"], 3)
            self.assertEqual({issue["kind"] for issue in result["issues"]}, {
                "checksum_mismatch", "missing", "unreferenced_file",
            })
            self.assertEqual(first_path.read_bytes(), CSV.replace(b",10\n", b",11\n"))
            self.assertFalse(second_path.exists())
            self.assertEqual(orphan.read_bytes(), CSV)

    def test_missing_runtime_root_is_not_an_error_for_external_dataset(self):
        with Session(self.engine) as session:
            external = import_csv(
                session, content=CSV, source_filename="bundled.csv",
                dataset_key="external_data", name="外部", data_root=Path(self.temp_dir.name) / "bundled",
            )
            result = audit_dataset_storage(session, self.root)
            self.assertEqual(result, {"dataset_count": 1, "issue_count": 0, "issues": []})
            self.assertTrue(Path(external.storage_uri).is_file())

    def test_cli_exit_codes_with_isolated_database(self):
        db_path = Path(self.temp_dir.name) / "audit.db"
        file_engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(file_engine)
        try:
            with Session(file_engine) as session:
                dataset = import_csv(
                    session, content=CSV, source_filename="daily.csv",
                    dataset_key="cli_data", name="命令测试", data_root=self.root,
                )
                data_path = Path(dataset.storage_uri)
            env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}", "DATA_ROOT": str(self.root)}
            command = [sys.executable, str(Path(__file__).resolve().parents[2] / "tools" / "audit_dataset_storage.py")]
            clean = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
            self.assertEqual(clean.returncode, 0, clean.stderr)
            self.assertEqual(json.loads(clean.stdout)["issue_count"], 0)

            data_path.unlink()
            broken = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
            self.assertEqual(broken.returncode, 1, broken.stderr)
            self.assertEqual(json.loads(broken.stdout)["issues"][0]["kind"], "missing")

            nonexistent = Path(self.temp_dir.name) / "does_not_exist.db"
            absent = subprocess.run(
                command, env={**env, "DATABASE_URL": f"sqlite:///{nonexistent}"},
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(absent.returncode, 2)
            self.assertFalse(nonexistent.exists())
        finally:
            file_engine.dispose()


if __name__ == "__main__":
    unittest.main()
