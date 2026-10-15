import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.services.catalog import ensure_demo_catalog


class DemoCatalogTests(unittest.TestCase):
    def test_seed_quality_and_checksum_use_the_same_file_bytes(self):
        verified = b"trade_date,symbol,close\n2025-01-01,A,10\n"
        changed = b"trade_date,symbol,close\n2025-01-01,A,99\n"
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        try:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "demo.csv"
                path.write_bytes(changed)
                with Session(engine) as session, patch("app.services.catalog.sample_file", return_value=path), \
                     patch.object(Path, "read_bytes", return_value=verified) as read_bytes:
                    dataset, _ = ensure_demo_catalog(session)
                    self.assertEqual(dataset.checksum, hashlib.sha256(verified).hexdigest())
                    self.assertEqual(dataset.quality_report["numeric_summary"]["close"]["mean"], 10)
                    read_bytes.assert_called_once_with()
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
