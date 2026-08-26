from dataclasses import dataclass
from pathlib import Path
import shutil

from orchestrator.config import settings
from .build_harness import fuzzer_path
from .utils import RunResult, run


@dataclass
class Candidate:
    input_path: Path
    input_bytes: bytes
    result: RunResult


ARTIFACT_PREFIXES = ("crash-", "leak-", "oom-", "slow-unit-", "timeout-")
SANITIZER_MARKERS = (
    "AddressSanitizer",
    "UndefinedBehaviorSanitizer",
    "MemorySanitizer",
    "runtime error:",
)


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def seed_corpus(path: Path, seeds: list[bytes] | None = None) -> None:
    path.mkdir(parents=True, exist_ok=True)
    initial_seeds = seeds or [b"hello", b"!", b"A" * 8, b"A" * 15]
    for index, seed in enumerate(initial_seeds):
        (path / f"seed-{index:02d}").write_bytes(seed)


def run_fuzzer(
    target_dir: Path,
    corpus_dir: Path,
    artifact_dir: Path,
    *,
    runs: int,
    max_time_seconds: int,
    max_input_bytes: int,
) -> RunResult:
    artifact_prefix = artifact_dir.resolve().as_posix() + "/"
    command = [
        str(fuzzer_path(target_dir)),
        str(corpus_dir),
        f"-artifact_prefix={artifact_prefix}",
        f"-max_total_time={max_time_seconds}",
        f"-runs={runs}",
        f"-max_len={max_input_bytes}",
        "-print_final_stats=1",
    ]
    timeout = max(settings.command_timeout_seconds, max_time_seconds + 5)
    return run(command, target_dir, timeout)


def artifact_candidates(artifact_dir: Path, result: RunResult) -> list[Candidate]:
    if not artifact_dir.exists():
        return []
    artifacts = sorted(
        (
            path
            for path in artifact_dir.iterdir()
            if path.is_file() and path.name.startswith(ARTIFACT_PREFIXES)
        ),
        key=lambda p: (p.stat().st_size, p.name),
    )
    return [Candidate(path, path.read_bytes(), result) for path in artifacts]


def discover(
    target_dir: Path,
    max_time_seconds: int,
    max_runs: int,
    max_input_bytes: int,
    initial_seeds: list[bytes] | None = None,
) -> list[Candidate]:
    """Run a bounded libFuzzer campaign and return its concrete crash artifacts."""
    discovery_dir = target_dir / ".crs" / "discovery"
    corpus_dir = discovery_dir / "corpus"
    artifact_dir = discovery_dir / "artifacts"
    reset_directory(discovery_dir)
    corpus_dir.mkdir()
    artifact_dir.mkdir()
    seed_corpus(corpus_dir, initial_seeds)
    result = run_fuzzer(
        target_dir,
        corpus_dir,
        artifact_dir,
        runs=max_runs,
        max_time_seconds=max_time_seconds,
        max_input_bytes=max_input_bytes,
    )
    return artifact_candidates(artifact_dir, result)


def sanitizer_signature(stderr: str) -> str | None:
    for line in stderr.splitlines():
        if any(marker in line for marker in SANITIZER_MARKERS):
            return line.strip()
    return None


def deduplicate_candidates(candidates: list[Candidate], target_dir: Path) -> list[Candidate]:
    """Deduplicate candidates by crash signature so the same bug isn't patched repeatedly."""
    seen_signatures: set[str] = set()
    unique: list[Candidate] = []

    for candidate in sorted(candidates, key=lambda c: len(c.input_bytes)):
        # Check signature from initial fuzzer stderr or replay
        sig = sanitizer_signature(candidate.result.stderr)
        if not sig:
            replay = run(
                [str(fuzzer_path(target_dir)), str(candidate.input_path), "-runs=1"],
                target_dir,
                settings.command_timeout_seconds,
            )
            sig = sanitizer_signature(replay.stderr)

        sig_key = sig or f"crash-len-{len(candidate.input_bytes)}"
        if sig_key not in seen_signatures:
            seen_signatures.add(sig_key)
            unique.append(candidate)

    return unique
