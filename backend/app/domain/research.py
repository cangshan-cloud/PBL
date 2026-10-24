"""Small, dependency-free single-factor research engine.

The implementation deliberately uses the Python standard library so formula
tests run before the full data stack is installed. Production adapters can
later feed Parquet/DuckDB rows into the same public functions.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from math import fsum, isfinite, sqrt
from statistics import fmean, median, pstdev


@dataclass(frozen=True)
class PriceRow:
    trade_date: date
    symbol: str
    close: float
    turnover_rate: float | None = None
    total_mv: float | None = None
    pe: float | None = None
    adj_factor: float | None = None


@dataclass(frozen=True)
class Observation:
    trade_date: date
    symbol: str
    factor: float
    forward_return: float


def _returns_by_symbol(rows: list[PriceRow]) -> dict[str, list[tuple[date, float]]]:
    grouped: dict[str, list[tuple[date, float]]] = defaultdict(list)
    for row in rows:
        if row.close <= 0:
            raise ValueError("close must be positive")
        grouped[row.symbol].append((row.trade_date, row.close))
    for values in grouped.values():
        values.sort(key=lambda item: item[0])
    return grouped


def rows_by_symbol(rows: list[PriceRow]) -> dict[str, list[PriceRow]]:
    grouped: dict[str, list[PriceRow]] = defaultdict(list)
    for row in rows:
        if row.close <= 0:
            raise ValueError("close must be positive")
        grouped[row.symbol].append(row)
    for values in grouped.values():
        values.sort(key=lambda item: item.trade_date)
    return grouped


def calendar_positions(rows: list[PriceRow]) -> dict[date, int]:
    """Infer ordered market dates from the supplied cross-section."""
    return {day: index for index, day in enumerate(sorted({row.trade_date for row in rows}))}


def momentum_observations(rows: list[PriceRow], lookback: int = 20) -> list[Observation]:
    """Calculate close-to-close momentum at t and test against t+1 return."""
    if lookback < 1:
        raise ValueError("lookback must be positive")
    output: list[Observation] = []
    positions = calendar_positions(rows)
    for symbol, values in _returns_by_symbol(rows).items():
        for i in range(lookback, len(values) - 1):
            current_date, current = values[i]
            previous_date, previous = values[i - lookback]
            next_date, next_close = values[i + 1]
            if positions[current_date] - positions[previous_date] != lookback or positions[next_date] != positions[current_date] + 1:
                continue
            output.append(
                Observation(
                    trade_date=current_date,
                    symbol=symbol,
                    factor=current / previous - 1.0,
                    forward_return=next_close / current - 1.0,
                )
            )
    return output


def _rank(values: list[float]) -> list[float]:
    """Average ranks for ties, starting at rank 1."""
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    pos = 0
    while pos < len(order):
        end = pos
        while end + 1 < len(order) and values[order[end + 1]] == values[order[pos]]:
            end += 1
        average = (pos + 1 + end + 1) / 2
        for index in order[pos : end + 1]:
            ranks[index] = average
        pos = end + 1
    return ranks


def pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    if not all(isfinite(value) for value in (*left, *right)):
        return None
    left_scale, right_scale = max(map(abs, left)), max(map(abs, right))
    if not left_scale or not right_scale:
        return None
    scaled_left = [value / left_scale for value in left]
    scaled_right = [value / right_scale for value in right]
    left_mean, right_mean = fmean(scaled_left), fmean(scaled_right)
    centered_left = [value - left_mean for value in scaled_left]
    centered_right = [value - right_mean for value in scaled_right]
    left_sum = fsum(value * value for value in centered_left)
    right_sum = fsum(value * value for value in centered_right)
    denominator = sqrt(left_sum) * sqrt(right_sum)
    if not denominator:
        return None
    correlation = fsum(x * y for x, y in zip(centered_left, centered_right)) / denominator
    return max(-1.0, min(1.0, correlation))


def preprocess_observations(
    observations: list[Observation],
    *,
    winsorize: bool = True,
    standardize: bool = True,
    mad_scale: float = 3.0,
) -> list[Observation]:
    """Apply MAD winsorization and z-score normalization within each date."""
    if not isfinite(mad_scale) or mad_scale <= 0:
        raise ValueError("mad_scale must be finite and positive")
    by_date: dict[date, list[Observation]] = defaultdict(list)
    for item in observations:
        by_date[item.trade_date].append(item)

    output: list[Observation] = []
    for daily in by_date.values():
        values = [item.factor for item in daily]
        if not all(isfinite(value) for value in values):
            raise ValueError(f"non-finite factor observation: {daily[0].trade_date}")
        scale = max(map(abs, values), default=0.0)
        transformed = [value / scale for value in values] if scale else values[:]
        clipped = False
        if winsorize and len(values) > 1:
            center = median(transformed)
            mad = median(abs(value - center) for value in transformed)
            if mad > 0:
                distance = mad_scale * 1.4826 * mad
                winsorized = [min(center + distance, max(center - distance, value)) for value in transformed]
                clipped = winsorized != transformed
                transformed = winsorized
        if standardize and len(transformed) > 1:
            mean = fmean(transformed)
            deviation = pstdev(transformed)
            if deviation > 0:
                transformed = [(value - mean) / deviation for value in transformed]
            else:
                transformed = [value * scale for value in transformed] if clipped else values[:]
        else:
            transformed = [value * scale for value in transformed] if clipped else values[:]
        output.extend(
            Observation(item.trade_date, item.symbol, factor, item.forward_return)
            for item, factor in zip(daily, transformed)
        )
    return output


def _traded_notional(previous: set[str] | None, current: set[str]) -> float:
    """Sum buys and sells between equal-weight targets; initial entry costs one leg."""
    old = previous or set()
    return sum(
        abs((1 / len(current) if symbol in current else 0) - (1 / len(old) if symbol in old else 0))
        for symbol in old | current
    )


def ic_histogram(values: list[float]) -> list[dict[str, float | int]]:
    """Ten fixed-width IC bins in [-1, 1]; the last upper bound is inclusive."""
    counts = [0] * 10
    for value in values:
        index = min(9, max(0, int((value + 1.0) * 5 + 1e-12)))
        counts[index] += 1
    return [
        {"lower": round(-1 + index * 0.2, 1), "upper": round(-0.8 + index * 0.2, 1), "count": count}
        for index, count in enumerate(counts)
    ]


def _ensure_finite_result(value: object, path: str = "result") -> None:
    if isinstance(value, float) and not isfinite(value):
        raise ValueError(f"non-finite research result: {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _ensure_finite_result(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _ensure_finite_result(item, f"{path}[{index}]")


def evaluate(
    observations: list[Observation],
    groups: int = 5,
    *,
    winsorize: bool = True,
    standardize: bool = True,
    mad_scale: float = 3.0,
    transaction_cost_bps: float = 0.0,
) -> dict:
    """Return daily IC series, summary metrics and average quantile returns."""
    if groups < 2:
        raise ValueError("groups must be at least 2")
    if not 0 <= transaction_cost_bps <= 100:
        raise ValueError("transaction_cost_bps must be between 0 and 100")
    seen: set[tuple[date, str]] = set()
    for item in observations:
        key = (item.trade_date, item.symbol)
        if key in seen:
            raise ValueError(f"duplicate research observation: {item.trade_date} {item.symbol}")
        seen.add(key)
        if not isfinite(item.factor) or not isfinite(item.forward_return):
            raise ValueError(f"non-finite research observation: {item.trade_date} {item.symbol}")
    processed = preprocess_observations(
        observations,
        winsorize=winsorize,
        standardize=standardize,
        mad_scale=mad_scale,
    )
    by_date: dict[date, list[Observation]] = defaultdict(list)
    for item in processed:
        by_date[item.trade_date].append(item)

    ic_series: list[dict] = []
    group_returns: dict[int, list[float]] = defaultdict(list)
    group_nav = {bucket: 1.0 for bucket in range(1, groups + 1)}
    group_nav_series = {bucket: [] for bucket in range(1, groups + 1)}
    long_short_nav = 1.0
    long_short_net_nav = 1.0
    long_short_series: list[dict] = []
    top_members: set[str] | None = None
    bottom_members: set[str] | None = None
    turnover_values: list[float] = []
    long_short_turnover_values: list[float] = []
    group_skipped_constant_factor_days = 0
    group_skipped_insufficient_sample_days = 0
    daily_coverage: list[dict] = []
    for trade_date, daily in sorted(by_date.items()):
        diagnostic = {"date": trade_date.isoformat(), "eligible_symbols": len(daily),
                      "ic_status": "valid", "group_status": "valid"}
        daily_coverage.append(diagnostic)
        if len(daily) < 2:
            diagnostic["ic_status"] = "insufficient_sample"
            diagnostic["group_status"] = "insufficient_sample"
            group_skipped_insufficient_sample_days += 1
            continue
        factors = [item.factor for item in daily]
        returns = [item.forward_return for item in daily]
        ic = pearson(factors, returns)
        rank_ic = pearson(_rank(factors), _rank(returns))
        if ic is None:
            diagnostic["ic_status"] = "constant_factor_or_return"
        ic_series.append({"date": trade_date.isoformat(), "ic": ic, "rank_ic": rank_ic})

        if max(factors) == min(factors):
            diagnostic["group_status"] = "constant_factor"
            group_skipped_constant_factor_days += 1
            continue
        if len(daily) < groups:
            diagnostic["group_status"] = "insufficient_sample"
            group_skipped_insufficient_sample_days += 1
            continue

        ordered = sorted(daily, key=lambda item: (item.factor, item.symbol))
        daily_groups: dict[int, list[Observation]] = defaultdict(list)
        for index, item in enumerate(ordered):
            bucket = min(index * groups // len(ordered) + 1, groups)
            daily_groups[bucket].append(item)

        daily_means: dict[int, float] = {}
        for bucket in range(1, groups + 1):
            members = daily_groups.get(bucket, [])
            if members:
                daily_means[bucket] = fmean(item.forward_return for item in members)
                group_returns[bucket].append(daily_means[bucket])
                group_nav[bucket] *= 1.0 + daily_means[bucket]
            group_nav_series[bucket].append({"date": trade_date.isoformat(), "nav": group_nav[bucket]})
        current_top = {item.symbol for item in daily_groups.get(groups, [])}
        current_bottom = {item.symbol for item in daily_groups.get(1, [])}
        top_turnover = _traded_notional(top_members, current_top)
        bottom_turnover = _traded_notional(bottom_members, current_bottom)
        if top_members is not None and current_top:
            turnover_values.append(top_turnover / 2)
        if 1 in daily_means and groups in daily_means:
            long_short_return = daily_means[groups] - daily_means[1]
            portfolio_turnover = top_turnover + bottom_turnover
            trading_cost = portfolio_turnover * transaction_cost_bps / 10_000
            net_return = long_short_return - trading_cost
            long_short_nav *= 1.0 + long_short_return
            long_short_net_nav *= 1.0 + net_return
            long_short_turnover_values.append(portfolio_turnover)
            long_short_series.append({
                "date": trade_date.isoformat(),
                "return": long_short_return,
                "nav": long_short_nav,
                "turnover": portfolio_turnover,
                "cost": trading_cost,
                "net_return": net_return,
                "net_nav": long_short_net_nav,
            })
        if current_top:
            top_members = current_top
        if current_bottom:
            bottom_members = current_bottom

    valid_ic = [item["ic"] for item in ic_series if item["ic"] is not None]
    valid_rank_ic = [item["rank_ic"] for item in ic_series if item["rank_ic"] is not None]
    ic_mean = fmean(valid_ic) if valid_ic else None
    ic_std = (
        0.0 if max(valid_ic) - min(valid_ic) <= 1e-12 else pstdev(valid_ic)
    ) if len(valid_ic) > 1 else None
    long_short_returns = [item["return"] for item in long_short_series]
    long_short_net_returns = [item["net_return"] for item in long_short_series]
    result = {
        "coverage": len(processed),
        "daily_coverage": daily_coverage,
        "ic_mean": ic_mean,
        "ic_std": ic_std,
        "rank_ic_mean": fmean(valid_rank_ic) if valid_rank_ic else None,
        "icir": ic_mean / ic_std if ic_mean is not None and ic_std else None,
        "ic_positive_ratio": sum(value > 0 for value in valid_ic) / len(valid_ic) if valid_ic else None,
        "ic_series": ic_series,
        "group_skipped_constant_factor_days": group_skipped_constant_factor_days,
        "group_skipped_insufficient_sample_days": group_skipped_insufficient_sample_days,
        "ic_histogram": ic_histogram(valid_ic),
        "group_returns": [
            {"group": bucket, "mean_return": fmean(group_returns[bucket])}
            for bucket in sorted(group_returns)
        ],
        "group_nav": [
            {"group": bucket, "points": group_nav_series[bucket]}
            for bucket in range(1, groups + 1)
        ],
        "long_short_mean": fmean(long_short_returns) if long_short_returns else None,
        "long_short_total_return": long_short_nav - 1.0 if long_short_series else None,
        "long_short_net_mean": fmean(long_short_net_returns) if long_short_net_returns else None,
        "long_short_net_total_return": long_short_net_nav - 1.0 if long_short_series else None,
        "long_short_turnover": fmean(long_short_turnover_values) if long_short_turnover_values else None,
        "transaction_cost_bps": transaction_cost_bps,
        "cost_model": "equal_weight_target_traded_notional_v1",
        "long_short_series": long_short_series,
        "top_group_turnover": fmean(turnover_values) if turnover_values else None,
        "preprocessing": {
            "winsorize": winsorize,
            "standardize": standardize,
            "method": "MAD" if winsorize else "none",
            "mad_scale": mad_scale if winsorize else None,
        },
    }
    _ensure_finite_result(result)
    return result
