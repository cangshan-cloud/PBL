import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.verify_compose_stack import verify_snapshot


class ComposeStackSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.run = {"id": "run-1", "result": {"ic_mean": 0.2}}
        self.report = "<html>研究报告</html>"
        canonical = json.dumps(self.run["result"], ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
        self.bundle = {
            "schema_version": 1,
            "task": {"id": "run-1"},
            "result": dict(self.run["result"]),
            "result_sha256": hashlib.sha256(canonical).hexdigest(),
            "report_sha256": hashlib.sha256(self.report.encode("utf-8")).hexdigest(),
        }

    def test_matching_snapshot_passes(self):
        verify_snapshot(self.bundle, self.run, self.report)

    def test_changed_result_or_report_is_rejected(self):
        self.bundle["result"] = {"ic_mean": 0.3}
        with self.assertRaisesRegex(RuntimeError, "differs from the task"):
            verify_snapshot(self.bundle, self.run, self.report)
        self.bundle["result"] = dict(self.run["result"])
        self.bundle["result_sha256"] = "0" * 64
        with self.assertRaisesRegex(RuntimeError, "result checksum mismatch"):
            verify_snapshot(self.bundle, self.run, self.report)
        self.bundle["result_sha256"] = hashlib.sha256(json.dumps(
            self.run["result"], ensure_ascii=False, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        with self.assertRaisesRegex(RuntimeError, "report checksum mismatch"):
            verify_snapshot(self.bundle, self.run, self.report + " changed")

    def test_missing_task_or_result_is_rejected(self):
        self.bundle["task"] = None
        with self.assertRaisesRegex(RuntimeError, "does not match the completed run"):
            verify_snapshot(self.bundle, self.run, self.report)
        self.bundle["task"] = {"id": self.run["id"]}
        self.bundle["result"] = None
        with self.assertRaisesRegex(RuntimeError, "differs from the task"):
            verify_snapshot(self.bundle, self.run, self.report)


if __name__ == "__main__":
    unittest.main()
