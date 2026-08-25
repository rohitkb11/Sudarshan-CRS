from pathlib import Path
from orchestrator.config import settings
from .build_harness import fuzzer_path
from .discovery import Candidate, sanitizer_signature
from .utils import RunResult, run


def confirm(target_dir: Path, candidate: Candidate) -> tuple[bool, RunResult, str | None]:
    replay = run(
        [str(fuzzer_path(target_dir)), str(candidate.input_path), "-runs=1"],
        target_dir,
        settings.command_timeout_seconds,
    )
    signature = sanitizer_signature(replay.stderr)
    return signature is not None, replay, signature
