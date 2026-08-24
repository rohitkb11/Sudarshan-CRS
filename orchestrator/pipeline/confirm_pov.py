from pathlib import Path
from .discovery import Candidate, sanitizer_signature
from .utils import RunResult, run


def confirm(target_dir: Path, candidate: Candidate) -> tuple[bool, RunResult, str | None]:
    replay = run([str(target_dir / "build" / "parser"), candidate.input_text], target_dir)
    signature = sanitizer_signature(replay.stderr)
    return signature is not None, replay, signature
