"""Offline-check an archived HTML report and its disclosed delivery copy.

The two metadata JSON files must be independently saved from the platform's
dataset and report-summary APIs. This checks export consistency, not market truth.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from pathlib import Path


_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SECTION_START = '<section style="background:#fff5db;border-left:4px solid #d5a22f;padding:16px;margin-bottom:20px">'
_MARKER = "<strong>交付披露副本 · 非原始归档字节</strong>"
_FALLBACK = "数据来源和日历诊断仍需结合原始文件、授权和交易所记录核查；未命中已知异常不等于真实交易日认证。"
_DEMO_SHA = "c65db778f6a08c69e4b8d246e146bc67f158fd4d313350d8340009337614a10e"


def _object(path: Path, label: str) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA.fullmatch(value) is None:
        raise ValueError(f"{label} is not a SHA-256 digest")
    return value


def _count(report: dict, key: str) -> int:
    value = report.get(key, 0)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"quality report has invalid {key}")
    return value


def _risk_paragraphs(dataset: dict) -> list[str]:
    report = dataset.get("quality_report")
    if not isinstance(report, dict):
        raise ValueError("dataset metadata has no quality report")
    key = dataset.get("dataset_key")
    version = dataset.get("version")
    if not isinstance(key, str) or not isinstance(version, str):
        raise ValueError("dataset metadata has invalid key or version")
    risks = []
    if key == "demo_daily" and ((version == "0.2.0" and dataset["checksum"] == _DEMO_SHA) or report.get("source") == "bundled_demo"):
        risks.append("该版本为内置合成演示数据，按工作日生成而非真实沪深交易日历；研究结果仅供软件功能验收，不能作为真实市场证据。")
    weekend = _count(report, "weekend_row_count")
    if weekend:
        risks.append(f"质量报告含 {weekend} 行周末日期行情，请核对源文件。")
    closures = _count(report, "announced_weekday_closure_row_count")
    dates = report.get("announced_weekday_closure_dates") or []
    if not isinstance(dates, list) or any(not isinstance(value, str) for value in dates):
        raise ValueError("quality report has invalid closure dates")
    if closures:
        detail = f"（日期：{'、'.join(dates)}）" if dates else ""
        risks.append(f"质量报告含 {closures} 行沪深交易所公告休市工作日行情{detail}；规则版本：{report.get('announced_closure_calendar_version') or '未知'}。")
    years = report.get("calendar_uncovered_years") or []
    if not isinstance(years, list) or any(not isinstance(value, int) or isinstance(value, bool) for value in years):
        raise ValueError("quality report has invalid uncovered years")
    if years:
        risks.append(f"离线公告休市规则未覆盖 {'、'.join(map(str, years))} 年；不能把零命中解释为日期合规。")
    return risks or [_FALLBACK]


def verify_delivery(archived_path: Path, delivery_path: Path, dataset_path: Path, summary_path: Path) -> dict:
    dataset = _object(dataset_path, "dataset metadata")
    summary = _object(summary_path, "report summary")
    dataset_id = dataset.get("id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("dataset metadata has no ID")
    dataset_sha = _sha(dataset.get("checksum"), "dataset checksum")
    if summary.get("dataset_version_id") != dataset_id or summary.get("dataset_checksum_sha256") != dataset_sha:
        raise ValueError("report summary differs from dataset identity")
    run_id = summary.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError("report summary has no Run ID")
    archive_sha = _sha(summary.get("checksum"), "archived report checksum")
    archived = archived_path.read_bytes()
    if hashlib.sha256(archived).hexdigest() != archive_sha:
        raise ValueError("archived report bytes differ from report summary checksum")
    original = archived.decode("utf-8")
    delivery = delivery_path.read_text(encoding="utf-8")
    if original.count("<main>") != 1 or delivery.count("<main>") != 1:
        raise ValueError("report has invalid main structure")
    prefix = "<main>" + _SECTION_START
    if prefix not in delivery:
        raise ValueError("delivery copy has no leading disclosure section")
    before, remainder = delivery.split(prefix, 1)
    if "</section>" not in remainder:
        raise ValueError("delivery disclosure section is not closed")
    body, after = remainder.split("</section>", 1)
    if before + "<main>" + after != original:
        raise ValueError("delivery copy changes archived report outside the disclosure section")
    if not body.startswith(_MARKER):
        raise ValueError("delivery copy has invalid disclosure marker")
    paragraphs = re.findall(r"<p>(.*?)</p>", body[len(_MARKER):], flags=re.DOTALL)
    if not paragraphs or body != _MARKER + "".join(f"<p>{item}</p>" for item in paragraphs):
        raise ValueError("delivery copy has invalid disclosure paragraphs")
    if any(re.search(r"<[^>]+>", item) for item in paragraphs):
        raise ValueError("delivery disclosure contains unescaped HTML")
    expected_risks = _risk_paragraphs(dataset)
    expected_identity = f"数据版本 ID：{dataset_id}；数据 SHA-256：{dataset_sha}；原始报告 SHA-256：{archive_sha}。"
    actual = [html.unescape(item) for item in paragraphs]
    if actual != [*expected_risks, expected_identity]:
        raise ValueError("delivery disclosure differs from dataset quality or report identity")
    return {"run_id": run_id, "dataset_version_id": dataset_id, "dataset_checksum_sha256": dataset_sha,
            "archived_report_sha256": archive_sha, "risk_count": len(expected_risks), "verified": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archived_html", type=Path)
    parser.add_argument("delivery_html", type=Path)
    parser.add_argument("dataset_json", type=Path, help="Saved dataset-version API object")
    parser.add_argument("report_summary_json", type=Path, help="Saved single object from report-list API")
    args = parser.parse_args()
    try:
        result = verify_delivery(args.archived_html, args.delivery_html, args.dataset_json, args.report_summary_json)
        print(json.dumps(result, ensure_ascii=False))
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        parser.exit(1, f"verification failed: {exc}\n")


if __name__ == "__main__":
    main()
