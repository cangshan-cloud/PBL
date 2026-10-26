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
        self.run_id = "858c2667-19b8-4538-a02b-a3a16175adf5"
        self.result = {
            "ic_series": [{"date": "2024-01-02", "ic": -0.123456789, "rank_ic": None},
                          {"date": "2024-01-03", "ic": 0.2, "rank_ic": 0.25}],
            "long_short_series": [{"date": "2024-01-02", "return": -0.02, "nav": 0.98,
                                   "turnover": 2, "cost": 0.002, "net_return": -0.022,
                                   "net_nav": 0.978}],
            "transaction_cost_bps": 10,
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

    def tearDown(self):
        self.temp.cleanup()

    def _write_bundle(self):
        canonical = json.dumps(self.result, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.bundle.write_text(json.dumps({"schema_version": 1, "task": {"id": self.run_id},
                                           "result": self.result, "result_sha256": digest}), encoding="utf-8")

    def test_both_downloads_match_checksummed_bundle(self):
        self.assertEqual(verify_series_exports(self.bundle, self.ic, self.long_short),
                         {"ic_rows": 2, "long_short_rows": 1})

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
        self._write_bundle()
        self.ic.write_text("\ufeffrun_id,date,ic,rank_ic\r\n", encoding="utf-8", newline="")
        self.long_short.write_text(
            "\ufeffrun_id,date,gross_return,gross_nav,two_side_turnover,cost,net_return,net_nav,transaction_cost_bps\r\n",
            encoding="utf-8", newline="",
        )
        self.assertEqual(verify_series_exports(self.bundle, self.ic, self.long_short),
                         {"ic_rows": 0, "long_short_rows": 0})
        with self.assertRaisesRegex(ValueError, "at least one"):
            verify_series_exports(self.bundle)


if __name__ == "__main__":
    unittest.main()
