"use client";

import Link from "next/link";
import type { ElementSummary } from "@/lib/api/types";
import { LEVEL_LABEL, elementTitle } from "@/lib/explorer/hierarchy";
import { cn } from "@/lib/utils";
import { VersionChip } from "@/components/shared/version-chip";
import { Highlight } from "./highlight";

/**
 * Flat, ordered results (search and level-filtered views). A plain list of links, not a tree:
 * Tab moves between results, Up/Down also move, Up from the first result returns to search.
 */
export function ResultList({
  elements,
  q,
  exactIds,
  selectedId,
  label,
  hrefFor,
  onKeyboardOpen,
  onLeaveTop,
}: {
  elements: ElementSummary[];
  q?: string;
  exactIds?: ReadonlySet<string>;
  selectedId?: string;
  label: string;
  hrefFor: (el: ElementSummary) => string;
  onKeyboardOpen: () => void;
  onLeaveTop: () => void;
}) {
  const onKeyDown = (e: React.KeyboardEvent<HTMLUListElement>) => {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    const links = [...e.currentTarget.querySelectorAll<HTMLAnchorElement>("a")];
    const i = links.indexOf(document.activeElement as HTMLAnchorElement);
    if (i === -1) return;
    e.preventDefault();
    if (e.key === "ArrowDown") links[Math.min(i + 1, links.length - 1)].focus();
    else if (i === 0) onLeaveTop();
    else links[i - 1].focus();
  };

  return (
    <ul aria-label={label} onKeyDown={onKeyDown} className="divide-y divide-border">
      {elements.map((el) => {
        const needle = q?.trim().toLowerCase() ?? "";
        // Show the text that actually matched: the description when only it contains the query.
        const title =
          needle && el.name && !el.name.toLowerCase().includes(needle) &&
          el.description?.toLowerCase().includes(needle)
            ? el.description
            : elementTitle(el);
        const matchedNormalizedOnly =
          needle !== "" &&
          el.original_id !== el.element_id &&
          el.element_id.toLowerCase().includes(needle) &&
          !el.original_id.toLowerCase().includes(needle);
        const selected = el.element_id === selectedId;
        return (
          <li key={`${el.version}:${el.element_id}`}>
            <Link
              href={hrefFor(el)}
              data-node-id={el.element_id}
              aria-current={selected ? "true" : undefined}
              onClick={(e) => {
                if (e.detail === 0) onKeyboardOpen(); // keyboard-initiated activation
              }}
              className={cn(
                "block min-h-[52px] px-4 py-2 focus-visible:outline-offset-[-2px]",
                selected
                  ? "bg-cobalt-soft shadow-[inset_2px_0_0_var(--cs-cobalt)]"
                  : "hover:bg-surface-hover",
              )}
            >
              <span className="flex items-center gap-2">
                <VersionChip version={el.version} />
                <span className="font-mono text-id font-medium text-fg-1">
                  <Highlight text={el.original_id} q={q} />
                </span>
                {matchedNormalizedOnly && (
                  <span className="font-mono text-id text-fg-3">
                    (<Highlight text={el.element_id} q={q} />)
                  </span>
                )}
                <span className="text-caption text-fg-3">{LEVEL_LABEL[el.level]}</span>
                {exactIds?.has(el.element_id) && (
                  <span className="rounded-sm bg-surface-sunken px-1.5 text-label font-medium text-fg-2">
                    Exact ID
                  </span>
                )}
              </span>
              {title && (
                <span className="mt-0.5 block truncate text-ui-sm text-fg-2">
                  <Highlight text={title} q={q} />
                </span>
              )}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
