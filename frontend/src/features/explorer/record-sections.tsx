"use client";

import Link from "next/link";
import { useId, useState } from "react";
import { ChevronRight } from "lucide-react";
import type { ElementSummary } from "@/lib/api/types";
import { compareElements, elementTitle } from "@/lib/explorer/hierarchy";
import { recordHref, type ExplorerContext } from "@/lib/explorer/url";
import { cn } from "@/lib/utils";

/** Children of a function or category: every one is a link to its own record. */
export function ChildrenSection({
  parent,
  items,
  ctx,
}: {
  parent: ElementSummary;
  items: ElementSummary[];
  ctx: ExplorerContext;
}) {
  if (items.length === 0) return null;
  const sorted = [...items].sort(compareElements);
  const title = parent.level === "function" ? "Categories" : "Subcategories";
  return (
    <section aria-labelledby="children-heading" id="record-children" className="mt-10">
      <h3 id="children-heading" className="text-title-sm font-semibold text-fg-1">
        {title} ({items.length})
      </h3>
      <ul className="mt-2 divide-y divide-border rounded-lg border border-border bg-surface">
        {sorted.map((c) => (
          <li key={c.element_id}>
            <Link
              href={recordHref(c.version, c.element_id, ctx)}
              className="flex min-h-11 items-start gap-3 px-4 py-2.5 hover:bg-surface-hover focus-visible:-outline-offset-2"
            >
              <span className="w-20 shrink-0 pt-0.5 font-mono text-id font-medium text-fg-1">
                {c.original_id}
              </span>
              <span className="line-clamp-2 min-w-0 font-serif text-source text-fg-1">
                {elementTitle(c)}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

const REFERENCES_COLLAPSE_ABOVE = 6;

/** Informative references, verbatim strings from the structured data. */
export function ReferencesSection({ references }: { references: string[] }) {
  const long = references.length > REFERENCES_COLLAPSE_ABOVE;
  const [open, setOpen] = useState(!long);
  const id = useId();
  return (
    <section aria-labelledby="references-heading" id="record-references" className="mt-10">
      <h3 id="references-heading" className="text-title-sm font-semibold text-fg-1">
        Informative references ({references.length})
      </h3>
      {references.length === 0 ? (
        <p className="mt-1 text-caption text-fg-3">
          No informative references are recorded for this element in ControlShift&apos;s data.
        </p>
      ) : (
        <>
          {long && (
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
              {open ? "Hide references" : "Show references"}
            </button>
          )}
          <ul id={id} hidden={!open} className="mt-2 space-y-1.5">
            {references.map((r, i) => (
              <li key={`${i}:${r}`} className="font-mono text-mono-sm break-words text-fg-2">
                {r}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
