import hashlib
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.sample_data import load_price_file


class SampleDataLoaderTests(unittest.TestCase):
    def test_parses_the_same_bytes_that_passed_checksum_validation(self):
        verified = b"trade_date,symbol,close\n2025-01-01,A,10\n"
        changed_on_disk = b"trade_date,symbol,close\n2025-01-01,A,99\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            path.write_bytes(changed_on_disk)
            with patch.object(Path, "read_bytes", return_value=verified) as read_bytes:
                rows = load_price_file(path, hashlib.sha256(verified).hexdigest())
            read_bytes.assert_called_once_with()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].trade_date, date(2025, 1, 1))
        self.assertEqual(rows[0].close, 10.0)

    def test_rejects_mismatched_bytes_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.csv"
            path.write_bytes(b"not a CSV")
            with self.assertRaisesRegex(ValueError, "dataset checksum mismatch"):
                load_price_file(path, hashlib.sha256(b"different").hexdigest())


if __name__ == "__main__":
    unittest.main()
