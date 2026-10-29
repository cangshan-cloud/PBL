"""Audit internal daily counts and series dates in a saved research result.

This checks arithmetic and alignment, not factor values or market-data provenance.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path
from statistics import fmean, pstdev

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_reproducibility_export import load_verified_export


def _integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label}: expected nonnegative integer")
    return value


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label}: expected finite number")
    return float(value)


def _close(actual: object, expected: float, label: str) -> None:
    if not math.isclose(_number(actual, label), expected, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError(f"{label}: arithmetic mismatch")


def _optional_close(actual: object, expected: float | None, label: str) -> None:
    if expected is None:
        if actual is not None:
            raise ValueError(f"{label}: expected null")
    else:
        _close(actual, expected, label)


def _dated_rows(value: object, label: str) -> tuple[list[dict], list[str]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) or not isinstance(row.get("date"), str)
                                          for row in value):
        raise ValueError(f"{label}: invalid dated series")
    dates = [row["date"] for row in value]
    if dates != sorted(set(dates)):
        raise ValueError(f"{label}: dates are not unique and ordered")
    return value, dates


def _verify_ic_histogram(value: object, valid_ic: list[float]) -> None:
    """Check the ten fixed IC bins without invoking the research engine."""
    if not isinstance(value, list) or len(value) != 10 or any(not isinstance(row, dict) for row in value):
        raise ValueError("ic_histogram: expected ten bins")
    counts = [0] * 10
    for ic in valid_ic:
        if not -1 <= ic <= 1:
            raise ValueError("ic_series: IC outside correlation range")
        index = min(9, max(0, int((ic + 1.0) * 5 + 1e-12)))
        counts[index] += 1
    for index, row in enumerate(value):
        if set(row) != {"lower", "upper", "count"}:
            raise ValueError(f"ic_histogram[{index}]: unexpected fields")
        _close(row["lower"], round(-1 + index * 0.2, 1), f"ic_histogram[{index}].lower")
        _close(row["upper"], round(-0.8 + index * 0.2, 1), f"ic_histogram[{index}].upper")
        if _integer(row["count"], f"ic_histogram[{index}].count") != counts[index]:
            raise ValueError(f"ic_histogram[{index}].count: differs from daily IC series")


def _verify_component_ic_daily(result: dict, coverage_rows: list[dict]) -> dict[str, int]:
    composite = result.get("composite")
    if not isinstance(composite, dict) or not isinstance(composite.get("component_ic"), list):
        return {}
    components = composite["component_ic"]
    if not components or not any(isinstance(row, dict) and "daily" in row for row in components):
        return {}
    expected = {row["date"]: _integer(row.get("eligible_symbols"), f"{row['date']}.eligible_symbols")
                for row in coverage_rows if row.get("eligible_symbols", 0) > 0}
    factors: set[str] = set()
    for component in components:
        if not isinstance(component, dict) or not isinstance(component.get("factor"), str) or not component["factor"]:
            raise ValueError("component_ic: invalid factor")
        factor = component["factor"]
        if factor in factors:
            raise ValueError("component_ic: duplicate factor")
        factors.add(factor)
        daily, dates = _dated_rows(component.get("daily"), f"component_ic.{factor}.daily")
        if dates != list(expected):
            raise ValueError(f"component_ic.{factor}.daily: dates differ from common signal dates")
        values: list[float] = []
        ranks: list[float] = []
        for point in daily:
            day = point["date"]
            if _integer(point.get("observations"), f"component_ic.{factor}.{day}.observations") != expected[day]:
                raise ValueError(f"component_ic.{factor}.{day}.observations: differs from common coverage")
            for field, target in (("ic", values), ("rank_ic", ranks)):
                value = point.get(field)
                if value is not None:
                    measured = _number(value, f"component_ic.{factor}.{day}.{field}")
                    if not -1 <= measured <= 1 or expected[day] < 2:
                        raise ValueError(f"component_ic.{factor}.{day}.{field}: invalid correlation")
                    target.append(measured)
        if _integer(component.get("signal_date_count"), f"component_ic.{factor}.signal_date_count") != len(daily):
            raise ValueError(f"component_ic.{factor}.signal_date_count: differs from daily series")
        if _integer(component.get("valid_ic_dates"), f"component_ic.{factor}.valid_ic_dates") != len(values):
            raise ValueError(f"component_ic.{factor}.valid_ic_dates: differs from daily series")
        _optional_close(component.get("ic_mean"), fmean(values) if values else None, f"component_ic.{factor}.ic_mean")
        _optional_close(component.get("rank_ic_mean"), fmean(ranks) if ranks else None, f"component_ic.{factor}.rank_ic_mean")
    return {"component_ic_factors": len(factors), "component_ic_dates": len(expected)}


def verify_time_split_consistency(result: dict) -> dict[str, int]:
    """Reconcile saved split summaries with the full-range daily IC and coverage rows."""
    split = result.get("time_split")
    if not isinstance(split, dict):
        raise ValueError("time_split: missing split summary")
    daily, _ = _dated_rows(result.get("daily_coverage"), "daily_coverage")
    ic, _ = _dated_rows(result.get("ic_series"), "ic_series")
    ic_by_date = {row["date"]: row for row in ic}
    cutoff = split.get("validation_start_date")
    if not isinstance(cutoff, str):
        raise ValueError("time_split: missing validation start")
    try:
        if date.fromisoformat(cutoff).isoformat() != cutoff:
            raise ValueError("noncanonical date")
    except ValueError as exc:
        raise ValueError("time_split: invalid validation start date") from exc
    signal_dates = [row["date"] for row in daily if _integer(row.get("eligible_symbols"), "eligible_symbols") > 0]
    if any(row["eligible_symbols"] >= 2 and row["date"] not in ic_by_date for row in daily):
        raise ValueError("time_split: eligible cross-section has no IC point")
    earlier = [day for day in signal_dates if day < cutoff]
    later = [day for day in signal_dates if day >= cutoff]
    if len(earlier) < 3 or len(later) < 2:
        raise ValueError("time_split: insufficient signal dates")
    embargo = earlier[-1]
    if split.get("embargo_signal_date") != embargo:
        raise ValueError("time_split: embargo date differs from last pre-cutoff signal")
    if split.get("interpretation") != "retrospective_chronological_diagnostic_not_prospective_proof":
        raise ValueError("time_split: interpretation differs from research rule")

    summary = {}
    for name, dates in (("research", earlier[:-1]), ("validation", later)):
        saved = split.get(name)
        if not isinstance(saved, dict):
            raise ValueError(f"time_split.{name}: missing summary")
        selected = set(dates)
        if saved.get("start_date") != dates[0] or saved.get("end_date") != dates[-1]:
            raise ValueError(f"time_split.{name}: date bounds differ")
        count = sum(row["eligible_symbols"] for row in daily if row["date"] in selected)
        for field, expected in (("observation_count", count), ("signal_date_count", len(dates))):
            if _integer(saved.get(field), f"time_split.{name}.{field}") != expected:
                raise ValueError(f"time_split.{name}.{field}: count differs")
        points = [ic_by_date[day] for day in dates if day in ic_by_date]
        values = [_number(point["ic"], f"{point['date']}.ic") for point in points if point["ic"] is not None]
        ranks = [_number(point["rank_ic"], f"{point['date']}.rank_ic")
                 for point in points if point["rank_ic"] is not None]
        if _integer(saved.get("valid_ic_dates"), f"time_split.{name}.valid_ic_dates") != len(values):
            raise ValueError(f"time_split.{name}.valid_ic_dates: count differs")
        mean = fmean(values) if values else None
        deviation = (0.0 if max(values) - min(values) <= 1e-12 else pstdev(values)) if len(values) > 1 else None
        derived = {"ic_mean": mean, "rank_ic_mean": fmean(ranks) if ranks else None,
                   "icir": mean / deviation if mean is not None and deviation else None,
                   "ic_positive_ratio": sum(value > 0 for value in values) / len(values) if values else None}
        for field, expected in derived.items():
            actual = saved.get(field)
            if expected is None:
                if actual is not None:
                    raise ValueError(f"time_split.{name}.{field}: expected null")
            else:
                _close(actual, expected, f"time_split.{name}.{field}")
        summary[f"{name}_signal_dates"] = len(dates)
        summary[f"{name}_valid_ic_dates"] = len(values)
    return summary


def verify_result_consistency(bundle_path: Path, *, require_v2: bool = False) -> dict[str, int]:
    bundle = load_verified_export(bundle_path, require_v2=require_v2)
    result = bundle["result"]
    daily, daily_dates = _dated_rows(result.get("daily_coverage"), "daily_coverage")
    ic, ic_dates = _dated_rows(result.get("ic_series"), "ic_series")
    long_short, long_short_dates = _dated_rows(result.get("long_short_series"), "long_short_series")
    expected_ic_dates: list[str] = []
    expected_group_dates: list[str] = []
    ic_by_date = {row["date"]: row for row in ic}
    candidate_total = eligible_total = zero_days = 0
    for row in daily:
        day = row["date"]
        candidates = _integer(row.get("candidate_symbols"), f"{day}.candidate_symbols")
        eligible = _integer(row.get("eligible_symbols"), f"{day}.eligible_symbols")
        excluded = _integer(row.get("excluded_symbols"), f"{day}.excluded_symbols")
        if candidates != eligible + excluded:
            raise ValueError(f"{day}: candidate/eligible/excluded counts differ")
        ratio = row.get("coverage_ratio")
        if candidates:
            _close(ratio, eligible / candidates, f"{day}.coverage_ratio")
        elif ratio is not None:
            raise ValueError(f"{day}.coverage_ratio: expected null for zero candidates")
        candidate_total += candidates
        eligible_total += eligible
        zero_days += eligible == 0

        ic_status = row.get("ic_status")
        group_status = row.get("group_status")
        if eligible == 0:
            expected_ic, expected_group = "no_observation", "no_observation"
        elif eligible == 1:
            expected_ic, expected_group = "insufficient_sample", "insufficient_sample"
        else:
            expected_ic_dates.append(day)
            point = ic_by_date.get(day)
            if point is None:
                raise ValueError(f"{day}: missing IC point for eligible cross-section")
            expected_ic = "valid" if point.get("ic") is not None else "constant_factor_or_return"
            if point.get("ic") is not None:
                _number(point["ic"], f"{day}.ic")
            if point.get("rank_ic") is not None:
                _number(point["rank_ic"], f"{day}.rank_ic")
            if group_status not in {"valid", "constant_factor", "insufficient_sample"}:
                raise ValueError(f"{day}.group_status: invalid for eligible cross-section")
            expected_group = group_status
            if group_status == "valid":
                expected_group_dates.append(day)
        if ic_status != expected_ic or group_status != expected_group:
            raise ValueError(f"{day}: IC/group status conflicts with eligible observations or IC point")

    if ic_dates != expected_ic_dates:
        raise ValueError("ic_series: dates differ from eligible cross-sections")
    valid_ic = [point["ic"] for point in ic if point["ic"] is not None]
    valid_rank_ic = [point["rank_ic"] for point in ic if point["rank_ic"] is not None]
    ic_mean = fmean(valid_ic) if valid_ic else None
    ic_std = (0.0 if max(valid_ic) - min(valid_ic) <= 1e-12 else pstdev(valid_ic)) if len(valid_ic) > 1 else None
    for field, expected in (
        ("ic_mean", ic_mean), ("ic_std", ic_std),
        ("rank_ic_mean", fmean(valid_rank_ic) if valid_rank_ic else None),
        ("icir", ic_mean / ic_std if ic_mean is not None and ic_std else None),
        ("ic_positive_ratio", sum(value > 0 for value in valid_ic) / len(valid_ic) if valid_ic else None),
    ):
        _optional_close(result.get(field), expected, field)
    _verify_ic_histogram(result.get("ic_histogram"), valid_ic)
    if long_short_dates != expected_group_dates:
        raise ValueError("long_short_series: dates differ from valid group dates")
    groups = result.get("group_nav")
    if not isinstance(groups, list):
        raise ValueError("group_nav: missing groups")
    group_ids = []
    group_daily_returns: dict[int, list[float | None]] = {}
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("group_nav: invalid group")
        group_ids.append(group.get("group"))
        _, dates = _dated_rows(group.get("points"), "group_nav.points")
        if dates != expected_group_dates:
            raise ValueError("group_nav: dates differ from valid group dates")
        previous_nav = 1.0
        daily_returns: list[float | None] = []
        for point in group["points"]:
            nav = _number(point.get("nav"), f"group_nav.{group['group']}.{point['date']}.nav")
            if previous_nav == 0:
                if nav != 0:
                    raise ValueError("group_nav: zero NAV cannot recover to a nonzero value")
                daily_returns.append(None)
            else:
                daily_returns.append(nav / previous_nav - 1.0)
            previous_nav = nav
        group_daily_returns[group["group"]] = daily_returns
    if group_ids != list(range(1, len(groups) + 1)):
        raise ValueError("group_nav: group IDs are not sequential")
    if expected_group_dates and len(groups) < 2:
        raise ValueError("group_nav: valid group dates require at least two groups")
    saved_group_returns = result.get("group_returns")
    if not isinstance(saved_group_returns, list) or any(not isinstance(item, dict) for item in saved_group_returns):
        raise ValueError("group_returns: invalid summary")
    expected_return_groups = group_ids if expected_group_dates else []
    if [item.get("group") for item in saved_group_returns] != expected_return_groups:
        raise ValueError("group_returns: group IDs differ from NAV series")
    for item in saved_group_returns:
        derived = group_daily_returns[item["group"]]
        if all(value is not None for value in derived):
            _close(item.get("mean_return"), fmean(derived), f"group_returns.{item['group']}.mean_return")
    for row in daily:
        if row["group_status"] == "valid" and row["eligible_symbols"] < len(groups):
            raise ValueError(f"{row['date']}: valid group has too few observations")
        if row["group_status"] == "constant_factor" and ic_by_date[row["date"]].get("ic") is not None:
            raise ValueError(f"{row['date']}: constant factor cannot have valid IC")

    gross_nav = net_nav = 1.0
    cost_bps = _number(result.get("transaction_cost_bps"), "transaction_cost_bps")
    group_return_dates_checked = 0
    for index, row in enumerate(long_short):
        day = row["date"]
        gross_return = _number(row.get("return"), f"{day}.return")
        if group_ids:
            bottom = group_daily_returns[1][index]
            top = group_daily_returns[len(groups)][index]
            if bottom is not None and top is not None:
                _close(gross_return, top - bottom, f"{day}.long_short_group_return")
                group_return_dates_checked += 1
        turnover = _number(row.get("turnover"), f"{day}.turnover")
        if turnover < 0 or cost_bps < 0:
            raise ValueError(f"{day}: negative turnover or transaction cost")
        cost = turnover * cost_bps / 10_000
        _close(row.get("cost"), cost, f"{day}.cost")
        net_return = gross_return - cost
        _close(row.get("net_return"), net_return, f"{day}.net_return")
        gross_nav *= 1 + gross_return
        net_nav *= 1 + net_return
        _close(row.get("nav"), gross_nav, f"{day}.nav")
        _close(row.get("net_nav"), net_nav, f"{day}.net_nav")
    gross_returns = [row["return"] for row in long_short]
    net_returns = [row["net_return"] for row in long_short]
    turnovers = [row["turnover"] for row in long_short]
    for field, expected in (
        ("long_short_mean", fmean(gross_returns) if gross_returns else None),
        ("long_short_net_mean", fmean(net_returns) if net_returns else None),
        ("long_short_total_return", gross_nav - 1.0 if long_short else None),
        ("long_short_net_total_return", net_nav - 1.0 if long_short else None),
        ("long_short_turnover", fmean(turnovers) if turnovers else None),
    ):
        _optional_close(result.get(field), expected, field)

    for field, expected in (("candidate_coverage", candidate_total), ("coverage", eligible_total),
                            ("zero_observation_days", zero_days),
                            ("group_skipped_constant_factor_days", sum(row["group_status"] == "constant_factor" for row in daily)),
                            ("group_skipped_insufficient_sample_days", sum(row["group_status"] == "insufficient_sample" for row in daily))):
        if _integer(result.get(field), field) != expected:
            raise ValueError(f"{field}: aggregate differs from daily coverage")
    if candidate_total:
        _close(result.get("coverage_ratio"), eligible_total / candidate_total, "coverage_ratio")
    elif result.get("coverage_ratio") is not None:
        raise ValueError("coverage_ratio: expected null for zero candidates")
    summary = {"daily_dates": len(daily_dates), "ic_dates": len(ic_dates),
               "group_dates": len(expected_group_dates), "eligible_observations": eligible_total,
               "group_return_dates_checked": group_return_dates_checked,
               "histogram_ic_count": len(valid_ic)}
    summary.update(_verify_component_ic_daily(result, daily))
    task = bundle.get("task")
    parameters = task.get("parameters") if isinstance(task, dict) else None
    declared_cutoff = parameters.get("validation_start_date") if isinstance(parameters, dict) else None
    if "time_split" in result:
        if not isinstance(result["time_split"], dict) or declared_cutoff != result["time_split"].get("validation_start_date"):
            raise ValueError("time_split: cutoff differs from declared task parameter")
        summary.update(verify_time_split_consistency(result))
    elif declared_cutoff is not None:
        raise ValueError("time_split: declared task cutoff has no saved split summary")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reproducibility_json", type=Path)
    parser.add_argument("--require-v2", action="store_true", help="Reject legacy V1 bundles")
    args = parser.parse_args()
    try:
        print(json.dumps(verify_result_consistency(args.reproducibility_json,
                                                   require_v2=args.require_v2), ensure_ascii=False))
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.exit(1, f"research result consistency failed: {exc}\n")


if __name__ == "__main__":
    main()
