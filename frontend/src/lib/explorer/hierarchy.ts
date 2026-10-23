import type { ElementLevel, ElementSummary, FrameworkVersion } from "@/lib/api/types";
import type { ExplorerContext } from "./url";

/** Official NIST function order (display constant; the API orders by element_id). */
export const FUNCTION_ORDER: Record<FrameworkVersion, string[]> = {
  "2.0": ["GV", "ID", "PR", "DE", "RS", "RC"],
  "1.1": ["ID", "PR", "DE", "RS", "RC"],
};

function fnRank(version: FrameworkVersion, functionId: string): number {
  const i = FUNCTION_ORDER[version].indexOf(functionId);
  return i === -1 ? FUNCTION_ORDER[version].length : i;
}

/** NIST function order first, then element_id: deterministic for every list the UI shows. */
export function compareElements(a: ElementSummary, b: ElementSummary): number {
  return (
    fnRank(a.version, a.function_id) - fnRank(b.version, b.function_id) ||
    a.function_id.localeCompare(b.function_id) ||
    a.element_id.localeCompare(b.element_id)
  );
}

export const sortElements = (els: ElementSummary[]) => [...els].sort(compareElements);

export interface TreeNode {
  element: ElementSummary;
  children: TreeNode[];
  /** Subcategories at or below this node (a subcategory counts itself as 0). */
  subcategoryCount: number;
}

/**
 * Builds Function > Category > Subcategory trees. Elements whose parent is not in the set (for
 * example a category shown on its own by a filter) become roots, so filtered trees stay valid.
 */
export function buildTree(elements: ElementSummary[]): TreeNode[] {
  const nodes = new Map<string, TreeNode>();
  for (const e of elements) nodes.set(e.element_id, { element: e, children: [], subcategoryCount: 0 });
  const roots: TreeNode[] = [];
  for (const node of nodes.values()) {
    const parent = node.element.parent_id ? nodes.get(node.element.parent_id) : undefined;
    (parent ? parent.children : roots).push(node);
  }
  const finish = (n: TreeNode): number => {
    n.children.sort((a, b) => compareElements(a.element, b.element));
    n.subcategoryCount = n.children.reduce(
      (sum, c) => sum + (c.element.level === "subcategory" ? 1 : 0) + finish(c),
      0,
    );
    return n.subcategoryCount;
  };
  roots.sort((a, b) => compareElements(a.element, b.element));
  roots.forEach(finish);
  return roots;
}

export interface FlatRow {
  node: TreeNode;
  /** 1 = function, 2 = category, 3 = subcategory (aria-level). */
  depth: number;
  parentId: string | null;
}

/** Depth-first list of the rows that are currently visible given the expanded branches. */
export function flattenVisible(roots: TreeNode[], expanded: ReadonlySet<string>): FlatRow[] {
  const out: FlatRow[] = [];
  const walk = (nodes: TreeNode[], depth: number, parentId: string | null) => {
    for (const node of nodes) {
      out.push({ node, depth, parentId });
      if (node.children.length && expanded.has(node.element.element_id)) {
        walk(node.children, depth + 1, node.element.element_id);
      }
    }
  };
  walk(roots, 1, null);
  return out;
}

export function indexById(elements: ElementSummary[]): Map<string, ElementSummary> {
  return new Map(elements.map((e) => [e.element_id, e]));
}

/** Parent chain, nearest first. */
export function ancestorsOf(el: ElementSummary, byId: Map<string, ElementSummary>): ElementSummary[] {
  const out: ElementSummary[] = [];
  let cur = el.parent_id ? byId.get(el.parent_id) : undefined;
  while (cur) {
    out.push(cur);
    cur = cur.parent_id ? byId.get(cur.parent_id) : undefined;
  }
  return out;
}

/** Finds a record by canonical or printed ID, case-insensitively. */
export function findElement(elements: ElementSummary[], id: string): ElementSummary | undefined {
  const u = id.trim().toUpperCase();
  return (
    elements.find((e) => e.element_id.toUpperCase() === u) ??
    elements.find((e) => e.original_id.toUpperCase() === u)
  );
}

type Filters = Pick<ExplorerContext, "level" | "fn" | "cat">;

/** Same semantics as GET /catalog/elements for level / function / category (exact match). */
export function filterElements(elements: ElementSummary[], f: Filters): ElementSummary[] {
  return elements.filter(
    (e) =>
      (!f.level || e.level === f.level) &&
      (!f.fn || e.function_id === f.fn) &&
      (!f.cat || e.category_id === f.cat),
  );
}

/** Drops filters that cannot apply: unknown function/category, category outside the function, or
 *  a category filter combined with level=function (functions have no category). */
export function sanitizeContext(ctx: ExplorerContext, elements: ElementSummary[] | null): ExplorerContext {
  const out: ExplorerContext = { ...ctx };
  if (!elements) {
    delete out.fn;
    delete out.cat;
    return out;
  }
  const fnIds = new Set(elements.filter((e) => e.level === "function").map((e) => e.element_id));
  const cats = new Map(elements.filter((e) => e.level === "category").map((e) => [e.element_id, e]));
  if (out.fn && !fnIds.has(out.fn)) delete out.fn;
  if (out.cat) {
    const c = cats.get(out.cat);
    if (!c || (out.fn && c.function_id !== out.fn)) delete out.cat;
  }
  if (out.level === "function") delete out.cat;
  return out;
}

export const functionsOf = (els: ElementSummary[]) =>
  sortElements(els.filter((e) => e.level === "function"));

export const categoriesOf = (els: ElementSummary[], fn?: string) =>
  sortElements(els.filter((e) => e.level === "category" && (!fn || e.function_id === fn)));

const norm = (s: string) => s.trim().toLowerCase();

export function isExactIdMatch(el: ElementSummary, q: string): boolean {
  const n = norm(q);
  return n !== "" && (norm(el.element_id) === n || norm(el.original_id) === n);
}

/** Display order for search results: an exact ID match first, then NIST order. */
export function orderSearchResults(results: ElementSummary[], q: string) {
  const sorted = sortElements(results);
  const exact = sorted.filter((e) => isExactIdMatch(e, q));
  const rest = sorted.filter((e) => !isExactIdMatch(e, q));
  return { elements: [...exact, ...rest], exactIds: new Set(exact.map((e) => e.element_id)) };
}

export interface TextPart {
  text: string;
  match: boolean;
}

/** Splits text on case-insensitive occurrences of q, for highlighting (display only). */
export function splitHighlight(text: string, q: string): TextPart[] {
  const needle = q.trim().toLowerCase();
  if (!needle) return [{ text, match: false }];
  const parts: TextPart[] = [];
  const hay = text.toLowerCase();
  let i = 0;
  for (;;) {
    const at = hay.indexOf(needle, i);
    if (at === -1) break;
    if (at > i) parts.push({ text: text.slice(i, at), match: false });
    parts.push({ text: text.slice(at, at + needle.length), match: true });
    i = at + needle.length;
  }
  if (i < text.length) parts.push({ text: text.slice(i), match: false });
  return parts.length ? parts : [{ text, match: false }];
}

export const LEVEL_LABEL: Record<ElementLevel, string> = {
  function: "Function",
  category: "Category",
  subcategory: "Subcategory",
};

/** Title for an element in lists: name when present, otherwise the official description. */
export const elementTitle = (e: ElementSummary): string | null => e.name ?? e.description;
