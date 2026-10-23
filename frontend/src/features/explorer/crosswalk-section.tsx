"use client";

import { useState } from "react";
import { Notice } from "@/components/shared/notice";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import type { Crosswalk, ElementDetail } from "@/lib/api/types";
import { describeEntry, isLongText, statusLabel } from "@/lib/explorer/crosswalk";
import { recordHref } from "@/lib/explorer/url";
import { CrosswalkEntryRow } from "./crosswalk-entry";
import { useExplorer } from "./explorer-provider";

function jumpTo(row: number) {
  const el = document.getElementById(`crosswalk-row-${row}`);
  el?.scrollIntoView({ block: "center" });
  el?.focus({ preventScroll: true });
}

/** Derived summary chip: dashed, always labelled Derived; the API's own note opens on demand. */
export function DerivedSummary({ summary }: { summary: Crosswalk["summary"] }) {
  return (
    <Popover>
      <PopoverTrigger
        aria-label={`Derived classification: ${statusLabel(summary.status)}. Show explanation`}
        className="inline-flex min-h-11 items-center rounded-full border border-dashed border-derived-border px-2.5 text-caption font-medium text-derived hover:bg-surface-hover min-[900px]:min-h-6"
      >
        Derived: {statusLabel(summary.status)}
      </PopoverTrigger>
      <PopoverContent align="start" className="w-80">
        <p className="text-ui-sm font-semibold text-fg-1">ControlShift-derived classification</p>
        <p className="text-ui-sm text-fg-2">{summary.note}</p>
        <p className="text-caption text-fg-3">
          This label is ControlShift&apos;s reading of the workbook rows. It is not a field of the
          NIST workbook, and the rows below are the official records.
        </p>
      </PopoverContent>
    </Popover>
  );
}

/** Official crosswalk rows for the open record (docs/frontend-design-spec.md section 9.4 and 10). */
export function CrosswalkSection({ detail }: { detail: ElementDetail }) {
  const { ctx, followCrosswalk } = useExplorer();
  const { crosswalk } = detail;
  const { entries, summary, lookup } = crosswalk;
  const reverse = lookup === "reverse";
  const [open, setOpen] = useState<ReadonlySet<number>>(new Set());
  const expandable = entries.filter((e) => isLongText(reverse ? e.focal_description : e.reference_description));
  const allOpen = expandable.length > 0 && expandable.every((e) => open.has(e.excel_row));
  const first = entries[0];

  const current = {
    version: detail.version,
    elementId: detail.element_id,
    printedId: detail.original_id,
  };
  const toggle = (row: number) =>
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(row)) next.delete(row);
      else next.add(row);
      return next;
    });

  return (
    <section aria-labelledby="crosswalk-heading" id="record-crosswalk" className="mt-10">
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-1">
        <div className="min-w-0">
          <h3 id="crosswalk-heading" className="text-title-sm font-semibold text-fg-1">
            {reverse ? "Referenced by CSF 2.0 · official crosswalk" : "Official crosswalk · CSF 2.0 → CSF 1.1"}
          </h3>
          <p className="mt-0.5 text-caption text-fg-3" title={crosswalk.direction}>
            {first
              ? `${entries.length} workbook ${entries.length === 1 ? "row" : "rows"} · ${first.source_file} · sheet ${first.sheet}`
              : "0 workbook rows"}
          </p>
        </div>
        {expandable.length > 1 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-11 min-[900px]:h-7"
            onClick={() => setOpen(allOpen ? new Set() : new Set(expandable.map((e) => e.excel_row)))}
          >
            {allOpen ? "Collapse all" : "Expand all"}
          </Button>
        )}
      </div>
      <div className="mt-2">
        <DerivedSummary summary={summary} />
      </div>

      {summary.status === "mapped_and_new_in_2_0" && (
        <Notice
          variant="ambiguous"
          className="mt-4"
          title="Multiple crosswalk entries require interpretation"
          actions={entries.map((e) => (
            <Button
              key={e.excel_row}
              variant="outline"
              size="sm"
              className="h-11 min-[900px]:h-7"
              onClick={() => jumpTo(e.excel_row)}
            >
              Jump to row {e.excel_row}
            </Button>
          ))}
        >
          <p>
            The official transition workbook contains {entries.length} entries for{" "}
            {detail.original_id}. ControlShift preserves all of them and does not choose between
            interpretations.
          </p>
          <ul className="mt-2 list-disc space-y-0.5 pl-5">
            {entries.map((e) => (
              <li key={e.excel_row}>{describeEntry(e)}</li>
            ))}
          </ul>
        </Notice>
      )}

      {entries.length === 0 ? (
        <Notice variant="no-reference" className="mt-4" title="No crosswalk reference">
          No row in the official NIST transition workbook {reverse ? "references" : "lists"} this CSF{" "}
          {detail.version} element. The workbook does not state whether the element was retained,
          merged or dropped.
        </Notice>
      ) : (
        <ol
          aria-label="Official crosswalk rows"
          className="mt-4 divide-y divide-border rounded-lg border border-border bg-surface"
        >
          {entries.map((entry) => (
            <CrosswalkEntryRow
              key={entry.excel_row}
              entry={entry}
              lookup={lookup}
              ctx={ctx}
              expanded={open.has(entry.excel_row)}
              onToggleExpanded={() => toggle(entry.excel_row)}
              onFollow={(target) =>
                followCrosswalk({
                  fromHref: recordHref(current.version, current.elementId, ctx),
                  fromLabel: `${current.printedId} (CSF ${current.version})`,
                  row: entry.excel_row,
                  toKey: `${target.version}/${target.elementId}`,
                })
              }
            />
          ))}
        </ol>
      )}
    </section>
  );
}
