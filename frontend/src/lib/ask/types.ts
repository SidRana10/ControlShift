/**
 * Normalised shapes for POST /ask. The backend declares `answer`, `evidence`, `verification`,
 * `context` and `provider` as untyped dicts (src/controlshift/api/schemas.py AnswerResponse), so these
 * types describe what the pipeline actually puts in them (generation/schema.py LLMAnswer,
 * evidence/bundle.py EvidenceBundle, evidence/assemble.py) and `parseAskResponse` builds them from the
 * raw JSON defensively. Field names keep the backend's snake_case.
 */
import type { FrameworkVersion } from "@/lib/api/types";

export type AskStatus = "answered" | "abstained" | "evidence_only" | "rejected";

/** What the browser sends to the same-origin proxy (the proxy forwards only these fields). */
export interface AskRequestBody {
  question: string;
  /** Prefixes "In CSF x:" to the question on the backend; not a separate retrieval filter. */
  version?: FrameworkVersion;
}

export interface KeyChange {
  statement: string;
  citations: string[];
}

export interface MappingClaim {
  focal_id: string;
  reference_id: string | null;
  note: string;
  citations: string[];
}

/** The model's validated output (GenerationResult.answer). Null unless the model returned valid JSON. */
export interface GeneratedAnswer {
  answer: string;
  key_changes: KeyChange[];
  citations: string[];
  mappings: MappingClaim[];
  uncertainties: string[];
  unresolved_questions: string[];
  abstained: boolean;
  abstention_reason: string | null;
}

/** evidence.control_records[]: an exact record from the NIST framework, with its own chunk. */
export interface ControlRecordEvidence {
  kind: "control";
  citation_id: string;
  chunk_id: string;
  version: string;
  control_id: string;
  element_id: string;
  level: string | null;
  name: string | null;
  description: string | null;
  source_file: string;
  page: number | null;
  printed_page: string | null;
  section: string | null;
  text: string;
}

/** evidence.crosswalk_records[]: one official transition-workbook row, verbatim. */
export interface CrosswalkEvidence {
  kind: "crosswalk";
  citation_id: string;
  excel_row: number;
  sheet: string;
  source_file: string;
  focal_version: string;
  focal_id: string;
  focal_description: string | null;
  reference_version: string;
  reference_id: string | null;
  reference_description: string | null;
  mapping_type: string | null;
  comments: string | null;
  via: string[];
}

/** evidence.passages[]: a retrieved chunk of NIST text (control chunk or narrative). */
export interface PassageEvidence {
  kind: "passage";
  citation_id: string;
  chunk_id: string;
  version: string;
  control_id: string | null;
  chunk_type: string;
  source_file: string;
  page: number | null;
  printed_page: string | null;
  section: string | null;
  text: string;
  /** null for passages attached because they mention a retrieved control. */
  rank: number | null;
  origin: string | null;
}

export type EvidenceItem = ControlRecordEvidence | CrosswalkEvidence | PassageEvidence;

/** ControlShift's own statements about the evidence (conflicts, unmapped controls, gaps). */
export interface EvidenceNote {
  kind: "conflict" | "unmapped" | "missing";
  /** Human-readable, taken from backend fields (note / reason / detail); may be composed from kind. */
  text: string;
  citations: string[];
}

export interface Evidence {
  query_type: string | null;
  referenced_versions: string[];
  searched_versions: string[];
  control_ids: string[];
  controls: ControlRecordEvidence[];
  crosswalk: CrosswalkEvidence[];
  passages: PassageEvidence[];
  notes: EvidenceNote[];
  unresolved_questions: string[];
  retrieval_mode: string | null;
  k_per_version: number | null;
}

export interface AnswerVerification {
  /** verification.answer_citations, present only when a model answer passed validation. */
  answer_citations: { checked: number; scope: string; valid: boolean } | null;
  /** verification.evidence_bundle */
  evidence_bundle: { citations_checked: number; invalid: number; scope: string } | null;
  semantic_faithfulness: string | null;
}

export interface AskResult {
  question: string;
  effective_question: string;
  status: AskStatus;
  answer: GeneratedAnswer | null;
  abstention_reason: string | null;
  rejection: string[];
  system_uncertainties: string[];
  warnings: string[];
  verification: AnswerVerification;
  disclaimer: string;
  provider: { name: string | null; model: string | null };
  attempts: number;
  /** null when the response carried no evidence object. */
  evidence: Evidence | null;
}
