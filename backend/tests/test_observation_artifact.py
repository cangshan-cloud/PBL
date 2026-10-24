import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.domain.research import Observation
from app.services.observation_artifact import create_observation_artifact, read_observation_artifact


class ObservationArtifactTests(unittest.TestCase):
    def test_roundtrip_and_checksum_guard(self):
        with tempfile.TemporaryDirectory() as root:
            observations = [Observation(date(2025, 1, 3), "B", 2.0, .02),
                            Observation(date(2025, 1, 2), "A", 1.0, .01)]
            artifact = create_observation_artifact("run-1", observations, Path(root))
            restored = read_observation_artifact(artifact)
            self.assertEqual(len(restored), 2)
            self.assertEqual(restored[(date(2025, 1, 2), "A")], observations[1])
            path = Path(artifact.storage_uri)
            path.write_bytes(path.read_bytes() + b"changed")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                read_observation_artifact(artifact)

    def test_missing_artifact_is_value_error(self):
        with tempfile.TemporaryDirectory() as root:
            artifact = create_observation_artifact("run-2", [], Path(root))
            Path(artifact.storage_uri).unlink()
            with self.assertRaisesRegex(ValueError, "unavailable"):
                read_observation_artifact(artifact)
