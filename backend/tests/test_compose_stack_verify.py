import hashlib
import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from tools.verify_compose_stack import main, verify_snapshot
from verify_compose_real_sample import main as real_sample_main


class ComposeStackSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.run = {"id": "run-1", "result": {"ic_mean": 0.2}}
        self.report = "<html>研究报告</html>"
        canonical = json.dumps(self.run["result"], ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
        self.bundle = {
            "schema_version": 2,
            "task": {"id": "run-1"},
            "result": dict(self.run["result"]),
            "result_sha256": hashlib.sha256(canonical).hexdigest(),
            "report_sha256": hashlib.sha256(self.report.encode("utf-8")).hexdigest(),
        }
        canonical_bundle = json.dumps(self.bundle, ensure_ascii=False, sort_keys=True,
                                      separators=(",", ":")).encode("utf-8")
        self.bundle["bundle_sha256"] = hashlib.sha256(canonical_bundle).hexdigest()

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

    def test_v2_metadata_checksum_and_v1_legacy(self):
        self.bundle["dataset"] = {"checksum_sha256": "changed"}
        with self.assertRaisesRegex(RuntimeError, "bundle checksum mismatch"):
            verify_snapshot(self.bundle, self.run, self.report)
        self.bundle.pop("dataset")
        self.bundle.pop("bundle_sha256")
        self.bundle["schema_version"] = 1
        verify_snapshot(self.bundle, self.run, self.report)

    def test_write_check_requires_acknowledgement_before_network(self):
        with patch.dict(os.environ, {"FACTORLAB_SMOKE_URL": "http://127.0.0.1:18002/api/v1"}), \
                patch("tools.verify_compose_stack.request") as request, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main([])
        self.assertEqual(raised.exception.code, 2)
        request.assert_not_called()

    def test_write_check_requires_explicit_target_before_network(self):
        with patch.dict(os.environ, {"FACTORLAB_SMOKE_PASSWORD": "test"}, clear=True), \
                patch("tools.verify_compose_stack.request") as request, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main(["--acknowledge-writes"])
        self.assertEqual(raised.exception.code, 2)
        request.assert_not_called()

    def test_confirmed_target_reaches_login(self):
        with patch.dict(os.environ, {"FACTORLAB_SMOKE_URL": "http://127.0.0.1:18002/api/v1",
                                      "FACTORLAB_SMOKE_PASSWORD": "test"}), \
                patch("tools.verify_compose_stack.request", side_effect=RuntimeError("sentinel")) as request:
            with self.assertRaisesRegex(RuntimeError, "sentinel"):
                main(["--acknowledge-writes"])
        request.assert_called_once()

    def test_real_sample_requires_acknowledgement_before_file_or_network(self):
        with patch.dict(os.environ, {"FACTORLAB_SMOKE_URL": "http://127.0.0.1:18002/api/v1"}), \
                patch("verify_compose_real_sample.request") as request, \
                patch("verify_compose_real_sample.Path.read_bytes") as read_bytes, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                real_sample_main([])
        self.assertEqual(raised.exception.code, 2)
        request.assert_not_called()
        read_bytes.assert_not_called()


if __name__ == "__main__":
    unittest.main()
