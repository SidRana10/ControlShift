"use client";

import Link from "next/link";
import { Fragment, useEffect, useRef } from "react";
import { ChevronLeft } from "lucide-react";
import { Notice } from "@/components/shared/notice";
import { SourceTag } from "@/components/shared/source-tags";
import { StateBlock } from "@/components/shared/state-block";
import { VersionChip } from "@/components/shared/version-chip";
import { buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { loadDetail } from "@/lib/explorer/catalog-cache";
import { LEVEL_LABEL, ancestorsOf, indexById } from "@/lib/explorer/hierarchy";
import { hasContext, listHref, recordHref } from "@/lib/explorer/url";
import { useLoader } from "@/lib/explorer/use-loader";
import { useDelayedFlag } from "./use-delayed-flag";
import { useExplorer } from "./explorer-provider";

/**
 * Record pane for /explorer/{version}/{id}. This milestone shows identity, official text and the
 * source line only; children, references, source details and the crosswalk come next.
 */
export function RecordPane() {
  const ex = useExplorer();
  const { loc, elements, selected, version, ctx } = ex;
  const recordVersion = loc.kind === "record" ? loc.version : null;
  const recordId = loc.kind === "record" ? loc.recordId : "";

  const detail = useLoader(recordVersion ? `detail:${recordVersion}:${recordId}` : null, () =>
    loadDetail(recordVersion!, recordId),
  );
  const heading = useRef<HTMLHeadingElement>(null);
  const showSkeleton = useDelayedFlag(detail.status === "loading" && !selected);

  // Canonical URL: /explorer/1.1/PR.AT-1 (or lower-case) becomes /explorer/1.1/PR.AT-01.
  const canonical = detail.status === "success" ? detail.data?.element_id : undefined;
  const { replaceWithCanonical } = ex;
  useEffect(() => {
    if (canonical && canonical !== recordId) replaceWithCanonical(canonical);
  }, [canonical, recordId, replaceWithCanonical]);

  // Move focus to the record heading after a keyboard open, and always on narrow screens
  // where the record is a separate screen.
  const summary = detail.data ?? selected;
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

  if (detail.status === "error" && !selected) {
    const notFound = detail.error?.kind === "api" && detail.error.code === "not_found";
    return (
      <div className="px-4 py-6 min-[900px]:px-10 min-[900px]:py-8">
        {back}
        {notFound ? (
          <StateBlock
            title={`${recordId} was not found in CSF ${recordVersion}`}
            actions={
              <Link
                href={listHref(recordVersion, { q: recordId })}
                className={buttonVariants({ variant: "outline" })}
              >
                Search for “{recordId}”
              </Link>
            }
          >
            It is not a function, category or subcategory of this framework version.
          </StateBlock>
        ) : (
          <Notice
            variant="error"
            title={
              detail.error?.kind === "unreachable"
                ? "ControlShift API is unreachable"
                : "This record could not be loaded"
            }
            actions={
              <button
                type="button"
                onClick={detail.reload}
                className={buttonVariants({ variant: "outline", size: "sm" })}
              >
                Retry
              </button>
            }
          >
            {detail.error?.kind === "unreachable"
              ? "Start the FastAPI service (controlshift-serve) and retry."
              : detail.error?.message}
          </Notice>
        )}
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="px-4 py-6 min-[900px]:px-10 min-[900px]:py-8" aria-busy="true">
        {back}
        {showSkeleton && (
          <div aria-hidden="true" className="space-y-3">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-7 w-40" />
            <Skeleton className="h-5 w-full" />
            <Skeleton className="h-5 w-4/5" />
          </div>
        )}
      </div>
    );
  }

  const byId = elements ? indexById(elements) : null;
  const trail = byId ? ancestorsOf(summary, byId).reverse() : [];
  const prov = detail.data?.provenance.chunk;
  const normalized = summary.original_id !== summary.element_id;

  return (
    <article className="px-4 py-6 min-[900px]:px-10 min-[900px]:py-8">
      {back}
      <div className="max-w-[720px]">
        <nav aria-label="Breadcrumb" className="text-caption text-fg-3">
          <ol className="flex flex-wrap items-center gap-x-1.5">
            <li>
              <Link href={listHref(summary.version)} className="hover:text-fg-1 hover:underline">
                CSF {summary.version}
              </Link>
            </li>
            {trail.map((a) => (
              <Fragment key={a.element_id}>
                <li aria-hidden="true">›</li>
                <li>
                  <Link
                    href={recordHref(a.version, a.element_id, ctx)}
                    className="hover:text-fg-1 hover:underline"
                  >
                    {a.name ?? a.original_id} ({a.original_id})
                  </Link>
                </li>
              </Fragment>
            ))}
          </ol>
        </nav>

        <div className="mt-4 flex items-center gap-2">
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
        {normalized && (
          <p className="mt-0.5 text-caption text-fg-3">Normalized as {summary.element_id}</p>
        )}
        {summary.name && <p className="mt-2 text-name-lg font-semibold text-fg-1">{summary.name}</p>}

        {summary.description ? (
          <p className="mt-3 font-serif text-source-lg text-fg-1">{summary.description}</p>
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

        <Notice variant="info" className="mt-8" title="The complete record view is coming next">
          Children, informative references, source details and the official crosswalk are not shown
          yet. What appears above is read from the live Catalog API.
        </Notice>
      </div>
    </article>
  );
}
