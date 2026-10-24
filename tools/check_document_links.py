"""Check Markdown file links and disclose references to local-only QA artifacts."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit


LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
LOCAL_ONLY = ("output/playwright/", ".playwright-cli/")


def _tracked_files(root: Path) -> set[str] | None:
    """Return Git-index paths, or None for a source archive without .git."""
    if not (root / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return {item.decode("utf-8") for item in result.stdout.split(b"\0") if item}


def audit(root: Path) -> tuple[list[str], list[str], int]:
    """Return broken portable links, local-only links, and checked link count."""
    root = root.resolve()
    errors: list[str] = []
    local: list[str] = []
    checked = 0
    tracked = _tracked_files(root)
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
                exists = destination.is_file() or destination.is_dir()
                is_local_only = relative.startswith(LOCAL_ONLY) and (
                    (tracked is None and not exists)
                    or (tracked is not None and relative not in tracked)
                )
                if is_local_only:
                    local.append(location)
                elif not exists:
                    errors.append(f"missing portable target: {location}")
                elif tracked is not None and destination.is_file() and relative not in tracked:
                    errors.append(f"untracked portable target: {location}")
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
