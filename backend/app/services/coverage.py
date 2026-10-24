"""Join evaluated observations to the selected market-day candidate universe."""

from __future__ import annotations

from datetime import date


def enrich_daily_coverage(result: dict, market_dates: list[date], candidate_counts: dict[date, int]) -> None:
    existing = {date.fromisoformat(item["date"]): item for item in result.get("daily_coverage", [])}
    enriched: list[dict] = []
    for day in sorted(set(market_dates)):
        candidates = candidate_counts.get(day, 0)
        if candidates < 0:
            raise ValueError("negative candidate count")
        row = dict(existing.pop(day, {"date": day.isoformat(), "eligible_symbols": 0,
                                      "ic_status": "no_observation", "group_status": "no_observation"}))
        eligible = row["eligible_symbols"]
        if eligible > candidates:
            raise ValueError(f"eligible observations exceed candidates: {day}")
        row["candidate_symbols"] = candidates
        row["excluded_symbols"] = candidates - eligible
        row["coverage_ratio"] = eligible / candidates if candidates else None
        enriched.append(row)
    if existing:
        raise ValueError("research observations outside candidate market dates")
    if sum(item["eligible_symbols"] for item in enriched) != result["coverage"]:
        raise ValueError("daily coverage does not reconcile to total observations")
    result["daily_coverage"] = enriched
    result["zero_observation_days"] = sum(item["eligible_symbols"] == 0 for item in enriched)
    total_candidates = sum(item["candidate_symbols"] for item in enriched)
    result["candidate_coverage"] = total_candidates
    result["coverage_ratio"] = result["coverage"] / total_candidates if total_candidates else None
