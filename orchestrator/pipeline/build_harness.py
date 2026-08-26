from pathlib import Path
from .utils import RunResult, run
from orchestrator.config import settings


def clean(target_dir: Path) -> RunResult:
    """Remove target build outputs without touching scan artifacts or source."""
    return run(
        [settings.make, "clean"],
        target_dir,
        settings.command_timeout_seconds,
    )


def binary_path(target_dir: Path, mode: str) -> Path:
    return target_dir / "build" / mode / "parser"


def fuzzer_path(target_dir: Path) -> Path:
    return target_dir / "build" / "fuzzer" / "parser_fuzzer"


def _cxx_bin() -> str:
    if "clang" in settings.clang:
        return settings.clang.replace("clang", "clang++")
    if "gcc" in settings.clang:
        return settings.clang.replace("gcc", "g++")
    return "clang++"


def build(
    target_dir: Path,
    sanitized: bool = True,
    *,
    clean_first: bool = True,
) -> RunResult:
    mode = "sanitized" if sanitized else "normal"
    goals = ["clean", "build"] if clean_first else ["build"]
    return run(
        [settings.make, *goals, f"MODE={mode}", f"CC={settings.clang}", f"CXX={_cxx_bin()}"],
        target_dir,
        settings.command_timeout_seconds,
    )


def build_fuzzer(target_dir: Path, *, clean_first: bool = True) -> RunResult:
    goals = ["clean", "fuzz"] if clean_first else ["fuzz"]
    return run(
        [settings.make, *goals, "MODE=fuzzer", f"CC={settings.clang}", f"CXX={_cxx_bin()}"],
        target_dir,
        settings.command_timeout_seconds,
    )
