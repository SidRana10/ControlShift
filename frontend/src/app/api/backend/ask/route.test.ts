import { afterEach, describe, expect, it, vi } from "vitest";
import { POST } from "./route";

const post = (body: unknown) =>
  POST(new Request("http://localhost/api/backend/ask", { method: "POST", body: typeof body === "string" ? body : JSON.stringify(body) }));

afterEach(() => vi.unstubAllGlobals());

describe("POST /api/backend/ask proxy", () => {
  it("forwards only question and version to FastAPI /ask", async () => {
    const upstream = vi.fn(async () => Response.json({ status: "answered" }));
    vi.stubGlobal("fetch", upstream);
    const res = await post({ question: "  What is GV.SC-03?  ", version: "2.0", retrieval_k: 99, generate: false, api_key: "x" });
    expect(res.status).toBe(200);
    const [url, init] = upstream.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8000/ask");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ question: "What is GV.SC-03?", version: "2.0" });
  });

  it.each([
    ["not json", "{nope"],
    ["blank question", { question: "   " }],
    ["no question", {}],
    ["too long", { question: "x".repeat(2001) }],
    ["bad version", { question: "ok", version: "3.0" }],
  ])("rejects %s with the error envelope and no upstream call", async (_n, body) => {
    const upstream = vi.fn();
    vi.stubGlobal("fetch", upstream);
    const res = await post(body);
    expect(res.status).toBe(422);
    expect((await res.json()).error.code).toBe("invalid_request");
    expect(upstream).not.toHaveBeenCalled();
  });

  it("passes FastAPI's error envelope and status through unchanged", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Response.json({ error: { code: "provider_error", message: "m", details: null } }, { status: 502 })));
    const res = await post({ question: "q" });
    expect(res.status).toBe(502);
    expect((await res.json()).error.code).toBe("provider_error");
  });

  it("maps an unreachable backend, a timeout and a non-JSON reply to envelopes", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("fetch failed"); }));
    let res = await post({ question: "q" });
    expect([res.status, (await res.json()).error.code]).toEqual([502, "api_unreachable"]);

    vi.stubGlobal("fetch", vi.fn(async () => { throw new DOMException("t", "TimeoutError"); }));
    res = await post({ question: "q" });
    expect([res.status, (await res.json()).error.code]).toEqual([504, "proxy_timeout"]);

    vi.stubGlobal("fetch", vi.fn(async () => new Response("<html>bad gateway</html>", { status: 502 })));
    res = await post({ question: "q" });
    expect([res.status, (await res.json()).error.code]).toEqual([502, "api_unreachable"]);
  });
});
