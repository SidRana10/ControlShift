"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ChevronLeft } from "lucide-react";
import { Notice } from "@/components/shared/notice";
import { StateBlock } from "@/components/shared/state-block";
import { VersionChip } from "@/components/shared/version-chip";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { DerivedSummary } from "@/features/explorer/crosswalk-section";
import { useDelayedFlag } from "@/features/explorer/use-delayed-flag";
import type { ElementDetail, FrameworkVersion } from "@/lib/api/types";
import { loadCrosswalk } from "@/lib/compare/cache";
import { TYPE_LABEL, compareHref, type CompareState } from "@/lib/compare/url";
import { loadDetail, loadElements } from "@/lib/explorer/catalog-cache";
import { describeEntry } from "@/lib/explorer/crosswalk";
import { listHref } from "@/lib/explorer/url";
import { useLoader } from "@/lib/explorer/use-loader";
import { NoReferencePanel, RelationshipDetails, RowConnector, RowItem } from "./relationship";
import { RecordCard } from "./record-card";

const EXAMPLES: { label: string; note: string; href: string }[] = [
  { label: "GV.SC-03", note: "CSF 2.0 · two workbook rows, 25 and 26", href: compareHref({ focal: "GV.SC-03" }) },
  { label: "ID.IM-03", note: "CSF 2.0 · seven workbook rows", href: compareHref({ focal: "ID.IM-03" }) },
  { label: "ID.SC-02", note: "CSF 1.1 · referenced by several rows (reverse lookup)", href: compareHref({ ref: "ID.SC-02" }) },
  { label: "RC.CO-02", note: "CSF 1.1 · no workbook row references it", href: compareHref({ ref: "RC.CO-02" }) },
];

/** Shown when nothing is selected (desktop). Counts come from the live API and count workbook rows. */
export function Orientation() {
  const all = useLoader("orientation", () => loadCrosswalk({}));
  const d = all.data;
  const first = d?.entries[0];
  return (
    <div className="max-w-[720px] px-4 py-8 min-[900px]:px-10">
      <div className="flex items-center gap-2">
        <VersionChip version="2.0" />
        <span aria-hidden="true" className="text-fg-3">→</span>
        <VersionChip version="1.1" />
        <h2 className="ml-1 text-name-lg font-semibold text-fg-1">Official CSF 2.0 → CSF 1.1 crosswalk</h2>
      </div>
      {d ? (
        <p className="mt-2 text-body text-fg-2">
          {d.total} workbook rows
          {first && (
            <>
              {" "}
              from <span className="font-mono text-id">{first.source_file}</span>, sheet {first.sheet}
            </>
          )}
          . A row is not a unique control: one element can have several rows. Ingest labels (a ControlShift
          classification, not a workbook column):{" "}
          {(["mapped", "new_in_2_0", "unmapped"] as const).filter((t) => d.type_counts[t] > 0).map((t, i) => (
            <span key={t}>
              {i > 0 && ", "}
              {TYPE_LABEL[t]} <span className="font-mono text-id text-fg-3">({t})</span> {d.type_counts[t]}
            </span>
          ))}
          .
        </p>
      ) : all.status === "error" ? (
        <p className="mt-2 text-body text-fg-2">
          Workbook details could not be loaded.{" "}
          <Button variant="link" className="h-auto p-0 text-body" onClick={all.reload}>
            Retry
          </Button>
        </p>
      ) : null}
      <p className="mt-3 text-body text-fg-2">
        Search or filter the rows on the left and select one to see the two official records side by
        side. The direction is fixed by the workbook: CSF 2.0 is the focal side and CSF 1.1 is the
        referenced side. Nothing here is generated, and matching IDs in the two versions are never
        treated as equivalent.
      </p>
      <h3 className="mt-6 text-label font-medium tracking-[0.04em] text-fg-3 uppercase">Examples</h3>
      <ul className="mt-2 divide-y divide-border rounded-lg border border-border">
        {EXAMPLES.map((e) => (
          <li key={e.href}>
            <Link href={e.href} className="flex min-h-11 flex-wrap items-baseline gap-x-3 px-3 py-2 hover:bg-surface-hover">
              <span className="font-mono text-id font-medium text-cobalt">{e.label}</span>
              <span className="text-ui-sm text-fg-2">{e.note}</span>
            </Link>
          </li>
        ))}
        <li>
          <Link href={compareHref({ type: "new_in_2_0" })} className="flex min-h-11 flex-wrap items-baseline gap-x-3 px-3 py-2 hover:bg-surface-hover">
            <span className="text-ui-sm font-medium text-cobalt">Rows with no reference element</span>
            <span className="text-ui-sm text-fg-2">filter by the “New in 2.0” ingest label</span>
          </Link>
        </li>
      </ul>
    </div>
  );
}

function Skel() {
  return (
    <div aria-hidden="true" className="space-y-3">
      <Skeleton className="h-4 w-40" />
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-40 w-full" />
    </div>
  );
}

/** The comparison for one inspected element and one selected workbook row. */
export function Inspector({ state, backHref }: { state: CompareState; backHref: string }) {
  const heading = useRef<HTMLHeadingElement>(null);
  const [open, setOpen] = useState<ReadonlySet<number>>(new Set());

  // A bare ?row=N resolves to its focal element from the full workbook list (loaded once, cached).
  const bare = !state.focal && !state.ref && state.row !== undefined;
  const all = useLoader(bare ? "rows:all" : null, () => loadCrosswalk({}));
  const rowHit = bare ? all.data?.entries.find((r) => r.excel_row === state.row) : undefined;
  const subject: { version: FrameworkVersion; id: string } | null = state.focal
    ? { version: "2.0", id: state.focal }
    : state.ref
      ? { version: "1.1", id: state.ref }
      : rowHit
        ? { version: "2.0", id: rowHit.focal_element_id }
        : null;

  const detail = useLoader(subject ? `detail:${subject.version}:${subject.id}` : null, () =>
    loadDetail(subject!.version, subject!.id),
  );
  const subjectDetail: ElementDetail | undefined =
    detail.status === "success" && subject && detail.data?.version === subject.version ? detail.data : undefined;

  const entries = subjectDetail?.crosswalk.entries ?? [];
  const selected = entries.find((e) => e.excel_row === state.row) ?? entries[0];
  const forward = subject?.version === "2.0";
  const otherVersion: FrameworkVersion = forward ? "1.1" : "2.0";
  const otherId = selected ? (forward ? selected.reference_element_id : selected.focal_element_id) : null;
  const other = useLoader(otherId ? `detail:${otherVersion}:${otherId}` : null, () => loadDetail(otherVersion, otherId!));
  const otherDetail = other.status === "success" && otherId ? other.data : undefined;
  const el20 = useLoader("elements:2.0", () => loadElements("2.0"));
  const el11 = useLoader("elements:1.1", () => loadElements("1.1"));

  const showSkeleton = useDelayedFlag(detail.status === "loading" || (bare && all.status === "loading"));
  const subjectKey = subjectDetail?.element_id;
  useEffect(() => {
    if (subjectKey && window.matchMedia("(max-width: 899px)").matches) heading.current?.focus({ preventScroll: true });
  }, [subjectKey]);

  const back = (
    <Link
      href={backHref}
      className="-ml-2 mb-4 inline-flex h-11 items-center gap-1 rounded-md px-2 text-ui font-medium text-cobalt hover:underline min-[900px]:hidden"
    >
      <ChevronLeft aria-hidden="true" strokeWidth={1.5} className="size-4" />
      Back to results
    </Link>
  );
  const frame = (children: React.ReactNode) => (
    <div className="px-4 py-6 min-[900px]:px-10 min-[900px]:py-8">
      {back}
      {children}
    </div>
  );

  if (bare && all.status === "error")
    return frame(
      <Notice variant="error" title="Workbook rows could not be loaded" actions={<Button variant="outline" size="sm" className="h-11 min-[900px]:h-7" onClick={all.reload}>Retry</Button>}>
        Row {state.row} could not be looked up.
      </Notice>,
    );
  if (bare && all.status === "success" && !rowHit)
    return frame(
      <StateBlock title={`Workbook row ${state.row} was not found`} actions={<Link href={compareHref({})} className={buttonVariants({ variant: "outline" })}>Browse all rows</Link>}>
        The workbook has no row with that number in the data ControlShift ingested.
      </StateBlock>,
    );
  if (!subject || (detail.status === "loading" && !subjectDetail))
    return frame(
      <div role="status" aria-busy="true" aria-label="Loading comparison">
        {showSkeleton && <Skel />}
      </div>,
    );
  if (detail.status === "error") {
    const notFound = detail.error?.kind === "api" && detail.error.code === "not_found";
    return frame(
      notFound ? (
        <StateBlock
          title={`${subject.id} was not found in CSF ${subject.version}`}
          actions={<Link href={compareHref({ q: subject.id })} className={buttonVariants({ variant: "outline" })}>Search the workbook for “{subject.id}”</Link>}
        >
          It is not a function, category or subcategory of that framework version.
        </StateBlock>
      ) : (
        <Notice
          variant="error"
          title={detail.error?.kind === "unreachable" ? "ControlShift API is unreachable" : "This comparison could not be loaded"}
          actions={<Button variant="outline" size="sm" className="h-11 min-[900px]:h-7" onClick={detail.reload}>Retry</Button>}
        >
          {detail.error?.kind === "unreachable" ? "Start the FastAPI service (controlshift-serve) and retry." : "The API did not return a usable response."}
        </Notice>
      ),
    );
  }
  const d = subjectDetail!;
  const summary = d.crosswalk.summary;
  const elements = (v: FrameworkVersion) => (v === "2.0" ? el20.data : el11.data);
  const toggle = (row: number) =>
    setOpen((p) => {
      const n = new Set(p);
      if (n.has(row)) n.delete(row);
      else n.add(row);
      return n;
    });
  const rowMismatch = state.row !== undefined && entries.length > 0 && !entries.some((e) => e.excel_row === state.row);
  const ctx = { q: state.q, type: state.type };
  const subjectCard = (
    <RecordCard
      version={d.version}
      role={forward ? "focal" : "reference"}
      detail={d}
      fallback={{ elementId: d.element_id, printedId: d.original_id, description: d.description }}
      elements={elements(d.version)}
      isSubject
    />
  );
  const otherCard =
    selected && otherId ? (
      <RecordCard
        version={otherVersion}
        role={forward ? "reference" : "focal"}
        detail={otherDetail}
        fallback={{
          elementId: otherId,
          printedId: (forward ? selected.reference_original_id : selected.focal_original_id) ?? otherId,
          description: forward ? selected.reference_description : selected.focal_description,
        }}
        elements={elements(otherVersion)}
        isSubject={false}
      />
    ) : null;
  const pair = forward ? [subjectCard, otherCard] : [otherCard, subjectCard];
  const sideSwitch =
    selected &&
    (forward
      ? selected.reference_element_id && (
          <Link
            href={compareHref({ ref: selected.reference_element_id, row: selected.excel_row, ...ctx })}
            className="inline-flex min-h-11 items-center text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
          >
            Inspect from the CSF 1.1 side ({selected.reference_original_id ?? selected.reference_element_id})
          </Link>
        )
      : (
          <Link
            href={compareHref({ focal: selected.focal_element_id, row: selected.excel_row, ...ctx })}
            className="inline-flex min-h-11 items-center text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
          >
            Inspect from the CSF 2.0 side ({selected.focal_original_id})
          </Link>
        ));

  return frame(
    <div aria-busy={other.status === "loading"} className="max-w-[1100px]">
      <p className="flex items-center gap-2 text-caption text-fg-3">
        <VersionChip version={d.version} /> Inspecting a CSF {d.version} element
        {forward ? "" : " · reverse lookup (rows that reference it)"}
      </p>
      <h2 ref={heading} tabIndex={-1} className="mt-1 font-mono text-id-lg font-medium text-fg-1 outline-none">
        {d.original_id}
      </h2>
      <p className="mt-1 text-caption text-fg-3" title={d.crosswalk.direction}>
        {entries.length} workbook {entries.length === 1 ? "row" : "rows"} {forward ? "list" : "reference"} this element · direction CSF 2.0 → CSF 1.1
      </p>
      <div className="mt-2">
        <DerivedSummary summary={summary} />
      </div>

      {summary.status === "mapped_and_new_in_2_0" && (
        <Notice
          variant="ambiguous"
          className="mt-4 max-w-[720px]"
          title="Multiple crosswalk entries require interpretation"
          actions={entries.map((e) => (
            <Link
              key={e.excel_row}
              href={compareHref({ ...(forward ? { focal: d.element_id } : { ref: d.element_id }), row: e.excel_row, ...ctx })}
              className={buttonVariants({ variant: "outline", size: "sm", className: "h-11 min-[900px]:h-7" })}
            >
              Compare row {e.excel_row}
            </Link>
          ))}
        >
          <p>
            The official transition workbook contains {entries.length} entries for {d.original_id}.
            ControlShift preserves all of them and does not choose between interpretations.
          </p>
          <ul className="mt-2 list-disc space-y-0.5 pl-5">
            {entries.map((e) => (
              <li key={e.excel_row}>{describeEntry(e)}</li>
            ))}
          </ul>
        </Notice>
      )}
      {rowMismatch && (
        <Notice variant="info" className="mt-4 max-w-[720px]" title={`Row ${state.row} is not one of this element's rows`}>
          Showing row {selected?.excel_row} instead.
        </Notice>
      )}

      {!selected ? (
        <div className="mt-6 grid gap-4 min-[1480px]:grid-cols-2">
          {subjectCard}
          <Notice variant="no-reference" title="No crosswalk reference">
            No row in the official NIST transition workbook {forward ? "lists" : "references"} this CSF {d.version} element.
            The workbook does not state whether the element was retained, merged or dropped.
          </Notice>
        </div>
      ) : (
        <>
          <section aria-labelledby="sel-heading" className="mt-6">
            <h3 id="sel-heading" className="text-title-sm font-semibold text-fg-1">
              Selected relationship · workbook row {selected.excel_row}
            </h3>
            <div className="mt-3 flex flex-col gap-2 min-[1480px]:grid min-[1480px]:grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] min-[1480px]:items-stretch min-[1480px]:gap-3">
              {pair[0] ?? <NoReferencePanel entry={selected} />}
              <RowConnector entry={selected} />
              {pair[1] ?? <NoReferencePanel entry={selected} />}
            </div>
            <div className="mt-5">
              <RelationshipDetails entry={selected} summary={summary} actions={sideSwitch} />
            </div>
          </section>

          <section aria-labelledby="rows-heading" className="mt-8 max-w-[720px]">
            <h3 id="rows-heading" className="text-title-sm font-semibold text-fg-1">
              {forward ? "Workbook rows for" : "Workbook rows referencing"} {d.original_id} ({entries.length})
            </h3>
            <p className="mt-0.5 text-caption text-fg-3">
              Every row is shown separately, in workbook order. {entries.length > 1 && "The selected row is highlighted."}
            </p>
            <ol aria-label="Workbook rows" className="mt-3 divide-y divide-border rounded-lg border border-border bg-surface">
              {entries.map((e) => (
                <RowItem
                  key={e.excel_row}
                  entry={e}
                  selected={e.excel_row === selected.excel_row}
                  subjectSide={forward ? "focal" : "reference"}
                  state={{ ...(forward ? { focal: d.element_id } : { ref: d.element_id }), ...ctx }}
                  expanded={open.has(e.excel_row)}
                  onToggleText={() => toggle(e.excel_row)}
                />
              ))}
            </ol>
          </section>
        </>
      )}
      <p className="mt-8 text-caption text-fg-3">
        Back to <Link href={listHref(d.version)} className="text-cobalt hover:underline">browse CSF {d.version} in Control Explorer</Link>.
      </p>
    </div>,
  );
}
