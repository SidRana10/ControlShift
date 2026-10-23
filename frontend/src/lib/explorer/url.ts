import type { ElementLevel, FrameworkVersion } from "@/lib/api/types";

/** Browsing context carried in the URL (docs/frontend-design-spec.md section 8.1). */
export interface ExplorerContext {
  level?: ElementLevel;
  fn?: string;
  cat?: string;
  q?: string;
}

export const DEFAULT_VERSION: FrameworkVersion = "2.0";
export const VERSIONS: FrameworkVersion[] = ["2.0", "1.1"];
export const MAX_QUERY_LENGTH = 200;
export const LEVELS: ElementLevel[] = ["function", "category", "subcategory"];

const FN_RE = /^[A-Za-z]{2}$/;
const CAT_RE = /^[A-Za-z]{2}\.[A-Za-z]{2}$/;

export const isVersion = (v: unknown): v is FrameworkVersion => v === "1.1" || v === "2.0";
export const isLevel = (v: unknown): v is ElementLevel =>
  v === "function" || v === "category" || v === "subcategory";

type Params = { get(name: string): string | null };

/** Reads and validates browsing-context parameters; invalid values are dropped, never thrown. */
export function parseContext(sp: Params): ExplorerContext {
  const ctx: ExplorerContext = {};
  const level = sp.get("level");
  if (isLevel(level)) ctx.level = level;
  const fn = sp.get("fn");
  if (fn && FN_RE.test(fn)) ctx.fn = fn.toUpperCase();
  const cat = sp.get("cat");
  if (cat && CAT_RE.test(cat)) ctx.cat = cat.toUpperCase();
  const q = sp.get("q")?.trim().slice(0, MAX_QUERY_LENGTH);
  if (q) ctx.q = q;
  return ctx;
}

export type ExplorerLocation =
  | { kind: "list"; version: FrameworkVersion; ctx: ExplorerContext }
  | {
      kind: "record";
      /** Version segment exactly as written in the path; null when it is not 1.1 / 2.0. */
      version: FrameworkVersion | null;
      versionParam: string;
      recordId: string;
      ctx: ExplorerContext;
    };

export function parseLocation(pathname: string, sp: Params): ExplorerLocation {
  const ctx = parseContext(sp);
  const m = /^\/explorer\/([^/]+)\/([^/]+)\/?$/.exec(pathname);
  if (m) {
    const versionParam = decodeURIComponent(m[1]);
    return {
      kind: "record",
      version: isVersion(versionParam) ? versionParam : null,
      versionParam,
      recordId: decodeURIComponent(m[2]),
      ctx,
    };
  }
  const v = sp.get("v");
  return { kind: "list", version: isVersion(v) ? v : DEFAULT_VERSION, ctx };
}

function contextQuery(ctx: ExplorerContext, first?: [string, string]): string {
  const qs = new URLSearchParams();
  if (first) qs.set(first[0], first[1]);
  if (ctx.level) qs.set("level", ctx.level);
  if (ctx.fn) qs.set("fn", ctx.fn);
  if (ctx.cat) qs.set("cat", ctx.cat);
  if (ctx.q) qs.set("q", ctx.q);
  const s = qs.toString();
  return s ? `?${s}` : "";
}

/** Browse URL: /explorer?v=2.0&level=…  (the version is always explicit once the user acts). */
export function listHref(version: FrameworkVersion, ctx: ExplorerContext = {}): string {
  return `/explorer${contextQuery(ctx, ["v", version])}`;
}

/** Canonical record URL: /explorer/2.0/GV.SC-03 plus the browsing context. */
export function recordHref(
  version: FrameworkVersion,
  elementId: string,
  ctx: ExplorerContext = {},
): string {
  return `/explorer/${version}/${encodeURIComponent(elementId)}${contextQuery(ctx)}`;
}

export const hasContext = (ctx: ExplorerContext) =>
  Boolean(ctx.level || ctx.fn || ctx.cat || ctx.q);
export const hasFilters = (ctx: ExplorerContext) => Boolean(ctx.level || ctx.fn || ctx.cat);
