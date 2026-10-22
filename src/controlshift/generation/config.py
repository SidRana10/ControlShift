"""Runtime settings from environment variables (a local .env is loaded by the entry points).
No secret or model name has a default in code."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _int(env: dict, key: str, default: int) -> int:
    try:
        return int(env.get(key, default))
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _float(env: dict, key: str, default: float) -> float:
    try:
        return float(env.get(key, default))
    except ValueError as exc:
        raise ValueError(f"{key} must be a number") from exc


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path("data/processed/controlshift.db")
    index_dir: Path = Path("data/indexes")
    retrieval_mode: str = "hybrid"  # none|bm25|dense|hybrid|hybrid_rerank
    llm_provider: str = "gemini"  # generator: gemini | mistral | groq
    gemini_api_key: str | None = field(default=None, repr=False)  # never printed
    gemini_model: str | None = None
    mistral_api_key: str | None = field(default=None, repr=False)  # never printed
    mistral_model: str | None = None
    groq_api_key: str | None = field(default=None, repr=False)  # generator key (LLM_PROVIDER=groq); never printed
    groq_model: str | None = None  # the GENERATOR model; the judge's model is JUDGE_MODEL
    groq_reasoning_format: str | None = None
    llm_timeout_seconds: float = 30.0
    request_timeout_seconds: float = 90.0
    context_chars: int = 12000  # evidence-context budget for the prompt
    max_passage_chars: int = 1500
    max_llm_attempts: int = 2  # first try + one repair retry

    @classmethod
    def from_env(cls, env: dict | None = None) -> Settings:
        e = dict(os.environ if env is None else env)
        return cls(
            db_path=Path(e.get("SQLITE_PATH", "data/processed/controlshift.db")),
            index_dir=Path(e.get("INDEX_DIR", "data/indexes")),
            retrieval_mode=e.get("RETRIEVAL_MODE", "hybrid"),
            llm_provider=e.get("LLM_PROVIDER", "gemini").lower(),
            gemini_api_key=e.get("GEMINI_API_KEY") or None,
            gemini_model=e.get("GEMINI_MODEL") or None,
            mistral_api_key=e.get("MISTRAL_API_KEY") or None,
            mistral_model=e.get("MISTRAL_MODEL") or None,
            # the Groq generator key defaults to the judge's Groq key when the judge is on Groq (same account)
            groq_api_key=e.get("GROQ_API_KEY") or (e.get("JUDGE_API_KEY") if e.get("JUDGE_PROVIDER", "").lower() == "groq" else None) or None,
            groq_model=e.get("GROQ_MODEL") or None,
            groq_reasoning_format=e.get("GROQ_REASONING_FORMAT") or None,
            llm_timeout_seconds=_float(e, "LLM_TIMEOUT_SECONDS", 30.0),
            request_timeout_seconds=_float(e, "REQUEST_TIMEOUT_SECONDS", 90.0),
            context_chars=_int(e, "GENERATION_CONTEXT_CHARS", 12000),
            max_passage_chars=_int(e, "GENERATION_MAX_PASSAGE_CHARS", 1500),
            max_llm_attempts=_int(e, "LLM_MAX_ATTEMPTS", 2),
        )
