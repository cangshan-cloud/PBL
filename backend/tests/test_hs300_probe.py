import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from probe_hs300_history import collect, query_rows


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
    def __init__(self, dates):
        self.dates = dates
        self.queries = []

    def query_trade_dates(self, **kwargs):
        return Result(["calendar_date", "is_trading_day"], self.dates)

    def query_hs300_stocks(self, day):
        self.queries.append(day)
        return Result(["code", "updateDate"], [[f"sh.{600000 + i:06d}", day] for i in range(300)])


class Hs300ProbeTests(unittest.TestCase):
    def test_collects_only_trading_day_rosters_and_preserves_source_update_date(self):
        source = Source([["2024-06-28", "1"], ["2024-06-29", "0"], ["2024-06-30", "0"], ["2024-07-01", "1"]])
        calendar, members = collect(source, "2024-06-28", "2024-07-01")
        self.assertEqual(len(calendar), 4)
        self.assertEqual(source.queries, ["2024-06-28", "2024-07-01"])
        self.assertEqual(len(members), 600)
        self.assertEqual(members[0]["update_date"], "2024-06-28")

    def test_rejects_calendar_gap_and_bad_roster(self):
        with self.assertRaisesRegex(ValueError, "every requested date"):
            collect(Source([["2024-06-28", "1"], ["2024-06-30", "0"]]), "2024-06-28", "2024-06-30")

        class ShortSource(Source):
            def query_hs300_stocks(self, day):
                return Result(["code", "updateDate"], [["sh.600000", day]])

        with self.assertRaisesRegex(ValueError, "300 unique"):
            collect(ShortSource([["2024-06-28", "1"]]), "2024-06-28", "2024-06-28")

    def test_rejects_missing_fields(self):
        with self.assertRaisesRegex(ValueError, "fields missing"):
            query_rows(Result(["code"], [["sh.600000"]]), {"code", "updateDate"})


if __name__ == "__main__":
    unittest.main()
