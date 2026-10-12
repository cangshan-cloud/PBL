"""Run a lightweight performance check against the bundled demo dataset."""

from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.domain.factors import FACTOR_REGISTRY, calculate_factor  # noqa: E402
from app.domain.research import evaluate  # noqa: E402
from app.services.sample_data import load_sample_prices  # noqa: E402


def main() -> None:
    load_started = perf_counter()
    rows = load_sample_prices()
    load_seconds = perf_counter() - load_started
    print(f"dataset: {len(rows)} rows, {len({row.symbol for row in rows})} symbols, load={load_seconds:.4f}s")

    total_started = perf_counter()
    for factor_key, definition in FACTOR_REGISTRY.items():
        started = perf_counter()
        observations = calculate_factor(factor_key, rows, definition.default_lookback)
        metrics = evaluate(observations, groups=5)
        elapsed = perf_counter() - started
        print(
            f"{factor_key}: coverage={metrics['coverage']}, "
            f"dates={len(metrics['ic_series'])}, elapsed={elapsed:.4f}s"
        )
    total_seconds = perf_counter() - total_started
    print(f"all six factors: {total_seconds:.4f}s")
    if total_seconds > 10:
        raise SystemExit("demo research performance exceeds the 10-second course-demo baseline")


if __name__ == "__main__":
    main()
