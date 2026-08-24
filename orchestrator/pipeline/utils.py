from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass
class RunResult:
    command: list[str]
    exit_code: int
    stdout: str
    stderr: str


def run(command: list[str], cwd: Path, timeout: int = 30) -> RunResult:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
    return RunResult(command, completed.returncode, completed.stdout, completed.stderr)
