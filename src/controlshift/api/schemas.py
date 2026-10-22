from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_CTRL = re.compile(r"^[A-Za-z]{2}\.[A-Za-z]{2}(?:-\d{1,2})?$")


def _clean(v: str) -> str:
    v = v.strip()
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", v):
        raise ValueError("must not contain control characters")
    if not v:
        raise ValueError("must not be blank")
    return v


class _Req(BaseModel):
    model_config = ConfigDict(extra="forbid")
    retrieval_k: int = Field(5, ge=1, le=10, description="passages retrieved per version")
    generate: bool = Field(True, description="false = return the evidence bundle only")
    include_evidence: bool = True


class AskRequest(_Req):
    question: str = Field(..., max_length=2000)
    version: Literal["1.1", "2.0"] | None = Field(
        None, description="restrict to one framework version (prefixed to the question when it "
                          "does not name a version itself)")

    _q = field_validator("question")(lambda cls, v: _clean(v))


class CompareRequest(_Req):
    question: str = Field(..., max_length=2000)
    control_ids: list[str] = Field(default_factory=list, max_length=5)

    _q = field_validator("question")(lambda cls, v: _clean(v))

    @field_validator("control_ids")
    @classmethod
    def _ids(cls, v):
        for c in v:
            if not _CTRL.match(c.strip()):
                raise ValueError(f"invalid control id {c!r}")
        return [c.strip().upper() for c in v]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class AnswerResponse(BaseModel):
    question: str
    effective_question: str
    status: Literal["answered", "abstained", "evidence_only", "rejected"]
    answer: dict | None = None
    abstention_reason: str | None = None
    rejection: list[str] = []
    system_uncertainties: list[str] = []
    warnings: list[str] = []
    verification: dict = {}
    disclaimer: str
    provider: dict = {}
    context: dict = {}
    attempts: int = 0
    evidence: dict | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: dict
    retrieval: dict
    llm: dict
