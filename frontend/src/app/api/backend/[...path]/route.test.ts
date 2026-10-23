import { afterEach, describe, expect, it, vi } from "vitest";
import { GET } from "./route";

const get = (path: string, search = "") =>
  GET(new Request(`http://localhost/api/backend/${path}${search}`), {
    params: Promise.resolve({ path: path.split("/") }),
  });

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("GET /api/backend/* read-only proxy", () => {
  it.each([
    "health",
    "crosswalk",
    "catalog/versions",
    "catalog/elements",
    "catalog/elements/2.0/GV.SC-03",
  ])("forwards %s with its query string to the configured backend", async (path) => {
    vi.stubEnv("CONTROLSHIFT_API_URL", "http://backend.test:9000/");
    const upstream = vi.fn<(url: string) => Promise<Response>>(async () => Response.json({ ok: true }));
    vi.stubGlobal("fetch", upstream);
    const res = await get(path, "?q=a&type=mapped");
    expect(res.status).toBe(200);
    expect(upstream.mock.calls[0][0]).toBe(`http://backend.test:9000/${path}?q=a&type=mapped`);
  });

  it.each(["docs", "openapi.json", "compare", "ask", "catalog", "catalog/elements/2.0", "catalog/elements/2.0/GV/extra", "../health", "crosswalk/x"])(
    "does not expose %s",
    async (path) => {
      const upstream = vi.fn();
      vi.stubGlobal("fetch", upstream);
      const res = await get(path);
      expect(res.status).toBe(404);
      expect(upstream).not.toHaveBeenCalled();
    },
  );

  it("passes backend errors through and reports an unreachable backend as a plain 502", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => Response.json({ error: { code: "not_found", message: "m", details: null } }, { status: 404 })));
    expect((await get("catalog/elements/2.0/ZZ.ZZ-99")).status).toBe(404);
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("fetch failed"); }));
    const res = await get("health");
    expect(res.status).toBe(502);
    expect(await res.text()).toBe("Bad Gateway");
  });
});
