"""Read-only structural audit of the project change ledger."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


ROW_ID = re.compile(r"^(?:CHG|DEC)-(\d{8})-\d{3}$")
RECORD_LINK = re.compile(r"\[记录\]\((changes/[^)]+\.md)\)")
PACKET_NAMES = {
    letter: pattern
    for letter, pattern in zip("ABCD", ("A_*.md", "B_*.md", "C_*.md", "D_*.md"))
}


def audit(root: Path, since: date = date(2026, 10, 21)) -> tuple[list[str], int, int]:
    """Return errors, indexed row count, and strictly checked recent CHG count."""
    docs = root / "docs"
    index = docs / "CHANGE_INDEX.md"
    errors: list[str] = []
    if not index.is_file():
        return [f"missing index: {index}"], 0, 0

    packets: dict[str, str] = {}
    for letter, pattern in PACKET_NAMES.items():
        matches = list((docs / "member-deliverables").glob(pattern))
        if len(matches) != 1:
            errors.append(f"packet {letter}: expected one file, found {len(matches)}")
        else:
            packets[letter] = matches[0].read_text(encoding="utf-8")

    ids: set[str] = set()
    paths: set[str] = set()
    row_count = recent_count = 0
    for number, line in enumerate(index.read_text(encoding="utf-8").splitlines(), 1):
        if not re.match(r"^\| (?:CHG|DEC)-", line):
            continue
        row_count += 1
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6:
            errors.append(f"index line {number}: expected six columns")
            continue
        record_id, listed_date, _, _, link_cell, location = cells
        match = ROW_ID.fullmatch(record_id)
        if not match:
            errors.append(f"index line {number}: invalid ID {record_id}")
            continue
        if record_id in ids:
            errors.append(f"index line {number}: duplicate ID {record_id}")
        ids.add(record_id)
        try:
            record_date = date.fromisoformat(f"{match[1][:4]}-{match[1][4:6]}-{match[1][6:]}")
        except ValueError:
            errors.append(f"index line {number}: invalid ID date {record_id}")
            continue
        if listed_date != record_date.isoformat():
            errors.append(f"index line {number}: date mismatch for {record_id}")
        link = RECORD_LINK.fullmatch(link_cell)
        if not link:
            errors.append(f"index line {number}: missing record link for {record_id}")
            continue
        relative = link[1]
        if Path(relative).parts[:1] != ("changes",) or ".." in Path(relative).parts:
            errors.append(f"index line {number}: unsafe record path {relative}")
            continue
        if relative in paths:
            errors.append(f"index line {number}: duplicate record path {relative}")
        paths.add(relative)
        record_file = docs / relative
        if not record_file.is_file():
            errors.append(f"index line {number}: missing record {relative}")
            continue
        if not location:
            errors.append(f"index line {number}: empty location for {record_id}")
        if record_date < since or not record_id.startswith("CHG-"):
            continue
        recent_count += 1
        content = record_file.read_text(encoding="utf-8")
        headings = re.findall(r"^## (.+)$", content, re.MULTILINE)
        if record_id not in content.splitlines()[0]:
            errors.append(f"{relative}: first heading omits {record_id}")
        for label, required in (
            ("decision", lambda h: "决策" in h),
            ("locations", lambda h: "修改" in h and "位置" in h),
            ("verification", lambda h: "验证" in h),
        ):
            if not any(required(h) for h in headings):
                errors.append(f"{relative}: missing {label} heading")
        if not re.search(r"`(?:backend|frontend|tools|docs)/[^`]+`|`docker-compose[^`]+`", content):
            errors.append(f"{relative}: no repository-relative location")
        for letter, packet in packets.items():
            if f"[{record_id}](../{relative})" not in packet:
                errors.append(f"packet {letter}: missing link to {record_id}")

    for file in (docs / "changes").glob("20??-??-??-*.md"):
        try:
            file_date = date.fromisoformat(file.name[:10])
        except ValueError:
            errors.append(f"invalid dated record filename: {file.name}")
            continue
        if file_date >= since and f"changes/{file.name}" not in paths:
            errors.append(f"unindexed recent record: changes/{file.name}")
    return errors, row_count, recent_count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--since", type=date.fromisoformat, default=date(2026, 10, 21))
    args = parser.parse_args()
    errors, rows, recent = audit(args.root, args.since)
    if errors:
        print("FAIL change ledger:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"PASS change ledger: {rows} indexed records; {recent} recent CHG records linked in A/B/C/D")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
