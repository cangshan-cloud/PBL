import csv
import math
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.independent_hs300_spotcheck import spotcheck


class IndependentHs300SpotcheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "prices_source" / "symbols").mkdir(parents=True)
        (self.root / "members_source" / "daily_rosters").mkdir(parents=True)
        self.days = [date(2024, 1, 1) + timedelta(days=index) for index in range(22)]
        self.signal_day = self.days[20]
        with (self.root / "prices_source" / "trade_calendar.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("calendar_date", "is_trading_day"))
            writer.writerows((day.isoformat(), "1") for day in self.days)
        with (self.root / "members_source" / "daily_rosters" / f"{self.signal_day}.csv").open(
            "w", newline="", encoding="utf-8",
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(("query_date", "code", "update_date"))
            writer.writerow((self.signal_day.isoformat(), "sh.600000", "2024-01-01"))
        self.write_bars()

    def tearDown(self):
        self.temp.cleanup()

    def write_bars(self, next_status="1"):
        with (self.root / "prices_source" / "symbols" / "sh_600000.csv").open(
            "w", newline="", encoding="utf-8",
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(("date", "close", "volume", "turn", "tradestatus", "isST"))
            writer.writerows((day.isoformat(), str(100 + index), "100", str(index + 1),
                              next_status if index == 21 else "1", "0") for index, day in enumerate(self.days))

    def test_four_formulas_and_next_market_return(self):
        result = spotcheck(self.root, self.signal_day, "sh.600000")
        self.assertEqual(result["window_start_date"], self.days[0].isoformat())
        self.assertEqual(result["next_market_date"], self.days[21].isoformat())
        self.assertAlmostEqual(result["momentum_20d"], 0.2)
        self.assertAlmostEqual(result["reversal_5d"], -(120 / 115 - 1))
        returns = [(101 + index) / (100 + index) - 1 for index in range(20)]
        average = sum(returns) / 20
        self.assertAlmostEqual(result["volatility_20d"], math.sqrt(sum((item - average) ** 2 for item in returns) / 20))
        self.assertAlmostEqual(result["turnover_20d"], 11.5)
        self.assertAlmostEqual(result["forward_return"], 121 / 120 - 1)
        self.assertIsNone(result["label_reason"])

    def test_next_day_suspension_keeps_signal_but_has_no_return(self):
        self.write_bars(next_status="0")
        result = spotcheck(self.root, self.signal_day, "sh.600000")
        self.assertAlmostEqual(result["momentum_20d"], 0.2)
        self.assertIsNone(result["forward_return"])
        self.assertEqual(result["label_reason"], "label_suspended")

    def test_rejects_invalid_symbol_and_missing_window_row(self):
        with self.assertRaisesRegex(ValueError, "symbol must"):
            spotcheck(self.root, self.signal_day, "../../oops")
        self.days.pop(10)
        self.write_bars()
        with self.assertRaisesRegex(ValueError, "window row"):
            spotcheck(self.root, self.signal_day, "sh.600000")


if __name__ == "__main__":
    unittest.main()
