from dataclasses import dataclass
import json
import logging
from pathlib import Path
import shutil

from orchestrator.config import ROOT, settings
from .utils import run

logger = logging.getLogger(__name__)


@dataclass
class Finding:
    rule_id: str
    file_path: str
    line: int
    message: str
    severity: str


def run_semgrep(target_dir: Path) -> list[Finding]:
    """Run Semgrep static analyzer against the target source.
    
    Uses custom rules in static_analysis/semgrep_rules/ if available,
    falling back to p/c ruleset. Gracefully degrades if semgrep is missing.
    """
    semgrep_bin = shutil.which("semgrep")
    if not semgrep_bin:
        logger.info("semgrep not found in PATH; skipping static analysis stage.")
        return []

    local_rules = ROOT / "static_analysis" / "semgrep_rules"
    config_arg = f"--config={local_rules}" if local_rules.is_dir() else "--config=p/c"

    command = [
        semgrep_bin,
        "scan",
        config_arg,
        "--json",
        "--quiet",
        "--timeout=20",
    ]

    result = run(command, target_dir, settings.command_timeout_seconds)
    if result.exit_code != 0 and not result.stdout:
        logger.warning("Semgrep execution failed: %s", result.stderr)
        return []

    findings: list[Finding] = []
    try:
        data = json.loads(result.stdout)
        for item in data.get("results", []):
            findings.append(
                Finding(
                    rule_id=item.get("check_id", "unknown"),
                    file_path=item.get("path", ""),
                    line=item.get("start", {}).get("line", 1),
                    message=item.get("extra", {}).get("message", ""),
                    severity=item.get("extra", {}).get("severity", "WARNING"),
                )
            )
    except Exception as exc:
        logger.warning("Failed to parse Semgrep output: %s", exc)

    return findings


def generate_seeds_from_findings(findings: list[Finding]) -> list[bytes]:
    """Generate targeted fuzzing seeds based on static analysis findings."""
    seeds = [b"hello", b"!", b"A" * 8, b"A" * 15, b"A" * 16, b"A" * 32, b"A" * 64]
    for finding in findings:
        rid = finding.rule_id.lower()
        if any(k in rid for k in ("buffer", "overflow", "cwe-120", "strcpy", "strcat", "copy", "bounds")):
            seeds.extend([b"%" * 32, b"A" * 128, b"A" * 256, b"\x00" * 16, b"\xff" * 16])
        if any(k in rid for k in ("format", "sprintf", "printf", "cwe-134")):
            seeds.extend([b"%s%s%s%s", b"%x%x%x%x", b"%n", b"%p%p%p%p", b"%99999999s"])
        if any(k in rid for k in ("gets", "cwe-676")):
            seeds.extend([b"A" * 1024, b"\n", b"\r\n"])
    return list(dict.fromkeys(seeds))  # Deduplicate while preserving order
