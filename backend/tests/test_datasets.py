import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
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


if __name__ == "__main__":
    unittest.main()
