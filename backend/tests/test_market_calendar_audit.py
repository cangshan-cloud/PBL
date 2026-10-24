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
from app.models import DatasetVersion
from app.services.datasets import import_csv
from app.services.market_calendar_audit import audit_existing_dataset_calendars


CSV = b"trade_date,symbol,close\n2025-01-28,000001.SZ,10\n2025-01-28,600000.SH,11\n2025-02-05,000001.SZ,12\n"


class MarketCalendarAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "runtime"
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_rechecks_verified_legacy_csv_without_updating_record_or_file(self):
        with Session(self.engine) as session:
            dataset = import_csv(session, content=CSV, source_filename="daily.csv",
                                 dataset_key="old_daily", name="旧版", data_root=self.root)
            dataset.status = "published"
            dataset.quality_report = {"valid": True}
            session.commit()
            before = Path(dataset.storage_uri).read_bytes()
            result = audit_existing_dataset_calendars(session)
            session.refresh(dataset)
            self.assertEqual(dataset.quality_report, {"valid": True})
            self.assertEqual(Path(dataset.storage_uri).read_bytes(), before)
            self.assertEqual(result["audited_count"], 1)
            self.assertEqual(result["error_count"], 0)
            item = result["items"][0]
            self.assertEqual(item["announced_weekday_closure_dates"], ["2025-01-28"])
            self.assertEqual(item["announced_weekday_closure_row_count"], 2)
            self.assertEqual(item["calendar_uncovered_years"], [])

    def test_skips_historical_bundle_and_reports_checksum_mismatch(self):
        with Session(self.engine) as session:
            dataset = import_csv(session, content=CSV, source_filename="daily.csv",
                                 dataset_key="audit_daily", name="普通", data_root=self.root)
            dataset.status = "published"
            historical = DatasetVersion(dataset_key="hs300_2024", name="历史", version="bundle",
                                        checksum="a" * 64, storage_uri="/not/read/manifest.json",
                                        quality_report={"dataset_kind": "hs300_bundle_v1"}, status="published")
            session.add(historical)
            session.commit()
            Path(dataset.storage_uri).write_bytes(CSV.replace(b",10\n", b",13\n"))
            result = audit_existing_dataset_calendars(session)
            self.assertEqual(result["error_count"], 1)
            self.assertEqual(result["skipped_count"], 1)
            self.assertEqual({item["status"] for item in result["items"]}, {"error", "skipped_historical_bundle"})

    def test_cli_reads_isolated_db_and_rejects_missing_db_without_creating_it(self):
        db_path = Path(self.temp_dir.name) / "audit.db"
        file_engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(file_engine)
        try:
            with Session(file_engine) as session:
                dataset = import_csv(session, content=CSV, source_filename="daily.csv",
                                     dataset_key="cli_daily", name="命令", data_root=self.root)
                dataset.status = "published"
                session.commit()
                dataset_id = dataset.id
            command = [sys.executable, str(Path(__file__).resolve().parents[2] / "tools" / "audit_market_calendar.py")]
            env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"}
            completed = subprocess.run(command + ["--dataset-id", dataset_id], env=env,
                                       capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["items"][0]["announced_weekday_closure_row_count"], 2)
            unknown = subprocess.run(command + ["--dataset-id", "00000000-0000-0000-0000-000000000000"],
                                     env=env, capture_output=True, text=True, check=False)
            self.assertEqual(unknown.returncode, 2, unknown.stderr)
            with Session(file_engine) as session:
                stored = session.get(DatasetVersion, dataset_id)
                Path(stored.storage_uri).write_bytes(CSV.replace(b",10\n", b",13\n"))
            changed = subprocess.run(command + ["--dataset-id", dataset_id], env=env,
                                     capture_output=True, text=True, check=False)
            self.assertEqual(changed.returncode, 1, changed.stderr)
            self.assertEqual(json.loads(changed.stdout)["error_count"], 1)
            absent = Path(self.temp_dir.name) / "absent.db"
            missing = subprocess.run(command, env={**env, "DATABASE_URL": f"sqlite:///{absent}"},
                                     capture_output=True, text=True, check=False)
            self.assertEqual(missing.returncode, 2)
            self.assertFalse(absent.exists())
        finally:
            file_engine.dispose()


if __name__ == "__main__":
    unittest.main()
