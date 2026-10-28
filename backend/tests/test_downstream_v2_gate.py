import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.verify_historical_audit_exports import verify_exports
from tools.verify_historical_recomputation import verify_recomputation
from tools.verify_research_result_consistency import verify_result_consistency
from tools.verify_series_exports import verify_series_exports


class DownstreamV2GateTests(unittest.TestCase):
    def test_each_strict_consumer_rejects_v1_before_reading_other_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "reproducibility.json"
            result = {}
            bundle.write_text(json.dumps({
                "schema_version": 1, "result": result,
                "result_sha256": hashlib.sha256(b"{}").hexdigest(),
            }), encoding="utf-8")
            missing = root / "intentionally-missing-input"
            consumers = (
                lambda: verify_exports(bundle, missing, missing, require_v2=True),
                lambda: verify_recomputation(bundle, missing, require_v2=True),
                lambda: verify_result_consistency(bundle, require_v2=True),
                lambda: verify_series_exports(bundle, ic_path=missing, require_v2=True),
            )
            for consume in consumers:
                with self.subTest(consumer=consume.__code__.co_firstlineno):
                    with self.assertRaisesRegex(ValueError, "not schema v2"):
                        consume()


if __name__ == "__main__":
    unittest.main()
