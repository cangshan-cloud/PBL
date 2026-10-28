import csv
import gzip
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.verify_historical_composite_spotcheck import _standardize, verify


class HistoricalCompositeSpotcheckTests(unittest.TestCase):
    def test_mad_clipping_and_population_z_score(self):
        values = _standardize([0.0, 1.0, 2.0, 100.0])
        self.assertAlmostEqual(sum(values), 0.0)
        self.assertLess(values[-1], 2.0)  # Outlier was clipped before z-score.
        self.assertEqual(_standardize([5.0, 5.0, 5.0]), [5.0] * 3)

    def test_daily_keys_and_values_must_match_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "prices_source" / "symbols").mkdir(parents=True)
            (root / "members_source" / "daily_rosters").mkdir(parents=True)
            days = [date(2024, 1, 1) + timedelta(days=index) for index in range(22)]
            day = days[20]
            with (root / "prices_source" / "trade_calendar.csv").open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(("calendar_date", "is_trading_day"))
                writer.writerows((item.isoformat(), "1") for item in days)
            symbols = ["sh.600001", "sh.600002", "sh.600003"]
            with (root / "members_source" / "daily_rosters" / f"{day}.csv").open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(("code",))
                writer.writerows((symbol,) for symbol in symbols)
            for offset, symbol in enumerate(symbols):
                with (root / "prices_source" / "symbols" / f"{symbol.replace('.', '_')}.csv").open("w", newline="") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(("date", "close", "volume", "turn", "tradestatus", "isST"))
                    writer.writerows((item.isoformat(), str(100 + index * (offset + 1)), "100", str(offset + 1), "1", "0")
                                     for index, item in enumerate(days))
            from tools.independent_hs300_spotcheck import spotcheck
            points = {symbol: spotcheck(root, day, symbol) for symbol in symbols}
            keys = ("momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d")
            z = {key: _standardize([points[symbol][key] for symbol in symbols]) for key in keys}
            rows = [{"date": day.isoformat(), "symbol": symbol,
                     "factor": sum(z[key][index] for key in keys) / 4,
                     "forward_return": points[symbol]["forward_return"]}
                    for index, symbol in enumerate(symbols)]
            artifact = root / "observations.jsonl.gz"
            artifact.write_bytes(gzip.compress(("\n".join(json.dumps(row) for row in rows) + "\n").encode()))
            self.assertEqual(verify(root, artifact, day)["compared_count"], 3)
            rows[0]["factor"] += 0.01
            artifact.write_bytes(gzip.compress(("\n".join(json.dumps(row) for row in rows) + "\n").encode()))
            with self.assertRaisesRegex(ValueError, "observation mismatch"):
                verify(root, artifact, day)
            rows.pop()
            artifact.write_bytes(gzip.compress(("\n".join(json.dumps(row) for row in rows) + "\n").encode()))
            with self.assertRaisesRegex(ValueError, "observation keys disagree"):
                verify(root, artifact, day)


if __name__ == "__main__":
    unittest.main()
