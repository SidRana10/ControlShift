/**
 * Same-origin, read-only proxy for the FastAPI GET endpoints the UI uses. A route handler rather
 * than a next.config rewrite so CONTROLSHIFT_API_URL is read at request time: `next build` does not
 * bake the backend address in, and one build can run against any backend. Only the paths below are
 * forwarded (no /docs, /openapi.json, /compare or anything else); every other path is a 404 and
 * every other method a 405. POST /ask has its own handler in ../ask/route.ts.
 */
const API_URL = () => (process.env.CONTROLSHIFT_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");
const TIMEOUT_MS = 30_000;

const ALLOWED = [
  /^health$/,
  /^crosswalk$/,
  /^catalog\/versions$/,
  /^catalog\/elements$/,
  /^catalog\/elements\/[^/]+\/[^/]+$/,
];

export async function GET(request: Request, { params }: { params: Promise<{ path: string[] }> }) {
  const path = (await params).path.join("/");
  if (!ALLOWED.some((re) => re.test(path))) {
    return Response.json({ error: { code: "not_found", message: "Not found.", details: null } }, { status: 404 });
  }
  const search = new URL(request.url).search;
  try {
    const upstream = await fetch(`${API_URL()}/${path}${search}`, {
      headers: { accept: "application/json" },
      cache: "no-store",
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: {
        "content-type": upstream.headers.get("content-type") ?? "application/json",
        "cache-control": "no-store",
      },
    });
  } catch {
    // Plain 502: the client treats a non-envelope 5xx as "API unreachable".
    return new Response("Bad Gateway", { status: 502 });
  }
}
