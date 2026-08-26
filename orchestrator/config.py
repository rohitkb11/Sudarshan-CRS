from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    clang: str = os.getenv("CLANG_BIN", "clang")
    make: str = os.getenv("MAKE_BIN", "make")
    retry_cap: int = int(os.getenv("RETRY_CAP", "3"))
    fuzz_time_seconds: int = int(os.getenv("FUZZ_TIME_SECONDS", "10"))
    fuzz_runs: int = int(os.getenv("FUZZ_RUNS", "100000"))
    fuzz_max_input_bytes: int = int(os.getenv("FUZZ_MAX_INPUT_BYTES", "256"))
    differential_fuzz_runs: int = int(os.getenv("DIFFERENTIAL_FUZZ_RUNS", "2000"))
    command_timeout_seconds: int = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "30"))
    data_dir: Path = ROOT / "data"

    # LLM Provider selection: 'groq' (default when GROQ_API_KEY set) or 'anthropic'
    llm_provider: str = os.getenv("LLM_PROVIDER", "groq" if os.getenv("GROQ_API_KEY") else "anthropic")

    # Groq API settings (Ultra-fast LLM reasoning for Cyber-Reasoning)
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model_fast: str = os.getenv("GROQ_MODEL_FAST", "openai/gpt-oss-20b")
    groq_model_strong: str = os.getenv("GROQ_MODEL_STRONG", "openai/gpt-oss-20b")
    groq_temperature: float = float(os.getenv("GROQ_TEMPERATURE", "0.6"))
    groq_top_p: float = float(os.getenv("GROQ_TOP_P", "0.95"))
    groq_max_completion_tokens: int = int(os.getenv("GROQ_MAX_COMPLETION_TOKENS", "4096"))
    groq_reasoning_effort: str = os.getenv("GROQ_REASONING_EFFORT", "default")

    # Anthropic API settings (Alternative provider)
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    llm_model_fast: str = os.getenv("LLM_MODEL_FAST", "claude-3-5-haiku-20241022")
    llm_model_strong: str = os.getenv("LLM_MODEL_STRONG", "claude-sonnet-4-20250514")


settings = Settings()
