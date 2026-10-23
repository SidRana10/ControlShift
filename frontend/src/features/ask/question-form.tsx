"use client";

import { useId } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { FrameworkVersion } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export const MAX_QUESTION_CHARS = 2000;
export type Scope = "any" | FrameworkVersion;

const SCOPES: { value: Scope; label: string }[] = [
  { value: "any", label: "Any version" },
  { value: "2.0", label: "CSF 2.0" },
  { value: "1.1", label: "CSF 1.1" },
];

export function QuestionForm({
  question,
  onQuestionChange,
  scope,
  onScopeChange,
  loading,
  hasOutput,
  onSubmit,
  onClear,
  onCancel,
  textareaRef,
}: {
  question: string;
  onQuestionChange: (q: string) => void;
  scope: Scope;
  onScopeChange: (s: Scope) => void;
  loading: boolean;
  hasOutput: boolean;
  onSubmit: () => void;
  onClear: () => void;
  onCancel: () => void;
  textareaRef: React.RefObject<HTMLTextAreaElement | null>;
}) {
  const fieldId = useId();
  const hintId = useId();
  const trimmed = question.trim();
  const canSubmit = trimmed.length > 0 && !loading;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (canSubmit) onSubmit();
      }}
      aria-busy={loading}
    >
      <label htmlFor={fieldId} className="text-title-sm font-semibold text-fg-1">
        Your question
      </label>
      <textarea
        id={fieldId}
        ref={textareaRef}
        value={question}
        readOnly={loading}
        maxLength={MAX_QUESTION_CHARS}
        rows={3}
        aria-describedby={hintId}
        placeholder="For example: What does GV.SC-03 require?"
        onChange={(e) => onQuestionChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            e.currentTarget.form?.requestSubmit();
          }
        }}
        className="mt-2 block w-full resize-y rounded-md border border-border-strong bg-surface px-3 py-2 text-ui text-fg-1 placeholder:text-fg-4 read-only:bg-surface-sunken"
      />
      <p id={hintId} className="mt-1 text-caption text-fg-3">
        Enter to ask, Shift+Enter for a new line.
        {question.length > 1800 && (
          <span className="ml-2 tabular-nums">
            {question.length.toLocaleString()} / {MAX_QUESTION_CHARS.toLocaleString()}
          </span>
        )}
      </p>

      <fieldset className="mt-4" disabled={loading}>
        <legend className="text-ui-sm font-medium text-fg-1">Version scope</legend>
        <div className="mt-1 inline-flex rounded-md border border-border-strong bg-surface p-0.5">
          {SCOPES.map((s) => (
            <label
              key={s.value}
              className={cn(
                "flex min-h-11 cursor-pointer items-center rounded-sm px-3 text-ui-sm font-medium text-fg-2 has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-cobalt min-[900px]:min-h-7",
                scope === s.value ? "bg-surface-sunken text-fg-1" : "hover:bg-surface-hover",
              )}
            >
              <input
                type="radio"
                name="scope"
                value={s.value}
                checked={scope === s.value}
                onChange={() => onScopeChange(s.value)}
                className="sr-only"
              />
              {s.label}
            </label>
          ))}
        </div>
        <p className="mt-1 text-caption text-fg-3">
          {scope === "any"
            ? "ControlShift decides which versions to search from the question."
            : `Asks the API to scope the question to CSF ${scope} (it prefixes “In CSF ${scope}:”). The evidence panel shows which versions were actually searched.`}
        </p>
      </fieldset>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <Button type="submit" disabled={!canSubmit} className="min-h-11 px-5 min-[900px]:min-h-8">
          {loading ? (
            <>
              <Loader2 aria-hidden="true" className="motion-safe:animate-spin" strokeWidth={1.5} />
              Asking…
            </>
          ) : (
            "Ask"
          )}
        </Button>
        {loading ? (
          <Button type="button" variant="outline" onClick={onCancel} className="min-h-11 min-[900px]:min-h-8">
            Cancel
          </Button>
        ) : (
          (hasOutput || question.length > 0) && (
            <Button type="button" variant="ghost" onClick={onClear} className="min-h-11 min-[900px]:min-h-8">
              Clear
            </Button>
          )
        )}
      </div>
    </form>
  );
}
