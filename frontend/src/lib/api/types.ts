/**
 * Response types for the endpoints the frontend uses. They mirror the Pydantic models in
 * src/controlshift/api/catalog.py and the health payload in src/controlshift/api/services.py,
 * and keep the backend's snake_case field names.
 */
export type FrameworkVersion = "1.1" | "2.0";
export type ElementLevel = "function" | "category" | "subcategory";

export interface SourceDocument {
  source_file: string;
  kind: string;
  sha256: string;
  bytes: number;
  pages: number | null;
}

export interface ElementCounts {
  function: number;
  category: number;
  subcategory: number;
}

export interface VersionInfo {
  version: FrameworkVersion;
  name: string;
  source_document: SourceDocument;
  counts: ElementCounts;
  total_elements: number;
}

export interface VersionList {
  versions: VersionInfo[];
}

export interface ElementSummary {
  version: FrameworkVersion;
  element_id: string;
  original_id: string;
  level: ElementLevel;
  name: string | null;
  description: string | null;
  function_id: string;
  category_id: string | null;
  parent_id: string | null;
}

export interface ElementList {
  count: number;
  elements: ElementSummary[];
}

export interface ChunkProvenance {
  chunk_id: string;
  page: number;
  printed_page: string | null;
  section: string;
}

export interface Provenance {
  source_document: SourceDocument;
  chunk: ChunkProvenance;
}

export type MappingType = "mapped" | "new_in_2_0" | "unmapped";

export interface CrosswalkEntry {
  excel_row: number;
  sheet: string;
  source_file: string;
  focal_version: FrameworkVersion;
  focal_element_id: string;
  focal_original_id: string;
  focal_description: string | null;
  reference_version: FrameworkVersion;
  reference_element_id: string | null;
  reference_original_id: string | null;
  reference_description: string | null;
  comments: string | null;
  strength: string | null;
  mapping_type: MappingType;
}

export type CrosswalkStatus =
  | "mapped_only"
  | "new_in_2_0_only"
  | "mapped_and_new_in_2_0"
  | "no_crosswalk_reference"
  | "unclassified";

export interface CrosswalkSummary {
  derived: true;
  status: CrosswalkStatus;
  mapped_row_count: number;
  new_in_2_0_row_count: number;
  excel_rows: number[];
  note: string;
}

export interface Crosswalk {
  direction: string;
  queried_role: "focal" | "reference";
  lookup: "forward" | "reverse";
  entries: CrosswalkEntry[];
  summary: CrosswalkSummary;
}

export interface ElementDetail extends ElementSummary {
  parent: ElementSummary | null;
  children: ElementSummary[];
  informative_references: string[];
  provenance: Provenance;
  crosswalk: Crosswalk;
}

export interface MappingTypeCounts {
  mapped: number;
  new_in_2_0: number;
  unmapped: number;
}

/** GET /crosswalk: one page of official workbook rows, in workbook order. */
export interface CrosswalkList {
  direction: string;
  /** Rows matching every filter. */
  total: number;
  count: number;
  limit: number;
  offset: number;
  /** Rows matching all filters except `type`. */
  type_counts: MappingTypeCounts;
  entries: CrosswalkEntry[];
}

export interface HealthResponse {
  status: "ok";
  database: { chunks: number; elements: number; crosswalk_rows: number };
  retrieval: { mode: string; models_loaded: string[] };
  llm: { configured: boolean; provider: string | null; model: string | null };
}

/** Error envelope returned by the FastAPI app: {"error": {"code", "message", "details"}}. */
export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: { field: string; problem: string }[] | null;
  };
}
