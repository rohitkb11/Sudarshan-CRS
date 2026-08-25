from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    clang: str = os.getenv("CLANG_BIN", "clang")
    make: str = os.getenv("MAKE_BIN", "make")
    retry_cap: int = 3
    fuzz_time_seconds: int = int(os.getenv("FUZZ_TIME_SECONDS", "10"))
    fuzz_runs: int = int(os.getenv("FUZZ_RUNS", "100000"))
    fuzz_max_input_bytes: int = int(os.getenv("FUZZ_MAX_INPUT_BYTES", "256"))
    differential_fuzz_runs: int = int(os.getenv("DIFFERENTIAL_FUZZ_RUNS", "2000"))
    command_timeout_seconds: int = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "30"))
    data_dir: Path = ROOT / "data"


settings = Settings()
