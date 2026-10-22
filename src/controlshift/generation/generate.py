"""Grounded answer generation: LLM call + deterministic validation of everything it returns."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from ..evidence.assemble import validate_bundle
from ..evidence.bundle import EvidenceBundle
from ..evidence.citations import XWALK_PREFIX, validate_citations
from ..ingest.models import normalize_control_id
from ..store.queries import KnowledgeStore
from .config import Settings
from .context import EvidenceContext, build_context
from .prompt import SYSTEM_PROMPT, build_prompt
from .provider import LLMProvider, ProviderError
from .schema import LLMAnswer

DISCLAIMER = ("Citations are checked structurally (the cited chunk or crosswalk row exists and its "
              "version/page/section/mapping endpoints match the database). That does not prove the "
              "answer's statements are faithful to the cited text; semantic faithfulness is not "
              "verified. No model confidence is reported.")
REMOVAL_WORDS = re.compile(r"\b(removed|deleted|retired|dropped|eliminated|discontinued|"
                           r"deprecated|no longer (?:exists?|included|part))\b", re.IGNORECASE)

NO_PROVIDER_WARNING = (
    "No LLM provider is configured (set GEMINI_API_KEY and GEMINI_MODEL); the evidence bundle is "
    "returned without a generated answer.")

ANSWERED, ABSTAINED, EVIDENCE_ONLY, REJECTED = "answered", "abstained", "evidence_only", "rejected"


@dataclass
class GenerationResult:
    status: str
    answer: dict | None = None  # validated LLM output
    abstention_reason: str | None = None
    rejection: list[str] = field(default_factory=list)  # why an LLM answer was refused
    system_uncertainties: list[str] = field(default_factory=list)  # added by the pipeline
    verification: dict = field(default_factory=dict)
    context: dict = field(default_factory=dict)
    provider: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    attempts: int = 0
    disclaimer: str = DISCLAIMER

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def insufficient_evidence(bundle: EvidenceBundle) -> str | None:
    if bundle.query_type == "unsupported":
        return "The question could not be interpreted: " + " ".join(bundle.unresolved_questions)
    if not (bundle.control_records or bundle.crosswalk_records or bundle.passages):
        return "No evidence was found in the NIST documents or the official crosswalk."
    return None


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise TypeError("top-level JSON value must be an object")
    return data


def _all_citations(a: LLMAnswer) -> list[str]:
    cites = list(a.citations)
    for k in a.key_changes:
        cites += k.citations
    for m in a.mappings:
        cites += m.citations
    return cites


class GroundedGenerator:
    def __init__(self, provider: LLMProvider | None, settings: Settings | None = None):
        self.provider, self.settings = provider, settings or Settings()

    def generate(self, bundle: EvidenceBundle, store: KnowledgeStore) -> GenerationResult:
        pinfo = ({"name": self.provider.name, "model": self.provider.model}
                 if self.provider else {"name": None, "model": None})
        reason = insufficient_evidence(bundle)
        if reason:  # abstain without spending an API call
            return GenerationResult(ABSTAINED, abstention_reason=reason, provider=pinfo,
                                    verification=self._bundle_verification(store, bundle))
        if self.provider is None:
            return GenerationResult(
                EVIDENCE_ONLY, provider=pinfo, verification=self._bundle_verification(store, bundle),
                warnings=[NO_PROVIDER_WARNING])
        ctx = build_context(bundle, self.settings.context_chars, self.settings.max_passage_chars)
        warnings = [f"Passage {f['citation_id']} contains text resembling an instruction "
                    f"({f['match']!r}); it was passed to the model as untrusted data."
                    for f in ctx.injection_flags]
        if ctx.omitted:
            warnings.append(f"{len(ctx.omitted)} lower-ranked passage(s) were left out of the "
                            "prompt for space.")
        result = GenerationResult(REJECTED, provider=pinfo, context=ctx.summary(),
                                  warnings=warnings,
                                  verification=self._bundle_verification(store, bundle))
        repair: str | None = None
        for attempt in range(1, max(1, self.settings.max_llm_attempts) + 1):
            result.attempts = attempt
            raw = self.provider.generate(SYSTEM_PROMPT, build_prompt(bundle, ctx, repair))
            try:
                parsed = LLMAnswer.model_validate(_parse_json(raw))
            except (ValueError, TypeError, ValidationError) as exc:
                repair = f"it was not valid JSON for the required schema ({_short(exc)})."
                result.rejection = [f"invalid model output: {_short(exc)}"]
                continue
            problems = self._validate(parsed, bundle, ctx, store)
            if problems:
                repair = "; ".join(problems[:5]) + "."
                result.rejection = problems
                continue
            result.rejection = []
            result.answer = parsed.model_dump()
            result.status = ABSTAINED if parsed.abstained else ANSWERED
            result.abstention_reason = parsed.abstention_reason if parsed.abstained else None
            result.system_uncertainties = self._system_uncertainties(bundle, ctx, parsed)
            result.verification["answer_citations"] = {
                "checked": len(set(_all_citations(parsed))), "scope": "structural", "valid": True}
            return result
        return result  # status stays REJECTED; no unvalidated answer text is returned

    # ---- validation -------------------------------------------------------------------------
    def _validate(self, a: LLMAnswer, bundle: EvidenceBundle, ctx: EvidenceContext,
                  store: KnowledgeStore) -> list[str]:
        problems: list[str] = []
        cited = _all_citations(a)
        unknown = sorted({c for c in cited if c not in ctx.allowed_citations})
        if unknown:
            problems.append(f"cited ids not in the supplied evidence: {unknown}")
        known = [c for c in set(cited) if c in ctx.allowed_citations]
        claims = [c for c in bundle.claims() if c.citation_id in known]
        for chk in validate_citations(store.conn, claims, ctx.allowed_citations):
            if not chk.valid:
                problems.append(f"citation {chk.citation_id} failed structural check: "
                                f"{'; '.join(chk.errors)}")
        if not a.abstained:
            if not a.citations:
                problems.append("the answer has no top-level citations")
            problems += [f"key_change {i + 1} has no citation"
                         for i, k in enumerate(a.key_changes) if not k.citations]
            problems += [f"mapping {m.focal_id}->{m.reference_id} has no citation"
                         for m in a.mappings if not m.citations]
            problems += self._check_mappings(a, bundle)
            problems += self._check_removal_claims(a, bundle)
        return problems

    def _check_mappings(self, a: LLMAnswer, bundle: EvidenceBundle) -> list[str]:
        rows = {r["citation_id"]: r for r in bundle.crosswalk_records}
        out = []
        for m in a.mappings:
            focal = normalize_control_id(m.focal_id.upper())
            ref = normalize_control_id(m.reference_id.upper()) if m.reference_id else None
            cited_rows = [rows[c] for c in m.citations if c.startswith(XWALK_PREFIX) and c in rows]
            if not any(normalize_control_id(r["focal_id"].upper()) == focal and (
                    normalize_control_id(r["reference_id"].upper()) if r["reference_id"] else None
            ) == ref for r in cited_rows):
                out.append(f"mapping {m.focal_id}->{m.reference_id} is not an official crosswalk "
                           "row among its citations (mappings must be copied from a cited "
                           "official_crosswalk block)")
        return out

    def _check_removal_claims(self, a: LLMAnswer, bundle: EvidenceBundle) -> list[str]:
        texts = {r["citation_id"]: r["text"] for r in bundle.control_records + bundle.passages}
        for r in bundle.crosswalk_records:
            texts[r["citation_id"]] = " ".join(str(r[k] or "") for k in
                                               ("focal_description", "reference_description", "comments"))
        out = []
        statements = [(a.answer, a.citations)] + [(k.statement, k.citations) for k in a.key_changes]
        for stmt, cites in statements:
            for m in REMOVAL_WORDS.finditer(stmt):
                word = m.group(1).lower()
                if not any(word in texts.get(c, "").lower() for c in cites):
                    out.append(f"statement claims something was '{word}' but no cited evidence "
                               "says so (absence of a mapping is not removal)")
                    break
        return out

    # ---- helpers ---------------------------------------------------------------------------------
    def _system_uncertainties(self, bundle, ctx, a: LLMAnswer) -> list[str]:
        out = []
        mentioned = " ".join(a.uncertainties + [a.answer]).upper()
        for c in bundle.conflicts:
            if c["control_id"].upper() not in mentioned or "conflict" not in mentioned.lower():
                out.append(f"Official workbook records for {c['control_id']} are not consistent "
                           f"({', '.join(c['citations'])}): {c['note']}")
        if ctx.omitted:
            out.append("Some retrieved passages were omitted from the prompt for space; the "
                       "answer may not reflect them.")
        return out

    @staticmethod
    def _bundle_verification(store: KnowledgeStore, bundle: EvidenceBundle) -> dict:
        v = validate_bundle(store, bundle)
        return {"evidence_bundle": v, "semantic_faithfulness": "not verified"}


def _short(exc: Exception) -> str:
    return re.sub(r"\s+", " ", str(exc))[:200]


__all__ = ["DISCLAIMER", "GenerationResult", "GroundedGenerator", "ProviderError"]
