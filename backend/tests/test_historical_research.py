import sys
import hashlib
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.historical_research import HistoricalBar, _bar, _validate_loaded_counts, _verified_csv_rows, calculate_historical_observations


def bar(close=100.0, turnover=1.0, volume=100.0, status="1", st="0"):
    return HistoricalBar(close, turnover, volume, status, st)


class HistoricalResearchTests(unittest.TestCase):
    def setUp(self):
        self.days = [date(2023, 12, 1) + timedelta(days=index) for index in range(23)]
        self.members = {self.days[20]: {"A"}, self.days[21]: {"A"}}
        self.bars = {"A": {day: bar(100 + index) for index, day in enumerate(self.days)}}

    def test_warmup_and_next_market_day(self):
        observations, audit = calculate_historical_observations(self.days, self.members, self.bars, "momentum_20d")
        self.assertEqual([item.trade_date for item in observations], self.days[20:22])
        self.assertAlmostEqual(observations[0].factor, 120 / 100 - 1)
        self.assertAlmostEqual(observations[0].forward_return, 121 / 120 - 1)
        self.assertEqual(audit["totals"]["candidate_count"], 2)
        self.assertEqual(audit["totals"]["nonmember_count"], 0)

    def test_historical_csv_parser_uses_only_verified_bytes(self):
        verified = b"date,code,close\n2025-01-01,sh.600000,10\n"
        changed = b"date,code,close\n2025-01-01,sh.600000,99\n"
        relative = "prices_source/symbols/sh_600000.csv"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / relative
            path.parent.mkdir(parents=True)
            path.write_bytes(changed)
            hashes = {relative: hashlib.sha256(verified).hexdigest()}
            with patch.object(Path, "read_bytes", return_value=verified) as read_bytes:
                rows = _verified_csv_rows(root, relative, hashes)
            read_bytes.assert_called_once_with()
            self.assertEqual(rows[0]["close"], "10")
            with self.assertRaisesRegex(ValueError, "historical bundle file checksum mismatch"):
                _verified_csv_rows(root, relative, hashes)

    def test_historical_bar_rejects_nonfinite_numeric_fields(self):
        valid = {"close": "10", "turn": "0.5", "volume": "100", "tradestatus": "1", "isST": "0"}
        for field, invalid in (("close", "NaN"), ("turn", "Infinity"), ("volume", "1e999")):
            with self.subTest(field=field, invalid=invalid):
                with self.assertRaisesRegex(ValueError, f"non-finite historical price field: {field}"):
                    _bar({**valid, field: invalid})
        self.assertEqual(_bar({**valid, "turn": ""}).turnover, None)

    def test_historical_loaded_counts_must_match_manifest(self):
        members = {self.days[20]: {"A"}, self.days[21]: {"A"}}
        bars = {"A": {self.days[20]: bar(), self.days[21]: bar()}}
        manifest = {"member_trading_days": 2, "member_rows": 2, "price_symbols": 1, "price_rows": 2}
        _validate_loaded_counts(manifest, members, bars)
        for field in manifest:
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, f"historical bundle summary mismatch: {field}"):
                    _validate_loaded_counts({**manifest, field: manifest[field] + 1}, members, bars)

    def test_missing_intermediate_day_does_not_compress_window(self):
        del self.bars["A"][self.days[10]]
        observations, audit = calculate_historical_observations(self.days, self.members, self.bars, "momentum_20d")
        self.assertEqual(observations, [])
        self.assertEqual(audit["totals"]["invalid_contiguous_window"], 2)

    def test_next_day_suspension_does_not_remove_signal(self):
        self.bars["A"][self.days[21]] = bar(status="0", volume=None)
        observations, audit = calculate_historical_observations(self.days, self.members, self.bars, "momentum_20d")
        self.assertEqual(observations, [])
        self.assertEqual(audit["daily"][0]["factor_signal"], 1)
        self.assertEqual(audit["daily"][0]["label_suspended"], 1)
        self.assertEqual(audit["unlabeled_signals"][0]["symbol"], "A")
        self.assertEqual(audit["unlabeled_signals"][0]["reason"], "label_suspended")
        self.assertEqual(audit["daily"][1]["signal_suspended"], 1)

    def test_exit_on_next_day_still_has_label(self):
        self.members = {self.days[20]: {"A"}}
        observations, _ = calculate_historical_observations(self.days, self.members, self.bars, "reversal_5d")
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0].trade_date, self.days[20])

    def test_out_of_calendar_label_not_fabricated(self):
        self.days = self.days[:21]
        self.members = {self.days[-1]: {"A"}}
        _, audit = calculate_historical_observations(self.days, self.members, self.bars, "momentum_20d")
        self.assertEqual(audit["totals"]["label_out_of_calendar"], 1)


if __name__ == "__main__":
    unittest.main()
