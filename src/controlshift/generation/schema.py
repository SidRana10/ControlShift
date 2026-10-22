"""Structured output the LLM must return. Unknown keys (e.g. a self-reported 'confidence') are
ignored: uncalibrated model confidence is never surfaced."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Base(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class KeyChange(_Base):
    statement: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)


class MappingClaim(_Base):
    """An official CSF crosswalk relationship: focal = CSF 2.0 element, reference = CSF 1.1
    element (or null when the official row says the element is conceptually new)."""

    focal_id: str = Field(min_length=1)
    reference_id: str | None = None
    note: str = ""
    citations: list[str] = Field(default_factory=list)

    @field_validator("reference_id")
    @classmethod
    def _blank_is_none(cls, v):
        return v or None


class LLMAnswer(_Base):
    answer: str = ""
    key_changes: list[KeyChange] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    mappings: list[MappingClaim] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    abstained: bool = False
    abstention_reason: str | None = None

    @model_validator(mode="after")
    def _check(self):
        if self.abstained:
            if not (self.abstention_reason or self.answer):
                raise ValueError("an abstention needs a reason")
        elif not self.answer:
            raise ValueError("answer must not be empty unless abstained")
        return self
