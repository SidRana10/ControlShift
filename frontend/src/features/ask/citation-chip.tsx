"use client";

import { VersionChip } from "@/components/shared/version-chip";
import { itemLabel, itemVersion } from "@/lib/ask/citations";
import type { EvidenceItem } from "@/lib/ask/types";
import { cn } from "@/lib/utils";

/**
 * A citation the answer makes. When the cited id is among the returned evidence it is a button that
 * jumps to that entry; otherwise it is shown as plain text saying so, never as a working link.
 */
export function CitationChip({
  citationId,
  item,
  active,
  onSelect,
}: {
  citationId: string;
  item: EvidenceItem | undefined;
  active: boolean;
  onSelect: (citationId: string, origin: HTMLElement) => void;
}) {
  if (!item) {
    return (
      <span
        title="This citation is not among the evidence returned with the answer."
        className="inline-flex min-h-7 items-center gap-1 rounded-sm border border-dashed border-border-strong px-1.5 font-mono text-id text-fg-3"
      >
        {citationId}
        <span className="font-sans text-caption">(not in returned evidence)</span>
      </span>
    );
  }
  const version = itemVersion(item);
  const label = itemLabel(item);
  return (
    <button
      type="button"
      data-citation={citationId}
      aria-pressed={active}
      aria-label={`Citation: ${version ? `CSF ${version} ` : ""}${label}. Show in evidence`}
      onClick={(e) => onSelect(citationId, e.currentTarget)}
      className={cn(
        "inline-flex min-h-11 items-center gap-1.5 rounded-md border border-border-strong bg-surface px-2 text-cobalt hover:bg-surface-hover active:bg-surface-pressed min-[900px]:min-h-7",
        active && "border-cobalt bg-cobalt-soft",
      )}
    >
      {version && <VersionChip version={version} />}
      <span className={cn("text-id", item.kind !== "passage" || item.control_id ? "font-mono font-medium" : "font-sans")}>
        {label}
      </span>
    </button>
  );
}

export function CitationList({
  ids,
  index,
  activeId,
  onSelect,
  label,
}: {
  ids: string[];
  index: Map<string, EvidenceItem>;
  activeId: string | null;
  onSelect: (citationId: string, origin: HTMLElement) => void;
  label: string;
}) {
  if (ids.length === 0) return null;
  return (
    <ul aria-label={label} className="flex flex-wrap gap-1.5">
      {ids.map((id) => (
        <li key={id}>
          <CitationChip citationId={id} item={index.get(id)} active={activeId === id} onSelect={onSelect} />
        </li>
      ))}
    </ul>
  );
}
