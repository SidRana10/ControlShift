"use client";

import Link from "next/link";
import { Fragment, useEffect, useRef } from "react";
import { ArrowLeft, ChevronLeft } from "lucide-react";
import { Notice } from "@/components/shared/notice";
import { SourceTag } from "@/components/shared/source-tags";
import { StateBlock } from "@/components/shared/state-block";
import { VersionChip } from "@/components/shared/version-chip";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { ElementDetail, ElementSummary } from "@/lib/api/types";
import { loadDetail } from "@/lib/explorer/catalog-cache";
import { LEVEL_LABEL, ancestorsOf, indexById } from "@/lib/explorer/hierarchy";
import { hasContext, listHref, recordHref } from "@/lib/explorer/url";
import { useLoader } from "@/lib/explorer/use-loader";
import { CrosswalkSection } from "./crosswalk-section";
import { useExplorer } from "./explorer-provider";
import { ChildrenSection, ReferencesSection } from "./record-sections";
import { SourceDetails } from "./source-details";
import { useDelayedFlag } from "./use-delayed-flag";

function SectionsSkeleton() {
  return (
    <div aria-hidden="true" className="mt-10 space-y-3">
      <Skeleton className="h-5 w-56" />
      <Skeleton className="h-3 w-72" />
      <Skeleton className="h-24 w-full" />
    </div>
  );
}

function scrollToSection(id: string) {
  return (e: React.MouseEvent) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ block: "start" });
  };
}

/** Wide-desktop facts rail (>=1640px): record facts, page anchors, source details. */
function FactsRail({ detail }: { detail: ElementDetail }) {
  const { ctx } = useExplorer();
  const fact = (label: string, value: React.ReactNode) => (
    <div className="grid grid-cols-[6rem_1fr] gap-x-2 py-1">
      <dt className="text-caption text-fg-3">{label}</dt>
      <dd className="min-w-0 text-ui-sm break-words text-fg-1">{value}</dd>
    </div>
  );
  const anchors: [string, string][] = [
    ["record-text", "Official text"],
    ["record-crosswalk", `Crosswalk (${detail.crosswalk.entries.length})`],
  ];
  if (detail.children.length) anchors.push(["record-children", `Children (${detail.children.length})`]);
  anchors.push(["record-references", `Informative references (${detail.informative_references.length})`]);
  return (
    <aside
      aria-label="Record facts"
      className="hidden w-[264px] shrink-0 border-l border-border bg-surface-sunken min-[1640px]:block"
    >
      <div className="sticky top-0 space-y-6 p-5">
        <div>
          <h3 className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">Record</h3>
          <dl className="mt-2">
            {fact("Version", `CSF ${detail.version}`)}
            {fact("Level", LEVEL_LABEL[detail.level])}
            {fact("Printed ID", <span className="font-mono text-id">{detail.original_id}</span>)}
            {detail.original_id !== detail.element_id &&
              fact("Normalized ID", <span className="font-mono text-id">{detail.element_id}</span>)}
            {detail.parent &&
              fact(
                "Parent",
                <Link
                  href={recordHref(detail.version, detail.parent.element_id, ctx)}
                  className="font-mono text-id text-cobalt hover:underline"
                >
                  {detail.parent.original_id}
                </Link>,
              )}
          </dl>
        </div>
        <nav aria-label="On this page">
          <h3 className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">On this page</h3>
          <ul className="mt-2 space-y-0.5">
            {anchors.map(([id, label]) => (
              <li key={id}>
                <a
                  href={`#${id}`}
                  onClick={scrollToSection(id)}
                  className="block rounded-md px-1 py-1 text-ui-sm text-fg-2 hover:text-fg-1"
                >
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <SourceDetails provenance={detail.provenance} />
      </div>
    </aside>
  );
}

/** The record view for /explorer/{version}/{id}. */
export function RecordPane() {
  const ex = useExplorer();
  const { loc, elements, selected, version, ctx, crosswalkReturn } = ex;
  const recordVersion = loc.kind === "record" ? loc.version : null;
  const recordId = loc.kind === "record" ? loc.recordId : "";

  const detail = useLoader(recordVersion ? `detail:${recordVersion}:${recordId}` : null, () =>
    loadDetail(recordVersion!, recordId),
  );
  const heading = useRef<HTMLHeadingElement>(null);
  const data: ElementDetail | undefined =
    detail.status === "success" && detail.data && detail.data.version === recordVersion ? detail.data : undefined;
  const summary: ElementSummary | undefined = data ?? selected;
  const showSkeleton = useDelayedFlag(detail.status === "loading" && !summary);

  // Canonical URL: /explorer/1.1/PR.AT-1 (or lower-case) becomes /explorer/1.1/PR.AT-01.
  const canonical = data?.element_id;
  const { replaceWithCanonical } = ex;
  useEffect(() => {
    if (canonical && canonical !== recordId) replaceWithCanonical(canonical);
  }, [canonical, recordId, replaceWithCanonical]);

  // Focus the record heading after a keyboard open, and always on narrow screens where the
  // record is a separate screen.
  const summaryId = summary?.element_id;
  const { consumeRecordFocus } = ex;
  useEffect(() => {
    if (!summaryId) return;
    const narrow = window.matchMedia("(max-width: 899px)").matches;
    if (consumeRecordFocus() || narrow) heading.current?.focus({ preventScroll: true });
  }, [summaryId, consumeRecordFocus]);

  if (loc.kind !== "record") return null;

  if (!recordVersion) {
    return (
      <div className="px-4 py-8 min-[900px]:px-10">
        <StateBlock
          title={`“${loc.versionParam}” is not a framework version`}
          actions={
            <Link href={listHref("2.0")} className={buttonVariants({ variant: "outline" })}>
              Browse CSF 2.0
            </Link>
          }
        >
          Available versions are CSF 2.0 and CSF 1.1.
        </StateBlock>
      </div>
    );
  }

  const backLabel = hasContext(ctx) ? "Back to results" : `Browse CSF ${version}`;
  const back = (
    <Link
      href={ex.backHref}
      className="-ml-2 mb-4 inline-flex h-11 items-center gap-1 rounded-md px-2 text-ui font-medium text-cobalt hover:underline min-[900px]:hidden"
    >
      <ChevronLeft aria-hidden="true" strokeWidth={1.5} className="size-4" />
      {backLabel}
    </Link>
  );
  const frame = (children: React.ReactNode) => (
    <div className="px-4 py-6 min-[900px]:px-10 min-[900px]:py-8">{back}{children}</div>
  );

  if (detail.status === "error" && !summary) {
    const notFound = detail.error?.kind === "api" && detail.error.code === "not_found";
    return frame(
      notFound ? (
        <StateBlock
          title={`${recordId} was not found in CSF ${recordVersion}`}
          actions={
            <Link href={listHref(recordVersion, { q: recordId })} className={buttonVariants({ variant: "outline" })}>
              Search for “{recordId}”
            </Link>
          }
        >
          It is not a function, category or subcategory of this framework version.
        </StateBlock>
      ) : (
        <Notice
          variant="error"
          title={detail.error?.kind === "unreachable" ? "ControlShift API is unreachable" : "This record could not be loaded"}
          actions={
            <Button variant="outline" size="sm" className="h-11 min-[900px]:h-7" onClick={detail.reload}>
              Retry
            </Button>
          }
        >
          {detail.error?.kind === "unreachable"
            ? "Start the FastAPI service (controlshift-serve) and retry."
            : detail.error?.message}
        </Notice>
      ),
    );
  }

  if (!summary) {
    return (
      <div className="px-4 py-6 min-[900px]:px-10 min-[900px]:py-8" aria-busy="true" role="status" aria-label="Loading record">
        {back}
        {showSkeleton && (
          <div aria-hidden="true" className="max-w-[720px] space-y-3">
            <Skeleton className="h-4 w-64" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-7 w-40" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-4/5" />
            <SectionsSkeleton />
          </div>
        )}
      </div>
    );
  }

  const byId = elements ? indexById(elements) : null;
  const trail = byId ? ancestorsOf(summary, byId).reverse() : data?.parent ? [data.parent] : [];
  const prov = data?.provenance.chunk;
  const normalized = summary.original_id !== summary.element_id;
  const returnChip =
    crosswalkReturn && crosswalkReturn.toKey === `${summary.version}/${summary.element_id}` ? crosswalkReturn : null;

  const main = (
    <div className="min-w-0 flex-1 px-4 py-6 min-[900px]:px-10 min-[900px]:py-8">
      {back}
      <div className="max-w-[720px]">
        {returnChip && (
          <Link
            href={returnChip.fromHref}
            className="mb-3 -ml-2 inline-flex min-h-11 items-center gap-1.5 rounded-md px-2 text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
          >
            <ArrowLeft aria-hidden="true" strokeWidth={1.5} className="size-3.5" />
            From {returnChip.fromLabel} · row {returnChip.row}
          </Link>
        )}
        <nav aria-label="Breadcrumb" className="text-caption text-fg-3">
          <ol className="flex flex-wrap items-center gap-x-1.5">
            <li>
              <Link href={listHref(summary.version)} className="inline-flex min-h-11 items-center hover:text-fg-1 hover:underline min-[900px]:min-h-0">
                CSF {summary.version}
              </Link>
            </li>
            {trail.map((a) => (
              <Fragment key={a.element_id}>
                <li aria-hidden="true">›</li>
                <li>
                  <Link
                    href={recordHref(a.version, a.element_id, ctx)}
                    className="inline-flex min-h-11 items-center hover:text-fg-1 hover:underline min-[900px]:min-h-0"
                  >
                    {a.name ?? a.original_id} ({a.original_id})
                  </Link>
                </li>
              </Fragment>
            ))}
          </ol>
        </nav>

        <div className="mt-2 flex items-center gap-2 min-[900px]:mt-4">
          <VersionChip version={summary.version} />
          <span className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
            {LEVEL_LABEL[summary.level]}
          </span>
        </div>
        <h2
          ref={heading}
          tabIndex={-1}
          className="mt-2 font-mono text-id-lg font-medium text-fg-1 outline-none focus-visible:outline-2"
        >
          {summary.original_id}
        </h2>
        {normalized && <p className="mt-0.5 text-caption text-fg-3">Normalized as {summary.element_id}</p>}
        {summary.name && <p className="mt-2 text-name-lg font-semibold text-fg-1">{summary.name}</p>}

        <div id="record-text" className="scroll-mt-4">
          {summary.description ? (
            <p className="mt-3 font-serif text-source-lg max-[899px]:text-[17px] max-[899px]:leading-[26px] text-fg-1">
              {summary.description}
            </p>
          ) : (
            <p className="mt-3 text-caption text-fg-3">
              NIST CSF {summary.version} does not provide a description for this {summary.level}.
            </p>
          )}
          <p className="mt-3 flex min-h-5 flex-wrap items-center gap-2 text-caption text-fg-2">
            {prov ? (
              <>
                <SourceTag />
                <span>
                  CSF {summary.version} ·{" "}
                  {prov.printed_page ? `p. ${prov.printed_page} (PDF p. ${prov.page})` : `PDF p. ${prov.page}`}
                </span>
              </>
            ) : (
              detail.status === "loading" && <Skeleton className="h-4 w-48" />
            )}
          </p>
        </div>
        {data && <SourceDetails provenance={data.provenance} className="mt-1 min-[1640px]:hidden" />}

        {data ? (
          <>
            <CrosswalkSection detail={data} />
            <ChildrenSection parent={data} items={data.children} ctx={ctx} />
            <ReferencesSection references={data.informative_references} />
          </>
        ) : detail.status === "error" ? (
          <Notice
            variant="error"
            className="mt-10"
            title={detail.error?.kind === "unreachable" ? "ControlShift API is unreachable" : "Record details could not be loaded"}
            actions={
              <Button variant="outline" size="sm" className="h-11 min-[900px]:h-7" onClick={detail.reload}>
                Retry
              </Button>
            }
          >
            The identity above comes from the framework list. Provenance, crosswalk, children and
            references need the record request, which failed.
          </Notice>
        ) : (
          <div aria-busy="true">
            <SectionsSkeleton />
          </div>
        )}
      </div>
    </div>
  );

  return (
    <article aria-label={`Record ${summary.original_id}`} className="flex min-h-full">
      {main}
      {data && <FactsRail detail={data} />}
    </article>
  );
}
