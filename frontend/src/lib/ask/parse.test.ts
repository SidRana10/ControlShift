import { describe, expect, it } from "vitest";
import { ASK_FIXTURES } from "@/test/fake-ask-api";
import { parseAskResponse } from "./parse";
import { allAnswerCitations, evidenceDomId, indexEvidence, pageLabel } from "./citations";

describe("parseAskResponse", () => {
  it.each([
    ["answered", "answered"],
    ["answeredMapping", "answered"],
    ["abstainedLlm", "abstained"],
    ["abstainedNoData", "abstained"],
    ["evidenceOnly", "evidence_only"],
    ["rejected", "rejected"],
  ] as const)("accepts the recorded %s response", (name, status) => {
    const r = parseAskResponse(ASK_FIXTURES[name]);
    expect(r?.status).toBe(status);
  });

  it("separates the model's answer from official evidence and keeps provenance fields", () => {
    const r = parseAskResponse(ASK_FIXTURES.answeredMapping)!;
    expect(r.answer?.citations).toEqual(["chunk:csf2.0:subcategory:GV.SC-03", "chunk:csf1.1:subcategory:ID.SC-2"]);
    expect(r.evidence?.controls[0]).toMatchObject({
      control_id: "GV.SC-03",
      version: "2.0",
      source_file: "nist_csf_2_0.pdf",
      page: 22,
      printed_page: "17",
    });
    expect(r.evidence?.crosswalk.map((c) => c.excel_row)).toEqual([25, 26]);
    expect(r.evidence?.crosswalk[1]).toMatchObject({ reference_id: null, mapping_type: "new_in_2_0" });
    expect(r.evidence?.notes.some((n) => n.kind === "conflict")).toBe(true);
    expect(r.verification.semantic_faithfulness).toBe("not verified");
    expect(r.verification.answer_citations).toEqual({ checked: 2, scope: "structural", valid: true });
  });

  it("represents a rejected response with no answer and the backend's reasons", () => {
    const r = parseAskResponse(ASK_FIXTURES.rejected)!;
    expect(r.answer).toBeNull();
    expect(r.rejection[0]).toMatch(/not in the supplied evidence/);
    expect(r.attempts).toBe(2);
  });

  it("rejects bodies that are not an AnswerResponse", () => {
    expect(parseAskResponse(null)).toBeNull();
    expect(parseAskResponse([])).toBeNull();
    expect(parseAskResponse({ question: "q", disclaimer: "d", status: "maybe" })).toBeNull();
    expect(parseAskResponse({ status: "answered", disclaimer: "d" })).toBeNull();
    expect(parseAskResponse({ status: "answered", question: "q" })).toBeNull();
  });

  it("drops malformed evidence entries instead of displaying guesses", () => {
    const r = parseAskResponse({
      question: "q",
      status: "evidence_only",
      disclaimer: "d",
      evidence: {
        control_records: [{ citation_id: "chunk:x" }, "junk", null],
        crosswalk_records: [{ citation_id: "xwalk:row1", excel_row: "one", focal_id: "A" }],
        passages: [{ citation_id: "chunk:p", version: "2.0", text: "t", page: "7" }],
      },
    })!;
    expect(r.evidence?.controls).toEqual([]);
    expect(r.evidence?.crosswalk).toEqual([]);
    expect(r.evidence?.passages).toHaveLength(1);
    expect(r.evidence?.passages[0].page).toBeNull();
  });

  it("returns evidence: null when none was sent", () => {
    const r = parseAskResponse({ question: "q", status: "evidence_only", disclaimer: "d" })!;
    expect(r.evidence).toBeNull();
    expect(r.answer).toBeNull();
  });
});

describe("citation helpers", () => {
  it("indexes every evidence kind by its citation id", () => {
    const r = parseAskResponse(ASK_FIXTURES.answeredMapping)!;
    const idx = indexEvidence(r.evidence);
    expect(idx.get("xwalk:row25")?.kind).toBe("crosswalk");
    expect(idx.get("chunk:csf2.0:subcategory:GV.SC-03")?.kind).toBe("control");
    expect(idx.size).toBe(9);
  });

  it("collects citations from the answer, key points and mappings once", () => {
    expect(
      allAnswerCitations({
        citations: ["a", "b"],
        key_changes: [{ citations: ["b", "c"] }],
        mappings: [{ citations: ["d"] }],
      }),
    ).toEqual(["a", "b", "c", "d"]);
  });

  it("builds DOM ids and page labels from the data only", () => {
    expect(evidenceDomId("xwalk:row25")).toBe("evidence-xwalk-row25");
    expect(pageLabel("17", 22)).toBe("p. 17 (PDF p. 22)");
    expect(pageLabel(null, 22)).toBe("PDF p. 22");
    expect(pageLabel(null, null)).toBeNull();
  });
});
