"""Independently compare one historical composite day with its private Run artifact.

Uses only source CSVs and the standard library; verify the sealed bundle and
artifact provenance separately before interpreting a passing comparison.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from datetime import date
from pathlib import Path
from statistics import fmean, median, pstdev

try:
    from tools.independent_hs300_spotcheck import spotcheck
except ModuleNotFoundError:  # Direct script invocation places tools/ on sys.path.
    from independent_hs300_spotcheck import spotcheck


FACTORS = ("momentum_20d", "reversal_5d", "volatility_20d", "turnover_20d")
INELIGIBLE = ("missing or non-trading window row:", "invalid window price or volume:",
              "invalid turnover:", "signal-day member is ST")


def _standardize(values: list[float]) -> list[float]:
    """MAD 3*1.4826 clipping and population z-score for one market day."""
    scale = max(map(abs, values))
    scaled = [value / scale for value in values] if scale else values[:]
    center = median(scaled)
    mad = median(abs(value - center) for value in scaled)
    if mad:
        radius = 3 * 1.4826 * mad
        scaled = [min(center + radius, max(center - radius, value)) for value in scaled]
    deviation = pstdev(scaled)
    if deviation:
        mean = fmean(scaled)
        return [(value - mean) / deviation for value in scaled]
    return values[:]


def verify(bundle_dir: Path, artifact_path: Path, signal_day: date,
           expected_artifact_sha256: str | None = None) -> dict:
    roster_path = bundle_dir / "members_source" / "daily_rosters" / f"{signal_day}.csv"
    with roster_path.open(newline="", encoding="utf-8") as handle:
        symbols = [row["code"] for row in csv.DictReader(handle)]
    if not symbols or len(symbols) != len(set(symbols)):
        raise ValueError("empty or duplicate daily roster")
    source: dict[str, dict] = {}
    skipped: dict[str, int] = {}
    for symbol in symbols:
        try:
            point = spotcheck(bundle_dir, signal_day, symbol)
        except ValueError as exc:
            if not str(exc).startswith(INELIGIBLE):
                raise
            reason = str(exc).split(":", 1)[0]
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        if point["forward_return"] is None:
            reason = point["label_reason"]
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        source[symbol] = point
    if len(source) < 2:
        raise ValueError("fewer than two independently valid observations")

    ordered = sorted(source)
    normalized = {}
    for key in FACTORS:
        daily = _standardize([source[symbol][key] for symbol in ordered])
        normalized[key] = dict(zip(ordered, daily))
    payload = artifact_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if expected_artifact_sha256 is not None and digest != expected_artifact_sha256:
        raise ValueError("observation artifact checksum mismatch")
    actual: dict[str, dict] = {}
    for line in gzip.decompress(payload).splitlines():
        item = json.loads(line)
        if item["date"] == signal_day.isoformat():
            symbol = item["symbol"]
            if symbol in actual:
                raise ValueError(f"duplicate artifact observation: {symbol}")
            actual[symbol] = item
    if set(actual) != set(source):
        raise ValueError(f"observation keys disagree: expected={len(source)} actual={len(actual)} "
                         f"missing={sorted(set(source)-set(actual))[:5]} extra={sorted(set(actual)-set(source))[:5]}")
    max_factor_error = max_return_error = 0.0
    for symbol in ordered:
        expected_factor = sum(normalized[key][symbol] for key in FACTORS) / len(FACTORS)
        factor_error = abs(float(actual[symbol]["factor"]) - expected_factor)
        return_error = abs(float(actual[symbol]["forward_return"]) - source[symbol]["forward_return"])
        if not math.isfinite(factor_error) or not math.isfinite(return_error) or factor_error > 1e-10 or return_error > 1e-12:
            raise ValueError(f"observation mismatch: {signal_day} {symbol} "
                             f"factor_error={factor_error} return_error={return_error}")
        max_factor_error = max(max_factor_error, factor_error)
        max_return_error = max(max_return_error, return_error)
    return {"signal_date": signal_day.isoformat(), "roster_count": len(symbols),
            "compared_count": len(source), "skipped": skipped,
            "max_factor_error": max_factor_error, "max_return_error": max_return_error,
            "artifact_sha256": digest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_dir", type=Path)
    parser.add_argument("artifact_path", type=Path)
    parser.add_argument("signal_date", type=date.fromisoformat)
    parser.add_argument("--artifact-sha256")
    args = parser.parse_args()
    try:
        result = verify(args.bundle_dir, args.artifact_path, args.signal_date, args.artifact_sha256)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(1, f"独立组合验算失败：{exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
