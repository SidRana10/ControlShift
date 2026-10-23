import { parseAskResponse } from "@/lib/ask/parse";
import type { AskRequestBody, AskResult } from "@/lib/ask/types";
import type {
  ApiErrorEnvelope,
  CrosswalkList,
  MappingType,
  ElementDetail,
  ElementLevel,
  ElementList,
  FrameworkVersion,
  HealthResponse,
  VersionList,
} from "./types";

/** Same-origin prefix; next.config.ts rewrites it to the FastAPI service. */
export const API_PREFIX = "/api/backend";

export type ApiErrorKind =
  | "unreachable" // network failure, or the proxy could not reach FastAPI
  | "timeout" // the browser gave up waiting (POST /ask only)
  | "api" // FastAPI answered with its error envelope
  | "unexpected"; // anything else (non-JSON body, unknown shape)

export class ApiError extends Error {
  constructor(
    readonly kind: ApiErrorKind,
    message: string,
    readonly status?: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function isEnvelope(body: unknown): body is ApiErrorEnvelope {
  if (typeof body !== "object" || body === null || !("error" in body)) return false;
  const e = (body as { error: unknown }).error;
  return (
    typeof e === "object" &&
    e !== null &&
    typeof (e as { code?: unknown }).code === "string" &&
    typeof (e as { message?: unknown }).message === "string"
  );
}

const isObject = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null;

/** Minimal shape guards: enough to reject an unexpected payload before the UI trusts it. */
const guards = {
  health: (b: unknown): b is HealthResponse =>
    isObject(b) && b.status === "ok" && isObject(b.database) && isObject(b.llm),
  crosswalk: (b: unknown): b is CrosswalkList =>
    isObject(b) &&
    typeof b.total === "number" &&
    Array.isArray(b.entries) &&
    isObject(b.type_counts) &&
    b.entries.every(
      (e: unknown) =>
        isObject(e) &&
        typeof e.excel_row === "number" &&
        typeof e.focal_element_id === "string" &&
        typeof e.focal_original_id === "string" &&
        typeof e.mapping_type === "string",
    ),
  versions: (b: unknown): b is VersionList => isObject(b) && Array.isArray(b.versions),
  elements: (b: unknown): b is ElementList => isObject(b) && Array.isArray(b.elements),
  element: (b: unknown): b is ElementDetail =>
    isObject(b) &&
    typeof b.element_id === "string" &&
    typeof b.original_id === "string" &&
    Array.isArray(b.children) &&
    Array.isArray(b.informative_references) &&
    isObject(b.provenance) &&
    isObject(b.provenance.chunk) &&
    isObject(b.provenance.source_document) &&
    isObject(b.crosswalk) &&
    Array.isArray(b.crosswalk.entries) &&
    isObject(b.crosswalk.summary),
};

async function send<T>(
  path: string,
  init: RequestInit,
  guard: (body: unknown) => body is T,
  signal?: AbortSignal,
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_PREFIX}${path}`, {
      ...init,
      headers: { accept: "application/json", ...init.headers },
      cache: "no-store",
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("unreachable", "The ControlShift API could not be reached.");
  }

  let body: unknown = undefined;
  try {
    body = await res.json();
  } catch {
    // Non-JSON body: handled below.
  }

  if (!res.ok) {
    if (isEnvelope(body)) {
      throw new ApiError("api", body.error.message, res.status, body.error.code);
    }
    // The Next.js proxy answers 5xx with a plain body when FastAPI is down.
    if (res.status >= 500) {
      throw new ApiError("unreachable", "The ControlShift API could not be reached.", res.status);
    }
    throw new ApiError("unexpected", "The API returned an unexpected response.", res.status);
  }
  if (!guard(body)) {
    throw new ApiError("unexpected", "The API returned an unexpected response.", res.status);
  }
  return body;
}

const get = <T>(path: string, guard: (body: unknown) => body is T, signal?: AbortSignal) =>
  send(path, {}, guard, signal);

export const getHealth = (signal?: AbortSignal) => get("/health", guards.health, signal);

export const getVersions = (signal?: AbortSignal) =>
  get("/catalog/versions", guards.versions, signal);

export interface ListElementsParams {
  version?: FrameworkVersion;
  level?: ElementLevel;
  function?: string;
  category?: string;
  q?: string;
}

export function listElements(params: ListElementsParams = {}, signal?: AbortSignal) {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) qs.set(key, value);
  }
  const suffix = qs.size ? `?${qs}` : "";
  return get(`/catalog/elements${suffix}`, guards.elements, signal);
}

export interface CrosswalkParams {
  focal?: string;
  reference?: string;
  type?: MappingType;
  q?: string;
  limit?: number;
  offset?: number;
}

export function listCrosswalk(params: CrosswalkParams = {}, signal?: AbortSignal) {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") qs.set(key, String(value));
  }
  return get(`/crosswalk${qs.size ? `?${qs}` : ""}`, guards.crosswalk, signal);
}

export const getElement = (version: FrameworkVersion, elementId: string, signal?: AbortSignal) =>
  get(
    `/catalog/elements/${version}/${encodeURIComponent(elementId)}`,
    guards.element,
    signal,
  );

/** The backend allows 90s per request by default; the browser waits a little longer than that. */
export const ASK_TIMEOUT_MS = 120_000;

/**
 * POST /ask through the same-origin proxy. `signal` cancels the request; independently, the call
 * fails with an ApiError("timeout") after `timeoutMs`. HTTP 200 bodies are normalised by
 * parseAskResponse; anything it rejects becomes an "unexpected" error.
 */
export async function askQuestion(
  request: AskRequestBody,
  signal?: AbortSignal,
  timeoutMs: number = ASK_TIMEOUT_MS,
): Promise<AskResult> {
  const controller = new AbortController();
  let timedOut = false;
  const onAbort = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener("abort", onAbort, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  try {
    const body = await send(
      "/ask",
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      },
      (b): b is object => parseAskResponse(b) !== null,
      controller.signal,
    );
    return parseAskResponse(body)!;
  } catch (err) {
    if (timedOut) throw new ApiError("timeout", "The request took too long.");
    throw err;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onAbort);
  }
}
