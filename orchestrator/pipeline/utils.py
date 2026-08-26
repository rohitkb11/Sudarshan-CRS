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
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout.decode("utf-8", errors="replace") if isinstance(completed.stdout, bytes) else (completed.stdout or "")
        stderr = completed.stderr.decode("utf-8", errors="replace") if isinstance(completed.stderr, bytes) else (completed.stderr or "")
        return RunResult(command, completed.returncode, stdout, stderr)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        stderr += f"\nCommand exceeded the {timeout}-second hard timeout."
        return RunResult(command, 124, stdout, stderr)
    except FileNotFoundError as error:
        return RunResult(command, 127, "", f"Executable not found: {error}")
    except OSError as error:
        return RunResult(command, 126, "", f"OS execution error: {error}")
