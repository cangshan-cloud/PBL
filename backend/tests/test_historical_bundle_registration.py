import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.services.datasets import DatasetValidationError, publish_dataset_version, register_hs300_bundle
from app.services.historical_bundle import verify_historical_bundle


class HistoricalBundleRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        file_hash = hashlib.sha256(b"sample").hexdigest()
        manifest = {
            "schema_version": 1, "research_start": "2024-01-01", "research_end": "2024-12-31",
            "price_basis": "source_close", "price_adjustflag": "1",
            "factor_windows": {"momentum": 20, "reversal": 5, "volatility": 20, "turnover": 20},
            "file_sha256": {"members_source/sample.csv": file_hash},
            "member_trading_days": 242, "member_rows": 72600,
            "price_symbols": 328, "price_rows": 95776,
        }
        identity = {key: manifest[key] for key in (
            "schema_version", "research_start", "research_end", "price_basis",
            "price_adjustflag", "factor_windows", "file_sha256",
        )}
        version = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.bundle_id = f"hs300_2024_{version[:16]}"
        manifest.update(version_sha256=version, bundle_id=self.bundle_id)
        self.bundle_dir = self.root / "real" / "bundles" / self.bundle_id
        (self.bundle_dir / "members_source").mkdir(parents=True)
        (self.bundle_dir / "members_source" / "sample.csv").write_bytes(b"sample")
        (self.bundle_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def tearDown(self):
        self.engine.dispose()
        self.temp.cleanup()

    def test_register_publish_and_reject_duplicate(self):
        with Session(self.engine, expire_on_commit=False) as session:
            dataset = register_hs300_bundle(session, bundle_id=self.bundle_id, data_root=self.root / "runtime")
            self.assertEqual(dataset.status, "draft")
            self.assertEqual(dataset.quality_report["dataset_kind"], "hs300_bundle_v1")
            self.assertEqual(publish_dataset_version(session, dataset).status, "published")
            with self.assertRaises(DatasetValidationError):
                register_hs300_bundle(session, bundle_id=self.bundle_id, data_root=self.root / "runtime")

    def test_tampering_blocks_publication(self):
        with Session(self.engine, expire_on_commit=False) as session:
            dataset = register_hs300_bundle(session, bundle_id=self.bundle_id, data_root=self.root / "runtime")
            (self.bundle_dir / "members_source" / "sample.csv").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                publish_dataset_version(session, dataset)
            self.assertEqual(dataset.status, "draft")

    def test_unsafe_bundle_id_and_extra_file(self):
        with Session(self.engine) as session:
            with self.assertRaises(DatasetValidationError):
                register_hs300_bundle(session, bundle_id="../other", data_root=self.root / "runtime")
        (self.bundle_dir / "extra.txt").write_text("extra")
        with self.assertRaisesRegex(ValueError, "file set mismatch"):
            verify_historical_bundle(self.bundle_dir / "manifest.json")


if __name__ == "__main__":
    unittest.main()
