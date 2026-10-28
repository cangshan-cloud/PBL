"""Independently audit historical group and long-short metrics from Run observations.

This read-only standard-library checker targets the fixed-cost historical mode.
It does not authenticate the original market data or model trading feasibility.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean


def _compare(actual: float | None, expected: float | None, label: str) -> float:
    if actual is None or expected is None:
        if actual is not expected:
            raise ValueError(f"{label} null mismatch")
        return 0.0
    difference = abs(float(actual) - expected)
    if not math.isfinite(difference) or difference > 1e-11:
        raise ValueError(f"{label} mismatch: actual={actual} expected={expected}")
    return difference


def _turnover(old: set[str] | None, new: set[str]) -> float:
    before = old or set()
    return sum(abs((1 / len(new) if symbol in new else 0.0) -
                   (1 / len(before) if symbol in before else 0.0))
               for symbol in before | new)


def _dated_rows(rows: list[dict], label: str) -> dict[str, dict]:
    if not isinstance(rows, list):
        raise ValueError(f"missing {label}")
    output = {}
    for row in rows:
        day = row["date"]
        if day in output:
            raise ValueError(f"duplicate {label} date: {day}")
        output[day] = row
    return output


def verify(artifact_path: Path, reproducibility_path: Path,
           expected_artifact_sha256: str | None = None, *, groups: int = 5) -> dict:
    if groups < 2:
        raise ValueError("groups must be at least two")
    payload = artifact_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if expected_artifact_sha256 is not None and digest != expected_artifact_sha256:
        raise ValueError("observation artifact checksum mismatch")
    document = json.loads(reproducibility_path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 2 or not isinstance(document.get("result"), dict):
        raise ValueError("expected completed V2 reproducibility result")
    result = document["result"]
    if result.get("transaction_cost_bps") != 10.0 or result.get("cost_model") != "equal_weight_target_traded_notional_v1":
        raise ValueError("historical cost model must be fixed at 10 bps")
    daily: dict[str, list[tuple[float, str, float]]] = defaultdict(list)
    seen = set()
    for line in gzip.decompress(payload).splitlines():
        row = json.loads(line)
        key = (row["date"], row["symbol"])
        if key in seen:
            raise ValueError(f"duplicate observation: {key}")
        seen.add(key)
        factor, forward = float(row["factor"]), float(row["forward_return"])
        if not math.isfinite(factor) or not math.isfinite(forward):
            raise ValueError(f"non-finite observation: {key}")
        daily[key[0]].append((factor, key[1], forward))
    if not seen or len(seen) != result.get("coverage"):
        raise ValueError("observation count disagrees with saved coverage")
    saved_groups = result.get("group_nav")
    if not isinstance(saved_groups, list) or len(saved_groups) != groups:
        raise ValueError("group NAV count mismatch")
    nav_by_group = {}
    for item in saved_groups:
        number = item["group"]
        if number in nav_by_group:
            raise ValueError(f"duplicate NAV group: {number}")
        nav_by_group[number] = _dated_rows(item["points"], f"group {number} NAV")
    if set(nav_by_group) != set(range(1, groups + 1)):
        raise ValueError("group NAV keys mismatch")
    saved_long_short = _dated_rows(result.get("long_short_series"), "long-short")
    nav = {number: 1.0 for number in nav_by_group}
    group_returns = defaultdict(list)
    gross_nav = net_nav = 1.0
    gross_returns, net_returns, top_turnovers, portfolio_turnovers = [], [], [], []
    previous_top: set[str] | None = None
    previous_bottom: set[str] | None = None
    max_error = 0.0
    for day in sorted(daily):
        ordered = sorted(daily[day])  # Factor then symbol; ties are deterministic.
        if len(ordered) < groups or ordered[0][0] == ordered[-1][0]:
            raise ValueError(f"unsupported insufficient or constant historical group day: {day}")
        buckets: dict[int, list[tuple[float, str, float]]] = defaultdict(list)
        for index, observation in enumerate(ordered):
            buckets[index * groups // len(ordered) + 1].append(observation)
        for number in range(1, groups + 1):
            mean = fmean(row[2] for row in buckets[number])
            group_returns[number].append(mean)
            nav[number] *= 1 + mean
            if day not in nav_by_group[number]:
                raise ValueError(f"missing group {number} NAV day: {day}")
            max_error = max(max_error, _compare(nav_by_group[number][day]["nav"], nav[number],
                                                f"{day} group {number} NAV"))
        top = {row[1] for row in buckets[groups]}
        bottom = {row[1] for row in buckets[1]}
        top_turnover = _turnover(previous_top, top)
        bottom_turnover = _turnover(previous_bottom, bottom)
        if previous_top is not None:
            top_turnovers.append(top_turnover / 2)
        turnover = top_turnover + bottom_turnover
        gross = group_returns[groups][-1] - group_returns[1][-1]
        cost = turnover * 10 / 10_000
        net = gross - cost
        gross_nav *= 1 + gross
        net_nav *= 1 + net
        gross_returns.append(gross)
        net_returns.append(net)
        portfolio_turnovers.append(turnover)
        if day not in saved_long_short:
            raise ValueError(f"missing long-short day: {day}")
        expected = {"return": gross, "nav": gross_nav, "turnover": turnover,
                    "cost": cost, "net_return": net, "net_nav": net_nav}
        for name, value in expected.items():
            max_error = max(max_error, _compare(saved_long_short[day][name], value,
                                                f"{day} long-short {name}"))
        previous_top, previous_bottom = top, bottom
    dates = set(daily)
    if set(saved_long_short) != dates or any(set(points) != dates for points in nav_by_group.values()):
        raise ValueError("saved group or long-short dates disagree with observations")
    saved_means = result.get("group_returns")
    if not isinstance(saved_means, list) or len(saved_means) != groups:
        raise ValueError("group mean count mismatch")
    means_by_group = {item["group"]: item["mean_return"] for item in saved_means}
    if len(means_by_group) != groups or set(means_by_group) != set(nav_by_group):
        raise ValueError("group mean keys mismatch")
    for number in nav_by_group:
        max_error = max(max_error, _compare(means_by_group[number], fmean(group_returns[number]),
                                            f"group {number} mean"))
    summary = {"long_short_mean": fmean(gross_returns), "long_short_total_return": gross_nav - 1,
               "long_short_net_mean": fmean(net_returns), "long_short_net_total_return": net_nav - 1,
               "long_short_turnover": fmean(portfolio_turnovers),
               "top_group_turnover": fmean(top_turnovers) if top_turnovers else None}
    for name, value in summary.items():
        max_error = max(max_error, _compare(result.get(name), value, name))
    return {"run_id": document.get("task", {}).get("id"), "observation_count": len(seen),
            "date_count": len(dates), "groups": groups, "max_absolute_error": max_error,
            "artifact_sha256": digest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_path", type=Path)
    parser.add_argument("reproducibility_json", type=Path)
    parser.add_argument("--artifact-sha256")
    parser.add_argument("--groups", type=int, default=5)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.artifact_path, args.reproducibility_json,
                                args.artifact_sha256, groups=args.groups), ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f"独立分组验算失败：{exc}\n")


if __name__ == "__main__":
    main()
