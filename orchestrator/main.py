from pathlib import Path
from fastapi import FastAPI, HTTPException
from orchestrator.config import ROOT, settings
from orchestrator.models.schemas import PipelineResult, ScanRequest
from orchestrator.pipeline.build_harness import build
from orchestrator.pipeline.confirm_pov import confirm
from orchestrator.pipeline.context_map import build_context_map
from orchestrator.pipeline.discovery import discover
from orchestrator.pipeline.patch_gen import apply_rule_patch
from orchestrator.pipeline.patch_memory import PatchMemory
from orchestrator.pipeline.report import write_report
from orchestrator.pipeline.verify import verify
from orchestrator.pipeline.workspace import create_workspace
from orchestrator.pipeline.artifacts import write_patch

app = FastAPI(title="AI Kavach CRS", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scans", response_model=PipelineResult)
def scan(request: ScanRequest) -> PipelineResult:
    source_target = ROOT / "targets" / request.target
    if not source_target.is_dir():
        raise HTTPException(404, f"Unknown target: {request.target}")
    target_dir = create_workspace(source_target, settings.data_dir / "runs")
    initial_build = build(target_dir, sanitized=True)
    if initial_build.exit_code != 0:
        return PipelineResult(status="error", target=request.target, message="Sanitized build failed: " + initial_build.stderr[-500:])
    build_context_map(target_dir)
    for candidate in discover(target_dir, settings.fuzz_cases):
        confirmed, _, signature = confirm(target_dir, candidate)
        if not confirmed:
            continue
        patch_source = target_dir / "src" / "parser.c"
        before_patch = patch_source.read_text(encoding="utf-8")
        outcome = apply_rule_patch(target_dir)
        if not outcome.applied:
            return PipelineResult(status="unverified", target=request.target, crash_signature=signature, message=outcome.message)
        after_patch = patch_source.read_text(encoding="utf-8")
        patch_file = write_patch(before_patch, after_patch, "src/parser.c", settings.data_dir / "reports" / f"{target_dir.name}.patch")
        verification = verify(target_dir, candidate.input_text)
        passed = all([verification.clean_rebuild, verification.pov_replay, verification.regression_suite, verification.differential_refuzz])
        result = PipelineResult(status="verified" if passed else "unverified", target=request.target, vulnerability=outcome.bug_class,
                                crash_signature=signature, patch_applied=True, attempts=1, verification=verification,
                                patch_path=str(patch_file.relative_to(ROOT)) if patch_file else None,
                                workspace_path=str(target_dir.relative_to(ROOT)), message=outcome.message)
        if passed:
            PatchMemory(settings.data_dir / "patch_memory.jsonl").record(outcome.bug_class, outcome.root_cause, outcome.fix_pattern)
        result.report_path = str(write_report(ROOT, result).relative_to(ROOT))
        return result
    return PipelineResult(status="no_vulnerability", target=request.target, message="No sanitizer-confirmed crash within the fuzz budget.")
