import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.run_isolated_historical_replay import PRIVATE_ROOT, main, require_private_new_output


class IsolatedHistoricalReplayTests(unittest.TestCase):
    def test_output_must_be_new_and_inside_ignored_private_directory(self):
        candidate = PRIVATE_ROOT / f"unused-replay-{uuid4().hex}"
        self.assertEqual(require_private_new_output(candidate), candidate)
        for rejected in (ROOT / "outputs" / "public-replay", PRIVATE_ROOT):
            with self.subTest(rejected=rejected):
                with self.assertRaises(ValueError):
                    require_private_new_output(rejected)
        existing = PRIVATE_ROOT / "bundles"
        if existing.exists():
            with self.assertRaisesRegex(ValueError, "already exists"):
                require_private_new_output(existing)

    def test_cli_requires_explicit_private_output_acknowledgment(self):
        candidate = PRIVATE_ROOT / f"unused-replay-{uuid4().hex}"
        args = ["run_isolated_historical_replay.py", str(PRIVATE_ROOT / "absent.json"), str(candidate)]
        with patch.object(sys, "argv", args):
            with self.assertRaises(SystemExit) as error:
                main()
        self.assertEqual(error.exception.code, 2)
        self.assertFalse(candidate.exists())


if __name__ == "__main__":
    unittest.main()
