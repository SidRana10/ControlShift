import type {
  ApiErrorEnvelope,
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
  versions: (b: unknown): b is VersionList => isObject(b) && Array.isArray(b.versions),
  elements: (b: unknown): b is ElementList => isObject(b) && Array.isArray(b.elements),
  element: (b: unknown): b is ElementDetail =>
    isObject(b) && typeof b.element_id === "string" && isObject(b.crosswalk),
};

async function get<T>(
  path: string,
  guard: (body: unknown) => body is T,
  signal?: AbortSignal,
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_PREFIX}${path}`, {
      headers: { accept: "application/json" },
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

export const getElement = (version: FrameworkVersion, elementId: string, signal?: AbortSignal) =>
  get(
    `/catalog/elements/${version}/${encodeURIComponent(elementId)}`,
    guards.element,
    signal,
  );
