import sys
import tempfile
import unittest
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base
from app.domain.historical_research import HistoricalBar
from app.models import DatasetVersion, RunStatus
from app.services.runs import create_historical_run, execute_research_run


class HistoricalTaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.temp.cleanup()

    def test_dedicated_task_produces_metrics_report_and_audit(self):
        days = [date(2023, 12, 1) + timedelta(days=index) for index in range(29)]
        symbols = [f"sh.{index:06d}" for index in range(10)]
        members = {day: set(symbols) for day in days[21:-1]}
        bars = {
            symbol: {day: HistoricalBar(100 + index * (1 + rank / 10), 1 + rank / 10, 100, "1", "0")
                     for index, day in enumerate(days)}
            for rank, symbol in enumerate(symbols)
        }
        with Session(self.engine, expire_on_commit=False) as session:
            dataset = DatasetVersion(
                dataset_key="hs300_2024", name="test bundle", version="test",
                checksum="0" * 64, storage_uri="/unused/manifest.json", source_filename="manifest.json",
                quality_report={"dataset_kind": "hs300_bundle_v1", "bundle_id": "test"}, status="published",
            )
            session.add(dataset)
            session.commit()
            run = create_historical_run(session, {"dataset_version_id": dataset.id})
            settings = replace(get_settings(), data_root=Path(self.temp.name))
            with patch("app.services.runs.load_historical_bundle", return_value=(days, members, bars)), \
                 patch("app.services.runs.get_settings", return_value=settings):
                completed = execute_research_run(session, run.id)
            self.assertEqual(completed.status, RunStatus.SUCCESS)
            metrics = next(item.content for item in completed.artifacts if item.artifact_type == "metrics")
            self.assertEqual(metrics["coverage"], 70)
            self.assertEqual(set(metrics["historical_audit"]),
                             {"momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d"})
            report = next(item for item in completed.artifacts if item.artifact_type == "report_html")
            self.assertIn("历史样本与排除审计", Path(report.storage_uri).read_text())

    def test_requires_published_historical_bundle(self):
        with Session(self.engine) as session:
            dataset = DatasetVersion(dataset_key="old_csv", name="csv", version="1", checksum="x",
                                     storage_uri="/unused.csv", quality_report={}, status="published")
            session.add(dataset)
            session.commit()
            with self.assertRaisesRegex(ValueError, "published CSI 300 bundle"):
                create_historical_run(session, {"dataset_version_id": dataset.id})


if __name__ == "__main__":
    unittest.main()
