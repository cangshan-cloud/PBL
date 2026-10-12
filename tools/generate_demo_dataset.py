"""Generate the deterministic offline demo dataset used by FactorLab."""

from __future__ import annotations

import argparse
import csv
import io
import math
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "sample" / "daily_prices.csv"
COLUMNS = [
    "trade_date", "symbol", "open", "high", "low", "close", "volume",
    "amount", "adj_factor", "turnover_rate", "total_mv", "pe",
]


def business_dates(start: date, count: int) -> list[date]:
    output: list[date] = []
    current = start
    while len(output) < count:
        if current.weekday() < 5:
            output.append(current)
        current += timedelta(days=1)
    return output


def render() -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    dates = business_dates(date(2025, 1, 2), 120)
    for symbol_index in range(1, 21):
        symbol = f"DEMO{symbol_index:02d}"
        close = 18.0 + symbol_index * 2.2
        shares = 80_000_000 + symbol_index * 7_500_000
        for day_index, trade_date in enumerate(dates):
            previous = close
            trend = (symbol_index - 10.5) * 0.00035
            cycle = 0.007 * math.sin(day_index / 7 + symbol_index * 0.55)
            pulse = 0.0025 * math.cos(day_index / 3 + symbol_index * 0.31)
            close = max(2.0, previous * (1 + trend + cycle + pulse))
            open_price = previous * (1 + 0.002 * math.sin(day_index + symbol_index))
            high = max(open_price, close) * 1.006
            low = min(open_price, close) * 0.994
            volume = int(700_000 + symbol_index * 45_000 + 180_000 * (1 + math.sin(day_index / 5 + symbol_index)))
            turnover = 0.35 + symbol_index * 0.055 + 0.22 * (1 + math.sin(day_index / 9 + symbol_index / 3))
            total_mv = close * shares / 10_000
            pe = 7.5 + symbol_index * 0.7 + 1.8 * math.sin(day_index / 13 + symbol_index / 4)
            writer.writerow({
                "trade_date": trade_date.isoformat(),
                "symbol": symbol,
                "open": f"{open_price:.4f}",
                "high": f"{high:.4f}",
                "low": f"{low:.4f}",
                "close": f"{close:.4f}",
                "volume": volume,
                "amount": f"{volume * close:.2f}",
                "adj_factor": "1.000000",
                "turnover_rate": f"{turnover:.4f}",
                "total_mv": f"{total_mv:.2f}",
                "pe": f"{pe:.4f}",
            })
    return stream.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the committed snapshot is not reproducible")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not TARGET.is_file() or TARGET.read_text(encoding="utf-8") != expected:
            raise SystemExit("demo dataset is not up to date; run tools/generate_demo_dataset.py")
        print("demo dataset is reproducible")
        return
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected, encoding="utf-8", newline="")
    print(f"generated {TARGET}: 2400 rows")


if __name__ == "__main__":
    main()
