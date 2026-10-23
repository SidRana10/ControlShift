import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, askQuestion } from "@/lib/api/client";
import { describeAskError } from "@/lib/ask/errors";
import {
  ASK_FIXTURES,
  errorEnvelope,
  installAskApi,
  json,
  respond,
  type AskFixtureName,
} from "@/test/fake-ask-api";
import { AskWorkspace } from "./ask-workspace";

const ta = () => screen.getByRole("textbox", { name: "Your question" });
const result = () => screen.getByRole("article");
const evidence = () => screen.getByRole("complementary", { name: /Retrieved evidence/ });

async function ask(user: ReturnType<typeof userEvent.setup>, q: string) {
  await user.clear(ta());
  await user.type(ta(), q);
  await user.keyboard("{Enter}");
}

beforeEach(() => {
  installAskApi(() => respond("answered"));
});
afterEach(() => vi.unstubAllGlobals());

function serve(name: AskFixtureName) {
  return installAskApi(() => respond(name));
}

describe("initial state", () => {
  it("shows orientation, examples that only fill the question, and the three source labels", async () => {
    const user = userEvent.setup();
    const { fetchMock } = installAskApi(() => respond("answered"));
    render(<AskWorkspace />);
    expect(screen.getByRole("heading", { name: "Try an example" })).toBeInTheDocument();
    expect(screen.getByText("NIST")).toBeInTheDocument();
    expect(screen.getByText("Derived")).toBeInTheDocument();
    expect(screen.getByText("AI-generated")).toBeInTheDocument();
    expect(screen.getByText(/keeps no conversation history/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ask" })).toBeDisabled();

    await user.click(screen.getByRole("button", { name: "What does GV.SC-03 require?" }));
    expect(ta()).toHaveValue("What does GV.SC-03 require?");
    expect(ta()).toHaveFocus();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("submitting a question", () => {
  it("sends exactly the trimmed question on Enter and disables duplicates while loading", async () => {
    const user = userEvent.setup();
    const { calls } = installAskApi(async () => {
      await new Promise((r) => setTimeout(r, 50));
      return respond("answered");
    });
    render(<AskWorkspace />);
    await user.type(ta(), "  What does GV.SC-03 require?  ");
    await user.keyboard("{Enter}");
    expect(screen.getByRole("button", { name: "Asking…" })).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent("Searching the NIST evidence");
    await user.keyboard("{Enter}"); // textarea is read-only while loading; Ask is disabled
    await user.click(screen.getByRole("button", { name: "Asking…" }));
    await screen.findByRole("article");
    expect(calls).toHaveLength(1);
    expect(calls[0]).toMatchObject({ question: "What does GV.SC-03 require?" });
    expect(calls[0].version).toBeUndefined();
  });

  it("keeps Shift+Enter for new lines and sends the chosen version scope", async () => {
    const user = userEvent.setup();
    const { calls } = serve("versioned");
    render(<AskWorkspace />);
    await user.type(ta(), "line one{Shift>}{Enter}{/Shift}line two");
    expect(ta()).toHaveValue("line one\nline two");
    await user.click(screen.getByRole("radio", { name: "CSF 1.1" }));
    expect(screen.getByText(/prefixes “In CSF 1.1:”/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByRole("article");
    expect(calls[0]).toMatchObject({ question: "line one\nline two", version: "1.1" });
  });

  it("moves focus to the result heading and labels the effective question and searched versions", async () => {
    const user = userEvent.setup();
    serve("versioned");
    render(<AskWorkspace />);
    await ask(user, "How is data at rest protected?");
    const heading = await screen.findByRole("heading", { name: "How is data at rest protected?" });
    await waitFor(() => expect(heading).toHaveFocus());
    expect(within(result()).getByText(/Sent to the API as:/)).toHaveTextContent("In CSF 1.1: How is data at rest protected?");
    expect(within(result()).getByText(/Evidence searched in CSF 1.1/)).toBeInTheDocument();
    // the version scope is described as a request, never as an enforced filter
    expect(within(result()).queryByText(/restricted|only CSF/i)).toBeNull();
  });
});

describe("answered result", () => {
  it("labels the model's text AI-generated, apart from the official evidence", async () => {
    const user = userEvent.setup();
    serve("answeredMapping");
    render(<AskWorkspace />);
    await ask(user, "How does GV.SC-03 map to CSF 1.1?");
    await screen.findByRole("article");
    const a = result();
    expect(within(a).getByText("AI-generated")).toBeInTheDocument();
    expect(within(a).getByText(/scripted test explanation/)).toBeInTheDocument();
    expect(within(a).getByText(/semantic faithfulness is not verified/i)).toBeInTheDocument();
    expect(within(a).getByText(/Semantic faithfulness: not verified/)).toBeInTheDocument();
    expect(within(a).getByText(/2 cited sources checked for existence and provenance \(structural\)/)).toBeInTheDocument();
    expect(within(a).getByText(/Written by fake \(fake-model-1\)/)).toBeInTheDocument();
    // generated text is never set in the official-text serif
    expect(within(a).getByText(/scripted test explanation/).className).not.toMatch(/font-serif/);
    // ControlShift's own caveat is visible, not hidden
    expect(within(a).getByText("Evidence caveats from ControlShift")).toBeInTheDocument();
    expect(within(a).getByText(/xwalk:row25, xwalk:row26/)).toBeInTheDocument();
  });

  it("links each citation to its evidence entry, marks it, and returns focus to the chip", async () => {
    const user = userEvent.setup();
    serve("answeredMapping");
    render(<AskWorkspace />);
    await ask(user, "How does GV.SC-03 map to CSF 1.1?");
    await screen.findByRole("article");

    const chip = within(screen.getByRole("list", { name: "Answer citations" })).getByRole("button", {
      name: /Citation: CSF 1.1 ID.SC-2/,
    });
    expect(chip).toHaveAttribute("aria-pressed", "false");
    await user.click(chip);
    const entry = document.getElementById("evidence-chunk-csf1-1-subcategory-ID-SC-2")!;
    expect(entry).toHaveAttribute("data-active");
    expect(entry).toHaveFocus();
    expect(chip).toHaveAttribute("aria-pressed", "true");
    expect(within(entry).getByText("Cited in answer")).toBeInTheDocument();
    expect(within(entry).getByText(/Suppliers and third party partners/)).toBeInTheDocument();

    await user.click(within(entry).getByRole("button", { name: /Back to the citation in the answer/ }));
    expect(chip).toHaveFocus();
  });

  it("shows official text with NIST source, version, page, section and a real Explorer link", async () => {
    const user = userEvent.setup();
    serve("answeredMapping");
    render(<AskWorkspace />);
    await ask(user, "How does GV.SC-03 map to CSF 1.1?");
    await screen.findByRole("article");
    const entry = document.getElementById("evidence-chunk-csf2-0-subcategory-GV-SC-03")!;
    expect(within(entry).getByText("NIST")).toBeInTheDocument();
    expect(within(entry).getByText(/CSF 2.0 · p. 17 \(PDF p. 22\)/)).toBeInTheDocument();
    expect(within(entry).getByText("Core > Govern (GV) > GV.SC-03")).toBeInTheDocument();
    expect(within(entry).getByText(/Cybersecurity supply chain risk management is integrated/).className).toMatch(/font-serif/);
    expect(within(entry).getByRole("link", { name: /Open GV.SC-03 in Control Explorer/ })).toHaveAttribute("href", "/explorer/2.0/GV.SC-03");

    await user.click(within(entry).getByRole("button", { name: "Source details" }));
    expect(within(entry).getByText("nist_csf_2_0.pdf")).toBeVisible();
    expect(within(entry).getByText("csf2.0:subcategory:GV.SC-03")).toBeVisible();
  });

  it("renders both official workbook rows, in order, with the derived label and no merging", async () => {
    const user = userEvent.setup();
    serve("answeredMapping");
    render(<AskWorkspace />);
    await ask(user, "How does GV.SC-03 map to CSF 1.1?");
    await screen.findByRole("article");
    const rows = within(evidence()).getByRole("heading", { name: /Official crosswalk rows/ }).closest("section")!;
    const [r25, r26] = within(rows).getAllByRole("listitem");
    expect(r25).toHaveTextContent("Row 25");
    expect(r26).toHaveTextContent("Row 26");
    expect(within(r25).getByRole("link", { name: /Open ID.SC-2 in Control Explorer/ })).toHaveAttribute("href", "/explorer/1.1/ID.SC-2");
    expect(within(r26).getByText("No reference element")).toBeInTheDocument();
    expect(within(r26).getByText("“Conceptually new in 2.0”")).toBeInTheDocument();
    expect(within(r26).getByText("new_in_2_0")).toBeInTheDocument();
    expect(within(r26).getByText("Derived")).toBeInTheDocument();
    expect(within(r26).getByText(/sheet Relationships/)).toBeInTheDocument();
  });

  it("filters the inspector to entries the answer cites", async () => {
    const user = userEvent.setup();
    serve("answeredMapping");
    render(<AskWorkspace />);
    await ask(user, "How does GV.SC-03 map to CSF 1.1?");
    await screen.findByRole("article");
    expect(within(evidence()).getByText(/Retrieved evidence/)).toHaveTextContent("(9)");
    await user.click(screen.getByRole("button", { name: "Cited in answer (2)" }));
    expect(within(evidence()).getAllByText("Cited in answer")).toHaveLength(2);
    expect(within(evidence()).queryByText(/Row 25/)).toBeNull();
  });

  it("summarises evidence by version without inventing counts", async () => {
    const user = userEvent.setup();
    serve("answeredMapping");
    render(<AskWorkspace />);
    await ask(user, "How does GV.SC-03 map to CSF 1.1?");
    await screen.findByRole("article");
    expect(within(evidence()).getByText(/CSF 1.1: 4 · CSF 2.0: 3 · Transition workbook: 2 rows/)).toBeInTheDocument();
    expect(within(evidence()).getByText(/Searched CSF 1.1, CSF 2.0 · retrieval: bm25/)).toBeInTheDocument();
  });
});

describe("other statuses", () => {
  it("evidence-only: states that nothing was generated and shows the evidence", async () => {
    const user = userEvent.setup();
    serve("evidenceOnly");
    render(<AskWorkspace />);
    await ask(user, "What does GV.SC-03 require?");
    await screen.findByRole("article");
    expect(within(result()).getByText("Evidence only")).toBeInTheDocument();
    expect(within(result()).getByText("No answer was generated")).toBeInTheDocument();
    expect(within(result()).getByText(/no language model configured/)).toBeInTheDocument();
    expect(within(result()).queryByText("AI-generated")).toBeNull();
    expect(within(result()).queryByText(/Sources cited for the answer/)).toBeNull();
    expect(within(evidence()).getByRole("heading", { name: /Official control records/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cited in answer (0)" })).toBeNull();
  });

  it("abstained by the model: shows its reason under an AI-generated label", async () => {
    const user = userEvent.setup();
    serve("abstainedLlm");
    render(<AskWorkspace />);
    await ask(user, "What does GV.SC-03 require? [abstain]");
    await screen.findByRole("article");
    expect(within(result()).getByText("No answer given")).toBeInTheDocument();
    expect(within(result()).getByText(/The supplied evidence does not describe this topic\./)).toBeInTheDocument();
    expect(within(result()).getByText("AI-generated")).toBeInTheDocument();
    expect(within(result()).getByText(/The model’s reason/)).toBeInTheDocument();
  });

  it("abstained before the model: uses the backend's reason, says no model was asked, and shows empty evidence honestly", async () => {
    const user = userEvent.setup();
    serve("abstainedNoData");
    render(<AskWorkspace />);
    await ask(user, "zzzzqqq xyzzy");
    await screen.findByRole("article");
    expect(within(result()).getByText(/The question could not be interpreted|No evidence was found/)).toBeInTheDocument();
    expect(within(result()).getByText(/stopped before asking a language model/)).toBeInTheDocument();
    expect(within(result()).queryByText("AI-generated")).toBeNull();
    expect(within(evidence()).getByText("No evidence was returned")).toBeInTheDocument();
  });

  it("rejected: withholds all model text, explains, and keeps the checks and evidence", async () => {
    const user = userEvent.setup();
    serve("rejected");
    render(<AskWorkspace />);
    await ask(user, "What does GV.SC-03 require? [reject]");
    await screen.findByRole("article");
    expect(within(result()).getByText("Answer withheld")).toBeInTheDocument();
    expect(within(result()).getByText("The model’s answer was withheld")).toBeInTheDocument();
    expect(within(result()).getByText(/after 2 attempts/)).toBeInTheDocument();
    expect(within(result()).queryByText("AI-generated")).toBeNull();
    expect(within(result()).queryByText("x")).toBeNull();
    await user.click(within(result()).getByText(/Why the answer failed the checks/));
    expect(within(result()).getByText(/cited ids not in the supplied evidence/)).toBeInTheDocument();
    expect(within(evidence()).getAllByRole("listitem").length).toBeGreaterThan(0);
  });
});

describe("missing data", () => {
  const base = ASK_FIXTURES.answered as Record<string, unknown>;

  it("shows a citation absent from the evidence as plain text, not a link", async () => {
    const user = userEvent.setup();
    installAskApi(() =>
      json(200, { ...base, answer: { ...(base.answer as object), citations: ["chunk:csf2.0:ghost"] } }),
    );
    render(<AskWorkspace />);
    await ask(user, "q");
    await screen.findByRole("article");
    const list = screen.getByRole("list", { name: "Answer citations" });
    expect(within(list).queryByRole("button")).toBeNull();
    expect(within(list).getByText(/not in returned evidence/)).toBeInTheDocument();
  });

  it("handles an answer with no citations and a response with no evidence object", async () => {
    const user = userEvent.setup();
    installAskApi(() =>
      json(200, { ...base, evidence: null, answer: { ...(base.answer as object), citations: [], key_changes: [] } }),
    );
    render(<AskWorkspace />);
    await ask(user, "q");
    await screen.findByRole("article");
    expect(screen.getByText("The answer lists no top-level citations.")).toBeInTheDocument();
    expect(screen.getByText(/did not include an evidence bundle/)).toBeInTheDocument();
  });

  it("flags an answered status that carries no answer text", async () => {
    const user = userEvent.setup();
    installAskApi(() => json(200, { ...base, answer: null }));
    render(<AskWorkspace />);
    await ask(user, "q");
    expect(await screen.findByText("The response had no answer text")).toBeInTheDocument();
  });
});

describe("failures and retry", () => {
  it.each([
    ["provider_error", 502, "The language model provider returned an error"],
    ["provider_timeout", 504, "The answer took too long"],
    ["request_timeout", 504, "The answer took too long"],
    ["internal_error", 500, "The API ran into an internal error"],
    ["provider_not_configured", 502, "No language model is configured"],
    ["invalid_request", 422, "That question can’t be sent"],
  ])("maps %s to actionable copy without leaking the backend message", async (code, status, title) => {
    const user = userEvent.setup();
    installAskApi(() => errorEnvelope(status, code, "Groq returned HTTP 503 (secret_token)"));
    render(<AskWorkspace />);
    await ask(user, "q");
    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText(title)).toBeInTheDocument();
    expect(within(alert).getByText(code)).toBeInTheDocument();
    expect(alert).not.toHaveTextContent(/Groq|secret_token|HTTP 503/);
  });

  it("reports an unreachable backend, then retries the same question successfully", async () => {
    const user = userEvent.setup();
    let fail = true;
    const { calls } = installAskApi(() => {
      if (fail) throw new TypeError("network down");
      return respond("answered");
    });
    render(<AskWorkspace />);
    await ask(user, "What does GV.SC-03 require?");
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("ControlShift API is unreachable");
    expect(alert).toHaveTextContent("controlshift-serve");
    expect(ta()).toHaveValue("What does GV.SC-03 require?");

    fail = false;
    await user.click(within(alert).getByRole("button", { name: "Try again" }));
    await screen.findByRole("article");
    expect(screen.queryByRole("alert")).toBeNull();
    expect(calls.map((c) => c.question)).toEqual(["What does GV.SC-03 require?", "What does GV.SC-03 require?"]);
  });

  it("treats a malformed 200 and a plain-text 502 as unexpected / unreachable, never as results", async () => {
    const user = userEvent.setup();
    installAskApi(() => json(200, { status: "answered", note: "no question or disclaimer" }));
    const { unmount } = render(<AskWorkspace />);
    await ask(user, "q");
    expect(await screen.findByRole("alert")).toHaveTextContent("returned a response ControlShift can’t read");
    expect(screen.queryByRole("article")).toBeNull();
    unmount();

    installAskApi(() => new Response("Bad Gateway", { status: 502 }));
    render(<AskWorkspace />);
    await ask(user, "q");
    expect(await screen.findByRole("alert")).toHaveTextContent("ControlShift API is unreachable");
  });

  it("explains a client-side timeout", () => {
    const copy = describeAskError(new ApiError("timeout", "x"));
    expect(copy.title).toBe("The answer took too long");
  });
});

describe("stale responses and cancellation", () => {
  it("ignores a cancelled question's late response when a newer question has been asked", async () => {
    const user = userEvent.setup();
    const { calls } = installAskApi(async ({ question }) => {
      if (question === "slow question") {
        await new Promise((r) => setTimeout(r, 150));
        return json(200, { ...ASK_FIXTURES.answered, question: "slow question", effective_question: "slow question" });
      }
      return json(200, { ...ASK_FIXTURES.answered, question: "fast question", effective_question: "fast question" });
    });
    render(<AskWorkspace />);
    await ask(user, "slow question");
    expect(screen.getByRole("button", { name: "Asking…" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(ta()).toHaveValue("slow question"); // Cancel keeps the text; Clear empties it
    expect(screen.queryByRole("status")).toBeNull();
    expect(calls[0].signal?.aborted).toBe(true);

    await ask(user, "fast question");
    await screen.findByRole("heading", { name: "fast question" });
    await act(() => new Promise((r) => setTimeout(r, 250))); // the slow response arrives late
    expect(screen.getByRole("heading", { name: "fast question" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "slow question" })).toBeNull();
  });

  it("Clear removes the result and the question and focuses the field", async () => {
    const user = userEvent.setup();
    render(<AskWorkspace />);
    await ask(user, "What does GV.SC-03 require?");
    await screen.findByRole("article");
    await user.click(screen.getByRole("button", { name: "Clear" }));
    expect(screen.queryByRole("article")).toBeNull();
    expect(ta()).toHaveValue("");
    expect(ta()).toHaveFocus();
    expect(screen.getByRole("heading", { name: "Try an example" })).toBeInTheDocument();
  });
});

describe("askQuestion client", () => {
  it("fails with a timeout error after the given time", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((_u: unknown, init: RequestInit) => new Promise((_res, rej) => {
        init.signal?.addEventListener("abort", () => rej(new DOMException("aborted", "AbortError")));
      })),
    );
    await expect(askQuestion({ question: "q" }, undefined, 20)).rejects.toMatchObject({ kind: "timeout" });
  });

  it("rethrows a caller abort as AbortError, not a timeout", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((_u: unknown, init: RequestInit) => new Promise((_res, rej) => {
        init.signal?.addEventListener("abort", () => rej(new DOMException("aborted", "AbortError")));
      })),
    );
    const ctl = new AbortController();
    const p = askQuestion({ question: "q" }, ctl.signal, 5_000);
    ctl.abort();
    await expect(p).rejects.toMatchObject({ name: "AbortError" });
  });
});

describe("responsive structure", () => {
  it("places evidence after the answer (stacked) and in a sticky side pane at wide widths", async () => {
    const user = userEvent.setup();
    serve("answeredMapping");
    render(<AskWorkspace />);
    await ask(user, "How does GV.SC-03 map to CSF 1.1?");
    await screen.findByRole("article");
    const aside = evidence();
    expect(result().compareDocumentPosition(aside) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(aside.className).toMatch(/min-\[1360px\]:sticky/);
    // touch targets: citation chips and controls are 44px tall below 900px
    const chip = within(screen.getByRole("list", { name: "Answer citations" })).getAllByRole("button")[0];
    expect(chip.className).toMatch(/min-h-11/);
    expect(screen.getByRole("button", { name: "Clear" }).className).toMatch(/min-h-11/);
    expect(document.body.innerHTML).not.toMatch(/overflow-x-scroll/);
  });
});
