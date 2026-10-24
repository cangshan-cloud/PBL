"""Tests for repository document link portability checks."""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "check_document_links.py"
SPEC = importlib.util.spec_from_file_location("check_document_links", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DocumentLinkAuditTests(unittest.TestCase):
    def test_distinguishes_missing_portable_and_local_only_links(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            docs = root / "docs"
            docs.mkdir()
            (docs / "exists.md").write_text("ok", encoding="utf-8")
            (docs / "index.md").write_text(
                "[ok](exists.md) [broken](missing.md) "
                "[private](../output/playwright/private.png) "
                "[web](https://example.com) [section](#top)",
                encoding="utf-8",
            )
            errors, local, checked = MODULE.audit(root)
            self.assertEqual(checked, 3)
            self.assertEqual(len(errors), 1)
            self.assertIn("missing.md", errors[0])
            self.assertEqual(len(local), 1)
            self.assertIn("private.png", local[0])

    def test_link_cannot_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            docs = root / "docs"
            docs.mkdir()
            (docs / "index.md").write_text("[escape](../../outside.txt)", encoding="utf-8")
            errors, _, _ = MODULE.audit(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("escapes repository", errors[0])

    def test_tracked_ignored_file_is_portable_but_untracked_file_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            docs = root / "docs"
            ignored = root / "output" / "playwright"
            qa = root / "outputs" / "qa"
            docs.mkdir()
            ignored.mkdir(parents=True)
            qa.mkdir(parents=True)
            (ignored / "tracked.png").write_bytes(b"image")
            (qa / "untracked.png").write_bytes(b"image")
            (docs / "index.md").write_text(
                "[tracked](../output/playwright/tracked.png) "
                "[untracked](../outputs/qa/untracked.png)", encoding="utf-8"
            )
            with patch.object(MODULE, "_tracked_files", return_value={"output/playwright/tracked.png"}):
                errors, local, checked = MODULE.audit(root)
            self.assertEqual(checked, 2)
            self.assertEqual(local, [])
            self.assertEqual(len(errors), 1)
            self.assertIn("untracked portable", errors[0])


if __name__ == "__main__":
    unittest.main()
