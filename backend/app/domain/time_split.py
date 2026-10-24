"""Chronological, boundary-embargoed IC diagnostics for a predeclared cutoff."""

from __future__ import annotations

from datetime import date

from app.domain.research import Observation, evaluate


def evaluate_time_split(
    observations: list[Observation], validation_start_date: str, *, groups: int,
    winsorize: bool, standardize: bool, mad_scale: float,
) -> dict:
    cutoff = date.fromisoformat(validation_start_date)
    dates = sorted({item.trade_date for item in observations})
    earlier = [day for day in dates if day < cutoff]
    later = [day for day in dates if day >= cutoff]
    if len(earlier) < 3 or len(later) < 2:
        raise ValueError("time split requires at least 3 research and 2 validation signal dates")
    # A research signal on the immediately preceding observed market date may
    # use the first validation day's return as its t+1 label. Remove it.
    embargo_date = earlier[-1]
    research = [item for item in observations if item.trade_date < embargo_date]
    validation = [item for item in observations if item.trade_date >= cutoff]

    def summary(items: list[Observation]) -> dict:
        result = evaluate(items, groups, winsorize=winsorize,
                          standardize=standardize, mad_scale=mad_scale,
                          transaction_cost_bps=0)
        return {
            "start_date": min(item.trade_date for item in items).isoformat(),
            "end_date": max(item.trade_date for item in items).isoformat(),
            "observation_count": result["coverage"],
            "signal_date_count": len({item.trade_date for item in items}),
            "valid_ic_dates": sum(point["ic"] is not None for point in result["ic_series"]),
            "ic_mean": result["ic_mean"],
            "rank_ic_mean": result["rank_ic_mean"],
            "icir": result["icir"],
            "ic_positive_ratio": result["ic_positive_ratio"],
        }

    return {"validation_start_date": cutoff.isoformat(),
            "embargo_signal_date": embargo_date.isoformat(),
            "research": summary(research), "validation": summary(validation),
            "interpretation": "retrospective_chronological_diagnostic_not_prospective_proof"}
