"""Check Markdown file links and disclose references to local-only QA artifacts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
LOCAL_ONLY = ("output/playwright/", ".playwright-cli/")


def audit(root: Path) -> tuple[list[str], list[str], int]:
    """Return broken portable links, local-only links, and checked link count."""
    root = root.resolve()
    errors: list[str] = []
    local: list[str] = []
    checked = 0
    docs = root / "docs"
    for source in sorted(docs.rglob("*.md")):
        content = source.read_text(encoding="utf-8")
        for line_number, line in enumerate(content.splitlines(), 1):
            for match in LINK.finditer(line):
                target = match.group(1).strip().split(' "', 1)[0].strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith(("//", "#", "mailto:")):
                    continue
                path_part = unquote(parsed.path)
                if not path_part:
                    continue
                checked += 1
                destination = (source.parent / path_part).resolve()
                location = f"{source.relative_to(root)}:{line_number}: {target}"
                try:
                    relative = destination.relative_to(root).as_posix()
                except ValueError:
                    errors.append(f"link escapes repository: {location}")
                    continue
                if relative.startswith(LOCAL_ONLY):
                    local.append(location)
                elif not destination.is_file() and not destination.is_dir():
                    errors.append(f"missing portable target: {location}")
    return errors, local, checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict-local", action="store_true", help="also reject ignored local-only links")
    args = parser.parse_args()
    errors, local, checked = audit(args.root.resolve())
    for item in errors:
        print(f"ERROR {item}")
    for item in local:
        print(f"LOCAL_ONLY {item}")
    print(f"Checked {checked} local Markdown links; {len(errors)} errors; {len(local)} local-only references")
    return 1 if errors or (args.strict_local and local) else 0


if __name__ == "__main__":
    raise SystemExit(main())
