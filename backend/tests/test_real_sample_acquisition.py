import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from fetch_real_a_share_sample import normalize_row
from verify_real_a_share_sample import group_date_audit, independent_momentum_ic_audit, observed_coverage_audit


VALID = {
    "date": "2024-01-02", "code": "sh.600000", "open": "7.1", "high": "7.4",
    "low": "7.0", "close": "7.3", "volume": "100", "amount": "730",
    "turn": "0.52", "tradestatus": "1", "peTTM": "5.2", "adjustflag": "1",
}


class RealSampleAcquisitionTests(unittest.TestCase):
    def test_independent_raw_momentum_ic_audit_detects_wrong_saved_value(self):
        lines = ["trade_date,symbol,close"]
        days = ("2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04")
        for index, day in enumerate(days):
            for symbol, growth in (("A", 1.1), ("B", 1.2), ("C", 1.3)):
                lines.append(f"{day},{symbol},{10 * growth ** index}")
        content = ("\n".join(lines) + "\n").encode()
        saved = [{"date": day, "ic": 1.0} for day in days[1:3]]
        checked = independent_momentum_ic_audit(content, saved, lookback=1, validation_start=days[2])
        self.assertEqual(observed_coverage_audit(content), {
            "observed_dates": 4, "min_rows_per_observed_date": 3, "max_rows_per_observed_date": 3,
            "min_rows_per_symbol": 4, "max_rows_per_symbol": 4,
        })
        self.assertEqual(checked["audited_ic_dates"], 2)
        self.assertEqual(checked["research_spot"]["stock_count"], 3)
        self.assertEqual(checked["validation_spot"]["date"], days[2])
        with self.assertRaisesRegex(ValueError, "independent raw momentum IC differs"):
            independent_momentum_ic_audit(content, [{"date": days[1], "ic": 0.0}], lookback=1,
                                          validation_start=days[1])

    def test_group_date_audit_rejects_misaligned_nav(self):
        result = {"coverage": 2, "ic_series": [{"date": "2024-01-02"}],
                  "long_short_series": [{"date": "2024-01-02"}],
                  "group_nav": [{"points": [{"date": "2024-01-03"}]}],
                  "group_skipped_constant_factor_days": 0,
                  "group_skipped_insufficient_sample_days": 0}
        with self.assertRaisesRegex(ValueError, "group NAV dates differ"):
            group_date_audit(result, "test")
        result["group_nav"][0]["points"][0]["date"] = "2024-01-02"
        self.assertEqual(group_date_audit(result, "test")["group_dates"], 1)

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
