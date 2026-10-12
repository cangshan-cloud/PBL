import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from fetch_real_a_share_sample import normalize_row


VALID = {
    "date": "2024-01-02", "code": "sh.600000", "open": "7.1", "high": "7.4",
    "low": "7.0", "close": "7.3", "volume": "100", "amount": "730",
    "turn": "0.52", "tradestatus": "1", "peTTM": "5.2", "adjustflag": "1",
}


class RealSampleAcquisitionTests(unittest.TestCase):
    def test_maps_source_fields_without_changing_units(self):
        row = normalize_row(VALID, "sh.600000")
        self.assertEqual(row["symbol"], "600000.SH")
        self.assertEqual(row["trade_date"], "2024-01-02")
        self.assertEqual(row["turnover_rate"], "0.52")
        self.assertEqual(row["pe"], "5.2")

    def test_rejects_suspension_and_adjustment_mismatch(self):
        for change in ({"tradestatus": "0"}, {"adjustflag": "3"}, {"close": ""}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                normalize_row({**VALID, **change}, "sh.600000")


if __name__ == "__main__":
    unittest.main()
