"""All settings in one place, read from the environment and the project's .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")  # never overrides variables that are already set

# name -> (key variable, base-URL variable, model variable, default base URL, default model)
PROVIDERS = {
    "groq": ("GROQ_API_KEY", "GROQ_BASE_URL", "GROQ_MODEL",
             "https://api.groq.com/openai/v1", "openai/gpt-oss-20b"),
    "openrouter": ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "OPENROUTER_MODEL",
                   "https://openrouter.ai/api/v1", ""),
}


class ConfigError(RuntimeError):
    """A required setting is missing or invalid. The message says how to fix it."""


@dataclass(frozen=True)
class ProviderSettings:
    name: str
    api_key: str
    base_url: str
    model: str

    def __repr__(self) -> str:  # never print the key
        return f"ProviderSettings(name={self.name!r}, base_url={self.base_url!r}, model={self.model!r})"


def provider(name: str | None = None) -> ProviderSettings:
    """Settings for the chosen model provider; raises ConfigError if the key or model is missing."""
    name = (name or os.getenv("LLM_PROVIDER") or "groq").strip().lower()
    if name not in PROVIDERS:
        raise ConfigError(f"LLM_PROVIDER must be one of {sorted(PROVIDERS)}, not {name!r}.")
    key_var, url_var, model_var, default_url, default_model = PROVIDERS[name]
    api_key = os.getenv(key_var, "").strip()
    if not api_key or api_key.startswith("your_"):
        raise ConfigError(f"{key_var} is not set. Copy .env.example to .env and put your key in it.")
    model = (os.getenv(model_var) or default_model).strip()
    if not model:
        raise ConfigError(f"{model_var} is not set in .env.")
    base_url = (os.getenv(url_var) or default_url).strip()
    return ProviderSettings(name=name, api_key=api_key, base_url=base_url, model=model)


def _path(variable: str, default: str) -> Path:
    path = Path(os.getenv(variable) or default)
    return path if path.is_absolute() else (ROOT / path).resolve()


DATA_DIR = ROOT / "data"
CHROMA_PATH = _path("CHROMA_PATH", "./storage/chroma")
DATABASE_PATH = _path("DATABASE_PATH", "./storage/decisions.db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL") or "all-MiniLM-L6-v2"
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K") or 5)
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD") or 0.80)
LOG_LEVEL = os.getenv("LOG_LEVEL") or "INFO"

# gpt-oss models think before answering; "low" keeps that short, which saves the daily token allowance
REASONING_EFFORT = (os.getenv("LLM_REASONING_EFFORT") or "low").strip().lower()
# Sent only when set; otherwise the provider's default temperature applies
TEMPERATURE = float(os.environ["LLM_TEMPERATURE"]) if os.getenv("LLM_TEMPERATURE") else None
