"""Cross-check the Dec 2024 BaoStock roster change against CSI's official list.

The 16+16 codes below are manually transcribed from the CSI adjustment PDF.
This verifies one announced boundary, not every possible index-maintenance event.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from verify_hs300_members import verify_snapshot

OFFICIAL_PDF = (
    "https://oss-ch.csindex.com.cn/notice/20241129172348-"
    "%E9%99%84%E4%BB%B6%EF%BC%9A%E9%83%A8%E5%88%86%E6%8C%87%E6%95%B0"
    "%E6%A0%B7%E6%9C%AC%E8%B0%83%E6%95%B4%E5%90%8D%E5%8D%95.pdf"
)
REMOVED = frozenset(
    "000733 002410 002603 002821 002841 300142 300223 300454 "
    "300496 300751 300919 300957 600132 600732 603899 688363".split()
)
ADDED = frozenset(
    "000630 000975 002028 002422 002463 300394 300502 600066 "
    "600160 600377 600482 601127 601136 688169 688472 688506".split()
)


def read_codes(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as source:
        return {row["code"].split(".", 1)[1] for row in csv.DictReader(source)}


def verify_official_boundary(target: Path) -> dict[str, object]:
    verified = verify_snapshot(target)
    changes = verified["changed_query_days"]
    if not any(row == {"query_date": "2024-12-16", "removed_count": 16, "added_count": 16} for row in changes):
        raise ValueError("expected 2024-12-16 16-for-16 boundary is absent")
    before = read_codes(target / "daily_rosters" / "2024-12-13.csv")
    after = read_codes(target / "daily_rosters" / "2024-12-16.csv")
    removed, added = before - after, after - before
    if removed != REMOVED or added != ADDED:
        raise ValueError(
            "official December adjustment mismatch: "
            f"missing_removed={sorted(REMOVED - removed)} "
            f"extra_removed={sorted(removed - REMOVED)} "
            f"missing_added={sorted(ADDED - added)} "
            f"extra_added={sorted(added - ADDED)}"
        )
    return {
        "source": OFFICIAL_PDF,
        "last_old_query_date": "2024-12-13",
        "first_new_query_date": "2024-12-16",
        "removed_match": len(REMOVED),
        "added_match": len(ADDED),
        "scope": "one official regular adjustment only; no claim of complete point-in-time accuracy",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify_official_boundary(args.snapshot_dir.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
