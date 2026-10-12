import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from fetch_hs300_prices import FIELDS, audit_member_days, collect_prices, empty_audit, finite_number, normalize_rows
from verify_hs300_prices import verify_prices


def source_row(day, status="1", st="0", close="10", volume="100"):
    return {
        "date": day, "code": "sh.600000", "open": "10", "high": "11", "low": "9",
        "close": close, "volume": volume, "turn": "0.1", "tradestatus": status,
        "isST": st, "adjustflag": "1",
    }


class Result:
    error_code = "0"
    error_msg = "success"

    def __init__(self, fields, rows):
        self.fields = fields
        self.rows = iter(rows)

    def next(self):
        self.current = next(self.rows, None)
        return self.current is not None

    def get_row_data(self):
        return self.current


class Source:
    def query_trade_dates(self, **kwargs):
        return Result(["calendar_date", "is_trading_day"], [["2024-01-02", "1"], ["2024-01-03", "1"]])

    def query_history_k_data_plus(self, code, fields, **kwargs):
        rows = [source_row("2024-01-02"), source_row("2024-01-03", status="0", close="10", volume="")]
        return Result(list(FIELDS), [[row[field] for field in FIELDS] for row in rows])


class Hs300PricesTests(unittest.TestCase):
    def test_preserves_suspended_row_without_filling_price(self):
        rows = normalize_rows([source_row("2024-01-03", status="0", close="10", volume="")], "sh.600000", {"2024-01-03"})
        self.assertEqual(rows[0]["tradestatus"], "0")
        self.assertEqual(rows[0]["close"], "10")
        self.assertEqual(rows[0]["volume"], "")

    def test_rejects_duplicate_date_and_adjustment_mismatch(self):
        with self.assertRaisesRegex(ValueError, "duplicate date"):
            normalize_rows([source_row("2024-01-02"), source_row("2024-01-02")], "sh.600000", {"2024-01-02"})
        with self.assertRaisesRegex(ValueError, "adjustment flag"):
            normalize_rows([{**source_row("2024-01-02"), "adjustflag": "3"}], "sh.600000", {"2024-01-02"})

    def test_volume_parser_distinguishes_zero_from_missing(self):
        self.assertEqual(finite_number("0.000000"), 0)
        self.assertIsNone(finite_number(""))
        self.assertIsNone(finite_number("NaN"))

    def test_member_day_audit_fails_closed_for_missing_and_unknown(self):
        audit = empty_audit()
        rows = [source_row("2024-01-02", status="", st="0"), source_row("2024-01-03", st="1")]
        audit_member_days(rows, {"2024-01-02", "2024-01-03", "2024-01-04"}, audit)
        self.assertEqual(audit["member_pairs"], 3)
        self.assertEqual(audit["unknown_status"], 1)
        self.assertEqual(audit["st"], 1)
        self.assertEqual(audit["missing_row"], 1)
        self.assertEqual(audit["normal"], 0)

    @patch("verify_hs300_prices.load_member_codes", return_value=(["sh.600000"], {"sh.600000": {"2024-01-02", "2024-01-03"}}, "a" * 64))
    @patch("fetch_hs300_prices.load_member_codes", return_value=(["sh.600000"], {"sh.600000": {"2024-01-02", "2024-01-03"}}, "a" * 64))
    def test_collect_audits_suspension_and_finalizes(self, _fetch_members, _verify_members):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "prices"
            manifest = collect_prices(Source(), Path(temp) / "members", target, "2024-01-02", "2024-01-03")
            self.assertEqual(manifest["symbol_count"], 1)
            self.assertEqual(manifest["member_day_audit"]["normal"], 1)
            self.assertEqual(manifest["member_day_audit"]["suspended"], 1)
            self.assertEqual(verify_prices(Path(temp) / "members", target)["row_count"], 2)
            with self.assertRaisesRegex(ValueError, "already finalized"):
                collect_prices(Source(), Path(temp) / "members", target, "2024-01-02", "2024-01-03")

            saved = target / "symbols" / "sh_600000.csv"
            saved.write_bytes(saved.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "symbol hash mismatch"):
                verify_prices(Path(temp) / "members", target)


if __name__ == "__main__":
    unittest.main()
