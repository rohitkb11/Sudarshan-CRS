from pathlib import Path
import sys

from orchestrator.config import settings
from orchestrator.models.schemas import CommandEvidence, VerificationResult
from .build_harness import binary_path, build, build_fuzzer, clean, fuzzer_path
from .discovery import artifact_candidates, reset_directory, run_fuzzer, sanitizer_signature, seed_corpus
from .utils import run


def _evidence(result, phase: str):
    return CommandEvidence(
        phase=phase,
        command=result.command,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def verify(target_dir: Path, pov_path: Path) -> VerificationResult:
    evidence = []

    # V1: Clean Rebuild
    cleaned = clean(target_dir)
    evidence.append(_evidence(cleaned, "V1 clean workspace"))
    normal_build = build(target_dir, sanitized=False, clean_first=False)
    evidence.append(_evidence(normal_build, "V1 normal build"))
    sanitized_build = build(target_dir, sanitized=True, clean_first=False)
    evidence.append(_evidence(sanitized_build, "V1 sanitizer build"))
    fuzzer_build = build_fuzzer(target_dir, clean_first=False)
    evidence.append(_evidence(fuzzer_build, "V1 fuzzer build"))
    v1 = all(
        result.exit_code == 0
        for result in (cleaned, normal_build, sanitized_build, fuzzer_build)
    )
    if not v1:
        return VerificationResult(
            clean_rebuild=False,
            pov_replay=False,
            regression_suite=False,
            differential_refuzz=False,
            evidence=evidence,
        )

    # V2: Original PoV Replay
    replay = run(
        [str(fuzzer_path(target_dir)), str(pov_path), "-runs=1"],
        target_dir,
        settings.command_timeout_seconds,
    )
    evidence.append(_evidence(replay, "V2 original PoV replay"))
    v2 = replay.exit_code == 0 and sanitizer_signature(replay.stderr) is None

    # V3: Regression Suite (Dynamically discover target regression tests)
    test_dir = target_dir / "tests"
    test_scripts = sorted(test_dir.glob("test_*.py")) if test_dir.is_dir() else []
    if test_scripts:
        test_script_rel = str(test_scripts[0].relative_to(target_dir))
        tests = run(
            [sys.executable, test_script_rel, str(binary_path(target_dir, "normal").resolve())],
            target_dir,
            settings.command_timeout_seconds,
        )
        evidence.append(_evidence(tests, f"V3 regression suite ({test_script_rel})"))
        v3 = tests.exit_code == 0
    else:
        # Fallback smoke test against normal binary
        tests = run(
            [str(binary_path(target_dir, "normal").resolve()), "smoke_test"],
            target_dir,
            settings.command_timeout_seconds,
        )
        evidence.append(_evidence(tests, "V3 regression smoke test"))
        v3 = tests.exit_code in (0, 1)

    # V4: Differential Re-Fuzz
    verification_dir = target_dir / ".crs" / "verification"
    corpus_dir = verification_dir / "corpus"
    artifact_dir = verification_dir / "artifacts"
    reset_directory(verification_dir)
    corpus_dir.mkdir()
    artifact_dir.mkdir()
    seed_corpus(corpus_dir, [pov_path.read_bytes()])
    refuzz = run_fuzzer(
        target_dir,
        corpus_dir,
        artifact_dir,
        runs=settings.differential_fuzz_runs,
        max_time_seconds=min(settings.fuzz_time_seconds, 5),
        max_input_bytes=settings.fuzz_max_input_bytes,
    )
    evidence.append(_evidence(refuzz, "V4 differential re-fuzz"))
    nearby_crashes = artifact_candidates(artifact_dir, refuzz)
    v4 = refuzz.exit_code == 0 and sanitizer_signature(refuzz.stderr) is None and not nearby_crashes

    return VerificationResult(
        clean_rebuild=v1,
        pov_replay=v2,
        regression_suite=v3,
        differential_refuzz=v4,
        evidence=evidence,
    )
