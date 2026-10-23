"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { Search, X } from "lucide-react";
import { Notice } from "@/components/shared/notice";
import { DerivedTag } from "@/components/shared/source-tags";
import { StateBlock } from "@/components/shared/state-block";
import { VersionChip } from "@/components/shared/version-chip";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Highlight } from "@/features/explorer/highlight";
import { useDelayedFlag } from "@/features/explorer/use-delayed-flag";
import type { CrosswalkEntry, CrosswalkList, MappingType } from "@/lib/api/types";
import { loadCrosswalk } from "@/lib/compare/cache";
import { MAX_Q, TYPE_LABEL, compareHref, hasFilters, type CompareState } from "@/lib/compare/url";
import { useLoader } from "@/lib/explorer/use-loader";
import { cn } from "@/lib/utils";

const norm = (s: string | null | undefined) => (s ?? "").trim().toLowerCase();

/** Which ends of a row equal the query exactly (either ID spelling), or is the row number. */
export function exactMatch(row: CrosswalkEntry, q: string | undefined) {
  const n = norm(q);
  if (!n) return { any: false, focal: false, reference: false };
  const focal = [row.focal_element_id, row.focal_original_id].some((x) => norm(x) === n);
  const reference = [row.reference_element_id, row.reference_original_id].some((x) => norm(x) === n);
  return { any: focal || reference || String(row.excel_row) === n, focal, reference };
}

/** Selecting a row opens it from the side the user searched for: an exact CSF 1.1 ID opens the 1.1 element. */
export function subjectFor(row: CrosswalkEntry, q: string | undefined): Pick<CompareState, "focal" | "ref"> {
  const m = exactMatch(row, q);
  if (m.reference && !m.focal && row.reference_element_id) return { ref: row.reference_element_id };
  return { focal: row.focal_element_id };
}

function SearchField({ q, onCommit }: { q: string; onCommit: (q: string) => void }) {
  const [draft, setDraft] = useState(q);
  const [prev, setPrev] = useState(q);
  const [sent, setSent] = useState(q);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const commitRef = useRef(onCommit);
  useEffect(() => {
    commitRef.current = onCommit;
  });
  useEffect(() => () => clearTimeout(timer.current), []);
  if (q !== prev) {
    setPrev(q);
    if (q !== sent) setDraft(q);
  }
  const commit = (v: string) => {
    clearTimeout(timer.current);
    setSent(v.trim());
    commitRef.current(v.trim());
  };
  return (
    <div className="relative">
      <Search aria-hidden="true" strokeWidth={1.5} className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-fg-3" />
      <input
        type="search"
        role="searchbox"
        aria-label="Search workbook rows"
        placeholder="Search ID, row number or text"
        value={draft}
        maxLength={MAX_Q}
        autoComplete="off"
        spellCheck={false}
        onChange={(e) => {
          const v = e.target.value;
          setDraft(v);
          clearTimeout(timer.current);
          timer.current = setTimeout(() => commit(v), 200);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit(draft);
          if (e.key === "Escape" && draft) {
            e.preventDefault();
            setDraft("");
            commit("");
          }
        }}
        className="h-11 w-full rounded-md border border-border-strong bg-surface pr-11 pl-9 text-ui text-fg-1 placeholder:text-fg-4 min-[900px]:h-9 min-[900px]:pr-9"
      />
      {draft && (
        <button
          type="button"
          aria-label="Clear search"
          onClick={() => {
            setDraft("");
            commit("");
          }}
          className="absolute top-1/2 right-0 flex size-11 -translate-y-1/2 items-center justify-center rounded-md text-fg-3 hover:text-fg-1 min-[900px]:right-1 min-[900px]:size-8"
        >
          <X aria-hidden="true" strokeWidth={1.5} className="size-4" />
        </button>
      )}
    </div>
  );
}

const TYPE_ORDER: MappingType[] = ["mapped", "new_in_2_0", "unmapped"];

function TypeFilter({ value, counts, onChange }: { value: MappingType | undefined; counts: CrosswalkList["type_counts"] | undefined; onChange: (t: MappingType | undefined) => void }) {
  const total = counts ? counts.mapped + counts.new_in_2_0 + counts.unmapped : undefined;
  const options: [MappingType | undefined, string, number | undefined][] = [
    [undefined, "All rows", total],
    ...TYPE_ORDER.filter((t) => t !== "unmapped" || (counts?.unmapped ?? 0) > 0 || value === "unmapped").map(
      (t): [MappingType, string, number | undefined] => [t, TYPE_LABEL[t], counts?.[t]],
    ),
  ];
  return (
    <fieldset>
      <legend className="flex items-center gap-2 text-caption text-fg-3">
        Ingest label <DerivedTag />
      </legend>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {options.map(([t, label, n]) => (
          <button
            key={label}
            type="button"
            aria-pressed={value === t}
            title={t ? `Exact ingest value: ${t}` : undefined}
            onClick={() => onChange(t)}
            className={cn(
              "inline-flex min-h-11 items-center gap-1.5 rounded-md border px-2.5 text-ui-sm font-medium min-[900px]:min-h-7",
              value === t ? "border-cobalt bg-cobalt-soft text-fg-1" : "border-border-strong bg-surface text-fg-2 hover:bg-surface-hover",
            )}
          >
            {label}{" "}
            {n !== undefined && <span className="font-sans text-caption text-fg-3 tabular-nums">{n}</span>}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

/**
 * Searchable, filterable index of the official workbook rows (GET /crosswalk), always in workbook
 * order except that rows matching the query exactly come first. The count is workbook rows, not
 * controls: one element can have several rows.
 */
export function RelationshipIndex({
  state,
  selectedRow,
  onSearch,
  onType,
  onClear,
  className,
}: {
  state: CompareState;
  selectedRow: number | undefined;
  onSearch: (q: string) => void;
  onType: (t: MappingType | undefined) => void;
  onClear: () => void;
  className?: string;
}) {
  const { q, type } = state;
  const list = useLoader(`index:${q ?? ""}:${type ?? ""}`, () => loadCrosswalk({ q, type }));
  const data = list.data;
  const stale = list.status === "loading";
  const showSkeleton = useDelayedFlag(stale && !data);

  const rows = useMemo(() => {
    const entries = data?.entries ?? [];
    if (!q) return entries;
    const exact = entries.filter((r) => exactMatch(r, q).any);
    return [...exact, ...entries.filter((r) => !exactMatch(r, q).any)];
  }, [data, q]);

  const meta = data
    ? q || type
      ? `${data.total} workbook ${data.total === 1 ? "row matches" : "rows match"}${q ? ` “${q}”` : ""}${type ? ` · ${TYPE_LABEL[type]}` : ""}`
      : `${data.total} workbook rows`
    : "Loading workbook rows…";

  return (
    <section
      aria-label="Relationship index"
      className={cn("min-h-0 w-full flex-col border-border bg-surface min-[900px]:w-[320px] min-[900px]:shrink-0 min-[900px]:border-r min-[1320px]:w-[340px]", className)}
    >
      <div className="space-y-3 border-b border-border px-4 py-3">
        <SearchField q={q ?? ""} onCommit={onSearch} />
        <TypeFilter value={type} counts={data?.type_counts} onChange={onType} />
        <div className="flex min-h-6 items-center justify-between gap-2">
          <p role="status" aria-live="polite" className="text-caption text-fg-3">
            {meta}
          </p>
          {hasFilters(state) && (
            <Button variant="ghost" size="sm" className="h-11 min-[900px]:h-7" onClick={onClear}>
              Clear
            </Button>
          )}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto" aria-busy={stale}>
        {list.status === "error" && !data ? (
          <div className="p-4">
            <Notice
              variant="error"
              title={list.error?.kind === "unreachable" ? "ControlShift API is unreachable" : "Workbook rows could not be loaded"}
              actions={
                <Button variant="outline" size="sm" className="h-11 min-[900px]:h-7" onClick={list.reload}>
                  Retry
                </Button>
              }
            >
              {list.error?.kind === "unreachable"
                ? "Start the FastAPI service (controlshift-serve) and retry."
                : "The API did not return a usable response."}
            </Notice>
          </div>
        ) : showSkeleton ? (
          <div aria-hidden="true" className="space-y-3 p-4">
            {Array.from({ length: 8 }, (_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : data && rows.length === 0 ? (
          <StateBlock
            title="No workbook rows match"
            actions={
              <Button variant="outline" className="min-h-11 min-[900px]:min-h-8" onClick={onClear}>
                Clear filters
              </Button>
            }
          >
            Search covers IDs (either spelling), row numbers, official descriptions and workbook comments.
          </StateBlock>
        ) : (
          <ul aria-label="Workbook rows" className={cn("divide-y divide-border", stale && "opacity-60")}>
            {rows.map((r) => {
              const selected = r.excel_row === selectedRow;
              const exact = exactMatch(r, q).any;
              return (
                <li key={r.excel_row}>
                  <Link
                    href={compareHref({ ...subjectFor(r, q), row: r.excel_row, q, type })}
                    aria-current={selected ? "true" : undefined}
                    aria-label={`Row ${r.excel_row}: ${r.focal_original_id} ${r.reference_element_id ? `maps to ${r.reference_original_id ?? r.reference_element_id}` : "has no reference element"}`}
                    className={cn(
                      "block min-h-[52px] px-4 py-2 focus-visible:outline-offset-[-2px]",
                      selected ? "bg-cobalt-soft shadow-[inset_2px_0_0_var(--cs-cobalt)]" : "hover:bg-surface-hover",
                    )}
                  >
                    <span aria-hidden="true" className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                      <span className="font-mono text-mono-sm text-fg-3">ROW {r.excel_row}</span>
                      <VersionChip version="2.0" />
                      <span className="font-mono text-id font-medium text-fg-1">
                        <Highlight text={r.focal_original_id} q={q} />
                      </span>
                      <span className="text-fg-3">→</span>
                      {r.reference_element_id ? (
                        <>
                          <VersionChip version="1.1" />
                          <span className="font-mono text-id font-medium text-fg-1">
                            <Highlight text={r.reference_original_id ?? r.reference_element_id} q={q} />
                          </span>
                        </>
                      ) : (
                        <span className="text-ui-sm text-fg-2 italic">No reference element</span>
                      )}
                      {exact && (
                        <span className="rounded-sm bg-surface-sunken px-1.5 text-label font-medium text-fg-2">Exact match</span>
                      )}
                    </span>
                    {(r.focal_description || r.comments) && (
                      <span aria-hidden="true" className="mt-0.5 block truncate text-ui-sm text-fg-2">
                        <Highlight text={r.focal_description ?? `“${r.comments}”`} q={q} />
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
