"""Transparent multi-factor alignment and weighted composition."""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import fmean

from app.domain.research import Observation, pearson, preprocess_observations


def combine_factor_observations(
    components: dict[str, list[Observation]],
    weights: dict[str, float],
    *,
    winsorize: bool = True,
    standardize: bool = True,
    mad_scale: float = 3.0,
) -> tuple[list[Observation], dict]:
    if len(components) < 2:
        raise ValueError("composite research requires at least two factors")
    if set(components) != set(weights):
        raise ValueError("component factors and weights must match")
    if any(not math.isfinite(weight) or weight < 0 for weight in weights.values()):
        raise ValueError("factor weights must be finite and non-negative")
    total_weight = sum(weights.values())
    if not math.isfinite(total_weight) or total_weight <= 0:
        raise ValueError("factor weights must have a finite positive sum")
    for factor_key, values in components.items():
        for item in values:
            if not math.isfinite(item.factor) or not math.isfinite(item.forward_return):
                raise ValueError(f"non-finite factor observation: {factor_key} {item.trade_date} {item.symbol}")
    normalized_weights = {key: value / total_weight for key, value in weights.items()}
    processed = {
        key: preprocess_observations(
            values,
            winsorize=winsorize,
            standardize=standardize,
            mad_scale=mad_scale,
        )
        for key, values in components.items()
    }
    indexed = {}
    for factor_key, values in processed.items():
        by_key = {}
        for item in values:
            item_key = (item.trade_date, item.symbol)
            if item_key in by_key:
                raise ValueError(f"duplicate factor observation: {factor_key} {item.trade_date} {item.symbol}")
            by_key[item_key] = item
        indexed[factor_key] = by_key
    common_keys = set.intersection(*(set(values) for values in indexed.values()))
    if not common_keys:
        raise ValueError("selected factors have no common observations")
    ordered_keys = sorted(common_keys)
    factor_keys = list(components)

    combined: list[Observation] = []
    for item_key in ordered_keys:
        source = indexed[factor_keys[0]][item_key]
        if not math.isfinite(source.forward_return) or any(
            not math.isclose(indexed[key][item_key].forward_return, source.forward_return,
                             rel_tol=0, abs_tol=1e-12)
            for key in factor_keys[1:]
        ):
            raise ValueError(f"component forward returns disagree: {item_key[0]} {item_key[1]}")
        factor_value = sum(indexed[key][item_key].factor * normalized_weights[key] for key in indexed)
        if not math.isfinite(factor_value):
            raise ValueError(f"non-finite combined factor observation: {item_key[0]} {item_key[1]}")
        combined.append(Observation(source.trade_date, source.symbol, factor_value, source.forward_return))

    matrix: list[dict] = []
    for left in factor_keys:
        for right in factor_keys:
            daily_pairs: dict[object, list[tuple[float, float]]] = defaultdict(list)
            for trade_date, symbol in ordered_keys:
                daily_pairs[trade_date].append((indexed[left][(trade_date, symbol)].factor, indexed[right][(trade_date, symbol)].factor))
            correlations = []
            for pairs in daily_pairs.values():
                value = pearson([pair[0] for pair in pairs], [pair[1] for pair in pairs])
                if value is not None:
                    correlations.append(value)
            matrix.append({"left": left, "right": right, "correlation": fmean(correlations) if correlations else None})

    return combined, {
        "method": "weighted_sum",
        "weights": normalized_weights,
        "component_coverage": {key: len(values) for key, values in components.items()},
        "common_coverage": len(combined),
        "correlation_matrix": matrix,
        "component_preprocessing": {
            "winsorize": winsorize,
            "standardize": standardize,
            "method": "MAD" if winsorize else "none",
            "mad_scale": mad_scale if winsorize else None,
        },
    }
