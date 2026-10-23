"use client";

import Link from "next/link";
import { Fragment } from "react";
import { SourceTag } from "@/components/shared/source-tags";
import { VersionChip } from "@/components/shared/version-chip";
import { SourceDetails } from "@/features/explorer/source-details";
import type { ElementDetail, ElementSummary, FrameworkVersion } from "@/lib/api/types";
import { LEVEL_LABEL, ancestorsOf, indexById } from "@/lib/explorer/hierarchy";
import { recordHref } from "@/lib/explorer/url";
import { cn } from "@/lib/utils";

const INK: Record<FrameworkVersion, string> = {
  "2.0": "border-t-v20",
  "1.1": "border-t-v11",
};

/**
 * One official framework record, from the Catalog API. Version ink marks identity (top rule and
 * chip) only. Everything shown is a Catalog field: printed and normalized ID, level, name, verbatim
 * description, hierarchy, source page and provenance. Nothing is derived here.
 */
export function RecordCard({
  version,
  role,
  detail,
  fallback,
  elements,
  isSubject,
  headingRef,
}: {
  version: FrameworkVersion;
  /** "focal" (CSF 2.0 side) or "reference" (CSF 1.1 side) of the official workbook direction. */
  role: "focal" | "reference";
  detail: ElementDetail | undefined;
  /** Identity and description taken from the workbook row while the record request is pending. */
  fallback: { elementId: string; printedId: string; description: string | null };
  elements: ElementSummary[] | undefined;
  isSubject: boolean;
  headingRef?: React.Ref<HTMLHeadingElement>;
}) {
  const id = detail?.original_id ?? fallback.printedId;
  const elementId = detail?.element_id ?? fallback.elementId;
  const description = detail ? detail.description : fallback.description;
  const trail =
    detail && elements ? ancestorsOf(detail, indexById(elements)).reverse() : detail?.parent ? [detail.parent] : [];
  const prov = detail?.provenance.chunk;

  return (
    <article
      aria-label={`CSF ${version} record ${id}`}
      className={cn("min-w-0 rounded-lg border border-border border-t-2 bg-surface p-4", INK[version])}
    >
      <p className="flex flex-wrap items-center gap-2">
        <VersionChip version={version} />
        <span className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
          {detail ? LEVEL_LABEL[detail.level] : "Record"}
        </span>
        <span className="text-caption text-fg-3">
          {role === "focal" ? "CSF 2.0 · focal side" : "CSF 1.1 · referenced side"}
        </span>
      </p>
      <h3
        ref={headingRef}
        tabIndex={headingRef ? -1 : undefined}
        className="mt-2 font-mono text-name-lg font-medium text-fg-1 outline-none"
      >
        {id}
        {isSubject && <span className="sr-only"> (inspected record)</span>}
      </h3>
      {id !== elementId && <p className="text-caption text-fg-3">Normalized as {elementId}</p>}
      {detail?.name && <p className="mt-1 text-title-sm font-semibold text-fg-1">{detail.name}</p>}
      {trail.length > 0 && (
        <p className="mt-1 text-caption text-fg-3">
          {trail.map((a, i) => (
            <Fragment key={a.element_id}>
              {i > 0 && <span aria-hidden="true"> › </span>}
              <span>
                {a.name ?? a.original_id} ({a.original_id})
              </span>
            </Fragment>
          ))}
        </p>
      )}
      {description ? (
        <p className="mt-3 font-serif text-source text-fg-1">{description}</p>
      ) : (
        <p className="mt-3 text-caption text-fg-3">
          NIST CSF {version} does not provide a description for this {detail?.level ?? "record"}.
        </p>
      )}
      <p className="mt-3 flex flex-wrap items-center gap-2 text-caption text-fg-2">
        <SourceTag />
        {prov ? (
          <span>
            CSF {version} · {prov.printed_page ? `p. ${prov.printed_page} (PDF p. ${prov.page})` : `PDF p. ${prov.page}`}
          </span>
        ) : (
          <span>
            {detail ? `CSF ${version}` : "Workbook description · full record loading"}
          </span>
        )}
      </p>
      {detail && <SourceDetails provenance={detail.provenance} className="mt-1" />}
      <Link
        href={recordHref(version, elementId)}
        className="mt-1 inline-flex min-h-11 items-center text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
      >
        Open {id} in Control Explorer<span className="sr-only"> (CSF {version})</span>
      </Link>
    </article>
  );
}
