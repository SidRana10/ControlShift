import type {
  AnswerVerification,
  AskResult,
  AskStatus,
  ControlRecordEvidence,
  CrosswalkEvidence,
  Evidence,
  EvidenceNote,
  GeneratedAnswer,
  PassageEvidence,
} from "./types";

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
const str = (v: unknown): string | null => (typeof v === "string" ? v : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const strings = (v: unknown): string[] =>
  Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : [];
const list = (v: unknown): Obj[] => (Array.isArray(v) ? v.filter(isObj) : []);

const STATUSES: AskStatus[] = ["answered", "abstained", "evidence_only", "rejected"];

function parseAnswer(v: unknown): GeneratedAnswer | null {
  if (!isObj(v)) return null;
  return {
    answer: str(v.answer) ?? "",
    key_changes: list(v.key_changes).flatMap((k) =>
      str(k.statement) ? [{ statement: str(k.statement)!, citations: strings(k.citations) }] : [],
    ),
    citations: strings(v.citations),
    mappings: list(v.mappings).flatMap((m) =>
      str(m.focal_id)
        ? [
            {
              focal_id: str(m.focal_id)!,
              reference_id: str(m.reference_id),
              note: str(m.note) ?? "",
              citations: strings(m.citations),
            },
          ]
        : [],
    ),
    uncertainties: strings(v.uncertainties),
    unresolved_questions: strings(v.unresolved_questions),
    abstained: v.abstained === true,
    abstention_reason: str(v.abstention_reason),
  };
}

function parseControl(o: Obj): ControlRecordEvidence | null {
  const citation_id = str(o.citation_id);
  const version = str(o.version);
  const control_id = str(o.control_id);
  const element_id = str(o.element_id);
  if (!citation_id || !version || !control_id || !element_id) return null;
  return {
    kind: "control",
    citation_id,
    chunk_id: str(o.chunk_id) ?? citation_id,
    version,
    control_id,
    element_id,
    level: str(o.level),
    name: str(o.name),
    description: str(o.description),
    source_file: str(o.source_file) ?? "",
    page: num(o.page),
    printed_page: str(o.printed_page),
    section: str(o.section),
    text: str(o.text) ?? "",
  };
}

function parseCrosswalk(o: Obj): CrosswalkEvidence | null {
  const citation_id = str(o.citation_id);
  const excel_row = num(o.excel_row);
  const focal_id = str(o.focal_id);
  if (!citation_id || excel_row === null || !focal_id) return null;
  return {
    kind: "crosswalk",
    citation_id,
    excel_row,
    sheet: str(o.sheet) ?? "",
    source_file: str(o.source_file) ?? "",
    focal_version: str(o.focal_version) ?? "2.0",
    focal_id,
    focal_description: str(o.focal_description),
    reference_version: str(o.reference_version) ?? "1.1",
    reference_id: str(o.reference_id),
    reference_description: str(o.reference_description),
    mapping_type: str(o.mapping_type),
    comments: str(o.comments),
    via: strings(o.via),
  };
}

function parsePassage(o: Obj): PassageEvidence | null {
  const citation_id = str(o.citation_id);
  const version = str(o.version);
  const text = str(o.text);
  if (!citation_id || !version || text === null) return null;
  return {
    kind: "passage",
    citation_id,
    chunk_id: str(o.chunk_id) ?? citation_id,
    version,
    control_id: str(o.control_id),
    chunk_type: str(o.chunk_type) ?? "text",
    source_file: str(o.source_file) ?? "",
    page: num(o.page),
    printed_page: str(o.printed_page),
    section: str(o.section),
    text,
    rank: num(o.rank),
    origin: str(o.origin),
  };
}

function parseNotes(e: Obj): EvidenceNote[] {
  const notes: EvidenceNote[] = [];
  for (const c of list(e.conflicts)) {
    const note = str(c.note);
    if (note) notes.push({ kind: "conflict", text: note, citations: strings(c.citations) });
  }
  for (const u of list(e.unmapped_controls)) {
    const reason = str(u.reason);
    if (reason) {
      const id = str(u.control_id);
      notes.push({
        kind: "unmapped",
        text: id ? `${id}: ${reason}` : reason,
        citations: strings(u.citations),
      });
    }
  }
  for (const m of list(e.missing_evidence)) {
    const detail = str(m.detail);
    const kind = str(m.kind);
    const text = detail ?? (kind ? `Missing evidence: ${kind.replace(/_/g, " ")}` : null);
    if (text) notes.push({ kind: "missing", text, citations: strings(m.citations) });
  }
  return notes;
}

function parseEvidence(v: unknown): Evidence | null {
  if (!isObj(v)) return null;
  const retrieval = isObj(v.retrieval) ? v.retrieval : {};
  return {
    query_type: str(v.query_type),
    referenced_versions: strings(v.referenced_versions),
    searched_versions: strings(v.searched_versions),
    control_ids: strings(v.control_ids),
    controls: list(v.control_records).flatMap((o) => parseControl(o) ?? []),
    crosswalk: list(v.crosswalk_records).flatMap((o) => parseCrosswalk(o) ?? []),
    passages: list(v.passages).flatMap((o) => parsePassage(o) ?? []),
    notes: parseNotes(v),
    unresolved_questions: strings(v.unresolved_questions),
    retrieval_mode: str(retrieval.mode),
    k_per_version: num(retrieval.k_per_version),
  };
}

function parseVerification(v: unknown): AnswerVerification {
  const o = isObj(v) ? v : {};
  const ac = isObj(o.answer_citations) ? o.answer_citations : null;
  const eb = isObj(o.evidence_bundle) ? o.evidence_bundle : null;
  return {
    answer_citations:
      ac && num(ac.checked) !== null
        ? { checked: num(ac.checked)!, scope: str(ac.scope) ?? "structural", valid: ac.valid === true }
        : null,
    evidence_bundle:
      eb && num(eb.citations_checked) !== null
        ? {
            citations_checked: num(eb.citations_checked)!,
            invalid: num(eb.invalid) ?? 0,
            scope: str(eb.scope) ?? "",
          }
        : null,
    semantic_faithfulness: str(o.semantic_faithfulness),
  };
}

/**
 * Validates and normalises a 200 response from POST /ask. Returns null when the top level is not an
 * AnswerResponse (unknown status, missing question or disclaimer): the UI then reports an unexpected
 * response instead of rendering guesses. Malformed evidence entries are dropped individually; the
 * ones that remain are complete enough to display with honest provenance.
 */
export function parseAskResponse(body: unknown): AskResult | null {
  if (!isObj(body)) return null;
  const status = STATUSES.find((s) => s === body.status);
  const question = str(body.question);
  const disclaimer = str(body.disclaimer);
  if (!status || question === null || disclaimer === null) return null;
  const provider = isObj(body.provider) ? body.provider : {};
  return {
    question,
    effective_question: str(body.effective_question) ?? question,
    status,
    answer: parseAnswer(body.answer),
    abstention_reason: str(body.abstention_reason),
    rejection: strings(body.rejection),
    system_uncertainties: strings(body.system_uncertainties),
    warnings: strings(body.warnings),
    verification: parseVerification(body.verification),
    disclaimer,
    provider: { name: str(provider.name), model: str(provider.model) },
    attempts: num(body.attempts) ?? 0,
    evidence: parseEvidence(body.evidence),
  };
}
