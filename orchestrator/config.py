from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    clang: str = os.getenv("CLANG_BIN", "clang")
    make: str = os.getenv("MAKE_BIN", "make")
    retry_cap: int = 3
    fuzz_cases: int = 12
    command_timeout_seconds: int = 30
    data_dir: Path = ROOT / "data"


settings = Settings()
