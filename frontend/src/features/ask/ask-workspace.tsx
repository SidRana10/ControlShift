"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Notice } from "@/components/shared/notice";
import { DerivedTag, GeneratedTag, SourceTag } from "@/components/shared/source-tags";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { describeAskError } from "@/lib/ask/errors";
import { allAnswerCitations, evidenceDomId, indexEvidence } from "@/lib/ask/citations";
import { useMediaQuery } from "@/lib/use-media-query";
import { cn } from "@/lib/utils";
import { useDelayedFlag } from "@/features/explorer/use-delayed-flag";
import { AnswerView } from "./answer-view";
import { EvidenceInspector } from "./evidence-inspector";
import { EXAMPLE_QUESTIONS } from "./examples";
import { QuestionForm, type Scope } from "./question-form";
import { useAsk } from "./use-ask";

/** Two columns (answer | evidence) need roughly 1130px of workspace, i.e. a 1360px viewport. */
const TWO_PANE = "(min-width: 1360px)";

function Legend() {
  return (
    <section aria-labelledby="legend-h" className="mt-8 border-t border-border pt-6">
      <h2 id="legend-h" className="text-title-sm font-semibold text-fg-1">
        How to read a result
      </h2>
      <dl className="mt-3 space-y-3 text-body text-fg-2">
        <div className="flex gap-3">
          <dt className="w-24 shrink-0"><SourceTag /></dt>
          <dd>Verbatim text from the NIST CSF 1.1 or 2.0 documents, or a row of the NIST transition workbook.</dd>
        </div>
        <div className="flex gap-3">
          <dt className="w-24 shrink-0"><DerivedTag /></dt>
          <dd>A label or note computed by ControlShift. It is an interpretation, not a NIST field.</dd>
        </div>
        <div className="flex gap-3">
          <dt className="w-24 shrink-0"><GeneratedTag /></dt>
          <dd>
            Written by a language model from the retrieved evidence. Citations are checked for existence and
            provenance only; whether the wording is faithful to the cited text is not verified.
          </dd>
        </div>
      </dl>
      <p className="mt-4 text-caption text-fg-3">
        Each question is answered on its own. ControlShift keeps no conversation history.
      </p>
    </section>
  );
}

function Loading({ question }: { question: string }) {
  const skeleton = useDelayedFlag(true);
  const slow = useDelayedFlag(true, 10_000);
  return (
    <div className="mt-8">
      <Notice variant="info" title="Searching the NIST evidence and writing an answer…">
        <p>
          “{question}” {slow && "Still working. Generating an answer can take up to about 90 seconds."}
        </p>
      </Notice>
      {skeleton && (
        <div aria-hidden="true" className="mt-4 space-y-2">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
      )}
    </div>
  );
}

export function AskWorkspace() {
  const { state, submit, reset } = useAsk();
  const [question, setQuestion] = useState("");
  const [scope, setScope] = useState<Scope>("any");
  const [selection, setSelection] = useState<{ result: unknown; id: string } | null>(null);
  const [nonce, setNonce] = useState(0);
  const origin = useRef<HTMLElement | null>(null);
  const resultHeading = useRef<HTMLHeadingElement | null>(null);
  const textarea = useRef<HTMLTextAreaElement | null>(null);
  const twoPane = useMediaQuery(TWO_PANE);
  const evidenceHeading = useId();

  const result = state.status === "success" ? state.result : null;
  const index = useMemo(() => indexEvidence(result?.evidence ?? null), [result]);
  const citedIds = useMemo(() => new Set(result?.answer ? allAnswerCitations(result.answer) : []), [result]);

  // A selection belongs to the result it was made in, so a new result starts with none.
  const activeId = selection && selection.result === result ? selection.id : null;

  // A new result takes focus so assistive technology announces it.
  useEffect(() => {
    if (result) resultHeading.current?.focus();
  }, [result]);

  // Selecting a citation moves focus to its evidence entry and brings it into view.
  useEffect(() => {
    if (!activeId) return;
    const el = document.getElementById(evidenceDomId(activeId));
    el?.focus({ preventScroll: true });
    el?.scrollIntoView({ block: twoPane ? "nearest" : "start" });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only a new selection (nonce) should move focus
  }, [nonce]);

  const ask = (q = question) => {
    const trimmed = q.trim();
    if (trimmed) submit(trimmed, scope === "any" ? undefined : scope);
  };
  const clear = () => {
    reset();
    setQuestion("");
    setSelection(null);
    textarea.current?.focus();
  };

  const loading = state.status === "loading";
  const showEvidence = result !== null;

  return (
    <div className={cn("min-h-full", showEvidence && "min-[1360px]:grid min-[1360px]:grid-cols-[minmax(0,1fr)_440px]")}>
      <div className="px-4 py-4 min-[900px]:px-10 min-[900px]:py-8">
        <div className="mx-auto w-full max-w-[720px]">
          <p className="text-body text-fg-2">
            Ask about NIST CSF 1.1, CSF 2.0 and the official transition workbook. Answers are written from
            retrieved NIST text, and every answer lists the evidence behind it.
          </p>
          <div className="mt-4 min-[900px]:mt-6">
            <QuestionForm
              question={question}
              onQuestionChange={setQuestion}
              scope={scope}
              onScopeChange={setScope}
              loading={loading}
              hasOutput={state.status !== "idle"}
              onSubmit={() => ask()}
              onClear={clear}
              onCancel={() => {
                reset();
                textarea.current?.focus();
              }}
              textareaRef={textarea}
            />
          </div>

          {state.status === "idle" && (
            <>
              <section aria-labelledby="examples-h" className="mt-8">
                <h2 id="examples-h" className="text-title-sm font-semibold text-fg-1">
                  Try an example
                </h2>
                <ul className="mt-2 divide-y divide-border rounded-lg border border-border bg-surface">
                  {EXAMPLE_QUESTIONS.map((q) => (
                    <li key={q}>
                      <button
                        type="button"
                        onClick={() => {
                          setQuestion(q);
                          textarea.current?.focus();
                        }}
                        className="flex min-h-11 w-full items-center px-3 text-left text-ui text-fg-1 hover:bg-surface-hover active:bg-surface-pressed min-[900px]:min-h-9"
                      >
                        {q}
                      </button>
                    </li>
                  ))}
                </ul>
                <p className="mt-1 text-caption text-fg-3">Selecting an example fills in the question; it is not sent until you press Ask.</p>
              </section>
              <Legend />
            </>
          )}

          {loading && <Loading question={state.question} />}

          {state.status === "error" && (
            <ErrorBlock error={state.error} onRetry={() => ask(state.question)} />
          )}

          {result && (
            <div className="mt-8 border-t border-border pt-6">
              <AnswerView
                result={result}
                index={index}
                activeId={activeId}
                headingRef={resultHeading}
                onSelect={(id, el) => {
                  origin.current = el;
                  setSelection({ result, id });
                  setNonce((n) => n + 1);
                }}
              />
            </div>
          )}
        </div>
      </div>

      {showEvidence && (
        <aside
          aria-labelledby={evidenceHeading}
          className="border-t border-border bg-surface min-[1360px]:sticky min-[1360px]:top-0 min-[1360px]:h-[calc(100dvh-56px)] min-[1360px]:self-start min-[1360px]:overflow-y-auto min-[1360px]:border-t-0 min-[1360px]:border-l"
        >
          <div className="mx-auto w-full max-w-[720px] min-[1360px]:max-w-none">
            <EvidenceInspector
              headingId={evidenceHeading}
              evidence={result.evidence}
              citedIds={citedIds}
              activeId={activeId}
              onBackToAnswer={() => {
                origin.current?.focus();
                origin.current?.scrollIntoView({ block: "nearest" });
              }}
            />
          </div>
        </aside>
      )}
    </div>
  );
}

function ErrorBlock({ error, onRetry }: { error: import("@/lib/api/client").ApiError; onRetry: () => void }) {
  const copy = describeAskError(error);
  return (
    <div className="mt-8">
      <Notice
        variant="error"
        title={copy.title}
        actions={
          <Button variant="outline" onClick={onRetry} className="min-h-11 min-[900px]:min-h-8">
            Try again
          </Button>
        }
      >
        <p>{copy.body}</p>
        {copy.code && <p className="mt-1 font-mono text-mono-sm text-fg-3">{copy.code}</p>}
      </Notice>
    </div>
  );
}
