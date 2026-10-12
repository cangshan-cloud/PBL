from dataclasses import replace
from math import isfinite

from app.domain.research import PriceRow


def apply_price_basis(rows: list[PriceRow], basis: str) -> list[PriceRow]:
    if basis == "source_close":
        return rows
    if basis != "factor_adjusted":
        raise ValueError("unsupported price_basis")
    output = []
    for row in rows:
        factor = row.adj_factor
        if factor is None or not isfinite(factor) or factor <= 0:
            raise ValueError(f"missing or invalid adj_factor: {row.symbol} {row.trade_date}")
        close = row.close * factor
        if not isfinite(close) or close <= 0:
            raise ValueError("adjusted close must be finite and positive")
        output.append(replace(row, close=close))
    return output
