"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { ApiError } from "@/lib/api/client";
import type { ElementSummary, FrameworkVersion } from "@/lib/api/types";
import { loadElements } from "@/lib/explorer/catalog-cache";
import { useExpanded, toggleExpanded as storeToggle } from "@/lib/explorer/expansion-store";
import { findElement, sanitizeContext } from "@/lib/explorer/hierarchy";
import {
  DEFAULT_VERSION,
  MAX_QUERY_LENGTH,
  listHref,
  parseLocation,
  recordHref,
  type ExplorerContext,
  type ExplorerLocation,
} from "@/lib/explorer/url";
import { useLoader } from "@/lib/explorer/use-loader";

export interface VersionHint {
  recordId: string;
  from: FrameworkVersion;
  to: FrameworkVersion;
  ctx: ExplorerContext;
}

/** Set when a crosswalk link is followed, so the destination can offer a way back. */
export interface CrosswalkReturn {
  fromHref: string;
  fromLabel: string;
  row: number;
  /** "{version}/{element_id}" of the record that was opened. */
  toKey: string;
}

interface ExplorerState {
  loc: ExplorerLocation;
  /** Framework version being browsed (the path version for records; default when invalid). */
  version: FrameworkVersion;
  ctx: ExplorerContext;
  elements: ElementSummary[] | undefined;
  elementsStatus: "loading" | "success" | "error";
  elementsError: ApiError | undefined;
  reloadElements: () => void;
  /** The open record's summary, once the element list has loaded. */
  selected: ElementSummary | undefined;
  expanded: ReadonlySet<string>;
  toggleExpanded: (id: string, open?: boolean) => void;
  openRecord: (el: ElementSummary, opts?: { keyboard?: boolean }) => void;
  setVersion: (v: FrameworkVersion) => Promise<void>;
  updateContext: (patch: Partial<ExplorerContext>) => void;
  clearFilters: (opts?: { query?: boolean }) => void;
  hrefFor: (el: ElementSummary) => string;
  /** Href of the browse view with the current context (for "Back to results"). */
  backHref: string;
  versionHint: VersionHint | null;
  crosswalkReturn: CrosswalkReturn | null;
  followCrosswalk: (ret: CrosswalkReturn) => void;
  requestRecordFocus: () => void;
  consumeRecordFocus: () => boolean;
  replaceWithCanonical: (elementId: string) => void;
}

const Ctx = createContext<ExplorerState | null>(null);

export function useExplorer(): ExplorerState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useExplorer must be used inside <ExplorerProvider>");
  return v;
}

const clean = (c: ExplorerContext): ExplorerContext => {
  const out: ExplorerContext = {};
  if (c.level) out.level = c.level;
  if (c.fn) out.fn = c.fn;
  if (c.cat) out.cat = c.cat;
  const q = c.q?.trim().slice(0, MAX_QUERY_LENGTH);
  if (q) out.q = q;
  return out;
};

export function ExplorerProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const loc = useMemo(() => parseLocation(pathname, searchParams), [pathname, searchParams]);
  const version: FrameworkVersion = loc.version ?? DEFAULT_VERSION;
  const ctx = loc.ctx;

  const list = useLoader(`elements:${version}`, () => loadElements(version));
  const elements = list.data;
  const selected = useMemo(
    () => (loc.kind === "record" && elements ? findElement(elements, loc.recordId) : undefined),
    [loc, elements],
  );

  // Warm the other framework so switching versions is instant and filters can be reconciled.
  useEffect(() => {
    void loadElements(version === "2.0" ? "1.1" : "2.0").catch(() => {});
  }, [version]);

  const expanded = useExpanded(version);
  const toggleExpanded = useCallback(
    (id: string, open?: boolean) => storeToggle(version, id, open),
    [version],
  );

  const [versionHint, setHint] = useState<VersionHint | null>(null);
  const [crosswalkReturn, setCrosswalkReturn] = useState<CrosswalkReturn | null>(null);
  const focusRecord = useRef(false);

  const navigateContext = useCallback(
    (next: ExplorerContext, mode: "push" | "replace") => {
      const href =
        loc.kind === "record" && loc.version
          ? recordHref(loc.version, loc.recordId, next)
          : listHref(version, next);
      if (mode === "replace") router.replace(href, { scroll: false });
      else router.push(href, { scroll: false });
    },
    [loc, version, router],
  );

  const updateContext = useCallback(
    (patch: Partial<ExplorerContext>) => {
      const next: ExplorerContext = { ...ctx, ...patch };
      for (const k of Object.keys(next) as (keyof ExplorerContext)[]) {
        if (next[k] === undefined || next[k] === "") delete next[k];
      }
      if (elements) {
        if (patch.cat) {
          const c = elements.find((e) => e.element_id === patch.cat);
          if (c) next.fn = c.function_id;
        }
        if (patch.fn !== undefined) {
          const c = next.cat ? elements.find((e) => e.element_id === next.cat) : undefined;
          if (c && c.function_id !== next.fn) delete next.cat;
        }
      }
      if (next.level === "function") delete next.cat;
      navigateContext(clean(next), "replace");
    },
    [ctx, elements, navigateContext],
  );

  const clearFilters = useCallback(
    (opts?: { query?: boolean }) => {
      navigateContext(opts?.query ? {} : { q: ctx.q }, "replace");
    },
    [ctx.q, navigateContext],
  );

  const openRecord = useCallback(
    (el: ElementSummary, opts?: { keyboard?: boolean }) => {
      if (opts?.keyboard) focusRecord.current = true;
      router.push(recordHref(version, el.element_id, ctx), { scroll: false });
    },
    [router, version, ctx],
  );

  const setVersion = useCallback(
    async (v: FrameworkVersion) => {
      if (v === version && loc.kind === "list") return;
      // Filters only carry over when they exist in the target framework (IDs are not equivalent).
      const target = await loadElements(v).catch(() => null);
      const next = sanitizeContext(ctx, target);
      if (loc.kind === "record") {
        setHint({ recordId: selected?.original_id ?? loc.recordId, from: version, to: v, ctx: next });
      } else {
        setHint(null);
      }
      router.push(listHref(v, next), { scroll: false });
    },
    [version, loc, ctx, selected, router],
  );

  const replaceWithCanonical = useCallback(
    (elementId: string) => {
      if (loc.kind === "record" && loc.version) {
        router.replace(recordHref(loc.version, elementId, ctx), { scroll: false });
      }
    },
    [loc, ctx, router],
  );

  const value: ExplorerState = {
    loc,
    version,
    ctx,
    elements,
    elementsStatus: list.status === "error" ? "error" : list.status === "success" ? "success" : "loading",
    elementsError: list.error,
    reloadElements: list.reload,
    selected,
    expanded,
    toggleExpanded,
    openRecord,
    setVersion,
    updateContext,
    clearFilters,
    hrefFor: (el) => recordHref(version, el.element_id, ctx),
    backHref: listHref(version, ctx),
    versionHint,
    crosswalkReturn,
    followCrosswalk: setCrosswalkReturn,
    requestRecordFocus: () => {
      focusRecord.current = true;
    },
    consumeRecordFocus: () => {
      const v = focusRecord.current;
      focusRecord.current = false;
      return v;
    },
    replaceWithCanonical,
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
