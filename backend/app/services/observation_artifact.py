"""Checksummed, private per-run observations for matched-sample diagnostics."""

from __future__ import annotations

import gzip
import hashlib
import json
from datetime import date
from math import isfinite
from pathlib import Path

from app.domain.research import Observation
from app.models import Artifact


def create_observation_artifact(run_id: str, observations: list[Observation], data_root: Path) -> Artifact:
    target = data_root / "artifacts" / run_id / "observations.jsonl.gz"
    target.parent.mkdir(parents=True, exist_ok=True)
    lines = (
        json.dumps({"date": item.trade_date.isoformat(), "symbol": item.symbol,
                    "factor": item.factor, "forward_return": item.forward_return},
                   ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        for item in sorted(observations, key=lambda value: (value.trade_date, value.symbol))
    )
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    compressed = gzip.compress(payload, mtime=0)
    target.write_bytes(compressed)
    return Artifact(artifact_type="observations", name="observations.jsonl.gz",
                    storage_uri=str(target), checksum=hashlib.sha256(compressed).hexdigest(),
                    content={"schema_version": 1, "count": len(observations)})


def read_observation_artifact(artifact: Artifact) -> dict[tuple[date, str], Observation]:
    if not artifact.storage_uri or not artifact.checksum or (artifact.content or {}).get("schema_version") != 1:
        raise ValueError("invalid observation artifact metadata")
    try:
        compressed = Path(artifact.storage_uri).read_bytes()
    except OSError as exc:
        raise ValueError("observation artifact unavailable") from exc
    if hashlib.sha256(compressed).hexdigest() != artifact.checksum:
        raise ValueError("observation artifact checksum mismatch")
    output: dict[tuple[date, str], Observation] = {}
    try:
        lines = gzip.decompress(compressed).splitlines()
    except (OSError, EOFError) as exc:
        raise ValueError("invalid observation artifact compression") from exc
    for line in lines:
        raw = json.loads(line)
        item = Observation(date.fromisoformat(raw["date"]), str(raw["symbol"]),
                           float(raw["factor"]), float(raw["forward_return"]))
        if not isfinite(item.factor) or not isfinite(item.forward_return):
            raise ValueError("non-finite observation artifact value")
        key = (item.trade_date, item.symbol)
        if key in output:
            raise ValueError("duplicate observation artifact key")
        output[key] = item
    if len(output) != (artifact.content or {}).get("count"):
        raise ValueError("observation artifact count mismatch")
    return output
