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
    path = directory / f"{result.target}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.md"
    checks = result.verification
    body = ["# AI Kavach CRS Evidence Report", "", f"Status: **{result.status}**", f"Target: `{result.target}`",
            f"Vulnerability: {result.vulnerability or 'none'}", f"Crash signature: `{result.crash_signature or 'n/a'}`", "", "## Proof checklist"]
    if checks:
        body += [f"- V1 clean rebuild: {'PASS' if checks.clean_rebuild else 'FAIL'}",
                 f"- V2 original PoV replay: {'PASS' if checks.pov_replay else 'FAIL'}",
                 f"- V3 regression suite: {'PASS' if checks.regression_suite else 'FAIL'}",
                 f"- V4 differential re-fuzz: {'PASS' if checks.differential_refuzz else 'FAIL'}"]
    if result.patch_path:
        body += ["", f"Patch artifact: `{result.patch_path}`"]
    if result.pov_path:
        body += [
            "",
            "## Proof of vulnerability",
            "",
            f"Artifact: `{result.pov_path}`",
            f"SHA-256: `{result.pov_sha256}`",
            f"Base64: `{result.pov_base64}`",
        ]
    if result.confirmation:
        body += [
            "",
            "## Before-patch sanitizer evidence",
            "",
            f"Command: `{json.dumps(result.confirmation.command)}`",
            f"Exit code: `{result.confirmation.exit_code}`",
            "",
            "Standard error:",
            "",
            _indent(result.confirmation.stderr),
        ]
    if checks:
        body += ["", "## Verification command evidence"]
        for item in checks.evidence:
            body += [
                "",
                f"### {item.phase}",
                "",
                f"Command: `{json.dumps(item.command)}`",
                f"Exit code: `{item.exit_code}`",
                "",
                "Standard output:",
                "",
                _indent(item.stdout),
                "",
                "Standard error:",
                "",
                _indent(item.stderr),
            ]
    body += ["", "## Result", "", result.message]
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path
