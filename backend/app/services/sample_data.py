from __future__ import annotations

import csv
import hashlib
import io
from datetime import date
from pathlib import Path

from app.domain.research import PriceRow


def sample_file() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "sample" / "daily_prices.csv"


def load_sample_prices() -> list[PriceRow]:
    return load_price_file(sample_file())


def load_price_file(path: Path, expected_checksum: str | None = None) -> list[PriceRow]:
    if not path.is_file():
        raise FileNotFoundError(f"dataset file not found: {path.name}")
    content = path.read_bytes()
    if expected_checksum is not None:
        digest = hashlib.sha256(content).hexdigest()
        if digest != expected_checksum:
            raise ValueError("dataset checksum mismatch")
    def optional_number(row: dict[str, str], column: str) -> float | None:
        value = (row.get(column) or "").strip()
        return float(value) if value else None

    return [
        PriceRow(
            date.fromisoformat(row["trade_date"]),
            row["symbol"],
            float(row["close"]),
            turnover_rate=optional_number(row, "turnover_rate"),
            total_mv=optional_number(row, "total_mv"),
            pe=optional_number(row, "pe"),
            adj_factor=optional_number(row, "adj_factor"),
        )
        for row in csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    ]
