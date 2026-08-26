import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.config import ROOT, settings
from orchestrator.models.schemas import CommandEvidence, ScanRequest, VerificationResult
from orchestrator.pipeline.discovery import Candidate
from orchestrator.pipeline.patch_gen import PatchOutcome
from orchestrator.pipeline.utils import RunResult


class RetryLoopTests(unittest.TestCase):
    @patch("orchestrator.main.verify")
    @patch("orchestrator.main.generate_patch")
    @patch("orchestrator.main.confirm")
    @patch("orchestrator.main.discover")
    @patch("orchestrator.main.build_fuzzer")
    @patch("orchestrator.main.build")
    def test_retry_loop_recovers_on_second_attempt(
        self,
        mock_build,
        mock_build_fuzzer,
        mock_discover,
        mock_confirm,
        mock_generate_patch,
        mock_verify,
    ):
        from orchestrator.main import scan

        # Setup successful builds
        mock_build.return_value = RunResult([], 0, "", "")
        mock_build_fuzzer.return_value = RunResult([], 0, "", "")

        # Setup 1 candidate with AddressSanitizer stderr
        cand_path = Path("fake_crash")
        candidate = Candidate(
            cand_path,
            b"crash_payload",
            RunResult([], 1, "", "ERROR: AddressSanitizer: buffer-overflow"),
        )
        mock_discover.return_value = [candidate]
        mock_confirm.return_value = (
            True,
            RunResult([], 1, "", "ERROR: AddressSanitizer: buffer-overflow"),
            "ERROR: AddressSanitizer: buffer-overflow",
        )

        # Attempt 1: Patch applied, but verification fails (differential re-fuzz fail)
        fail_verif = VerificationResult(
            clean_rebuild=True,
            pov_replay=True,
            regression_suite=True,
            differential_refuzz=False,
            evidence=[CommandEvidence(phase="V4", command=[], exit_code=1)],
        )
        # Attempt 2: Patch applied, verification succeeds
        pass_verif = VerificationResult(
            clean_rebuild=True,
            pov_replay=True,
            regression_suite=True,
            differential_refuzz=True,
            evidence=[],
        )

        mock_generate_patch.side_effect = [
            PatchOutcome(True, "CWE-120", "cause1", "fix1", "patch1", patched_file="src/parser.c", tier="rule"),
            PatchOutcome(True, "CWE-120", "cause2", "fix2", "patch2", patched_file="src/parser.c", tier="llm"),
        ]
        mock_verify.side_effect = [fail_verif, pass_verif]

        result = scan(ScanRequest(target="example-target", mode="full"))

        self.assertEqual(result.status, "verified")
        self.assertEqual(result.attempts, 2)
        self.assertEqual(mock_generate_patch.call_count, 2)
        # Verify second call received prior failure information
        second_call_kwargs = mock_generate_patch.call_args_list[1][1]
        self.assertEqual(second_call_kwargs["attempt"], 2)
        self.assertIn("Differential re-fuzz", second_call_kwargs["prior_failure"])


if __name__ == "__main__":
    unittest.main()
