"""Built-in factor registry and dependency-free calculation functions."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean, pstdev
from typing import Callable

from app.domain.research import Observation, PriceRow, calendar_positions, rows_by_symbol


@dataclass(frozen=True)
class FactorDefinition:
    key: str
    name: str
    category: str
    version: str
    formula: str
    description: str
    required_columns: tuple[str, ...]
    default_lookback: int | None
    calculator: Callable[[list[PriceRow], int | None], list[Observation]]

    def public_dict(self) -> dict:
        return {
            "id": self.key,
            "name": self.name,
            "category": self.category,
            "version": self.version,
            "formula": self.formula,
            "description": self.description,
            "required_columns": list(self.required_columns),
            "default_lookback": self.default_lookback,
            "status": "available",
        }


def _observation(row: PriceRow, next_row: PriceRow, factor: float) -> Observation:
    return Observation(
        trade_date=row.trade_date,
        symbol=row.symbol,
        factor=factor,
        forward_return=next_row.close / row.close - 1.0,
    )


def _momentum(rows: list[PriceRow], lookback: int | None) -> list[Observation]:
    period = lookback or 20
    output: list[Observation] = []
    positions = calendar_positions(rows)
    for values in rows_by_symbol(rows).values():
        for index in range(period, len(values) - 1):
            if (positions[values[index].trade_date] - positions[values[index - period].trade_date] != period
                    or positions[values[index + 1].trade_date] != positions[values[index].trade_date] + 1):
                continue
            output.append(_observation(values[index], values[index + 1], values[index].close / values[index - period].close - 1.0))
    return output


def _reversal(rows: list[PriceRow], lookback: int | None) -> list[Observation]:
    return [
        Observation(item.trade_date, item.symbol, -item.factor, item.forward_return)
        for item in _momentum(rows, lookback or 5)
    ]


def _volatility(rows: list[PriceRow], lookback: int | None) -> list[Observation]:
    period = lookback or 20
    output: list[Observation] = []
    positions = calendar_positions(rows)
    for values in rows_by_symbol(rows).values():
        for index in range(period, len(values) - 1):
            if (positions[values[index].trade_date] - positions[values[index - period].trade_date] != period
                    or positions[values[index + 1].trade_date] != positions[values[index].trade_date] + 1):
                continue
            daily_returns = [values[pos].close / values[pos - 1].close - 1.0 for pos in range(index - period + 1, index + 1)]
            output.append(_observation(values[index], values[index + 1], pstdev(daily_returns)))
    return output


def _rolling_field(rows: list[PriceRow], lookback: int | None, field: str) -> list[Observation]:
    period = lookback or 20
    output: list[Observation] = []
    found = False
    positions = calendar_positions(rows)
    for values in rows_by_symbol(rows).values():
        for index in range(period - 1, len(values) - 1):
            if (positions[values[index].trade_date] - positions[values[index - period + 1].trade_date] != period - 1
                    or positions[values[index + 1].trade_date] != positions[values[index].trade_date] + 1):
                continue
            window = [getattr(values[pos], field) for pos in range(index - period + 1, index + 1)]
            if any(value is None for value in window):
                continue
            found = True
            output.append(_observation(values[index], values[index + 1], fmean(window)))
    if not found:
        raise ValueError(f"dataset does not contain enough non-empty {field} values")
    return output


def _point_field(rows: list[PriceRow], _: int | None, field: str) -> list[Observation]:
    output: list[Observation] = []
    found = False
    positions = calendar_positions(rows)
    for values in rows_by_symbol(rows).values():
        for index in range(len(values) - 1):
            if positions[values[index + 1].trade_date] != positions[values[index].trade_date] + 1:
                continue
            value = getattr(values[index], field)
            if value is None:
                continue
            found = True
            output.append(_observation(values[index], values[index + 1], value))
    if not found:
        raise ValueError(f"dataset does not contain non-empty {field} values")
    return output


FACTOR_REGISTRY = {
    item.key: item
    for item in (
        FactorDefinition("momentum_20d", "20日动量", "price", "1.0.0", "close(t) / close(t-N) - 1", "衡量过去一段时间的累计涨跌幅。", ("close",), 20, _momentum),
        FactorDefinition("reversal_5d", "5日反转", "price", "1.0.0", "-(close(t) / close(t-N) - 1)", "用短期收益的相反数衡量价格反转。", ("close",), 5, _reversal),
        FactorDefinition("volatility_20d", "20日波动率", "risk", "1.0.0", "std(daily_return, N)", "衡量窗口内日收益率的总体标准差。", ("close",), 20, _volatility),
        FactorDefinition("turnover_20d", "20日平均换手率", "liquidity", "1.0.0", "mean(turnover_rate, N)", "衡量股票在窗口内的平均换手水平。", ("close", "turnover_rate"), 20, lambda rows, lookback: _rolling_field(rows, lookback, "turnover_rate")),
        FactorDefinition("market_cap", "总市值", "size", "1.0.0", "total_mv(t)", "使用当日总市值衡量公司规模。", ("close", "total_mv"), None, lambda rows, lookback: _point_field(rows, lookback, "total_mv")),
        FactorDefinition("pe", "市盈率", "valuation", "1.0.0", "pe(t)", "使用当日市盈率衡量估值水平。", ("close", "pe"), None, lambda rows, lookback: _point_field(rows, lookback, "pe")),
    )
}


def get_factor(key: str) -> FactorDefinition:
    try:
        return FACTOR_REGISTRY[key]
    except KeyError as exc:
        raise ValueError(f"unsupported factor: {key}") from exc


def calculate_factor(key: str, rows: list[PriceRow], lookback: int | None = None) -> list[Observation]:
    definition = get_factor(key)
    if lookback is not None and not 2 <= lookback <= 120:
        raise ValueError("lookback must be between 2 and 120")
    observations = definition.calculator(rows, lookback or definition.default_lookback)
    if not observations:
        raise ValueError("dataset does not have enough history for this factor")
    return observations
