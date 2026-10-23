"use client";

import { useMemo, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import type { ElementSummary, FrameworkVersion } from "@/lib/api/types";
import { elementTitle, flattenVisible, type TreeNode } from "@/lib/explorer/hierarchy";
import { cn } from "@/lib/utils";

const INK: Record<FrameworkVersion, string> = { "2.0": "text-v20", "1.1": "text-v11" };

interface TreeViewProps {
  roots: TreeNode[];
  expanded: ReadonlySet<string>;
  selectedId: string | undefined;
  label: string;
  onToggle: (id: string, open?: boolean) => void;
  onOpen: (el: ElementSummary, opts?: { keyboard?: boolean }) => void;
}

/**
 * WAI-ARIA tree over a flat list of visible rows (aria-level carries the depth).
 * Roving tabindex: one row is tabbable. Keys: Up/Down, Home/End, Right (expand or enter),
 * Left (collapse or go to parent), Enter/Space (open the record). A chevron click only
 * expands or collapses; a row click opens the record.
 */
export function TreeView({ roots, expanded, selectedId, label, onToggle, onOpen }: TreeViewProps) {
  const rows = useMemo(() => flattenVisible(roots, expanded), [roots, expanded]);
  const [focusId, setFocusId] = useState<string | null>(null);
  const container = useRef<HTMLDivElement>(null);

  const tabStop =
    rows.find((r) => r.node.element.element_id === focusId) ??
    rows.find((r) => r.node.element.element_id === selectedId) ??
    rows[0];

  const focusRow = (id: string) => {
    setFocusId(id);
    container.current
      ?.querySelector<HTMLElement>(`[data-node-id="${CSS.escape(id)}"]`)
      ?.focus();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    const item = (e.target as HTMLElement).closest<HTMLElement>('[role="treeitem"]');
    if (!item || e.altKey || e.ctrlKey || e.metaKey) return;
    const id = item.dataset.nodeId!;
    const i = rows.findIndex((r) => r.node.element.element_id === id);
    if (i === -1) return;
    const row = rows[i];
    const branch = row.node.children.length > 0;
    const isOpen = expanded.has(id);
    const go = (idx: number) => {
      e.preventDefault();
      const target = rows[Math.max(0, Math.min(rows.length - 1, idx))];
      if (target) focusRow(target.node.element.element_id);
    };
    switch (e.key) {
      case "ArrowDown":
        return go(i + 1);
      case "ArrowUp":
        return go(i - 1);
      case "Home":
        return go(0);
      case "End":
        return go(rows.length - 1);
      case "ArrowRight":
        if (branch && !isOpen) {
          e.preventDefault();
          onToggle(id, true);
        } else if (branch && isOpen) go(i + 1);
        return;
      case "ArrowLeft":
        if (branch && isOpen) {
          e.preventDefault();
          onToggle(id, false);
        } else if (row.parentId) {
          e.preventDefault();
          focusRow(row.parentId);
        }
        return;
      case "Enter":
      case " ":
        e.preventDefault();
        onOpen(row.node.element, { keyboard: true });
        return;
    }
  };

  return (
    <div ref={container} role="tree" aria-label={label} onKeyDown={onKeyDown}>
      {rows.map(({ node, depth }) => {
        const el = node.element;
        const id = el.element_id;
        const branch = node.children.length > 0;
        const isOpen = expanded.has(id);
        const selected = id === selectedId;
        return (
          <div
            key={id}
            role="treeitem"
            data-node-id={id}
            aria-level={depth}
            aria-selected={selected}
            aria-expanded={branch ? isOpen : undefined}
            tabIndex={tabStop?.node.element.element_id === id ? 0 : -1}
            onFocus={() => setFocusId(id)}
            onClick={() => onOpen(el)}
            style={{ paddingLeft: 4 + (depth - 1) * 16 }}
            className={cn(
              "flex min-h-11 cursor-pointer items-center pr-3 text-ui-sm focus-visible:outline-offset-[-2px] min-[900px]:min-h-8",
              selected
                ? "bg-cobalt-soft font-medium text-fg-1 shadow-[inset_2px_0_0_var(--cs-cobalt)]"
                : "text-fg-2 hover:bg-surface-hover",
            )}
          >
            <span
              aria-hidden="true"
              onClick={
                branch
                  ? (e) => {
                      e.stopPropagation();
                      onToggle(id);
                    }
                  : undefined
              }
              className={cn(
                "flex h-11 w-7 shrink-0 items-center justify-center min-[900px]:h-8 min-[900px]:w-6",
                branch && "rounded-md hover:text-fg-1",
              )}
            >
              {branch && (
                <ChevronRight
                  strokeWidth={1.5}
                  className={cn("size-3.5 text-fg-3 transition-transform duration-150", isOpen && "rotate-90")}
                />
              )}
            </span>
            <span
              className={cn(
                "shrink-0 font-mono text-id font-medium",
                INK[el.version],
                el.level === "subcategory" && "min-w-[4.25rem]",
                "mr-2",
              )}
            >
              {el.original_id}
            </span>{" "}
            {el.level === "subcategory" ? (
              <span className="min-w-0 flex-1 truncate">{elementTitle(el)}</span>
            ) : (
              <>
                <span
                  className={cn("min-w-0 flex-1 truncate", el.level === "function" && "font-medium text-fg-1")}
                  title={el.name ?? undefined}
                >
                  {el.name}
                </span>
                {" "}
                <span className="ml-2 shrink-0 text-caption text-fg-3 tabular-nums">
                  {node.subcategoryCount}
                  <span className="sr-only"> subcategories</span>
                </span>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
