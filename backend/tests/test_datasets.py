import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import DatasetVersion
from app.services.datasets import DatasetValidationError, import_csv, preview_dataset, publish_dataset_version, validate_csv


VALID_CSV = b"""trade_date,symbol,open,high,low,close,volume
2025-01-02,000001.SZ,10,11,9,10.5,1000
2025-01-03,000001.SZ,10.5,11.2,10,11,1200
2025-01-02,600000.SH,8,8.5,7.8,8.2,900
"""


class DatasetValidationTests(unittest.TestCase):
    def test_rejects_nonfinite_values_in_required_and_optional_fields(self):
        for value in ("nan", "inf", "-inf", "1e309"):
            for column in ("close", "pe"):
                with self.subTest(value=value, column=column):
                    content = f"trade_date,symbol,close,pe\n2025-01-02,A,{value if column == 'close' else '10'},{value if column == 'pe' else '8'}\n".encode()
                    with self.assertRaises(DatasetValidationError) as caught:
                        validate_csv(content)
                    self.assertIn("有限数值", caught.exception.report["errors"][0])

    def test_trade_date_requires_exact_calendar_format(self):
        for value in ("20250102", "2025-W01-4", "2025-02-30"):
            with self.subTest(value=value):
                content = f"trade_date,symbol,close\n{value},A,10\n".encode()
                with self.assertRaises(DatasetValidationError) as caught:
                    validate_csv(content)
                self.assertIn("YYYY-MM-DD", caught.exception.report["errors"][0])

    def test_rejects_finite_rows_whose_quality_mean_overflows(self):
        content = b"trade_date,symbol,close\n2025-01-02,A,1e308\n2025-01-02,B,1e308\n"
        with self.assertRaises(DatasetValidationError) as caught:
            validate_csv(content)
        self.assertIn("均值溢出", caught.exception.report["errors"][0])

    def test_rejects_duplicate_headers_and_misaligned_rows(self):
        for content in (
            b"trade_date,symbol,close,close\n2025-01-02,A,10,11\n",
            b"trade_date,symbol,close\n2025-01-02,A,10,extra\n",
            b"trade_date,symbol,close,pe\n2025-01-02,A,10\n",
        ):
            with self.subTest(content=content):
                with self.assertRaises(DatasetValidationError):
                    validate_csv(content)

    def test_rejects_nonpositive_adjustment_factor(self):
        with self.assertRaises(DatasetValidationError):
            validate_csv(b"trade_date,symbol,close,adj_factor\n2025-01-02,A,10,0\n")

    def test_valid_csv_summary(self):
        parsed = validate_csv(VALID_CSV)
        self.assertEqual(parsed.row_count, 3)
        self.assertEqual(parsed.symbol_count, 2)
        self.assertTrue(parsed.report["valid"])
        self.assertEqual(parsed.report["missing_counts"]["volume"], 0)
        self.assertEqual(parsed.report["completeness"]["close"], 1.0)
        self.assertEqual(parsed.report["numeric_summary"]["close"]["min"], 8.2)
        self.assertEqual(parsed.report["internal_calendar_gap_count"], 0)

    def test_reports_internal_symbol_gaps_without_rejecting_csv(self):
        content = b"""trade_date,symbol,close
2025-01-02,A,10
2025-01-04,A,12
2025-01-02,B,20
2025-01-03,B,21
2025-01-04,B,22
2025-01-04,C,30
"""
        parsed = validate_csv(content)
        self.assertTrue(parsed.report["valid"])
        self.assertEqual(parsed.report["inferred_market_date_count"], 3)
        self.assertEqual(parsed.report["internal_calendar_gap_count"], 1)
        self.assertEqual(parsed.report["symbols_with_internal_calendar_gaps"], 1)

    def test_optional_missing_values_are_reported(self):
        content = b"trade_date,symbol,close,pe\n2025-01-02,A,10,12\n2025-01-03,A,11,\n"
        parsed = validate_csv(content)
        self.assertEqual(parsed.report["missing_counts"]["pe"], 1)
        self.assertEqual(parsed.report["completeness"]["pe"], 0.5)
        self.assertEqual(parsed.report["numeric_summary"]["pe"]["count"], 1)

    def test_duplicate_symbol_date_is_rejected(self):
        content = b"trade_date,symbol,close\n2025-01-02,A,10\n2025-01-02,A,11\n"
        with self.assertRaises(DatasetValidationError) as caught:
            validate_csv(content)
        self.assertIn("重复证券日期", caught.exception.report["errors"][0])

    def test_invalid_price_relationship_is_rejected(self):
        content = b"trade_date,symbol,open,high,low,close\n2025-01-02,A,10,9,8,10\n"
        with self.assertRaises(DatasetValidationError) as caught:
            validate_csv(content)
        self.assertIn("high", caught.exception.report["errors"][0])


class DatasetPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.temp_dir.cleanup()

    def test_import_then_publish(self):
        with Session(self.engine, expire_on_commit=False) as session:
            dataset = import_csv(
                session,
                content=VALID_CSV,
                source_filename="../../unsafe.csv",
                dataset_key="course_demo",
                name="课程演示数据",
                data_root=Path(self.temp_dir.name),
            )
            self.assertEqual(dataset.status, "draft")
            self.assertEqual(dataset.source_filename, "unsafe.csv")
            self.assertEqual(dataset.row_count, 3)
            self.assertEqual(dataset.symbol_count, 2)
            self.assertTrue(Path(dataset.storage_uri).is_file())
            preview = preview_dataset(dataset, limit=2)
            self.assertEqual(preview["preview_count"], 2)
            self.assertEqual(preview["columns"][:3], ["trade_date", "symbol", "open"])
            self.assertTrue(preview["truncated"])
            published = publish_dataset_version(session, dataset)
            self.assertEqual(published.status, "published")
            self.assertIsNotNone(published.published_at)

    def test_preview_parses_the_verified_byte_snapshot(self):
        with Session(self.engine, expire_on_commit=False) as session:
            dataset = import_csv(
                session, content=VALID_CSV, source_filename="daily.csv",
                dataset_key="course_demo", name="课程演示数据", data_root=Path(self.temp_dir.name),
            )
            Path(dataset.storage_uri).write_bytes(VALID_CSV.replace(b"10.5,1000", b"99.0,1000"))
            with patch.object(Path, "read_bytes", return_value=VALID_CSV) as read_bytes:
                preview = preview_dataset(dataset, limit=1)
            read_bytes.assert_called_once_with()
            self.assertEqual(preview["rows"][0]["close"], "10.5")

    def test_publish_rejects_changed_or_missing_file_without_changing_draft(self):
        with Session(self.engine, expire_on_commit=False) as session:
            dataset = import_csv(
                session,
                content=VALID_CSV,
                source_filename="daily.csv",
                dataset_key="course_demo",
                name="课程演示数据",
                data_root=Path(self.temp_dir.name),
            )
            path = Path(dataset.storage_uri)
            path.write_bytes(VALID_CSV.replace(b"10.5,1000", b"10.6,1000"))
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                publish_dataset_version(session, dataset)
            self.assertEqual(dataset.status, "draft")
            self.assertIsNone(dataset.published_at)

            path.unlink()
            with self.assertRaises(FileNotFoundError):
                publish_dataset_version(session, dataset)
            self.assertEqual(dataset.status, "draft")
            self.assertIsNone(dataset.published_at)

            path.write_bytes(VALID_CSV)
            self.assertEqual(publish_dataset_version(session, dataset).status, "published")
            path.unlink()
            with self.assertRaises(FileNotFoundError):
                publish_dataset_version(session, dataset)

    def test_import_cleans_file_and_database_state_when_commit_fails(self):
        data_root = Path(self.temp_dir.name)
        existing = data_root / "course_demo" / "existing" / "keep.csv"
        existing.parent.mkdir(parents=True)
        existing.write_bytes(b"existing data")
        with Session(self.engine) as session:
            with patch.object(session, "commit", side_effect=RuntimeError("database unavailable")):
                with self.assertRaisesRegex(RuntimeError, "database unavailable"):
                    import_csv(
                        session,
                        content=VALID_CSV,
                        source_filename="daily.csv",
                        dataset_key="course_demo",
                        name="课程演示数据",
                        data_root=data_root,
                    )
            self.assertEqual(list(session.scalars(select(DatasetVersion))), [])
        self.assertEqual(list(data_root.rglob("*.csv")), [existing])
        self.assertEqual(existing.read_bytes(), b"existing data")
        self.assertEqual(list((data_root / "course_demo").iterdir()), [existing.parent])

    def test_import_cleans_partial_file_when_disk_write_fails(self):
        data_root = Path(self.temp_dir.name)
        original_write = Path.write_bytes

        def partial_write(path: Path, content: bytes) -> int:
            original_write(path, content[:10])
            raise OSError("disk full")

        with Session(self.engine) as session:
            with patch.object(Path, "write_bytes", partial_write):
                with self.assertRaisesRegex(OSError, "disk full"):
                    import_csv(
                        session,
                        content=VALID_CSV,
                        source_filename="daily.csv",
                        dataset_key="course_demo",
                        name="课程演示数据",
                        data_root=data_root,
                    )
            self.assertEqual(list(session.scalars(select(DatasetVersion))), [])
        self.assertEqual(list(data_root.rglob("*.csv")), [])
        self.assertEqual(list((data_root / "course_demo").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
