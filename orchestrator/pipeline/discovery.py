from dataclasses import dataclass
from pathlib import Path
from .utils import RunResult, run


@dataclass
class Candidate:
    input_text: str
    result: RunResult


def discover(target_dir: Path, max_cases: int) -> list[Candidate]:
    """Seeded mutation loop for the MVP. Replace with libFuzzer once harnesses land."""
    binary = target_dir / "build" / "parser"
    seeds = ["A" * length for length in range(8, 8 + max_cases * 8, 8)]
    return [Candidate(seed, run([str(binary), seed], target_dir)) for seed in seeds]


def sanitizer_signature(stderr: str) -> str | None:
    for line in stderr.splitlines():
        if "AddressSanitizer" in line or "UndefinedBehaviorSanitizer" in line:
            return line.strip()
    return None
