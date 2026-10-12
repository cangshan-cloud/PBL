"""Transparent multi-factor alignment and weighted composition."""

from __future__ import annotations

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
    if any(weight < 0 for weight in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("factor weights must be non-negative with a positive sum")

    total_weight = sum(weights.values())
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
    indexed = {
        key: {(item.trade_date, item.symbol): item for item in values}
        for key, values in processed.items()
    }
    common_keys = set.intersection(*(set(values) for values in indexed.values()))
    if not common_keys:
        raise ValueError("selected factors have no common observations")

    combined: list[Observation] = []
    for item_key in sorted(common_keys):
        source = next(iter(indexed.values()))[item_key]
        factor_value = sum(indexed[key][item_key].factor * normalized_weights[key] for key in indexed)
        combined.append(Observation(source.trade_date, source.symbol, factor_value, source.forward_return))

    factor_keys = list(components)
    matrix: list[dict] = []
    for left in factor_keys:
        for right in factor_keys:
            daily_pairs: dict[object, list[tuple[float, float]]] = defaultdict(list)
            for trade_date, symbol in common_keys:
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
