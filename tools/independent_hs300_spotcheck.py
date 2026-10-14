"""Read sealed source CSVs directly and hand-check one historical member-day.

This intentionally does not import FactorLab's research code. Run the bundle
integrity verifier separately; this small checker does not authenticate data.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from datetime import date
from pathlib import Path


SYMBOL = re.compile(r"(?:sh|sz)\.\d{6}\Z")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def spotcheck(bundle_dir: Path, signal_day: date, symbol: str) -> dict:
    if not SYMBOL.fullmatch(symbol):
        raise ValueError("symbol must be sh.XXXXXX or sz.XXXXXX")
    root = bundle_dir.resolve(strict=True)
    calendar = [date.fromisoformat(row["calendar_date"]) for row in
                _rows(root / "prices_source" / "trade_calendar.csv") if row["is_trading_day"] == "1"]
    if calendar != sorted(set(calendar)) or signal_day not in calendar:
        raise ValueError("invalid calendar or signal day is not a market day")
    index = calendar.index(signal_day)
    if index < 20 or index + 1 >= len(calendar):
        raise ValueError("need 20 prior and one next market day")
    roster = _rows(root / "members_source" / "daily_rosters" / f"{signal_day.isoformat()}.csv")
    if symbol not in {row["code"] for row in roster}:
        raise ValueError("symbol is not a member on signal day")
    bars = {date.fromisoformat(row["date"]): row for row in
            _rows(root / "prices_source" / "symbols" / f"{symbol.replace('.', '_')}.csv")}

    def traded(day: date, *, turnover: bool = False) -> dict[str, str]:
        row = bars.get(day)
        if not row or row["tradestatus"] != "1" or not row["close"] or not row["volume"]:
            raise ValueError(f"missing or non-trading window row: {day}")
        if float(row["close"]) <= 0 or float(row["volume"]) <= 0:
            raise ValueError(f"invalid window price or volume: {day}")
        if turnover and (not row["turn"] or float(row["turn"]) < 0):
            raise ValueError(f"invalid turnover: {day}")
        return row

    window = [traded(day, turnover=(position > 0)) for position, day in
              enumerate(calendar[index - 20:index + 1])]
    current = window[-1]
    if current["isST"] != "0":
        raise ValueError("signal-day member is ST")
    closes = [float(row["close"]) for row in window]
    returns = [closes[position] / closes[position - 1] - 1 for position in range(1, len(closes))]
    mean_return = sum(returns) / len(returns)
    next_day = calendar[index + 1]
    following = bars.get(next_day)
    label_reason = None
    if following is None:
        label_reason = "label_missing_row"
    elif following["tradestatus"] not in {"0", "1"} or following["isST"] not in {"0", "1"}:
        raise ValueError("unknown next-day trading or ST state")
    elif following["tradestatus"] != "1":
        label_reason = "label_suspended"
    elif following["isST"] != "0":
        label_reason = "label_st"
    elif not following["close"] or not following["volume"] or float(following["close"]) <= 0 or float(following["volume"]) <= 0:
        label_reason = "label_no_valid_trade"
    return {
        "signal_date": signal_day.isoformat(), "symbol": symbol,
        "window_start_date": calendar[index - 20].isoformat(),
        "next_market_date": next_day.isoformat(),
        "close_t_minus_20": closes[0], "close_t_minus_5": closes[-6],
        "close_t": closes[-1], "close_t_plus_1": float(following["close"]) if following and following["close"] else None,
        "momentum_20d": closes[-1] / closes[0] - 1,
        "reversal_5d": -(closes[-1] / closes[-6] - 1),
        "volatility_20d": math.sqrt(sum((value - mean_return) ** 2 for value in returns) / len(returns)),
        "turnover_20d": sum(float(row["turn"]) for row in window[1:]) / 20,
        "forward_return": float(following["close"]) / closes[-1] - 1 if label_reason is None else None,
        "label_reason": label_reason,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("signal_date", type=date.fromisoformat)
    parser.add_argument("symbol")
    args = parser.parse_args()
    try:
        result = spotcheck(args.bundle_dir, args.signal_date, args.symbol)
    except (OSError, KeyError, ValueError) as exc:
        parser.exit(1, f"独立抽样验算失败：{exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
