"""Measure the PRD's 300-stock, three-trading-year single-factor workload.

The deterministic CSV is generated in a temporary directory. The timed section
starts at checksum verification and includes loading, factor calculation,
evaluation, and JSON artifact serialization. File generation is excluded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.domain.factors import calculate_factor  # noqa: E402
from app.domain.research import evaluate  # noqa: E402
from app.services.sample_data import load_price_file  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402
from app.db import Base  # noqa: E402
from app.models import RunStatus  # noqa: E402
from app.services.datasets import import_csv, publish_dataset_version  # noqa: E402
from app.services.reports import get_report  # noqa: E402
from app.services.runs import create_research_run, execute_research_run  # noqa: E402


def trading_dates(count: int) -> list[date]:
    output: list[date] = []
    current = date(2023, 1, 2)
    while len(output) < count:
        if current.weekday() < 5:
            output.append(current)
        current += timedelta(days=1)
    return output


def generate_csv(path: Path, symbols: int, days: int) -> str:
    dates = trading_dates(days)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination, lineterminator="\n")
        writer.writerow(("trade_date", "symbol", "close"))
        for symbol_index in range(symbols):
            close = 12.0 + symbol_index * 0.08
            symbol = f"PERF{symbol_index:04d}"
            for day_index, trade_date in enumerate(dates):
                daily_return = (symbol_index - symbols / 2) * 0.000008 + 0.006 * math.sin(day_index / 11 + symbol_index / 7)
                close *= 1 + daily_return
                writer.writerow((trade_date.isoformat(), symbol, f"{close:.6f}"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbols", type=int, default=300)
    parser.add_argument("--days", type=int, default=756, help="3 × 252 synthetic trading days")
    parser.add_argument("--limit-seconds", type=float, default=60)
    args = parser.parse_args()
    if args.symbols < 5 or args.days < 22 or args.limit_seconds <= 0:
        parser.error("symbols must be >= 5, days >= 22, and limit-seconds > 0")

    with tempfile.TemporaryDirectory(prefix="factorlab-benchmark-") as temporary:
        path = Path(temporary) / "daily_prices.csv"
        checksum = generate_csv(path, args.symbols, args.days)
        phases: dict[str, float] = {}
        started = perf_counter()
        rows = load_price_file(path, expected_checksum=checksum)
        phases["verify_and_load"] = perf_counter() - started
        started = perf_counter()
        observations = calculate_factor("momentum_20d", rows, 20)
        phases["factor"] = perf_counter() - started
        started = perf_counter()
        result = evaluate(observations, groups=5, transaction_cost_bps=10)
        phases["evaluate"] = perf_counter() - started
        started = perf_counter()
        artifact = json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")
        phases["serialize"] = perf_counter() - started

        os.environ["DATA_ROOT"] = str(Path(temporary) / "runtime")
        engine = create_engine(f"sqlite:///{Path(temporary) / 'benchmark.sqlite'}")
        Base.metadata.create_all(engine)
        try:
            with Session(engine, expire_on_commit=False) as session:
                ingest_started = perf_counter()
                dataset = import_csv(
                    session,
                    content=path.read_bytes(),
                    source_filename="benchmark.csv",
                    dataset_key="benchmark_prd",
                    name="PRD性能验收合成数据",
                    data_root=Path(temporary) / "runtime",
                )
                publish_dataset_version(session, dataset)
                ingest_seconds = perf_counter() - ingest_started
                run = create_research_run(session, {
                    "factor": "momentum_20d", "lookback": 20, "groups": 5,
                    "dataset_version_id": dataset.id, "transaction_cost_bps": 10,
                })
                run_started = perf_counter()
                completed = execute_research_run(session, run.id)
                full_run_seconds = perf_counter() - run_started
                report = get_report(session, completed.id)
                if completed.status != RunStatus.SUCCESS or report is None:
                    raise AssertionError("full research Run did not finish with an archived report")
                report_bytes = Path(report[1].storage_uri).stat().st_size
        finally:
            engine.dispose()

    elapsed = sum(phases.values())
    expected_coverage = args.symbols * (args.days - 21)
    if len(rows) != args.symbols * args.days or result["coverage"] != expected_coverage:
        raise AssertionError("benchmark input or observation count differs from the expected formula")
    print(f"platform={platform.platform()} python={platform.python_version()}")
    print(f"input={len(rows)} rows, {args.symbols} symbols, {args.days} weekdays; observations={result['coverage']}")
    print(" ".join(f"{name}={seconds:.3f}s" for name, seconds in phases.items()))
    print(f"calculation_total={elapsed:.3f}s ingest_excluded={ingest_seconds:.3f}s")
    print(f"full_run={full_run_seconds:.3f}s limit={args.limit_seconds:.1f}s json={len(artifact)} bytes report={report_bytes} bytes")
    if full_run_seconds > args.limit_seconds:
        raise SystemExit("PRD-scale single-factor benchmark exceeded the time limit")


if __name__ == "__main__":
    main()
