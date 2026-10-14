"""Compare research output with hand-calculated constants for a fixed tiny CSV."""

from __future__ import annotations

import csv
import math
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.domain.prices import apply_price_basis  # noqa: E402
from app.domain.research import PriceRow, evaluate, momentum_observations  # noqa: E402


def check(name: str, actual: float | int | None, expected: float) -> None:
    if actual is None or not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-10):
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def main() -> None:
    with (ROOT / "data" / "golden" / "daily_prices.csv").open(encoding="utf-8", newline="") as source:
        rows = [
            PriceRow(
                date.fromisoformat(item["trade_date"]),
                item["symbol"],
                float(item["close"]),
                adj_factor=float(item["adj_factor"]),
            )
            for item in csv.DictReader(source)
        ]
    observations = momentum_observations(apply_price_basis(rows, "factor_adjusted"), lookback=1)
    if len(observations) != 6:
        raise AssertionError(f"coverage: expected 6 observations, got {len(observations)}")
    by_key = {(item.trade_date.isoformat(), item.symbol): item for item in observations}
    check("C 2025-01-03 momentum", by_key[("2025-01-03", "C")].factor, -0.1)
    check("C 2025-01-03 forward return", by_key[("2025-01-03", "C")].forward_return, -0.1)
    check("C 2025-01-06 momentum", by_key[("2025-01-06", "C")].factor, -0.1)
    check("A 2025-01-06 forward return", by_key[("2025-01-06", "A")].forward_return, 0.1)

    result = evaluate(observations, groups=3, winsorize=False, standardize=False, transaction_cost_bps=10)
    for field, expected in {
        "coverage": 6,
        "ic_mean": 1,
        "rank_ic_mean": 1,
        "ic_positive_ratio": 1,
        "long_short_mean": 0.2,
        "long_short_total_return": 0.44,
        "long_short_net_total_return": 0.4376,
        "top_group_turnover": 0,
    }.items():
        check(field, result[field], expected)
    if result["icir"] is not None:
        raise AssertionError("icir: expected null because IC variance is zero")
    for group, expected in ((1, -0.1), (2, 0), (3, 0.1)):
        check(f"Q{group} mean", result["group_returns"][group - 1]["mean_return"], expected)
    check("first entry cost", result["long_short_series"][0]["cost"], 0.002)
    check("second day cost", result["long_short_series"][1]["cost"], 0)
    print("Golden research verification passed: 6 observations, IC/Rank IC, group returns, "
          "gross/net long-short returns, and transaction costs match hand-calculated values.")


if __name__ == "__main__":
    main()
