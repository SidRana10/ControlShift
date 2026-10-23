import { vi } from "vitest";
import answered from "./fixtures/ask/answered.json";
import answeredMapping from "./fixtures/ask/answered-mapping.json";
import abstainedLlm from "./fixtures/ask/abstained-llm.json";
import abstainedNoData from "./fixtures/ask/abstained-nodata.json";
import evidenceOnly from "./fixtures/ask/evidence-only.json";
import rejected from "./fixtures/ask/rejected.json";
import versioned from "./fixtures/ask/versioned.json";

/**
 * Recorded POST /ask responses. They came from the real pipeline (real SQLite store, BM25
 * retrieval) with a scripted fake LLM, so the evidence is genuine NIST data and the answer text is
 * test text. No external provider was called.
 */
export const ASK_FIXTURES = {
  answered,
  answeredMapping,
  abstainedLlm,
  abstainedNoData,
  evidenceOnly,
  rejected,
  versioned,
};

export type AskFixtureName = keyof typeof ASK_FIXTURES;

export const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

export const errorEnvelope = (status: number, code: string, message = "backend message") =>
  json(status, { error: { code, message, details: null } });

export interface AskCall {
  question: string;
  version?: string;
  signal?: AbortSignal | null;
}

export type AskHandler = (call: AskCall) => Response | Promise<Response>;

/** Replaces fetch for POST /api/backend/ask. Returns the recorded calls. */
export function installAskApi(handler: AskHandler) {
  const calls: AskCall[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://test");
    if (url.pathname !== "/api/backend/ask" || init?.method !== "POST") {
      return json(404, { error: { code: "not_found", message: "no", details: null } });
    }
    const body = JSON.parse(String(init.body)) as { question: string; version?: string };
    const call: AskCall = { ...body, signal: init.signal };
    calls.push(call);
    return handler(call);
  });
  vi.stubGlobal("fetch", fetchMock);
  return { calls, fetchMock };
}

export const respond = (name: AskFixtureName) => json(200, ASK_FIXTURES[name]);
