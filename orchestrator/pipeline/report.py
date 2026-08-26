from pathlib import Path
from datetime import datetime, timezone
import json
from orchestrator.models.schemas import PipelineResult


def _clip(value: str, limit: int = 12000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n... clipped {len(value) - limit} characters ..."


def _indent(value: str) -> str:
    if not value:
        return "    <empty>"
    return "\n".join(f"    {line}" for line in _clip(value).splitlines())


def write_report(root: Path, result: PipelineResult) -> Path:
    directory = root / "data" / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    target_slug = result.target.replace("/", "-").replace("\\", "-")
    path = directory / f"{target_slug}-{result.scan_mode}-{stamp}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    checks = result.verification

    body = [
        "# AI Kavach CRS — Autonomous Verification & Evidence Report",
        "",
        "> Autonomous cyber-reasoning system report generated for the Indian Army / Terrier Cyber Quest 2026.",
        "",
        "## Executive Summary",
        "",
        f"- **Overall Status**: **{result.status.upper()}**",
        f"- **Target Software**: `{result.target}`",
        f"- **Scan Mode**: `{result.scan_mode.upper()}`",
        f"- **Vulnerability Class**: `{result.vulnerability or 'None Detected'}`",
        f"- **Crash Signature**: `{result.crash_signature or 'N/A'}`",
        f"- **Patch Attempts Used**: `{result.attempts}`",
        f"- **Result Summary**: {result.message}",
        "",
        "---",
        "",
        "## §8 Proof Checklist (Non-Negotiable Acceptance Criteria)",
        "",
        "A fix is deemed proven only when all four independent verification gates pass:",
        "",
    ]

    if checks:
        body += [
            f"| Gate | Verification Phase | Status | Objective |",
            f"|---|---|---|---|",
            f"| **V1** | Clean Rebuild | {'✅ **PASS**' if checks.clean_rebuild else '❌ **FAIL**'} | Patched code compiles cleanly under normal, sanitizer, and fuzzer modes |",
            f"| **V2** | Original PoV Replay | {'✅ **PASS**' if checks.pov_replay else '❌ **FAIL**'} | Exact input that caused original crash no longer triggers any sanitizer fault |",
            f"| **V3** | Regression Suite | {'✅ **PASS**' if checks.regression_suite else '❌ **FAIL**'} | Target's test suite passes completely with no functional regression |",
            f"| **V4** | Differential Re-Fuzz | {'✅ **PASS**' if checks.differential_refuzz else '❌ **FAIL**'} | Fuzzing variations around PoV reveal no residual or bypass vulnerabilities |",
            "",
        ]

    if result.patch_path:
        patch_file = root / result.patch_path
        patch_text = ""
        if patch_file.is_file():
            try:
                patch_text = patch_file.read_text(encoding="utf-8")
            except Exception:
                pass
        body += [
            "## Verified Patch Artifact",
            "",
            f"Artifact Path: `{result.patch_path}`",
            "",
            "```diff",
            patch_text or "No diff text available",
            "```",
            "",
        ]

    if result.pov_path:
        body += [
            "## Proof of Vulnerability (PoV)",
            "",
            f"- **Artifact**: `{result.pov_path}`",
            f"- **SHA-256 Digest**: `{result.pov_sha256}`",
            f"- **Base64 Payload**: `{result.pov_base64}`",
            "",
        ]

    if result.confirmation:
        body += [
            "## Pre-Patch Sanitizer Evidence (Ground Truth)",
            "",
            f"Command: `{json.dumps(result.confirmation.command)}`",
            f"Exit code: `{result.confirmation.exit_code}`",
            "",
            "```text",
            _clip(result.confirmation.stderr) or "<no stderr output>",
            "```",
            "",
        ]

    if checks and checks.evidence:
        body += ["## Step-by-Step Verification Command Trace", ""]
        for item in checks.evidence:
            body += [
                f"### Phase: {item.phase}",
                f"- **Command**: `{json.dumps(item.command)}`",
                f"- **Exit Code**: `{item.exit_code}`",
                "",
            ]
            if item.stdout.strip():
                body += [
                    "Standard Output:",
                    "```text",
                    _clip(item.stdout),
                    "```",
                    "",
                ]
            if item.stderr.strip():
                body += [
                    "Standard Error:",
                    "```text",
                    _clip(item.stderr),
                    "```",
                    "",
                ]

    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path
