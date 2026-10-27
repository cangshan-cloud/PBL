import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.verify_series_exports import verify_series_exports


class SeriesExportVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.bundle = root / "reproducibility.json"
        self.ic = root / "ic.csv"
        self.long_short = root / "long-short.csv"
        self.group_nav = root / "group-nav.csv"
        self.daily_coverage = root / "daily-coverage.csv"
        self.run_id = "858c2667-19b8-4538-a02b-a3a16175adf5"
        self.result = {
            "ic_series": [{"date": "2024-01-02", "ic": -0.123456789, "rank_ic": None},
                          {"date": "2024-01-03", "ic": 0.2, "rank_ic": 0.25}],
            "long_short_series": [{"date": "2024-01-02", "return": -0.02, "nav": 0.98,
                                   "turnover": 2, "cost": 0.002, "net_return": -0.022,
                                   "net_nav": 0.978}],
            "transaction_cost_bps": 10,
            "group_nav": [
                {"group": 1, "points": [{"date": "2024-01-02", "nav": 0.99},
                                        {"date": "2024-01-03", "nav": 1.01}]},
                {"group": 2, "points": [{"date": "2024-01-02", "nav": 1.02}]},
            ],
            "daily_coverage": [
                {"date": "2024-01-02", "candidate_symbols": 3, "eligible_symbols": 2,
                 "coverage_ratio": 2 / 3, "excluded_symbols": 1,
                 "ic_status": "valid", "group_status": "insufficient_sample"},
                {"date": "2024-01-03", "eligible_symbols": 0, "coverage_ratio": None,
                 "ic_status": "no_observation", "group_status": "no_observation"},
            ],
        }
        self._write_bundle()
        self.ic.write_text("\ufeffrun_id,date,ic,rank_ic\r\n"
                           f"{self.run_id},2024-01-02,-0.123456789,\r\n"
                           f"{self.run_id},2024-01-03,0.2,0.25\r\n", encoding="utf-8", newline="")
        self.long_short.write_text(
            "\ufeffrun_id,date,gross_return,gross_nav,two_side_turnover,cost,net_return,net_nav,transaction_cost_bps\r\n"
            f"{self.run_id},2024-01-02,-0.02,0.98,2,0.002,-0.022,0.978,10\r\n",
            encoding="utf-8", newline="",
        )
        self.group_nav.write_text(
            "\ufeffrun_id,group,date,nav\r\n"
            f"{self.run_id},1,2024-01-02,0.99\r\n"
            f"{self.run_id},1,2024-01-03,1.01\r\n"
            f"{self.run_id},2,2024-01-02,1.02\r\n",
            encoding="utf-8", newline="",
        )
        self.daily_coverage.write_text(
            "\ufeffrun_id,date,candidate_symbols,eligible_symbols,coverage_ratio,excluded_symbols,ic_status,group_status\r\n"
            f"{self.run_id},2024-01-02,3,2,{2 / 3},1,valid,insufficient_sample\r\n"
            f"{self.run_id},2024-01-03,,0,,,no_observation,no_observation\r\n",
            encoding="utf-8", newline="",
        )

    def tearDown(self):
        self.temp.cleanup()

    def _write_bundle(self):
        canonical = json.dumps(self.result, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.bundle.write_text(json.dumps({"schema_version": 1, "task": {"id": self.run_id},
                                           "result": self.result, "result_sha256": digest}), encoding="utf-8")

    def test_all_downloads_match_checksummed_bundle(self):
        self.assertEqual(verify_series_exports(self.bundle, self.ic, self.long_short,
                                               self.group_nav, self.daily_coverage),
                         {"ic_rows": 2, "long_short_rows": 1, "group_nav_rows": 3,
                          "daily_coverage_rows": 2})
        self.assertEqual(verify_series_exports(self.bundle, group_nav_path=self.group_nav),
                         {"group_nav_rows": 3})
        self.assertEqual(verify_series_exports(self.bundle, daily_coverage_path=self.daily_coverage),
                         {"daily_coverage_rows": 2})

    def test_daily_coverage_wrong_run_missing_row_status_ratio_and_columns_are_rejected(self):
        original = self.daily_coverage.read_bytes()
        self.daily_coverage.write_bytes(original.replace(self.run_id.encode(), b"wrong-run", 1))
        with self.assertRaisesRegex(ValueError, "run_id differs"):
            verify_series_exports(self.bundle, daily_coverage_path=self.daily_coverage)
        lines = original.splitlines(keepends=True)
        self.daily_coverage.write_bytes(lines[0] + lines[1])
        with self.assertRaisesRegex(ValueError, "row count differs"):
            verify_series_exports(self.bundle, daily_coverage_path=self.daily_coverage)
        self.daily_coverage.write_bytes(original.replace(b",valid,insufficient_sample", b",valid,valid"))
        with self.assertRaisesRegex(ValueError, "group_status differs"):
            verify_series_exports(self.bundle, daily_coverage_path=self.daily_coverage)
        self.daily_coverage.write_bytes(original.replace(str(2 / 3).encode(), b"0.5"))
        with self.assertRaisesRegex(ValueError, "coverage_ratio differs"):
            verify_series_exports(self.bundle, daily_coverage_path=self.daily_coverage)
        self.daily_coverage.write_bytes(original.replace(b"candidate_symbols", b"candidates"))
        with self.assertRaisesRegex(ValueError, "unexpected CSV columns"):
            verify_series_exports(self.bundle, daily_coverage_path=self.daily_coverage)

    def test_daily_coverage_requires_saved_series_and_preserves_nulls(self):
        original = self.daily_coverage.read_bytes()
        self.daily_coverage.write_bytes(original.replace(b",2024-01-03,,0,,", b",2024-01-03,0,0,,"))
        with self.assertRaisesRegex(ValueError, "candidate_symbols differs"):
            verify_series_exports(self.bundle, daily_coverage_path=self.daily_coverage)
        self.daily_coverage.write_bytes(original)
        del self.result["daily_coverage"]
        self._write_bundle()
        with self.assertRaisesRegex(ValueError, "no valid daily coverage series"):
            verify_series_exports(self.bundle, daily_coverage_path=self.daily_coverage)

    def test_wrong_run_missing_row_and_changed_value_are_rejected(self):
        original = self.ic.read_bytes()
        self.ic.write_bytes(original.replace(self.run_id.encode(), b"wrong-run", 1))
        with self.assertRaisesRegex(ValueError, "run_id differs"):
            verify_series_exports(self.bundle, self.ic)
        self.ic.write_bytes(original.splitlines(keepends=True)[0] + original.splitlines(keepends=True)[1])
        with self.assertRaisesRegex(ValueError, "row count differs"):
            verify_series_exports(self.bundle, self.ic)
        self.ic.write_bytes(original.replace(b"-0.123456789", b"-0.123456788"))
        with self.assertRaisesRegex(ValueError, "ic differs"):
            verify_series_exports(self.bundle, self.ic)

    def test_cost_and_schema_tampering_are_rejected(self):
        original = self.long_short.read_bytes()
        self.long_short.write_bytes(original.replace(b",0.002,-0.022", b",0.003,-0.022"))
        with self.assertRaisesRegex(ValueError, "cost differs"):
            verify_series_exports(self.bundle, long_short_path=self.long_short)
        self.long_short.write_bytes(original.replace(b"two_side_turnover", b"turnover"))
        with self.assertRaisesRegex(ValueError, "unexpected CSV columns"):
            verify_series_exports(self.bundle, long_short_path=self.long_short)

    def test_reordered_rows_and_nonfinite_numbers_are_rejected(self):
        lines = self.ic.read_bytes().splitlines(keepends=True)
        self.ic.write_bytes(lines[0] + lines[2] + lines[1])
        with self.assertRaisesRegex(ValueError, "date differs"):
            verify_series_exports(self.bundle, self.ic)
        self.ic.write_bytes((lines[0] + lines[1] + lines[2]).replace(b"-0.123456789", b"NaN"))
        with self.assertRaisesRegex(ValueError, "ic differs"):
            verify_series_exports(self.bundle, self.ic)

    def test_null_cannot_be_filled_and_number_cannot_be_blanked(self):
        original = self.ic.read_bytes()
        self.ic.write_bytes(original.replace(b"-0.123456789,\r\n", b"-0.123456789,0\r\n"))
        with self.assertRaisesRegex(ValueError, "rank_ic differs"):
            verify_series_exports(self.bundle, self.ic)
        self.ic.write_bytes(original.replace(b",0.2,0.25", b",,0.25"))
        with self.assertRaisesRegex(ValueError, "ic differs"):
            verify_series_exports(self.bundle, self.ic)

    def test_group_nav_wrong_group_order_and_value_are_rejected(self):
        original = self.group_nav.read_bytes()
        self.group_nav.write_bytes(original.replace(b",1,2024-01-02", b",2,2024-01-02", 1))
        with self.assertRaisesRegex(ValueError, "group differs"):
            verify_series_exports(self.bundle, group_nav_path=self.group_nav)
        self.group_nav.write_bytes(original.replace(b",1.01\r\n", b",1.02\r\n"))
        with self.assertRaisesRegex(ValueError, "nav differs"):
            verify_series_exports(self.bundle, group_nav_path=self.group_nav)
        lines = original.splitlines(keepends=True)
        self.group_nav.write_bytes(lines[0] + lines[2] + lines[1] + lines[3])
        with self.assertRaisesRegex(ValueError, "date differs"):
            verify_series_exports(self.bundle, group_nav_path=self.group_nav)

    def test_changed_bundle_checksum_and_ambiguous_json_are_rejected(self):
        body = self.bundle.read_text(encoding="utf-8")
        self.bundle.write_text(body.replace('"transaction_cost_bps": 10', '"transaction_cost_bps": 20'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "result checksum mismatch"):
            verify_series_exports(self.bundle, self.ic)
        self.bundle.write_text(body.replace('"schema_version": 1,', '"schema_version": 1, "schema_version": 1,'),
                               encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            verify_series_exports(self.bundle, self.ic)

    def test_empty_series_header_only_and_no_file_rejected(self):
        self.result["ic_series"] = []
        self.result["long_short_series"] = []
        self.result["group_nav"] = [{"group": 1, "points": []}, {"group": 2, "points": []}]
        self._write_bundle()
        self.ic.write_text("\ufeffrun_id,date,ic,rank_ic\r\n", encoding="utf-8", newline="")
        self.long_short.write_text(
            "\ufeffrun_id,date,gross_return,gross_nav,two_side_turnover,cost,net_return,net_nav,transaction_cost_bps\r\n",
            encoding="utf-8", newline="",
        )
        self.group_nav.write_text("\ufeffrun_id,group,date,nav\r\n", encoding="utf-8", newline="")
        self.assertEqual(verify_series_exports(self.bundle, self.ic, self.long_short, self.group_nav),
                         {"ic_rows": 0, "long_short_rows": 0, "group_nav_rows": 0})
        with self.assertRaisesRegex(ValueError, "at least one"):
            verify_series_exports(self.bundle)


if __name__ == "__main__":
    unittest.main()
