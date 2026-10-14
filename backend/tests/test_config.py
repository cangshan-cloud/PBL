import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings, parse_cors_origins


class ConfigTests(unittest.TestCase):
    def test_default_cors_origins_cover_both_loopback_frontend_names(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_settings().cors_origins, ("http://localhost:5173", "http://127.0.0.1:5173"))

    def test_cors_origins_can_be_set_for_isolated_local_ports(self):
        with patch.dict(os.environ, {"CORS_ORIGINS": " http://127.0.0.1:15173 , http://localhost:5173 "}):
            self.assertEqual(get_settings().cors_origins, ("http://127.0.0.1:15173", "http://localhost:5173"))

    def test_cors_origins_reject_wildcards_and_non_origins(self):
        for value in ("*", "", "http://localhost:5173/path", "https://user:pass@example.com", "ftp://example.com"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_cors_origins(value)


if __name__ == "__main__":
    unittest.main()
