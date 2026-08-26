import base64
import hashlib
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from orchestrator.config import ROOT, settings
from orchestrator.models.schemas import CommandEvidence, PipelineResult, ScanRequest
from orchestrator.pipeline.artifacts import write_patch
from orchestrator.pipeline.build_harness import build, build_fuzzer
from orchestrator.pipeline.confirm_pov import confirm
from orchestrator.pipeline.context_map import build_context_map
from orchestrator.pipeline.discovery import deduplicate_candidates, discover
from orchestrator.pipeline.patch_gen import generate_patch
from orchestrator.pipeline.patch_memory import PatchMemory
from orchestrator.pipeline.report import write_report
from orchestrator.pipeline.static_analysis import generate_seeds_from_findings, run_semgrep
from orchestrator.pipeline.verify import verify
from orchestrator.pipeline.workspace import create_workspace

logger = logging.getLogger("orchestrator")
app = FastAPI(title="AI Kavach CRS", version="0.2.0")


def safe_relpath(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except Exception:
        return str(path)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "retry_cap": settings.retry_cap,
        "llm_provider": settings.llm_provider,
        "groq_configured": bool(settings.groq_api_key),
        "anthropic_configured": bool(settings.anthropic_api_key),
        "llm_configured": bool(settings.groq_api_key or settings.anthropic_api_key),
    }


@app.get("/targets")
def list_targets():
    targets_dir = ROOT / "targets"
    if not targets_dir.is_dir():
        return {"targets": []}
    return {
        "targets": [
            p.name for p in targets_dir.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        ]
    }


@app.get("/patch-memory")
def get_patch_memory():
    memory = PatchMemory(settings.data_dir / "patch_memory.jsonl")
    return {
        "stats": memory.get_stats(),
        "entries": memory.list_all(),
    }


@app.post("/scans", response_model=PipelineResult)
def scan(request: ScanRequest) -> PipelineResult:
    target_clean = request.target.replace("\\", "/").strip("/")
    source_target = (ROOT / "targets" / target_clean).resolve()
    targets_root = (ROOT / "targets").resolve()
    try:
        source_target.relative_to(targets_root)
    except ValueError:
        raise HTTPException(400, "Invalid target path traversal")

    if not source_target.is_dir():
        raise HTTPException(404, f"Unknown target: {request.target}")

    # Step 0: Create isolated workspace
    target_dir = create_workspace(source_target, settings.data_dir / "runs")

    # Stage 1: Build Harness (Normal, Sanitized, Fuzzer)
    normal_build = build(target_dir, sanitized=False, clean_first=True)
    sanitized_build = build(target_dir, sanitized=True, clean_first=False)
    fuzzer_build = build_fuzzer(target_dir, clean_first=False)

    for label, build_result in (
        ("Normal", normal_build),
        ("Sanitized", sanitized_build),
        ("Fuzzer", fuzzer_build),
    ):
        if build_result.exit_code != 0:
            return PipelineResult(
                status="error",
                target=request.target,
                scan_mode=request.mode,
                workspace_path=safe_relpath(target_dir),
                message=f"{label} build failed: {build_result.stderr[-1000:]}",
            )

    # Stage 3: Context Map (Supporting code index)
    build_context_map(target_dir)

    # Static Analysis: Semgrep scan + smart seeds
    findings = run_semgrep(target_dir)
    initial_seeds = generate_seeds_from_findings(findings) if findings else None

    # Determine fuzzing parameters based on Full vs Delta scan mode (Guardrail 5)
    fuzz_time = settings.fuzz_time_seconds
    fuzz_runs = settings.fuzz_runs
    if request.mode == "delta":
        fuzz_time = max(3, fuzz_time // 2)
        fuzz_runs = max(10000, fuzz_runs // 2)

    # Stage 2: Discovery Engine
    candidates = discover(
        target_dir,
        fuzz_time,
        fuzz_runs,
        settings.fuzz_max_input_bytes,
        initial_seeds=initial_seeds,
    )

    # Deduplicate crash artifacts by signature (README Guardrail 4)
    unique_candidates = deduplicate_candidates(candidates, target_dir)

    patch_memory = PatchMemory(settings.data_dir / "patch_memory.jsonl")

    for candidate in unique_candidates:
        # Stage 4: Confirm Proof of Vulnerability (PoV)
        confirmed, replay, signature = confirm(target_dir, candidate)
        if not confirmed:
            continue

        # Snapshot original source files before patching for restoration on retries
        original_sources = {
            p: p.read_text(encoding="utf-8")
            for p in target_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in (".c", ".cpp", ".cc", ".cxx", ".h", ".hpp")
            and ".crs" not in p.parts and "build" not in p.parts
        }

        last_failure_reason = None
        last_result: PipelineResult | None = None

        # Stage 5 & 6: Tiered Patch Generation + Verification Retry Loop (Capped at retry_cap)
        for attempt in range(1, settings.retry_cap + 1):
            # Restore pristine source before each patch attempt
            for p, content in original_sources.items():
                p.write_text(content, encoding="utf-8")

            # Stage 5: Tiered Patch Generation (Rules -> Patch Memory -> LLM)
            outcome = generate_patch(
                target_dir,
                crash_signature=signature,
                patch_memory=patch_memory,
                attempt=attempt,
                prior_failure=last_failure_reason,
                pov_bytes=candidate.input_bytes,
            )

            if not outcome.applied:
                last_failure_reason = outcome.message
                continue

            patched_file_rel = outcome.patched_file or "src/parser.c"
            patched_file_path = target_dir / patched_file_rel
            before_patch = original_sources.get(patched_file_path, "")
            after_patch = patched_file_path.read_text(encoding="utf-8") if patched_file_path.exists() else ""

            patch_file = write_patch(
                before_patch,
                after_patch,
                patched_file_rel,
                settings.data_dir / "reports" / f"{target_dir.name}-attempt{attempt}.patch",
            )

            # Stage 6: Verification Suite (V1-V4 Proof Checklist)
            verification = verify(target_dir, candidate.input_path)
            passed = all([
                verification.clean_rebuild,
                verification.pov_replay,
                verification.regression_suite,
                verification.differential_refuzz,
            ])

            pov_bytes = candidate.input_bytes
            result = PipelineResult(
                status="verified" if passed else "unverified",
                target=request.target,
                scan_mode=request.mode,
                vulnerability=outcome.bug_class,
                crash_signature=signature,
                pov_path=safe_relpath(candidate.input_path),
                pov_sha256=hashlib.sha256(pov_bytes).hexdigest(),
                pov_base64=base64.b64encode(pov_bytes).decode("ascii"),
                confirmation=CommandEvidence(
                    phase="Pre-patch sanitizer replay",
                    command=replay.command,
                    exit_code=replay.exit_code,
                    stdout=replay.stdout,
                    stderr=replay.stderr,
                ),
                patch_applied=True,
                attempts=attempt,
                verification=verification,
                patch_path=safe_relpath(patch_file),
                workspace_path=safe_relpath(target_dir),
                message=f"Attempt {attempt}/{settings.retry_cap}: {outcome.message}",
            )

            if passed:
                # Stage 5.3: Record verified pattern into Patch Memory
                patch_memory.record(outcome.bug_class, outcome.root_cause, outcome.fix_pattern)
                # Stage 7: Evidence Report
                result.report_path = safe_relpath(write_report(ROOT, result))
                return result

            # Collect specific failure reasons to feed into the next retry
            failures = []
            if not verification.clean_rebuild:
                failures.append("Clean rebuild failed")
            if not verification.pov_replay:
                failures.append("Original PoV still crashes")
            if not verification.regression_suite:
                failures.append("Regression test suite failed")
            if not verification.differential_refuzz:
                failures.append("Differential re-fuzz found nearby crashes")
            last_failure_reason = "; ".join(failures) or "Verification check failed"
            last_result = result

        # If all retries exhausted for this candidate
        if last_result:
            last_result.report_path = safe_relpath(write_report(ROOT, last_result))
            return last_result

        return PipelineResult(
            status="unverified",
            target=request.target,
            scan_mode=request.mode,
            crash_signature=signature,
            message=f"Failed to generate a verified patch after {settings.retry_cap} attempts: {last_failure_reason}",
        )

    return PipelineResult(
        status="no_vulnerability",
        target=request.target,
        scan_mode=request.mode,
        message="No sanitizer-confirmed crash within the fuzz budget.",
    )


# Mount dashboard frontend if compiled static assets exist
dist_dir = ROOT / "dashboard" / "dist"
if dist_dir.is_dir():
    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def dashboard_index():
        return FileResponse(dist_dir / "index.html")
