from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from check_change_ledger import audit  # noqa: E402


RECORD_ID = "CHG-20261021-001"
RECORD_PATH = "changes/2026-10-21-001-example.md"


def make_ledger(root: Path) -> None:
    docs = root / "docs"
    (docs / "changes").mkdir(parents=True)
    (docs / "member-deliverables").mkdir()
    (docs / "CHANGE_INDEX.md").write_text(
        "| ID | 日期 | 类型 | 内容 | 记录 | 对应位置 |\n"
        f"| {RECORD_ID} | 2026-10-21 | test | example | [记录]({RECORD_PATH}) | `tools/example.py` |\n",
        encoding="utf-8",
    )
    (docs / RECORD_PATH).write_text(
        f"# {RECORD_ID} Example\n\n## 问题与决策\nDecision.\n\n"
        "## 修改内容与位置\n`tools/example.py`\n\n## 验证与边界\nVerified.\n",
        encoding="utf-8",
    )
    for letter in "ABCD":
        (docs / "member-deliverables" / f"{letter}_packet.md").write_text(
            f"[{RECORD_ID}](../{RECORD_PATH})\n", encoding="utf-8"
        )


class ChangeLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="factorlab-ledger-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        make_ledger(self.root)

    def test_valid_change_ledger(self) -> None:
        self.assertEqual(audit(self.root), ([], 1, 1))

    def test_missing_member_link_and_unindexed_record(self) -> None:
        (self.root / "docs/member-deliverables/C_packet.md").write_text("missing\n", encoding="utf-8")
        (self.root / "docs/changes/2026-10-21-002-orphan.md").write_text("orphan\n", encoding="utf-8")
        errors, _, _ = audit(self.root)
        self.assertTrue(any("packet C: missing link" in error for error in errors))
        self.assertTrue(any("unindexed recent record" in error for error in errors))

    def test_duplicate_id_and_missing_decision_heading(self) -> None:
        index = self.root / "docs/CHANGE_INDEX.md"
        index.write_text(index.read_text(encoding="utf-8") * 2, encoding="utf-8")
        record = self.root / "docs" / RECORD_PATH
        record.write_text(record.read_text(encoding="utf-8").replace("## 问题与决策", "## 背景"), encoding="utf-8")
        errors, _, _ = audit(self.root)
        self.assertTrue(any("duplicate ID" in error for error in errors))
        self.assertTrue(any("missing decision heading" in error for error in errors))

    def test_old_records_do_not_require_member_packets(self) -> None:
        self.assertEqual(audit(self.root, date(2026, 10, 22)), ([], 1, 0))


if __name__ == "__main__":
    unittest.main()
