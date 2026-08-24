from pathlib import Path
from orchestrator.models.schemas import CommandEvidence, VerificationResult
from .build_harness import build
from .discovery import sanitizer_signature
from .utils import run


def _evidence(result):
    return CommandEvidence(command=result.command, exit_code=result.exit_code, stdout=result.stdout, stderr=result.stderr)


def verify(target_dir: Path, pov: str) -> VerificationResult:
    evidence = []
    rebuilt = build(target_dir, sanitized=True)
    evidence.append(_evidence(rebuilt))
    v1 = rebuilt.exit_code == 0
    if not v1:
        return VerificationResult(clean_rebuild=False, pov_replay=False, regression_suite=False, differential_refuzz=False, evidence=evidence)
    replay = run([str(target_dir / "build" / "parser"), pov], target_dir)
    evidence.append(_evidence(replay))
    v2 = sanitizer_signature(replay.stderr) is None
    tests = run(["python", "tests/test_parser.py"], target_dir)
    evidence.append(_evidence(tests))
    v3 = tests.exit_code == 0
    variants = [pov[:-1], pov + "A", pov.replace("A", "B", 1)]
    fuzz_results = [run([str(target_dir / "build" / "parser"), item], target_dir) for item in variants if item]
    evidence.extend(_evidence(item) for item in fuzz_results)
    v4 = all(sanitizer_signature(item.stderr) is None for item in fuzz_results)
    return VerificationResult(clean_rebuild=v1, pov_replay=v2, regression_suite=v3, differential_refuzz=v4, evidence=evidence)
