import tempfile
import unittest
from pathlib import Path

from orchestrator.pipeline.discovery import (
    artifact_candidates,
    sanitizer_signature,
    seed_corpus,
)
from orchestrator.pipeline.utils import RunResult


class DiscoveryTests(unittest.TestCase):
    def test_seed_corpus_preserves_binary_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            corpus = Path(temporary)
            seed_corpus(corpus, [b"A\x00B"])

            self.assertEqual((corpus / "seed-00").read_bytes(), b"A\x00B")

    def test_only_libfuzzer_failure_artifacts_become_candidates(self):
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary)
            (artifacts / "crash-deadbeef").write_bytes(b"bad")
            (artifacts / "README.txt").write_text("ignore", encoding="utf-8")
            result = RunResult(["fuzzer"], 1, "", "AddressSanitizer")

            candidates = artifact_candidates(artifacts, result)

            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0].input_bytes, b"bad")
            self.assertIs(candidates[0].result, result)

    def test_sanitizer_signature_returns_first_ground_truth_line(self):
        stderr = "noise\nERROR: AddressSanitizer: stack-buffer-overflow\nmore noise"
        self.assertEqual(
            sanitizer_signature(stderr),
            "ERROR: AddressSanitizer: stack-buffer-overflow",
        )
        self.assertIsNone(sanitizer_signature("ordinary fuzzer progress"))


if __name__ == "__main__":
    unittest.main()
