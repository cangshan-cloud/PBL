"""Stable CSV exports for the historical research audit stored with a run."""

from __future__ import annotations

import csv
import io

from app.models import Run, RunStatus


def historical_audit_csv(run: Run, table: str) -> bytes:
    if table not in {"daily", "unlabeled"}:
        raise ValueError("unsupported historical audit table")
    if run.status != RunStatus.SUCCESS:
        raise ValueError("historical audit is only available for a successful run")
    artifact = next((item for item in run.artifacts if item.artifact_type == "metrics"), None)
    audit = (artifact.content or {}).get("historical_audit") if artifact else None
    if not isinstance(audit, dict) or not audit:
        raise ValueError("run has no historical audit")

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    if table == "daily":
        base = ("factor", "date")
        fields = sorted({key for item in audit.values() for row in item["daily"] for key in row if key != "date"})
        writer.writerow((*base, *fields))
        for factor, item in sorted(audit.items()):
            for row in item["daily"]:
                writer.writerow((factor, row["date"], *(row.get(key, 0) for key in fields)))
    else:
        writer.writerow(("factor", "date", "symbol", "factor_value", "next_market_date", "reason"))
        for factor, item in sorted(audit.items()):
            for row in item["unlabeled_signals"]:
                writer.writerow((factor, row["date"], row["symbol"], row["factor"],
                                 row["next_market_date"] or "", row["reason"]))
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")
