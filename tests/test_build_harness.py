import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrator.config import settings
from orchestrator.pipeline.build_harness import (
    binary_path,
    build,
    build_fuzzer,
    clean,
    fuzzer_path,
)
from orchestrator.pipeline.utils import RunResult


class BuildHarnessTests(unittest.TestCase):
    def setUp(self):
        self.target = Path("target")
        self.completed = RunResult([], 0, "", "")

    @patch("orchestrator.pipeline.build_harness.run")
    def test_clean_only_removes_build_outputs(self, run_mock):
        run_mock.return_value = self.completed

        self.assertIs(clean(self.target), self.completed)
        run_mock.assert_called_once_with(
            [settings.make, "clean"],
            self.target,
            settings.command_timeout_seconds,
        )

    @patch("orchestrator.pipeline.build_harness.run")
    def test_build_can_preserve_other_build_modes(self, run_mock):
        run_mock.return_value = self.completed

        build(self.target, sanitized=False, clean_first=False)

        run_mock.assert_called_once_with(
            [settings.make, "build", "MODE=normal", f"CC={settings.clang}"],
            self.target,
            settings.command_timeout_seconds,
        )

    @patch("orchestrator.pipeline.build_harness.run")
    def test_fuzzer_build_uses_dedicated_make_target(self, run_mock):
        run_mock.return_value = self.completed

        build_fuzzer(self.target, clean_first=False)

        run_mock.assert_called_once_with(
            [settings.make, "fuzz", "MODE=fuzzer", f"CC={settings.clang}"],
            self.target,
            settings.command_timeout_seconds,
        )

    def test_binary_locations_are_mode_specific(self):
        self.assertEqual(binary_path(self.target, "normal"), self.target / "build/normal/parser")
        self.assertEqual(fuzzer_path(self.target), self.target / "build/fuzzer/parser_fuzzer")


if __name__ == "__main__":
    unittest.main()
