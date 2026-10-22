"""LLM provider interface and the Gemini REST implementation (httpx; no vendor SDK)."""
from __future__ import annotations

import re
from typing import Protocol

import httpx

from .config import Settings

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


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


class GroqProvider:
    """Groq's OpenAI-compatible chat-completions API (used as the independent LLM judge)."""

    name = "groq"

    def __init__(self, api_key: str, model: str, timeout: float = 60.0,
                 base_url: str = GROQ_BASE_URL, client: httpx.Client | None = None):
        if not api_key or not model:
            raise ProviderNotConfigured("a Groq API key and model must both be set")
        self._key, self.model, self.timeout, self.base_url = api_key, model, timeout, base_url
        self._client = client  # injectable for tests (httpx.MockTransport)

    def generate(self, system: str, prompt: str) -> str:
        body = {"model": self.model, "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self._key}"}
        try:
            if self._client is not None:
                resp = self._client.post(url, json=body, headers=headers, timeout=self.timeout)
            else:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=body, headers=headers)
        except httpx.TimeoutException as exc:
            raise ProviderTimeout(f"Groq request timed out after {self.timeout:g}s") from exc
        except httpx.HTTPError as exc:  # type name only: no URL, headers or body
            raise ProviderFailure(f"Groq request failed ({type(exc).__name__})") from exc
        if resp.status_code != 200:
            raise ProviderFailure(f"Groq returned HTTP {resp.status_code}{_groq_error_token(resp)}")
        try:
            choice = resp.json()["choices"][0]
            text = choice["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderFailure("Groq response was unusable: no choices or message content") from exc
        if not isinstance(text, str) or not text.strip():
            raise ProviderFailure("Groq returned empty text")
        if choice.get("finish_reason") == "length":
            raise ProviderFailure("Groq output was cut off (finish_reason=length); the JSON would be incomplete")
        return text


def _groq_error_token(resp: httpx.Response) -> str:
    """' (rate_limit_exceeded)'-style short token from the error body; the message text is never copied."""
    try:
        err = resp.json()["error"]
        token = err.get("code") or err.get("type")
    except (ValueError, KeyError, TypeError, AttributeError):
        return ""
    return f" ({token})" if isinstance(token, str) and re.fullmatch(r"[a-z0-9_]{1,40}", token) else ""


def provider_from_settings(s: Settings) -> LLMProvider | None:
    """The configured provider, or None when credentials are absent (evidence-only mode)."""
    try:
        return GeminiProvider.from_settings(s)
    except ProviderNotConfigured:
        return None
