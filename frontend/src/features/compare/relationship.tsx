"use client";

import Link from "next/link";
import { useId } from "react";
import { CircleDashed } from "lucide-react";
import { DerivedTag, SourceTag } from "@/components/shared/source-tags";
import { VersionChip } from "@/components/shared/version-chip";
import { Connector } from "@/features/explorer/crosswalk-entry";
import { DerivedSummary } from "@/features/explorer/crosswalk-section";
import type { Crosswalk, CrosswalkEntry } from "@/lib/api/types";
import { isLongText } from "@/lib/explorer/crosswalk";
import { compareHref, type CompareState } from "@/lib/compare/url";
import { cn } from "@/lib/utils";

/** The workbook row that supplies the relationship between the two cards, in official direction. */
export function RowConnector({ entry }: { entry: CrosswalkEntry }) {
  return (
    <div
      className="flex items-center justify-center gap-2 py-1 min-[1480px]:w-28 min-[1480px]:flex-col min-[1480px]:py-0"
      role="img"
      aria-label={`Workbook row ${entry.excel_row}: official direction CSF 2.0 to CSF 1.1${
        entry.reference_element_id ? "" : ", no reference element"
      }`}
    >
      <span className="font-mono text-mono-sm text-fg-2">ROW {entry.excel_row}</span>
      <span className="flex w-24 min-[1480px]:w-full">
        <Connector mapped={Boolean(entry.reference_element_id)} />
      </span>
      <span className="text-caption text-fg-3">2.0 → 1.1</span>
    </div>
  );
}

/** Shown in place of the CSF 1.1 card when the row has no reference element: not a control card. */
export function NoReferencePanel({ entry }: { entry: CrosswalkEntry }) {
  return (
    <div className="min-w-0 rounded-lg border border-dashed border-border-strong bg-surface-sunken p-4">
      <p className="flex items-center gap-2 text-title-sm font-semibold text-fg-1">
        <CircleDashed aria-hidden="true" strokeWidth={1.5} className="size-4 text-fg-3" />
        No reference element
      </p>
      <p className="mt-1 text-body text-fg-2">
        Workbook row {entry.excel_row} lists a CSF 2.0 element with nothing in the CSF 1.1 column. That
        is all the row records; it does not say the element has no conceptual counterpart.
      </p>
      {entry.comments && (
        <div className="mt-3">
          <p className="flex items-center gap-2 text-caption text-fg-3">
            <SourceTag /> Workbook comment
          </p>
          <p className="font-serif text-source text-fg-1 italic">“{entry.comments}”</p>
        </div>
      )}
    </div>
  );
}

/** Official fields of the selected row, then (separately) what ControlShift derived from it. */
export function RelationshipDetails({
  entry,
  summary,
  actions,
}: {
  entry: CrosswalkEntry;
  summary: Crosswalk["summary"];
  actions: React.ReactNode;
}) {
  return (
    <section aria-label={`Workbook row ${entry.excel_row} details`} className="grid gap-4 min-[900px]:grid-cols-2">
      <div>
        <h4 className="flex items-center gap-2 text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
          <SourceTag /> Official workbook row
        </h4>
        <dl className="mt-2 text-ui-sm">
          {[
            ["Row", `${entry.excel_row}`],
            ["Sheet", entry.sheet],
            ["File", entry.source_file],
            ["Direction", "CSF 2.0 (focal) → CSF 1.1 (reference)"],
          ].map(([k, v]) => (
            <div key={k} className="grid grid-cols-[5rem_1fr] gap-x-3 py-0.5">
              <dt className="text-caption text-fg-3">{k}</dt>
              <dd className="min-w-0 break-words text-fg-1">{v}</dd>
            </div>
          ))}
          <div className="grid grid-cols-[5rem_1fr] gap-x-3 py-0.5">
            <dt className="text-caption text-fg-3">Comment</dt>
            <dd className="min-w-0">
              {entry.comments ? (
                <span className="font-serif text-source text-fg-1 italic">“{entry.comments}”</span>
              ) : (
                <span className="text-fg-3">None recorded</span>
              )}
            </dd>
          </div>
        </dl>
      </div>
      <div>
        <h4 className="flex items-center gap-2 text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
          <DerivedTag /> Derived by ControlShift
        </h4>
        <p className="mt-2 flex flex-wrap items-center gap-2 text-ui-sm text-fg-2">
          Ingest label: <span className="font-mono text-id">{entry.mapping_type}</span>
        </p>
        <div className="mt-2">
          <DerivedSummary summary={summary} />
        </div>
        <p className="mt-2 text-caption text-fg-3">
          These labels are ControlShift&apos;s reading of the workbook. They are not NIST fields and not
          a measure of how closely two elements match.
        </p>
        <div className="mt-1">{actions}</div>
      </div>
    </section>
  );
}

/** One workbook row in the list of all rows for the inspected element. Rows are never merged. */
export function RowItem({
  entry,
  selected,
  subjectSide,
  state,
  onToggleText,
  expanded,
}: {
  entry: CrosswalkEntry;
  selected: boolean;
  subjectSide: "focal" | "reference";
  state: CompareState;
  expanded: boolean;
  onToggleText: () => void;
}) {
  const textId = useId();
  const counterpartIsRef = subjectSide === "focal";
  const description = counterpartIsRef ? entry.reference_description : entry.focal_description;
  const long = isLongText(description);
  const href = compareHref({ ...state, row: entry.excel_row });
  return (
    <li
      id={`compare-row-${entry.excel_row}`}
      data-excel-row={entry.excel_row}
      tabIndex={-1}
      aria-current={selected ? "true" : undefined}
      className={cn(
        "relative px-4 py-3 outline-none focus-visible:outline-2 focus-visible:-outline-offset-2",
        selected && "bg-cobalt-soft shadow-[inset_2px_0_0_var(--cs-cobalt)]",
      )}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="font-mono text-mono-sm text-fg-3" title={`Workbook row ${entry.excel_row}, sheet ${entry.sheet}, ${entry.source_file}`}>
          ROW {entry.excel_row}
        </span>
        <span className="inline-flex flex-wrap items-center gap-1.5 text-ui-sm">
          <VersionChip version="2.0" />
          <span className="font-mono text-id font-medium">{entry.focal_original_id}</span>
          <span aria-hidden="true" className="text-fg-3">→</span>
          <span className="sr-only">maps to</span>
          {entry.reference_element_id ? (
            <>
              <VersionChip version="1.1" />
              <span className="font-mono text-id font-medium">{entry.reference_original_id ?? entry.reference_element_id}</span>
            </>
          ) : (
            <span className="text-fg-2 italic">No reference element</span>
          )}
        </span>
        <span className="ml-auto">
          {selected ? (
            <span className="text-ui-sm font-medium text-fg-1">Selected</span>
          ) : (
            <Link
              href={href}
              aria-label={`Compare workbook row ${entry.excel_row}`}
              className="inline-flex min-h-11 items-center text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
            >
              Compare this row
            </Link>
          )}
        </span>
      </div>
      {description && (
        <div className="mt-1">
          <p id={textId} className={cn("font-serif text-source text-fg-1", !expanded && "line-clamp-2")}>
            {description}
          </p>
          {long && (
            <button
              type="button"
              aria-expanded={expanded}
              aria-controls={textId}
              onClick={onToggleText}
              className="inline-flex min-h-11 items-center text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
            >
              {expanded ? "Show less" : "Show full text"}
            </button>
          )}
        </div>
      )}
      {entry.comments && (
        <p className="mt-1 text-caption text-fg-3">
          Workbook comment: <span className="font-serif text-ui-sm text-fg-1 italic">“{entry.comments}”</span>
        </p>
      )}
      <p className="mt-1 flex flex-wrap items-center gap-2 text-caption text-fg-2">
        Ingest label: <span className="font-mono text-id">{entry.mapping_type}</span>
        <DerivedTag />
      </p>
    </li>
  );
}
