"""Independently check saved daily IC and summary from a private Run observation artifact.

This does not authenticate the original market data or the observation artifact.
Use the V2 reproducibility checker and an explicit artifact digest separately.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import fmean, pstdev


def _pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) < 2 or len(left) != len(right):
        return None
    xmean, ymean = fmean(left), fmean(right)
    x = [value - xmean for value in left]
    y = [value - ymean for value in right]
    denominator = math.sqrt(math.fsum(value * value for value in x) *
                            math.fsum(value * value for value in y))
    if denominator == 0:
        return None
    return math.fsum(a * b for a, b in zip(x, y)) / denominator


def _ranks(values: list[float]) -> list[float]:
    result = [0.0] * len(values)
    order = sorted(range(len(values)), key=lambda index: values[index])
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for index in order[start:end]:
            result[index] = rank
        start = end
    return result


def _equal(actual: float | None, expected: float | None, label: str, tolerance: float = 1e-12) -> float:
    if actual is None or expected is None:
        if actual is not expected:
            raise ValueError(f"{label} null mismatch: actual={actual} expected={expected}")
        return 0.0
    difference = abs(float(actual) - expected)
    if not math.isfinite(difference) or difference > tolerance:
        raise ValueError(f"{label} mismatch: actual={actual} expected={expected} difference={difference}")
    return difference


def verify(artifact_path: Path, reproducibility_path: Path,
           expected_artifact_sha256: str | None = None) -> dict:
    payload = artifact_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if expected_artifact_sha256 is not None and digest != expected_artifact_sha256:
        raise ValueError("observation artifact checksum mismatch")
    document = json.loads(reproducibility_path.read_text(encoding="utf-8"))
    if document.get("schema_version") != 2 or not isinstance(document.get("result"), dict):
        raise ValueError("expected completed V2 reproducibility result")
    result = document["result"]
    by_date: dict[str, list[tuple[str, float, float]]] = defaultdict(list)
    keys: set[tuple[str, str]] = set()
    for line in gzip.decompress(payload).splitlines():
        row = json.loads(line)
        day, symbol = row["date"], row["symbol"]
        key = (day, symbol)
        if key in keys:
            raise ValueError(f"duplicate observation: {day} {symbol}")
        keys.add(key)
        factor, forward = float(row["factor"]), float(row["forward_return"])
        if not math.isfinite(factor) or not math.isfinite(forward):
            raise ValueError(f"non-finite observation: {day} {symbol}")
        by_date[day].append((symbol, factor, forward))
    if not keys or len(keys) != result.get("coverage"):
        raise ValueError("observation count disagrees with saved coverage")
    saved_series = result.get("ic_series")
    if not isinstance(saved_series, list):
        raise ValueError("missing saved IC series")
    saved = {}
    for row in saved_series:
        day = row["date"]
        if day in saved:
            raise ValueError(f"duplicate saved IC date: {day}")
        saved[day] = row
    if set(saved) != set(by_date):
        raise ValueError("saved IC dates disagree with observations")
    ic_values: list[float] = []
    rank_values: list[float] = []
    max_error = 0.0
    for day in sorted(by_date):
        daily = sorted(by_date[day])
        factors = [item[1] for item in daily]
        forwards = [item[2] for item in daily]
        ic = _pearson(factors, forwards)
        rank_ic = _pearson(_ranks(factors), _ranks(forwards))
        max_error = max(max_error, _equal(saved[day]["ic"], ic, f"{day} IC"),
                        _equal(saved[day]["rank_ic"], rank_ic, f"{day} Rank IC"))
        if ic is not None:
            ic_values.append(ic)
        if rank_ic is not None:
            rank_values.append(rank_ic)
    ic_mean = fmean(ic_values) if ic_values else None
    ic_std = (0.0 if max(ic_values) - min(ic_values) <= 1e-12 else pstdev(ic_values)) if len(ic_values) > 1 else None
    summary = {
        "ic_mean": ic_mean, "ic_std": ic_std,
        "rank_ic_mean": fmean(rank_values) if rank_values else None,
        "icir": ic_mean / ic_std if ic_mean is not None and ic_std else None,
        "ic_positive_ratio": sum(value > 0 for value in ic_values) / len(ic_values) if ic_values else None,
    }
    for name, expected in summary.items():
        max_error = max(max_error, _equal(result.get(name), expected, name))
    return {"run_id": document.get("task", {}).get("id"), "observation_count": len(keys),
            "date_count": len(by_date), "valid_ic_dates": len(ic_values),
            "max_absolute_error": max_error, "artifact_sha256": digest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_path", type=Path)
    parser.add_argument("reproducibility_json", type=Path)
    parser.add_argument("--artifact-sha256")
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.artifact_path, args.reproducibility_json,
                                args.artifact_sha256), ensure_ascii=False, indent=2))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, f"独立 IC 验算失败：{exc}\n")


if __name__ == "__main__":
    main()
