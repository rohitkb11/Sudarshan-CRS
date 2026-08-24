from pathlib import Path
from datetime import datetime, timezone
from orchestrator.models.schemas import PipelineResult


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
    body += ["", result.message]
    path.write_text("\n".join(body) + "\n", encoding="utf-8")
    return path
