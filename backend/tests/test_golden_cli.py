import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class GoldenCliTests(unittest.TestCase):
    def test_verifier_succeeds_with_windows_legacy_stdout_encoding(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "verify_golden_research.py")],
            env={**os.environ, "PYTHONIOENCODING": "cp1252"},
            capture_output=True,
            text=True,
            encoding="ascii",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Golden research verification passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
