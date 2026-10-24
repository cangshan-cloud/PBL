"""Check downloaded comparison JSON and optional CSV/HTML files without the API stack.

This verifies export consistency, not source market data or factor correctness.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path


DATASET_SOURCE_LABELS = {
    "bundled_demo": "内置演示数据",
    "historical_bundle": "历史研究数据包（来源另核）",
    "imported_csv": "导入 CSV（来源另核）",
}


def _matching_number(cell: str, expected: object) -> bool:
    if expected is None:
        return cell == ""
    if isinstance(expected, bool) or not isinstance(expected, (int, float)):
        return False
    try:
        return math.isclose(float(cell), expected, rel_tol=1e-12, abs_tol=1e-12)
    except ValueError:
        return False


class _ReportTableParser(HTMLParser):
    """Read ordered body rows from report tables, including row labels."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current_table: list[list[str]] | None = None
        self.in_body = False
        self.in_cell = False
        self.cell_parts: list[str] = []
        self.row: list[str] | None = None
        self.tables: list[list[list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.current_table = []
            self.tables.append(self.current_table)
        elif self.current_table is not None and tag == "tbody":
            self.in_body = True
        elif self.current_table is not None and self.in_body and tag == "tr":
            self.row = []
        elif self.row is not None and tag in ("td", "th"):
            self.in_cell = True
            self.cell_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self.in_cell:
            assert self.row is not None
            self.row.append("".join(self.cell_parts).strip())
            self.in_cell = False
        elif tag == "tr" and self.row is not None:
            assert self.current_table is not None
            self.current_table.append(self.row)
            self.row = None
        elif tag == "tbody" and self.current_table is not None:
            self.in_body = False
        elif tag == "table":
            self.current_table = None


def _html_ic_value(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    return f"{value:.4f}"


def _ic_row(rows: list[list[str]], item_count: int, section: str) -> list[str]:
    matches = [row for row in rows if row and row[0] == "IC均值"]
    if len(matches) != 1 or len(matches[0]) != item_count + 1:
        raise ValueError(f"comparison HTML has invalid {section} IC row")
    return matches[0][1:]


def verify_exports(json_path: Path, csv_path: Path | None = None, html_path: Path | None = None) -> dict:
    snapshot = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict) or snapshot.get("export_format") != "factorlab-comparison" or snapshot.get("export_schema_version") != 1:
        raise ValueError("unsupported comparison snapshot format or schema")
    items = snapshot.get("items")
    if not isinstance(items, list) or not 2 <= len(items) <= 6 or any(not isinstance(item, dict) for item in items):
        raise ValueError("comparison snapshot has no valid ordered items")
    run_ids = [item.get("run_id") for item in items]
    if any(not isinstance(value, str) or not value for value in run_ids) or len(set(run_ids)) != len(run_ids):
        raise ValueError("comparison snapshot has invalid or repeated run IDs")
    if snapshot.get("baseline_run_id") != run_ids[0]:
        raise ValueError("comparison baseline differs from first item")
    for item in items:
        checksum = item.get("dataset_checksum_sha256")
        if not isinstance(checksum, str) or re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
            raise ValueError("comparison snapshot has invalid dataset checksum")
    has_source = ["dataset_source_kind" in item for item in items]
    if any(has_source) and not all(has_source):
        raise ValueError("comparison snapshot has inconsistent dataset source fields")
    if all(has_source) and any(item["dataset_source_kind"] not in DATASET_SOURCE_LABELS for item in items):
        raise ValueError("comparison snapshot has invalid dataset source kind")
    warnings = snapshot.get("warnings")
    if not isinstance(warnings, list) or any(not isinstance(value, str) for value in warnings):
        raise ValueError("comparison snapshot has invalid warnings")
    for key in ("common_ic_date_count", "common_group_date_count"):
        value = snapshot.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"comparison snapshot has invalid {key}")

    summary = {"run_count": len(items), "baseline_run_id": run_ids[0], "warning_count": len(warnings),
               "csv_verified": False, "html_verified": False}
    if csv_path is not None:
        rows = list(csv.reader(io.StringIO(csv_path.read_text(encoding="utf-8-sig"))))
        if len(rows) < len(items) + 1:
            raise ValueError("comparison CSV has too few task rows")
        header = rows[0]
        required = {"run_id", "dataset_version_id", "dataset_checksum_sha256", "code_version", "ic_mean", "common_date_ic_mean"}
        if not required.issubset(header):
            raise ValueError("comparison CSV is missing identity or IC columns")
        if all(has_source) and "dataset_source_kind" not in header:
            raise ValueError("comparison CSV is missing dataset source kind")
        for item, cells in zip(items, rows[1:len(items) + 1], strict=True):
            if len(cells) != len(header):
                raise ValueError("comparison CSV task row has unexpected column count")
            row = dict(zip(header, cells, strict=True))
            for key in ("run_id", "dataset_version_id", "dataset_checksum_sha256", "code_version"):
                if row[key] != item.get(key):
                    raise ValueError(f"comparison CSV differs from JSON {key}")
            if all(has_source) and row["dataset_source_kind"] != item["dataset_source_kind"]:
                raise ValueError("comparison CSV differs from JSON dataset_source_kind")
            if not _matching_number(row["ic_mean"], (item.get("metrics") or {}).get("ic_mean")):
                raise ValueError("comparison CSV differs from JSON original IC")
            if not _matching_number(row["common_date_ic_mean"], (item.get("common_date_ic") or {}).get("ic_mean")):
                raise ValueError("comparison CSV differs from JSON common-date IC")
        tail = rows[len(items) + 1:]
        for label, key in (("共同有效IC日期数", "common_ic_date_count"),
                           ("共同多空分组日期数", "common_group_date_count")):
            if [label, str(snapshot[key])] not in tail:
                raise ValueError(f"comparison CSV differs from JSON {key}")
        exported_warnings = [row[1] for row in tail if len(row) >= 2 and row[0] == "风险提示"]
        if exported_warnings != warnings:
            raise ValueError("comparison CSV differs from JSON warnings")
        summary["csv_verified"] = True

    if html_path is not None:
        page = html_path.read_text(encoding="utf-8")
        parser = _ReportTableParser()
        parser.feed(page)
        if len(parser.tables) < 3 or len(parser.tables[0]) != len(items) or any(len(row) != 7 for row in parser.tables[0]):
            raise ValueError("comparison HTML has invalid task provenance rows")
        for index, (item, row) in enumerate(zip(items, parser.tables[0], strict=True)):
            version_cell = str(item.get("dataset_version"))
            if all(has_source):
                version_cell += DATASET_SOURCE_LABELS[item["dataset_source_kind"]]
            expected = ["基准" if index == 0 else f"候选 {index}", item.get("experiment_name"),
                        item.get("run_id"), item.get("dataset_version_id"),
                        item.get("dataset_checksum_sha256"), version_cell,
                        item.get("code_version")]
            if row != expected:
                raise ValueError(f"comparison HTML provenance row {index + 1} differs from JSON")
        original_ic_cells = _ic_row(parser.tables[1], len(items), "original")
        common_ic_cells = _ic_row(parser.tables[2], len(items), "common-date")
        for index, item in enumerate(items):
            original_value = _html_ic_value((item.get("metrics") or {}).get("ic_mean"))
            original_suffix = "基准" if index == 0 else "较基准 "
            if not original_ic_cells[index].startswith(original_value + original_suffix):
                raise ValueError(f"comparison HTML original IC column {index + 1} differs from JSON")
            common_value = _html_ic_value((item.get("common_date_ic") or {}).get("ic_mean"))
            if common_ic_cells[index] != common_value:
                raise ValueError(f"comparison HTML common-date IC column {index + 1} differs from JSON")
        for warning in warnings:
            if html.escape(warning) not in page:
                raise ValueError("comparison HTML omits a JSON warning")
        for key in ("common_ic_date_count", "common_group_date_count"):
            if str(snapshot[key]) not in page:
                raise ValueError(f"comparison HTML omits {key}")
        summary["html_verified"] = True
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("comparison_json", type=Path)
    parser.add_argument("--csv", type=Path, help="Optional downloaded comparison CSV")
    parser.add_argument("--html", type=Path, help="Optional downloaded comparison HTML")
    args = parser.parse_args()
    try:
        print(json.dumps(verify_exports(args.comparison_json, args.csv, args.html), ensure_ascii=False))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(1, f"verification failed: {exc}\n")


if __name__ == "__main__":
    main()
