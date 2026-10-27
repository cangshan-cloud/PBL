"""Audit internal daily counts and series dates in a saved research result.

This checks arithmetic and alignment, not factor values or market-data provenance.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

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


def _dated_rows(value: object, label: str) -> tuple[list[dict], list[str]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) or not isinstance(row.get("date"), str)
                                          for row in value):
        raise ValueError(f"{label}: invalid dated series")
    dates = [row["date"] for row in value]
    if dates != sorted(set(dates)):
        raise ValueError(f"{label}: dates are not unique and ordered")
    return value, dates


def verify_result_consistency(bundle_path: Path) -> dict[str, int]:
    result = load_verified_export(bundle_path)["result"]
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
    if long_short_dates != expected_group_dates:
        raise ValueError("long_short_series: dates differ from valid group dates")
    groups = result.get("group_nav")
    if not isinstance(groups, list):
        raise ValueError("group_nav: missing groups")
    group_ids = []
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("group_nav: invalid group")
        group_ids.append(group.get("group"))
        _, dates = _dated_rows(group.get("points"), "group_nav.points")
        if dates != expected_group_dates:
            raise ValueError("group_nav: dates differ from valid group dates")
    if group_ids != list(range(1, len(groups) + 1)):
        raise ValueError("group_nav: group IDs are not sequential")
    if expected_group_dates and len(groups) < 2:
        raise ValueError("group_nav: valid group dates require at least two groups")
    for row in daily:
        if row["group_status"] == "valid" and row["eligible_symbols"] < len(groups):
            raise ValueError(f"{row['date']}: valid group has too few observations")
        if row["group_status"] == "constant_factor" and ic_by_date[row["date"]].get("ic") is not None:
            raise ValueError(f"{row['date']}: constant factor cannot have valid IC")

    gross_nav = net_nav = 1.0
    cost_bps = _number(result.get("transaction_cost_bps"), "transaction_cost_bps")
    for row in long_short:
        day = row["date"]
        gross_return = _number(row.get("return"), f"{day}.return")
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
    return {"daily_dates": len(daily_dates), "ic_dates": len(ic_dates),
            "group_dates": len(expected_group_dates), "eligible_observations": eligible_total}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reproducibility_json", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify_result_consistency(args.reproducibility_json), ensure_ascii=False))
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.exit(1, f"research result consistency failed: {exc}\n")


if __name__ == "__main__":
    main()
