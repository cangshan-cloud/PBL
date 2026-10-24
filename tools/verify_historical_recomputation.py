"""Read-only replay of a historical export against the local sealed CSI 300 bundle.

This uses the current research engine, so it verifies reproducibility against
current code and source bytes, not independent factor-formula correctness.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.domain.composite import combine_factor_observations
from app.domain.historical_research import FACTOR_WINDOWS, calculate_historical_observations, load_historical_bundle
from app.domain.research import evaluate
from app.services.coverage import enrich_daily_coverage
from tools.verify_reproducibility_export import verify_export


def recompute_result(manifest_path: Path, manifest_checksum: str, groups: int) -> dict:
    calendar, members, bars = load_historical_bundle(manifest_path, manifest_checksum)
    components = {}
    audit = {}
    for key in FACTOR_WINDOWS:
        components[key], audit[key] = calculate_historical_observations(calendar, members, bars, key)
    observations, diagnostics = combine_factor_observations(
        components, {key: 0.25 for key in FACTOR_WINDOWS},
    )
    result = evaluate(observations, groups, winsorize=False,
                      standardize=False, transaction_cost_bps=10.0)
    enrich_daily_coverage(result, sorted(members), {day: len(codes) for day, codes in members.items()})
    result["composite"] = diagnostics
    result["preprocessing"] = diagnostics["component_preprocessing"]
    result["historical_audit"] = audit
    result["sample"] = {
        "price_basis": "source_close", "start_date": "2024-01-01",
        "end_date": "2024-12-31", "resolved_symbol_count": len(bars),
        "historical_bundle_id": manifest_path.parent.name,
        "interpretation": "conditional_research_not_executable_trading",
    }
    return result


def _same_result(left: object, right: object) -> bool:
    if type(left) is float and type(right) is float:
        return math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-12)
    if type(left) is dict and type(right) is dict:
        return left.keys() == right.keys() and all(_same_result(left[key], right[key]) for key in left)
    if type(left) is list and type(right) is list:
        return len(left) == len(right) and all(_same_result(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def verify_recomputation(export_path: Path, manifest_path: Path) -> dict[str, int | str]:
    verify_export(export_path)
    export = json.loads(export_path.read_text(encoding="utf-8"))
    task, dataset = export["task"], export["dataset"]
    parameters = task["parameters"]
    groups = parameters["groups"]
    expected_components = [
        {"key": key, "version": "1.0.0", "lookback": window, "weight": 0.25}
        for key, window in FACTOR_WINDOWS.items()
    ]
    if (task["status"] != "success" or task["dataset_version_id"] != dataset["id"] or
            type(groups) is not int or not 2 <= groups <= 10 or
            parameters != {
                "mode": "historical_hs300_2024", "dataset_version_id": dataset["id"],
                "groups": groups, "factors": list(FACTOR_WINDOWS), "lookbacks": FACTOR_WINDOWS,
                "weighting": "equal", "price_basis": "source_close",
                "components": expected_components, "winsorize": True,
                "standardize": True, "mad_scale": 3.0, "transaction_cost_bps": 10.0,
            }):
        raise ValueError("unsupported historical task configuration")
    result = recompute_result(manifest_path, dataset["checksum_sha256"], groups)
    saved = export["result"]
    if not _same_result(result, saved):
        changed = sorted(key for key in result.keys() | saved.keys()
                         if key not in result or key not in saved or not _same_result(result[key], saved[key]))
        raise ValueError(f"historical recomputation mismatch: {', '.join(changed)}")
    return {"bundle_id": manifest_path.parent.name, "groups": groups,
            "observations": result["coverage"], "factors": len(FACTOR_WINDOWS)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reproducibility_json", type=Path)
    parser.add_argument("manifest_json", type=Path)
    args = parser.parse_args()
    try:
        summary = verify_recomputation(args.reproducibility_json, args.manifest_json)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.exit(1, f"历史研究复算失败：{exc}\n")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
