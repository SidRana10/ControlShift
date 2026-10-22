"""LLM provider interface and the Gemini REST implementation (httpx; no vendor SDK)."""
from __future__ import annotations

from typing import Protocol

import httpx

from .config import Settings

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class ProviderError(Exception):
    """Base class for controlled provider failures (messages never contain credentials)."""

    code = "provider_error"


class ProviderNotConfigured(ProviderError):
    code = "provider_not_configured"


class ProviderTimeout(ProviderError):
    code = "provider_timeout"


class ProviderFailure(ProviderError):
    code = "provider_error"


class LLMProvider(Protocol):
    name: str
    model: str

    def generate(self, system: str, prompt: str) -> str:
        """Return the model's raw text (expected to be a JSON document)."""


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float = 30.0,
                 base_url: str = GEMINI_BASE_URL, client: httpx.Client | None = None):
        if not api_key or not model:
            raise ProviderNotConfigured("GEMINI_API_KEY and GEMINI_MODEL must both be set")
        self._key, self.model, self.timeout, self.base_url = api_key, model, timeout, base_url
        self._client = client  # injectable for tests (httpx.MockTransport)

    @classmethod
    def from_settings(cls, s: Settings, client: httpx.Client | None = None) -> GeminiProvider:
        if s.llm_provider != "gemini":
            raise ProviderNotConfigured(f"unsupported LLM_PROVIDER {s.llm_provider!r}")
        return cls(s.gemini_api_key or "", s.gemini_model or "", s.llm_timeout_seconds,
                   client=client)

    def generate(self, system: str, prompt: str) -> str:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
        }
        url = f"{self.base_url}/models/{self.model}:generateContent"
        try:
            if self._client is not None:
                resp = self._client.post(url, json=body, headers={"x-goog-api-key": self._key},
                                         timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=body, headers={"x-goog-api-key": self._key})
        except httpx.TimeoutException as exc:
            raise ProviderTimeout(f"Gemini request timed out after {self.timeout:g}s") from exc
        except httpx.HTTPError as exc:  # connection errors etc.; type name only, no URL/headers
            raise ProviderFailure(f"Gemini request failed ({type(exc).__name__})") from exc
        if resp.status_code != 200:
            raise ProviderFailure(f"Gemini returned HTTP {resp.status_code}{_error_status(resp)}")
        try:
            data = resp.json()
            candidate = data["candidates"][0]
            text = "".join(p.get("text", "") for p in candidate["content"]["parts"])
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            reason = "no candidates (blocked or empty response)"
            raise ProviderFailure(f"Gemini response was unusable: {reason}") from exc
        if not text.strip():
            raise ProviderFailure("Gemini returned empty text")
        return text


def _error_status(resp: httpx.Response) -> str:
    """' UNAVAILABLE'-style status word from Google's error body (only a short enum-like token is
    kept; the message text, which could echo request content, is never copied)."""
    try:
        status = resp.json()["error"]["status"]
    except (ValueError, KeyError, TypeError):
        return ""
    return f" {status}" if isinstance(status, str) and status.isupper() and len(status) <= 40 else ""


def provider_from_settings(s: Settings) -> LLMProvider | None:
    """The configured provider, or None when credentials are absent (evidence-only mode)."""
    try:
        return GeminiProvider.from_settings(s)
    except ProviderNotConfigured:
        return None
