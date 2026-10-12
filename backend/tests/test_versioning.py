import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.versioning import source_fingerprint


class VersioningTests(unittest.TestCase):
    def test_fingerprint_is_stable_across_line_endings_and_changes_with_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "app"
            root.mkdir()
            (root.parent / "pyproject.toml").write_bytes(b"[project]\nname = 'sample'\n")
            file = root / "research.py"
            file.write_bytes(b"x = 1\ny = 2\n")
            first = source_fingerprint(root)
            self.assertTrue(first.startswith("src-sha256:"))
            self.assertEqual(len(first), 75)
            file.write_bytes(b"x = 1\r\ny = 2\r\n")
            self.assertEqual(source_fingerprint(root), first)
            file.write_bytes(b"x = 1\ny = 3\n")
            self.assertNotEqual(source_fingerprint(root), first)


if __name__ == "__main__":
    unittest.main()
