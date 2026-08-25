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
    try:
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
        return RunResult(command, completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        stderr += f"\nCommand exceeded the {timeout}-second hard timeout."
        return RunResult(command, 124, stdout, stderr)
