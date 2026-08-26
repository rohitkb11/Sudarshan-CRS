import unittest
from unittest.mock import patch

from orchestrator.models.schemas import ScanRequest
from orchestrator.pipeline.discovery import Candidate
from orchestrator.pipeline.patch_gen import PatchOutcome
from orchestrator.pipeline.utils import RunResult
from orchestrator.models.schemas import VerificationResult


class DeltaScanTests(unittest.TestCase):
    @patch("orchestrator.main.verify")
    @patch("orchestrator.main.generate_patch")
    @patch("orchestrator.main.confirm")
    @patch("orchestrator.main.discover")
    @patch("orchestrator.main.build_fuzzer")
    @patch("orchestrator.main.build")
    def test_delta_scan_mode_passed_to_pipeline_result(
        self,
        mock_build,
        mock_build_fuzzer,
        mock_discover,
        mock_confirm,
        mock_generate_patch,
        mock_verify,
    ):
        from orchestrator.main import scan

        mock_build.return_value = RunResult([], 0, "", "")
        mock_build_fuzzer.return_value = RunResult([], 0, "", "")

        cand = Candidate(
            None,
            b"crash_data",
            RunResult([], 1, "", "AddressSanitizer: buffer-overflow"),
        )
        cand.input_path = "fake_path"
        mock_discover.return_value = [cand]
        mock_confirm.return_value = (True, RunResult([], 1, "", "AddressSanitizer"), "ERROR: AddressSanitizer: buffer-overflow")
        mock_generate_patch.return_value = PatchOutcome(
            True, "CWE-120", "cause", "fix", "msg", patched_file="src/parser.c", tier="rule"
        )
        mock_verify.return_value = VerificationResult(
            clean_rebuild=True,
            pov_replay=True,
            regression_suite=True,
            differential_refuzz=True,
            evidence=[],
        )

        result = scan(ScanRequest(target="example-target", mode="delta"))
        self.assertEqual(result.scan_mode, "delta")
        self.assertEqual(result.status, "verified")


if __name__ == "__main__":
    unittest.main()
