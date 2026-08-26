import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orchestrator.pipeline.static_analysis import (
    Finding,
    generate_seeds_from_findings,
    run_semgrep,
)


class StaticAnalysisTests(unittest.TestCase):
    def test_run_semgrep_graceful_when_not_found(self):
        with patch("shutil.which", return_value=None):
            findings = run_semgrep(Path("."))
            self.assertEqual(findings, [])

    def test_seed_generation_from_findings(self):
        findings = [
            Finding("c.lang.security.insecure-use-strcpy-fn.insecure-use-strcpy-fn", "src/parser.c", 10, "Buffer overflow", "ERROR"),
            Finding("c.lang.security.insecure-format-string.insecure-format-string", "src/log.c", 20, "Format string", "WARNING"),
        ]
        seeds = generate_seeds_from_findings(findings)
        self.assertIn(b"A" * 128, seeds)
        self.assertIn(b"%s%s%s%s", seeds)


if __name__ == "__main__":
    unittest.main()
