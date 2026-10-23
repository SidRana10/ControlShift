/**
 * Same-origin proxy for POST /ask. A route handler (not a rewrite) so that the browser can only send
 * the two fields the UI uses, the upstream call has its own timeout, and failures come back in the
 * API's error envelope. Provider credentials live in the FastAPI process and never reach this layer.
 */
const apiUrl = () => (process.env.CONTROLSHIFT_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
/** Longer than the backend's own REQUEST_TIMEOUT_SECONDS default (90s), so FastAPI's 504 wins. */
const UPSTREAM_TIMEOUT_MS = 100_000;
const MAX_QUESTION_LENGTH = 2000;

const envelope = (status: number, code: string, message: string, details: unknown[] | null = null) =>
  Response.json({ error: { code, message, details } }, { status });

export async function POST(request: Request) {
  let input: unknown;
  try {
    input = await request.json();
  } catch {
    return envelope(422, "invalid_request", "The request body is invalid.");
  }
  const body = typeof input === "object" && input !== null ? (input as Record<string, unknown>) : {};
  const question = typeof body.question === "string" ? body.question.trim() : "";
  if (!question || question.length > MAX_QUESTION_LENGTH) {
    return envelope(422, "invalid_request", "The request body is invalid.", [
      { field: "question", problem: `must be 1 to ${MAX_QUESTION_LENGTH} characters` },
    ]);
  }
  if (body.version !== undefined && body.version !== "1.1" && body.version !== "2.0") {
    return envelope(422, "invalid_request", "The request body is invalid.", [
      { field: "version", problem: "must be 1.1 or 2.0" },
    ]);
  }

  try {
    const upstream = await fetch(`${apiUrl()}/ask`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ question, ...(body.version ? { version: body.version } : {}) }),
      cache: "no-store",
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
    const text = await upstream.text();
    try {
      JSON.parse(text);
    } catch {
      return envelope(502, "api_unreachable", "The ControlShift API returned an unreadable response.");
    }
    return new Response(text, {
      status: upstream.status,
      headers: { "content-type": "application/json", "cache-control": "no-store" },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "TimeoutError") {
      return envelope(504, "proxy_timeout", "The ControlShift API did not respond in time.");
    }
    return envelope(502, "api_unreachable", "The ControlShift API could not be reached.");
  }
}
