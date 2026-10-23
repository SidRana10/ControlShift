"use client";

import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import { Notice } from "@/components/shared/notice";
import { StateBlock } from "@/components/shared/state-block";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { searchElements } from "@/lib/explorer/catalog-cache";
import { expandAll } from "@/lib/explorer/expansion-store";
import {
  ancestorsOf,
  buildTree,
  filterElements,
  indexById,
  orderSearchResults,
  sortElements,
} from "@/lib/explorer/hierarchy";
import { hasFilters } from "@/lib/explorer/url";
import { useLoader } from "@/lib/explorer/use-loader";
import { cn } from "@/lib/utils";
import { useExplorer } from "./explorer-provider";
import { FilterBar } from "./filter-bar";
import { ResultList } from "./result-list";
import { SearchField } from "./search-field";
import { TreeView } from "./tree-view";
import { useDelayedFlag } from "./use-delayed-flag";

function ListSkeleton() {
  return (
    <div aria-hidden="true" className="space-y-3 p-4">
      {[70, 90, 55, 80, 65, 85, 60, 75].map((w, i) => (
        <Skeleton key={i} className="h-4" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

/** Navigator pane: search, filters, and either the browse tree or a flat result list. */
export function Navigator({ className }: { className?: string }) {
  const ex = useExplorer();
  const { version, ctx, elements, elementsStatus, selected, loc, expanded } = ex;
  const searching = Boolean(ctx.q);
  const flat = searching || Boolean(ctx.level);
  const onRecord = loc.kind === "record";

  const searchState = useLoader(
    searching ? JSON.stringify({ version, ...ctx }) : null,
    () =>
      searchElements({
        version,
        level: ctx.level,
        function: ctx.fn,
        category: ctx.cat,
        q: ctx.q,
      }),
  );
  const showSkeleton = useDelayedFlag(
    elementsStatus === "loading" || (searching && searchState.status === "loading"),
  );

  const searchResults = useMemo(() => {
    const data = searchState.data?.elements;
    // Results kept from another framework while a new search loads must not be shown.
    if (!data || (data.length > 0 && data[0].version !== version)) return null;
    return orderSearchResults(data, ctx.q ?? "");
  }, [searchState.data, version, ctx.q]);

  const filtered = useMemo(() => (elements ? filterElements(elements, ctx) : []), [elements, ctx]);
  const roots = useMemo(() => buildTree(filtered), [filtered]);
  const levelList = useMemo(() => (flat && !searching ? sortElements(filtered) : []), [flat, searching, filtered]);

  const listed = searching ? searchResults?.elements : flat ? levelList : filtered;
  const searchPending = searching && (searchState.status === "loading" || searchState.status === "idle");

  // --- refs and DOM behaviour ----------------------------------------------------------
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const savedScroll = useRef(0);
  const lastOpened = useRef<string | null>(null);

  // "/" focuses search when typing elsewhere (only while the navigator is on screen).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
      const t = e.target as HTMLElement | null;
      if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
      const input = inputRef.current;
      if (!input || input.offsetParent === null) return;
      e.preventDefault();
      input.focus();
      input.select();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  // Keep the open record's branches expanded and the row in view.
  const selectedId = selected?.element_id;
  useEffect(() => {
    if (!selected || !elements) return;
    const byId = indexById(elements);
    expandAll(version, ancestorsOf(selected, byId).map((a) => a.element_id));
    lastOpened.current = selected.element_id;
    const raf = requestAnimationFrame(() => {
      bodyRef.current
        ?.querySelector(`[data-node-id="${CSS.escape(selected.element_id)}"]`)
        ?.scrollIntoView({ block: "nearest" });
    });
    return () => cancelAnimationFrame(raf);
  }, [selectedId, elements, version]); // eslint-disable-line react-hooks/exhaustive-deps

  // Narrow screens: the navigator is hidden while a record is open. Restore its scroll position
  // and put focus back on the row that was opened when the user returns to the results.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      if (el.offsetParent !== null) savedScroll.current = el.scrollTop;
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, []);
  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el || onRecord) return;
    el.scrollTop = savedScroll.current;
    if (window.matchMedia("(max-width: 899px)").matches && lastOpened.current) {
      el.querySelector<HTMLElement>(`[data-node-id="${CSS.escape(lastOpened.current)}"]`)?.focus({
        preventScroll: true,
      });
    }
  }, [onRecord]);

  const focusFirstResult = () => {
    const target = bodyRef.current?.querySelector<HTMLElement>(
      '[role="treeitem"][tabindex="0"], ul a',
    );
    target?.focus();
  };

  // --- selected record outside the current results ----------------------------------------
  const inResults =
    !selected || !listed || searchPending ? true : listed.some((e) => e.element_id === selected.element_id);

  // --- meta line ---------------------------------------------------------------------------
  const count = listed?.length ?? 0;
  let meta = "";
  if (elementsStatus === "success" || (elements && elementsStatus === "loading")) {
    if (searching) meta = searchPending ? "Searching…" : `${count} ${count === 1 ? "match" : "matches"} for “${ctx.q}” in CSF ${version}`;
    else if (flat || hasFilters(ctx)) meta = `${count} ${count === 1 ? "result" : "results"} · CSF ${version}`;
    else meta = `${count} elements · CSF ${version}`;
  }

  // --- body --------------------------------------------------------------------------------
  let body: React.ReactNode;
  const failed = elementsStatus === "error" || (searching && searchState.status === "error");
  if (failed) {
    const err = elementsStatus === "error" ? ex.elementsError : searchState.error;
    const unreachable = err?.kind === "unreachable";
    body = (
      <div className="p-4">
        <Notice
          variant="error"
          title={unreachable ? "ControlShift API is unreachable" : "Records could not be loaded"}
          actions={
            <Button
              variant="outline"
              size="sm"
              className="h-11 min-[900px]:h-7"
              onClick={elementsStatus === "error" ? ex.reloadElements : searchState.reload}
            >
              Retry
            </Button>
          }
        >
          {unreachable ? "Start the FastAPI service (controlshift-serve) and retry." : err?.message}
        </Notice>
      </div>
    );
  } else if (!elements || (searching && !searchResults && searchPending)) {
    body = showSkeleton ? <ListSkeleton /> : null;
  } else if (listed && listed.length === 0 && !searchPending) {
    body = searching ? (
      <StateBlock
        title={`No elements match “${ctx.q}” in CSF ${version}`}
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              className="h-11 min-[900px]:h-7"
              onClick={() => void ex.setVersion(version === "2.0" ? "1.1" : "2.0")}
            >
              Search CSF {version === "2.0" ? "1.1" : "2.0"} instead
            </Button>
            <Button variant="ghost" size="sm" className="h-11 min-[900px]:h-7" onClick={() => ex.updateContext({ q: undefined })}>
              Clear search
            </Button>
          </>
        }
      />
    ) : (
      <StateBlock
        title="No elements match these filters"
        actions={
          <Button variant="outline" size="sm" className="h-11 min-[900px]:h-7" onClick={() => ex.clearFilters()}>
            Clear filters
          </Button>
        }
      />
    );
  } else if (flat) {
    const items = (searching ? searchResults?.elements : levelList) ?? [];
    body = (
      <div className={cn(searching && searchPending && "opacity-60")} aria-busy={searchPending}>
        <ResultList
          elements={items}
          q={ctx.q}
          exactIds={searching ? searchResults?.exactIds : undefined}
          selectedId={selectedId}
          label={searching ? `Search results in CSF ${version}` : `Filtered elements in CSF ${version}`}
          hrefFor={ex.hrefFor}
          onKeyboardOpen={ex.requestRecordFocus}
          onLeaveTop={() => inputRef.current?.focus()}
        />
      </div>
    );
  } else {
    body = (
      <TreeView
        roots={roots}
        expanded={expanded}
        selectedId={selectedId}
        label={`CSF ${version} framework hierarchy`}
        onToggle={ex.toggleExpanded}
        onOpen={ex.openRecord}
      />
    );
  }

  return (
    <section
      aria-label="Navigator"
      className={cn(
        "min-h-0 w-full flex-col border-border bg-surface min-[900px]:w-[288px] min-[900px]:shrink-0 min-[900px]:border-r min-[1200px]:w-[320px] min-[1320px]:w-[340px]",
        className,
      )}
    >
      <div className="shrink-0 border-b border-border px-4 pt-3 pb-3">
        <SearchField inputRef={inputRef} onArrowDown={focusFirstResult} />
        <FilterBar />
        <p role="status" aria-live="polite" className="mt-2 min-h-4 text-caption text-fg-3">
          {meta}
        </p>
      </div>
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto" aria-busy={elementsStatus === "loading"}>
        {selected && !inResults && (
          <div className="flex items-start gap-2 border-b border-border bg-neutral-notice-soft px-4 py-2">
            <div className="min-w-0 flex-1 text-caption text-fg-2">
              <p className="font-medium text-fg-1">Selected record is outside the current results</p>
              <p className="truncate font-mono text-id">{selected.original_id}</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="h-11 shrink-0 min-[900px]:h-7"
              onClick={() => ex.clearFilters({ query: true })}
            >
              Clear filters
            </Button>
          </div>
        )}
        <div ref={bodyRef}>{body}</div>
      </div>
    </section>
  );
}
