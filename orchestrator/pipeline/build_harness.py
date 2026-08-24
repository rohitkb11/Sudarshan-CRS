from pathlib import Path
from .utils import RunResult, run
from orchestrator.config import settings


def build(target_dir: Path, sanitized: bool = True) -> RunResult:
    mode = "sanitized" if sanitized else "normal"
    return run([settings.make, "clean", "build", f"MODE={mode}", f"CC={settings.clang}"], target_dir, settings.command_timeout_seconds)
