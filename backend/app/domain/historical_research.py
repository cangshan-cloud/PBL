"""Strict calendar-aligned observations for the sealed CSI 300 bundle."""

from __future__ import annotations

import csv
import hashlib
import io
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import fmean, pstdev

from app.domain.research import Observation
from app.services.historical_bundle import verify_historical_bundle


FACTOR_WINDOWS = {"momentum_20d": 20, "reversal_5d": 5, "volatility_20d": 20, "turnover_20d": 20}


@dataclass(frozen=True)
class HistoricalBar:
    close: float | None
    turnover: float | None
    volume: float | None
    tradestatus: str
    is_st: str


def _bar(raw: dict[str, str]) -> HistoricalBar:
    def number(field: str) -> float | None:
        return float(raw[field]) if raw[field] else None

    return HistoricalBar(number("close"), number("turn"), number("volume"), raw["tradestatus"], raw["isST"])


def _verified_csv_rows(root: Path, relative: str, hashes: dict[str, str]) -> list[dict[str, str]]:
    path = root / relative
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != hashes.get(relative):
        raise ValueError(f"historical bundle file checksum mismatch: {relative}")
    return list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline="")))


def load_historical_bundle(manifest_path: Path, expected_checksum: str | None = None) -> tuple[list[date], dict[date, set[str]], dict[str, dict[date, HistoricalBar]]]:
    """Revalidate all files before loading; reject unknown member-day state."""
    verified = verify_historical_bundle(manifest_path, expected_checksum)
    root = manifest_path.parent
    hashes = verified["manifest"]["file_sha256"]
    calendar: list[date] = []
    for row in _verified_csv_rows(root, "prices_source/trade_calendar.csv", hashes):
        if row["is_trading_day"] == "1":
            calendar.append(date.fromisoformat(row["calendar_date"]))
    if not calendar or calendar != sorted(set(calendar)):
        raise ValueError("invalid historical trading calendar")
    members: dict[date, set[str]] = {}
    for day in (item for item in calendar if item.year == 2024):
        rows = _verified_csv_rows(root, f"members_source/daily_rosters/{day.isoformat()}.csv", hashes)
        if len(rows) != 300 or any(row["query_date"] != day.isoformat() or not row["update_date"] for row in rows):
            raise ValueError(f"invalid historical roster: {day}")
        codes = {row["code"] for row in rows}
        if len(codes) != 300:
            raise ValueError(f"duplicate historical members: {day}")
        members[day] = codes
    bars: dict[str, dict[date, HistoricalBar]] = {}
    for path in sorted((root / "prices_source" / "symbols").glob("*.csv")):
        symbol_bars: dict[date, HistoricalBar] = {}
        relative = path.relative_to(root).as_posix()
        for row in _verified_csv_rows(root, relative, hashes):
            code = row["code"]
            day = date.fromisoformat(row["date"])
            if code.replace(".", "_") != path.stem or day in symbol_bars:
                raise ValueError(f"invalid historical price row: {path.name} {day}")
            symbol_bars[day] = _bar(row)
        bars[path.stem.replace("_", ".")] = symbol_bars
    for day, codes in members.items():
        for code in codes:
            bar = bars.get(code, {}).get(day)
            if bar is None or bar.tradestatus not in {"0", "1"} or bar.is_st not in {"0", "1"}:
                raise ValueError(f"unknown historical member state: {day} {code}")
    return calendar, members, bars


def calculate_historical_observations(
    calendar: list[date], members: dict[date, set[str]], bars: dict[str, dict[date, HistoricalBar]],
    factor: str,
) -> tuple[list[Observation], dict[str, object]]:
    """Signal eligibility uses t only; label always uses the next market day."""
    if factor not in FACTOR_WINDOWS:
        raise ValueError("unsupported historical factor")
    window = FACTOR_WINDOWS[factor]
    if not calendar or calendar != sorted(set(calendar)) or not set(members).issubset(set(calendar)):
        raise ValueError("invalid historical calendar or rosters")
    observations: list[Observation] = []
    totals: Counter[str] = Counter()
    daily: list[dict[str, object]] = []
    unlabeled_signals: list[dict[str, object]] = []
    for index, day in enumerate(calendar):
        if day not in members:
            continue  # Warmup and post-year days supply inputs/labels, never signal samples.
        counts: Counter[str] = Counter()
        counts["candidate_count"] = len(members[day])
        counts["nonmember_count"] = len(set(bars) - members[day])
        next_day = calendar[index + 1] if index + 1 < len(calendar) else None
        for symbol in sorted(members[day]):
            current = bars.get(symbol, {}).get(day)
            if current is None or current.tradestatus not in {"0", "1"} or current.is_st not in {"0", "1"}:
                raise ValueError(f"unknown historical member state: {day} {symbol}")
            if current.tradestatus != "1":
                counts["signal_suspended"] += 1
                continue
            if current.is_st != "0":
                counts["signal_st"] += 1
                continue
            if current.volume is None or current.volume <= 0 or current.close is None or current.close <= 0:
                counts["signal_no_valid_trade"] += 1
                continue
            counts["eligible_signal"] += 1
            # Include t-N for price ratios; volatility uses the N consecutive returns.
            start = index - window if factor != "turnover_20d" else index - window + 1
            if start < 0:
                counts["insufficient_calendar_history"] += 1
                continue
            window_bars = [bars.get(symbol, {}).get(calendar[pos]) for pos in range(start, index + 1)]
            if any(item is None or item.tradestatus != "1" or item.close is None or item.close <= 0
                   or item.volume is None or item.volume <= 0 for item in window_bars):
                counts["invalid_contiguous_window"] += 1
                continue
            if factor == "turnover_20d" and any(item.turnover is None or item.turnover < 0 for item in window_bars):
                counts["invalid_contiguous_window"] += 1
                continue
            closes = [item.close for item in window_bars]
            if factor == "momentum_20d":
                value = closes[-1] / closes[0] - 1
            elif factor == "reversal_5d":
                value = -(closes[-1] / closes[0] - 1)
            elif factor == "volatility_20d":
                value = pstdev(closes[pos] / closes[pos - 1] - 1 for pos in range(1, len(closes)))
            else:
                value = fmean(item.turnover for item in window_bars)
            counts["factor_signal"] += 1
            label_reason = None
            if next_day is None:
                label_reason = "label_out_of_calendar"
            else:
                following = bars.get(symbol, {}).get(next_day)
                if following is None:
                    label_reason = "label_missing_row"
                elif following.tradestatus not in {"0", "1"} or following.is_st not in {"0", "1"}:
                    raise ValueError(f"unknown next-day state: {next_day} {symbol}")
                elif following.tradestatus != "1":
                    label_reason = "label_suspended"
                elif following.is_st != "0":
                    label_reason = "label_st"
                elif following.volume is None or following.volume <= 0 or following.close is None or following.close <= 0:
                    label_reason = "label_no_valid_trade"
            if label_reason:
                counts[label_reason] += 1
                unlabeled_signals.append({"date": day.isoformat(), "symbol": symbol,
                                          "factor": value, "next_market_date": next_day.isoformat() if next_day else None,
                                          "reason": label_reason})
                continue
            observations.append(Observation(day, symbol, value, following.close / current.close - 1))
            counts["valid_return"] += 1
        totals.update(counts)
        daily.append({"date": day.isoformat(), **counts})
    return observations, {"factor": factor, "totals": dict(totals), "daily": daily,
                          "unlabeled_signals": unlabeled_signals}
