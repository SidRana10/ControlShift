"use client";

import { useId } from "react";
import { Notice } from "@/components/shared/notice";
import { GeneratedTag } from "@/components/shared/source-tags";
import type { AskResult, EvidenceItem } from "@/lib/ask/types";
import { CitationList } from "./citation-chip";

interface Props {
  result: AskResult;
  index: Map<string, EvidenceItem>;
  activeId: string | null;
  onSelect: (citationId: string, origin: HTMLElement) => void;
  headingRef: React.RefObject<HTMLHeadingElement | null>;
}

const STATUS_LABEL: Record<AskResult["status"], string> = {
  answered: "Answered",
  abstained: "No answer given",
  evidence_only: "Evidence only",
  rejected: "Answer withheld",
};

function List({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <section className="mt-5">
      <h3 className="text-title-sm font-semibold text-fg-1">{title}</h3>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-body text-fg-2">
        {items.map((t, i) => (
          <li key={i}>{t}</li>
        ))}
      </ul>
    </section>
  );
}

function Details({ summary, items }: { summary: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <details className="mt-4 text-ui-sm text-fg-2">
      <summary className="inline-flex min-h-11 cursor-pointer items-center font-medium text-fg-2 hover:text-fg-1 min-[900px]:min-h-7">
        {summary} ({items.length})
      </summary>
      <ul className="mt-1 list-disc space-y-1 pl-5 break-words">
        {items.map((t, i) => (
          <li key={i}>{t}</li>
        ))}
      </ul>
    </details>
  );
}

/** What was and was not verified, in the API's own words plus the figures it reported. */
function Verification({ result }: { result: AskResult }) {
  const v = result.verification;
  const facts: string[] = [];
  if (v.answer_citations && v.answer_citations.checked > 0) {
    facts.push(
      `${v.answer_citations.checked} cited source${v.answer_citations.checked === 1 ? "" : "s"} checked for existence and provenance (${v.answer_citations.scope}).`,
    );
  }
  if (v.semantic_faithfulness) facts.push(`Semantic faithfulness: ${v.semantic_faithfulness}.`);
  const { name, model } = result.provider;
  return (
    <footer className="mt-6 border-t border-border pt-3 text-caption text-fg-3">
      <p>{result.disclaimer}</p>
      {facts.length > 0 && <p className="mt-1">{facts.join(" ")}</p>}
      {result.status === "answered" && name && (
        <p className="mt-1">
          Written by {name}
          {model ? ` (${model})` : ""}
          {result.attempts > 1 ? ` after ${result.attempts} attempts` : ""}.
        </p>
      )}
    </footer>
  );
}

function GeneratedAnswer({ result, index, activeId, onSelect }: Omit<Props, "headingRef">) {
  const a = result.answer!;
  const cites = a.citations;
  return (
    <div className="border-l-[3px] border-fg-3 pl-4 min-[900px]:pl-5">
      <div className="flex flex-wrap items-center gap-2">
        <GeneratedTag />
        <span className="text-caption text-fg-3">Written by a language model from the evidence on this page.</span>
      </div>
      <p className="mt-3 text-source whitespace-pre-line text-fg-1">{a.answer}</p>

      {cites.length === 0 ? (
        <p className="mt-3 text-caption text-fg-3">The answer lists no top-level citations.</p>
      ) : (
        <div className="mt-3">
          <p className="mb-1 text-caption text-fg-3">Sources cited for the answer as a whole</p>
          <CitationList ids={cites} index={index} activeId={activeId} onSelect={onSelect} label="Answer citations" />
        </div>
      )}

      {a.key_changes.length > 0 && (
        <section className="mt-5">
          <h3 className="text-title-sm font-semibold text-fg-1">Key points</h3>
          <ol className="mt-2 space-y-3">
            {a.key_changes.map((k, i) => (
              <li key={i}>
                <p className="text-body text-fg-1">{k.statement}</p>
                {k.citations.length === 0 ? (
                  <p className="text-caption text-fg-3">No citation given for this point.</p>
                ) : (
                  <div className="mt-1">
                    <CitationList ids={k.citations} index={index} activeId={activeId} onSelect={onSelect} label={`Citations for key point ${i + 1}`} />
                  </div>
                )}
              </li>
            ))}
          </ol>
        </section>
      )}

      {a.mappings.length > 0 && (
        <section className="mt-5">
          <h3 className="text-title-sm font-semibold text-fg-1">Mappings stated in the answer</h3>
          <p className="text-caption text-fg-3">
            Each was checked to match a cited official workbook row; the wording of any note is the model’s.
          </p>
          <ul className="mt-2 space-y-3">
            {a.mappings.map((m, i) => (
              <li key={i}>
                <p className="text-body text-fg-1">
                  <span className="font-mono text-id font-medium">{m.focal_id}</span>
                  <span aria-hidden="true"> → </span>
                  <span className="sr-only"> maps to </span>
                  {m.reference_id ? (
                    <span className="font-mono text-id font-medium">{m.reference_id}</span>
                  ) : (
                    <span className="italic">no reference element</span>
                  )}
                </p>
                {m.note && <p className="text-body text-fg-2">{m.note}</p>}
                <div className="mt-1">
                  <CitationList ids={m.citations} index={index} activeId={activeId} onSelect={onSelect} label={`Citations for mapping ${m.focal_id}`} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      <List title="Uncertainties the model noted" items={a.uncertainties} />
      <List title="Questions the model left unresolved" items={a.unresolved_questions} />
    </div>
  );
}

/** The result for one question, whatever its status. Never shows model text that was not validated. */
export function AnswerView({ result, index, activeId, onSelect, headingRef }: Props) {
  const metaId = useId();
  const status = result.status;
  const modelAbstained = status === "abstained" && result.answer !== null;
  const reason = result.abstention_reason ?? result.answer?.abstention_reason ?? null;
  const evidence = result.evidence;
  const noProviderWarning = result.warnings.filter((w) => /no llm provider/i.test(w));
  const otherWarnings = result.warnings.filter((w) => !noProviderWarning.includes(w));

  return (
    <article aria-labelledby={metaId}>
      <p className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">{STATUS_LABEL[status]}</p>
      <h2
        id={metaId}
        ref={headingRef}
        tabIndex={-1}
        className="mt-1 text-title-sm font-semibold text-fg-1 outline-none focus-visible:outline-2"
      >
        {result.question}
      </h2>
      {result.effective_question !== result.question && (
        <p className="mt-0.5 text-caption text-fg-3">
          Sent to the API as: <span className="text-fg-2">{result.effective_question}</span>
        </p>
      )}
      {evidence && (
        <p className="mt-0.5 text-caption text-fg-3">
          {evidence.searched_versions.length > 0
            ? `Evidence searched in ${evidence.searched_versions.map((v) => `CSF ${v}`).join(" and ")}`
            : "No framework version was searched"}
          {evidence.referenced_versions.length > 0 &&
            ` · named in the question: ${evidence.referenced_versions.map((v) => `CSF ${v}`).join(", ")}`}
          .
        </p>
      )}

      <div className="mt-4">
        {status === "answered" && result.answer && (
          <GeneratedAnswer result={result} index={index} activeId={activeId} onSelect={onSelect} />
        )}

        {status === "answered" && !result.answer && (
          <Notice variant="caution" title="The response had no answer text">
            <p>The API reported an answer but sent none. The retrieved evidence is shown beside this result.</p>
          </Notice>
        )}

        {status === "abstained" && (
          <Notice variant="info" title="No answer was given because the evidence was not sufficient">
            {reason ? (
              <p>
                {modelAbstained && (
                  <>
                    <GeneratedTag className="mr-2 align-middle" />
                    The model’s reason:{" "}
                  </>
                )}
                {reason}
              </p>
            ) : (
              <p>The API gave no reason.</p>
            )}
            {!modelAbstained && (
              <p className="mt-2">
                ControlShift stopped before asking a language model, so nothing was generated.
              </p>
            )}
          </Notice>
        )}

        {status === "evidence_only" && (
          <Notice variant="info" title="No answer was generated">
            <p>
              {noProviderWarning.length > 0
                ? "The API has no language model configured, so it returned only the evidence it retrieved."
                : "The API returned only the evidence it retrieved."}{" "}
              Nothing on this page is an AI-written answer. Read the evidence itself, or open the records in
              Control Explorer.
            </p>
          </Notice>
        )}

        {status === "rejected" && (
          <Notice variant="caution" title="The model’s answer was withheld">
            <p>
              A language model was asked, but its output did not pass ControlShift’s automated checks
              {result.attempts > 0 && ` after ${result.attempts} attempt${result.attempts === 1 ? "" : "s"}`}, so no
              answer text is shown. The retrieved evidence is still available. Asking again or rewording the
              question may help.
            </p>
          </Notice>
        )}
      </div>

      {result.system_uncertainties.length > 0 && (
        <div className="mt-4">
          <Notice variant="ambiguous" title="Evidence caveats from ControlShift">
            <ul className="list-disc space-y-1 pl-5">
              {result.system_uncertainties.map((t, i) => (
                <li key={i}>{t}</li>
              ))}
            </ul>
          </Notice>
        </div>
      )}

      {status === "rejected" && <Details summary="Why the answer failed the checks" items={result.rejection} />}
      <Details summary="Pipeline notes" items={otherWarnings} />
      <Verification result={result} />
    </article>
  );
}
