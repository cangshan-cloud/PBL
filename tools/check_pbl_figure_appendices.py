"""Check standalone PBL figure appendices and their source images."""

from __future__ import annotations

import sys
import zipfile

from docx import Document
from PIL import Image

from build_pbl_figure_appendices import ASSETS, FIGURES, FINAL, MODULES


def main() -> int:
    errors: list[str] = []
    expected = {f"{code}_{name}_设计图件附录.docx" for code, name in MODULES.items()}
    actual = {path.name for path in FINAL.glob("*.docx")}
    if expected != actual:
        errors.append(f"Word files differ: missing={expected-actual}, unexpected={actual-expected}")

    names = [item.filename for figures in FIGURES.values() for item in figures]
    if len(names) != 22 or len(set(names)) != 22:
        errors.append("expected 22 unique source figures")
    for filename in names:
        path = ASSETS / filename
        if not path.is_file():
            errors.append(f"missing image {filename}")
            continue
        with Image.open(path) as image:
            if image.size != (1800, 720):
                errors.append(f"unexpected image size {filename}: {image.size}")

    for code, module in MODULES.items():
        path = FINAL / f"{code}_{module}_设计图件附录.docx"
        if not path.is_file():
            continue
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                errors.append(f"corrupt Word member {path.name}: {bad}")
        doc = Document(path)
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        if len(doc.inline_shapes) != len(FIGURES[code]):
            errors.append(f"{code}: expected {len(FIGURES[code])} embedded figures")
        if "设计示意" not in text or "验收提示" not in text:
            errors.append(f"{code}: missing figure evidence boundary")
        for index, item in enumerate(FIGURES[code], 1):
            for required in (f"图 {code}{index:02d}  {item.title}", item.basis, item.check):
                if required not in text:
                    errors.append(f"{code}: missing text for {item.filename}: {required[:30]}")

    if errors:
        print("PBL figure appendix check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("PBL figure appendix check passed: 4 Word files, 22 unique embedded figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
