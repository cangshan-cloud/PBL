import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from build_hs300_bundle import build_bundle
from verify_hs300_bundle import verify_bundle


class Hs300BundleTests(unittest.TestCase):
    def test_sealed_bundle_detects_tampering_and_refuses_duplicate_id(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            members = root / "members"
            prices = root / "prices"
            (members / "daily_rosters").mkdir(parents=True)
            (prices / "symbols").mkdir(parents=True)
            (members / "manifest.json").write_text(json.dumps({"daily_roster_sha256": {"2024-01-02": "dummy"}}))
            (members / "trade_calendar.csv").write_text("calendar_date,is_trading_day\n2024-01-02,1\n")
            (members / "hs300_members_queries.csv").write_text("query_date,code,update_date\n2024-01-02,sh.600000,2024-01-02\n")
            (members / "daily_rosters" / "2024-01-02.csv").write_text("query_date,code,update_date\n2024-01-02,sh.600000,2024-01-02\n")
            (prices / "manifest.json").write_text(json.dumps({"request": {"codes": ["sh.600000"]}}))
            (prices / "request.json").write_text("{}")
            (prices / "trade_calendar.csv").write_text("calendar_date,is_trading_day\n2024-01-02,1\n")
            (prices / "symbols" / "sh_600000.csv").write_text("date,code\n2024-01-02,sh.600000\n")
            member_result = {"trading_day_count": 1, "member_row_count": 1}
            price_result = {"symbol_count": 1, "row_count": 1, "member_day_audit": {"member_pairs": 1}}
            price_manifest = {"request": {"codes": ["sh.600000"]}}
            with patch("build_hs300_bundle.validate_sources", return_value=(member_result, price_result, price_manifest)):
                bundle, manifest = build_bundle(members, prices, root / "bundles")
                self.assertEqual(len(manifest["file_sha256"]), 8)
                with self.assertRaises(FileExistsError):
                    build_bundle(members, prices, root / "bundles")
            with patch("verify_hs300_bundle.validate_sources", return_value=(member_result, price_result, price_manifest)):
                self.assertEqual(verify_bundle(bundle)["verified_files"], 8)
                path = bundle / "prices_source" / "symbols" / "sh_600000.csv"
                path.write_bytes(path.read_bytes() + b"tampered")
                with self.assertRaisesRegex(ValueError, "bundle hash mismatch"):
                    verify_bundle(bundle)


if __name__ == "__main__":
    unittest.main()
