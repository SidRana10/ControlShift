"use client";

import { useEffect, useRef, useState } from "react";
import { Search, X } from "lucide-react";
import { MAX_QUERY_LENGTH } from "@/lib/explorer/url";
import { useExplorer } from "./explorer-provider";

const DEBOUNCE_MS = 150;

/** Search box: debounced into the `q` URL parameter (replace), cleared with Escape or the X button. */
export function SearchField({
  inputRef,
  onArrowDown,
}: {
  inputRef: React.RefObject<HTMLInputElement | null>;
  onArrowDown: () => void;
}) {
  const { ctx, updateContext } = useExplorer();
  const urlQ = ctx.q ?? "";
  const [draft, setDraft] = useState(urlQ);
  const [prevUrlQ, setPrevUrlQ] = useState(urlQ);
  const [sent, setSent] = useState(urlQ);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const update = useRef(updateContext);

  useEffect(() => {
    update.current = updateContext;
  });
  useEffect(() => () => clearTimeout(timer.current), []);

  // Back/forward (or any change not made here) replaces the draft; our own commits do not.
  if (urlQ !== prevUrlQ) {
    setPrevUrlQ(urlQ);
    if (urlQ !== sent) setDraft(urlQ);
  }

  const commit = (value: string) => {
    clearTimeout(timer.current);
    const q = value.trim();
    setSent(q);
    update.current({ q: q || undefined });
  };

  return (
    <div className="relative">
      <Search
        aria-hidden="true"
        strokeWidth={1.5}
        className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-fg-3"
      />
      <input
        ref={inputRef}
        type="search"
        role="searchbox"
        aria-label="Search ID or text"
        placeholder="Search ID or text"
        value={draft}
        maxLength={MAX_QUERY_LENGTH}
        autoComplete="off"
        spellCheck={false}
        onChange={(e) => {
          const v = e.target.value;
          setDraft(v);
          clearTimeout(timer.current);
          timer.current = setTimeout(() => commit(v), DEBOUNCE_MS);
        }}
        onKeyDown={(e) => {
          if (e.key === "Escape") {
            e.preventDefault();
            if (draft) {
              setDraft("");
              commit("");
            } else e.currentTarget.blur();
          } else if (e.key === "Enter") {
            commit(draft);
          } else if (e.key === "ArrowDown") {
            e.preventDefault();
            onArrowDown();
          }
        }}
        className="h-11 w-full rounded-md border border-border-strong bg-surface pr-11 pl-9 text-ui text-fg-1 placeholder:text-fg-4 min-[900px]:h-9 min-[900px]:pr-9"
      />
      {draft ? (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => {
            setDraft("");
            commit("");
            inputRef.current?.focus();
          }}
          className="absolute top-1/2 right-0 flex size-11 -translate-y-1/2 items-center justify-center rounded-md text-fg-3 hover:text-fg-1 min-[900px]:right-1 min-[900px]:size-8"
        >
          <X aria-hidden="true" strokeWidth={1.5} className="size-4" />
        </button>
      ) : (
        <kbd
          aria-hidden="true"
          className="pointer-events-none absolute top-1/2 right-2 hidden -translate-y-1/2 rounded-sm border border-border bg-surface-sunken px-1.5 font-mono text-label text-fg-3 min-[900px]:block"
        >
          /
        </kbd>
      )}
    </div>
  );
}
