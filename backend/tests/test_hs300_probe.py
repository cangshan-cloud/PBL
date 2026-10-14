import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from probe_hs300_history import collect, query_rows
from fetch_hs300_members import collect_with_checkpoints
from verify_hs300_members import verify_snapshot


class Result:
    error_code = "0"
    error_msg = "success"

    def __init__(self, fields, rows):
        self.fields = fields
        self.rows = iter(rows)

    def next(self):
        self.current = next(self.rows, None)
        return self.current is not None

    def get_row_data(self):
        return self.current


class Source:
    def __init__(self, dates):
        self.dates = dates
        self.queries = []

    def query_trade_dates(self, **kwargs):
        return Result(["calendar_date", "is_trading_day"], self.dates)

    def query_hs300_stocks(self, day):
        self.queries.append(day)
        return Result(["code", "updateDate"], [[f"sh.{600000 + i:06d}", day] for i in range(300)])


class Hs300ProbeTests(unittest.TestCase):
    def setUp(self):
        version = patch("fetch_hs300_members.importlib.metadata.version", return_value="0.9.4")
        version.start()
        self.addCleanup(version.stop)

    def test_collects_only_trading_day_rosters_and_preserves_source_update_date(self):
        source = Source([["2024-06-28", "1"], ["2024-06-29", "0"], ["2024-06-30", "0"], ["2024-07-01", "1"]])
        calendar, members = collect(source, "2024-06-28", "2024-07-01")
        self.assertEqual(len(calendar), 4)
        self.assertEqual(source.queries, ["2024-06-28", "2024-07-01"])
        self.assertEqual(len(members), 600)
        self.assertEqual(members[0]["update_date"], "2024-06-28")

    def test_rejects_calendar_gap_and_bad_roster(self):
        with self.assertRaisesRegex(ValueError, "every requested date"):
            collect(Source([["2024-06-28", "1"], ["2024-06-30", "0"]]), "2024-06-28", "2024-06-30")

        class ShortSource(Source):
            def query_hs300_stocks(self, day):
                return Result(["code", "updateDate"], [["sh.600000", day]])

        with self.assertRaisesRegex(ValueError, "300 unique"):
            collect(ShortSource([["2024-06-28", "1"]]), "2024-06-28", "2024-06-28")

    def test_rejects_missing_fields(self):
        with self.assertRaisesRegex(ValueError, "fields missing"):
            query_rows(Result(["code"], [["sh.600000"]]), {"code", "updateDate"})

    def test_full_snapshot_and_finalized_guard(self):
        source = Source([["2024-06-28", "1"], ["2024-06-29", "0"], ["2024-06-30", "0"], ["2024-07-01", "1"]])
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "snapshot"
            manifest = collect_with_checkpoints(source, "2024-06-28", "2024-07-01", target)
            self.assertEqual(manifest["trading_day_count"], 2)
            self.assertEqual(manifest["member_row_count"], 600)
            self.assertEqual(len(manifest["daily_roster_sha256"]), 2)
            verified = verify_snapshot(target)
            self.assertEqual(verified["trading_day_count"], 2)
            self.assertEqual(verified["changed_query_days"], [])
            with self.assertRaisesRegex(ValueError, "already finalized"):
                collect_with_checkpoints(source, "2024-06-28", "2024-07-01", target)

            roster = target / "daily_rosters" / "2024-07-01.csv"
            roster.write_bytes(roster.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "daily roster hash mismatch"):
                verify_snapshot(target)

    def test_resume_uses_validated_checkpoint_without_refetching(self):
        source = Source([["2024-06-28", "1"], ["2024-06-29", "0"], ["2024-06-30", "0"], ["2024-07-01", "1"]])
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "snapshot"
            target.mkdir()
            roster_dir = target / "daily_rosters"
            roster_dir.mkdir()
            from probe_hs300_history import render_csv, normalize_members
            rows = normalize_members([{"code": f"sh.{600000 + i:06d}", "updateDate": "2024-06-28"} for i in range(300)], "2024-06-28")
            (roster_dir / "2024-06-28.csv").write_bytes(render_csv(rows, ("query_date", "code", "update_date")))
            manifest = collect_with_checkpoints(source, "2024-06-28", "2024-07-01", target)
            self.assertEqual(manifest["member_row_count"], 600)
            self.assertEqual(source.queries, ["2024-07-01"])

    def test_verifier_reports_query_day_change_without_claiming_effective_date(self):
        class ChangedSource(Source):
            def query_hs300_stocks(self, day):
                codes = [f"sh.{600000 + i:06d}" for i in range(300)]
                if day == "2024-07-01":
                    codes[-1] = "sz.000001"
                return Result(["code", "updateDate"], [[code, day] for code in codes])

        source = ChangedSource([["2024-06-28", "1"], ["2024-06-29", "0"], ["2024-06-30", "0"], ["2024-07-01", "1"]])
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "snapshot"
            collect_with_checkpoints(source, "2024-06-28", "2024-07-01", target)
            result = verify_snapshot(target)
            self.assertEqual(result["changed_query_days"], [{"query_date": "2024-07-01", "removed_count": 1, "added_count": 1}])
            self.assertIn("do not independently prove", result["caution"])


if __name__ == "__main__":
    unittest.main()
