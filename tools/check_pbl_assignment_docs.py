from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "outputs" / "pbl-assignments-2026-11-20" / "final"


def main() -> None:
    files = sorted(FINAL.glob("*.docx"))
    if len(files) != 16:
        raise SystemExit(f"expected 16 DOCX files, found {len(files)}")
    members: dict[str, int] = {}
    for path in files:
        member = path.name.split("_", 1)[0]
        members[member] = members.get(member, 0) + 1
        document = Document(path)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        text += "\n" + "\n".join(
            cell.text
            for table in document.tables
            for row in table.rows
            for cell in row.cells
        )
        checks = {
            "project title": "量化投资多因子研发平台" in text,
            "identity placeholder": "【待填写：" in text,
            "answer content": len(text) >= 1400,
            "diagram": len(document.inline_shapes) >= 1,
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise SystemExit(f"{path.name}: failed {', '.join(failed)}")
    if members != {"A": 4, "B": 4, "C": 4, "D": 4}:
        raise SystemExit(f"unexpected member distribution: {members}")
    print("PBL assignment check passed: 16 files, A/B/C/D each 4, content and diagrams present")


if __name__ == "__main__":
    main()
