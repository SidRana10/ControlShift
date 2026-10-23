"use client";

import Link from "next/link";
import { useId, useState } from "react";
import { ArrowUp, ChevronRight } from "lucide-react";
import { Notice } from "@/components/shared/notice";
import { DerivedTag, SourceTag } from "@/components/shared/source-tags";
import { VersionChip } from "@/components/shared/version-chip";
import { asVersion, evidenceDomId, itemLabel, itemVersion, pageLabel } from "@/lib/ask/citations";
import type {
  ControlRecordEvidence,
  CrosswalkEvidence,
  Evidence,
  EvidenceItem,
  PassageEvidence,
} from "@/lib/ask/types";
import { compareHref } from "@/lib/compare/url";
import { recordHref } from "@/lib/explorer/url";
import { cn } from "@/lib/utils";

const LONG_TEXT = 320;

function ExplorerLink({ version, id }: { version: string; id: string }) {
  const v = asVersion(version);
  if (!v) return null;
  return (
    <Link
      href={recordHref(v, id)}
      className="inline-flex min-h-11 items-center gap-1 text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
    >
      Open {id} in Control Explorer<span className="sr-only"> (CSF {v})</span>
    </Link>
  );
}

function Provenance({ rows }: { rows: [string, string | null][] }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const shown = rows.filter((r): r is [string, string] => Boolean(r[1]));
  return (
    <div>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((o) => !o)}
        className="-ml-1 inline-flex min-h-11 items-center gap-1 rounded-md px-1 text-ui-sm font-medium text-fg-2 hover:text-fg-1 min-[900px]:min-h-7"
      >
        <ChevronRight
          aria-hidden="true"
          strokeWidth={1.5}
          className={cn("size-3.5 transition-transform duration-150", open && "rotate-90")}
        />
        Source details
      </button>
      <dl id={id} hidden={!open} className="mb-1">
        {shown.map(([k, v]) => (
          <div key={k} className="grid grid-cols-[6rem_1fr] gap-x-3 py-0.5">
            <dt className="text-caption text-fg-3">{k}</dt>
            <dd className="min-w-0 font-mono text-mono-sm break-all text-fg-1">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function OfficialText({
  text,
  expanded,
  onToggle,
  italic,
}: {
  text: string;
  expanded: boolean;
  onToggle: () => void;
  italic?: boolean;
}) {
  const id = useId();
  const long = text.length > LONG_TEXT;
  return (
    <>
      <p
        id={id}
        className={cn(
          "font-serif text-source whitespace-pre-line text-fg-1",
          italic && "italic",
          !expanded && "line-clamp-4",
        )}
      >
        {text}
      </p>
      {long && (
        <button
          type="button"
          aria-expanded={expanded}
          aria-controls={id}
          onClick={onToggle}
          className="inline-flex min-h-11 items-center text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
        >
          {expanded ? "Show less" : "Show full text"}
        </button>
      )}
    </>
  );
}

function Header({
  item,
  citedByAnswer,
}: {
  item: EvidenceItem;
  citedByAnswer: boolean;
}) {
  const version = itemVersion(item);
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
      {version && <VersionChip version={version} />}
      <span className="font-mono text-id font-medium text-fg-1">{itemLabel(item)}</span>
      {item.kind === "crosswalk" && <span className="text-caption text-fg-3">Transition workbook</span>}
      {item.kind === "passage" && (
        <span className="text-caption text-fg-3">
          {item.chunk_type === "text" ? "Narrative text" : `Retrieved ${item.chunk_type}`}
          {item.rank !== null && ` · rank ${item.rank}`}
        </span>
      )}
      {item.kind === "control" && <span className="text-caption text-fg-3">Framework record</span>}
      {citedByAnswer && (
        <span className="rounded-sm border border-cobalt px-1.5 text-label leading-4 font-medium text-cobalt">
          Cited in answer
        </span>
      )}
    </div>
  );
}

function SourceLine({ file, version, page, section }: { file: string; version?: string; page?: string | null; section?: string | null }) {
  return (
    <p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-caption text-fg-3">
      <SourceTag />
      <span>
        {[version ? `CSF ${version}` : file, page].filter(Boolean).join(" · ")}
      </span>
      {section && <span className="min-w-0 break-words">{section}</span>}
    </p>
  );
}

function ControlBody({ item, expanded, onToggle }: { item: ControlRecordEvidence; expanded: boolean; onToggle: () => void }) {
  const text = item.description ?? item.text;
  return (
    <>
      <SourceLine
        file={item.source_file}
        version={item.version}
        page={pageLabel(item.printed_page, item.page)}
        section={item.section}
      />
      <div className="mt-2">
        {item.name && <p className="text-ui font-semibold text-fg-1">{item.name}</p>}
        <OfficialText text={text} expanded={expanded} onToggle={onToggle} />
      </div>
      <ExplorerLink version={item.version} id={item.element_id} />
      <Provenance
        rows={[
          ["File", item.source_file],
          ["Chunk", item.chunk_id],
          ["Citation", item.citation_id],
        ]}
      />
    </>
  );
}

function PassageBody({ item, expanded, onToggle }: { item: PassageEvidence; expanded: boolean; onToggle: () => void }) {
  return (
    <>
      <SourceLine
        file={item.source_file}
        version={item.version}
        page={pageLabel(item.printed_page, item.page)}
        section={item.section}
      />
      <div className="mt-2">
        <OfficialText text={item.text} expanded={expanded} onToggle={onToggle} />
      </div>
      {item.control_id && item.chunk_type !== "text" && (
        <ExplorerLink version={item.version} id={item.control_id} />
      )}
      <Provenance
        rows={[
          ["File", item.source_file],
          ["Chunk", item.chunk_id],
          ["Citation", item.citation_id],
        ]}
      />
    </>
  );
}

function End({ version, id, description, expanded, onToggle }: { version: string; id: string | null; description: string | null; expanded: boolean; onToggle: () => void }) {
  const v = asVersion(version);
  return (
    <div className="mt-2">
      <p className="flex items-center gap-2 text-caption text-fg-3">
        {v && <VersionChip version={v} />}
        {id ? <span className="font-mono text-id font-medium text-fg-1">{id}</span> : <span className="text-ui-sm text-fg-2 italic">No reference element</span>}
      </p>
      {description && <OfficialText text={description} expanded={expanded} onToggle={onToggle} />}
    </div>
  );
}

function CrosswalkBody({ item, expanded, onToggle }: { item: CrosswalkEvidence; expanded: boolean; onToggle: () => void }) {
  return (
    <>
      <p className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-caption text-fg-3">
        <SourceTag />
        <span>
          {item.source_file}
          {item.sheet && ` · sheet ${item.sheet}`} · row {item.excel_row}
        </span>
      </p>
      <p className="mt-1 text-caption text-fg-3">Direction fixed by the workbook: CSF 2.0 → CSF 1.1.</p>
      <End version={item.focal_version} id={item.focal_id} description={item.focal_description} expanded={expanded} onToggle={onToggle} />
      <End version={item.reference_version} id={item.reference_id} description={item.reference_description} expanded={expanded} onToggle={onToggle} />
      {item.comments && (
        <div className="mt-2">
          <p className="text-caption text-fg-3">Workbook comment:</p>
          <p className="font-serif text-source text-fg-1 italic">“{item.comments}”</p>
        </div>
      )}
      {item.mapping_type && (
        <p className="mt-2 flex flex-wrap items-center gap-2 text-caption text-fg-2">
          Ingest label: <span className="font-mono text-id">{item.mapping_type}</span>
          <DerivedTag />
        </p>
      )}
      <div className="flex flex-wrap gap-x-4">
        <ExplorerLink version={item.focal_version} id={item.focal_id} />
        {item.reference_id && <ExplorerLink version={item.reference_version} id={item.reference_id} />}
        <Link
          href={compareHref({ focal: item.focal_id, row: item.excel_row })}
          className="inline-flex min-h-11 items-center gap-1 text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
        >
          Compare row {item.excel_row} side by side
        </Link>
      </div>
    </>
  );
}

function EvidenceEntry({
  item,
  active,
  citedByAnswer,
  onBackToAnswer,
}: {
  item: EvidenceItem;
  active: boolean;
  citedByAnswer: boolean;
  onBackToAnswer: () => void;
}) {
  const [open, setOpen] = useState(false);
  const expanded = open || active;
  const toggle = () => setOpen((o) => !o);
  return (
    <li
      id={evidenceDomId(item.citation_id)}
      tabIndex={-1}
      aria-label={`${itemLabel(item)}${itemVersion(item) ? `, CSF ${itemVersion(item)}` : ""}${active ? " (selected citation)" : ""}`}
      data-active={active || undefined}
      className={cn(
        "relative px-4 py-3 outline-none focus-visible:outline-2 focus-visible:-outline-offset-2",
        active && "bg-cobalt-soft before:absolute before:inset-y-0 before:left-0 before:w-[2px] before:bg-cobalt",
      )}
    >
      <Header item={item} citedByAnswer={citedByAnswer} />
      {item.kind === "control" && <ControlBody item={item} expanded={expanded} onToggle={toggle} />}
      {item.kind === "passage" && <PassageBody item={item} expanded={expanded} onToggle={toggle} />}
      {item.kind === "crosswalk" && <CrosswalkBody item={item} expanded={expanded} onToggle={toggle} />}
      {active && (
        <button
          type="button"
          onClick={onBackToAnswer}
          className="mt-1 inline-flex min-h-11 items-center gap-1 text-ui-sm font-medium text-cobalt hover:underline min-[900px]:min-h-7"
        >
          <ArrowUp aria-hidden="true" className="size-3.5" strokeWidth={1.5} />
          Back to the citation in the answer
        </button>
      )}
    </li>
  );
}

function Group({
  title,
  description,
  items,
  activeId,
  citedIds,
  onBackToAnswer,
}: {
  title: string;
  description: string;
  items: EvidenceItem[];
  activeId: string | null;
  citedIds: Set<string>;
  onBackToAnswer: () => void;
}) {
  if (items.length === 0) return null;
  return (
    <section aria-labelledby={`grp-${title.replace(/\s+/g, "-")}`} className="border-t border-border first:border-t-0">
      <div className="px-4 pt-4 pb-2">
        <h3 id={`grp-${title.replace(/\s+/g, "-")}`} className="text-title-sm font-semibold text-fg-1">
          {title} <span className="font-normal text-fg-3">({items.length})</span>
        </h3>
        <p className="text-caption text-fg-3">{description}</p>
      </div>
      <ul className="divide-y divide-border border-y border-border">
        {items.map((item) => (
          <EvidenceEntry
            key={item.citation_id}
            item={item}
            active={activeId === item.citation_id}
            citedByAnswer={citedIds.has(item.citation_id)}
            onBackToAnswer={onBackToAnswer}
          />
        ))}
      </ul>
    </section>
  );
}

function versionSummary(evidence: Evidence): string[] {
  const counts = new Map<string, number>();
  for (const i of [...evidence.controls, ...evidence.passages]) {
    counts.set(`CSF ${i.version}`, (counts.get(`CSF ${i.version}`) ?? 0) + 1);
  }
  const parts = [...counts.entries()].sort().map(([k, n]) => `${k}: ${n}`);
  if (evidence.crosswalk.length) parts.push(`Transition workbook: ${evidence.crosswalk.length} row${evidence.crosswalk.length === 1 ? "" : "s"}`);
  return parts;
}

/**
 * Everything the backend returned as evidence, grouped by what it is. Official text is set in the
 * serif under a NIST tag; ControlShift's own notes carry the Derived tag. Entries cited by the
 * answer are marked, and a citation chip in the answer moves focus to its entry here.
 */
export function EvidenceInspector({
  evidence,
  citedIds,
  activeId,
  onBackToAnswer,
  headingId,
}: {
  evidence: Evidence | null;
  citedIds: Set<string>;
  activeId: string | null;
  onBackToAnswer: () => void;
  headingId: string;
}) {
  const [citedOnly, setCitedOnly] = useState(false);
  const total = evidence ? evidence.controls.length + evidence.crosswalk.length + evidence.passages.length : 0;
  const cited = evidence
    ? [...evidence.controls, ...evidence.crosswalk, ...evidence.passages].filter((i) => citedIds.has(i.citation_id)).length
    : 0;
  const keep = <T extends EvidenceItem>(items: T[]) => (citedOnly ? items.filter((i) => citedIds.has(i.citation_id)) : items);

  return (
    <div>
      <div className="border-b border-border px-4 py-3">
        <h2 id={headingId} className="text-title-sm font-semibold text-fg-1">
          Retrieved evidence <span className="font-normal text-fg-3">({total})</span>
        </h2>
        {evidence && total > 0 && (
          <>
            <p className="mt-0.5 text-caption text-fg-3">{versionSummary(evidence).join(" · ")}</p>
            <p className="text-caption text-fg-3">
              Searched {evidence.searched_versions.length ? evidence.searched_versions.map((v) => `CSF ${v}`).join(", ") : "no versions"}
              {evidence.retrieval_mode && ` · retrieval: ${evidence.retrieval_mode}`}
            </p>
          </>
        )}
        {cited > 0 && (
          <div role="group" aria-label="Evidence filter" className="mt-2 inline-flex rounded-md border border-border-strong p-0.5">
            {[
              [false, `All (${total})`],
              [true, `Cited in answer (${cited})`],
            ].map(([value, label]) => (
              <button
                key={String(value)}
                type="button"
                aria-pressed={citedOnly === value}
                onClick={() => setCitedOnly(value as boolean)}
                className={cn(
                  "min-h-11 rounded-sm px-2.5 text-ui-sm font-medium min-[900px]:min-h-7",
                  citedOnly === value ? "bg-surface-sunken text-fg-1" : "text-fg-2 hover:bg-surface-hover",
                )}
              >
                {label as string}
              </button>
            ))}
          </div>
        )}
      </div>

      {!evidence || total === 0 ? (
        <div className="px-4 py-4">
          <Notice variant="info" title="No evidence was returned">
            <p>
              {evidence
                ? "Retrieval found no records, crosswalk rows or passages for this question."
                : "This response did not include an evidence bundle, so there is nothing to inspect."}
            </p>
          </Notice>
        </div>
      ) : (
        <>
          <Group
            title="Official control records"
            description="Exact records from the NIST framework document for the named controls."
            items={keep(evidence.controls)}
            activeId={activeId}
            citedIds={citedIds}
            onBackToAnswer={onBackToAnswer}
          />
          <Group
            title="Official crosswalk rows"
            description="Rows of the NIST transition workbook, one per row, exactly as stored."
            items={keep(evidence.crosswalk)}
            activeId={activeId}
            citedIds={citedIds}
            onBackToAnswer={onBackToAnswer}
          />
          <Group
            title="Retrieved passages"
            description="Text found by search. Search ranks passages; it does not establish mappings."
            items={keep(evidence.passages)}
            activeId={activeId}
            citedIds={citedIds}
            onBackToAnswer={onBackToAnswer}
          />
        </>
      )}

      {evidence && (evidence.notes.length > 0 || evidence.unresolved_questions.length > 0) && (
        <section aria-labelledby={`${headingId}-notes`} className="border-t border-border px-4 py-4">
          <h3 id={`${headingId}-notes`} className="flex items-center gap-2 text-title-sm font-semibold text-fg-1">
            Notes on the evidence <DerivedTag />
          </h3>
          <p className="text-caption text-fg-3">Written by ControlShift while assembling the evidence; not NIST text.</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-ui-sm text-fg-2">
            {[...evidence.unresolved_questions, ...evidence.notes.map((n) => n.text)].map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
