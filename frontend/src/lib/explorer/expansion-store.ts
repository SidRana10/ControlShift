import { useMemo, useSyncExternalStore } from "react";
import type { FrameworkVersion } from "@/lib/api/types";
import { FUNCTION_ORDER } from "./hierarchy";

/**
 * Which tree branches are expanded, per framework version, kept in sessionStorage (UI state only;
 * the URL stays the source of truth for what is being browsed). Built on useSyncExternalStore so
 * the server render and first client render agree (defaults), then the stored state applies.
 */
const KEY = "controlshift.explorer.expanded";
type Stored = Partial<Record<FrameworkVersion, string[]>>;
const EMPTY: Stored = {};
const listeners = new Set<() => void>();
let memoryRaw: string | null = null; // used if sessionStorage is unavailable
let cache: { raw: string | null; value: Stored } = { raw: null, value: EMPTY };

function readRaw(): string | null {
  if (memoryRaw !== null) return memoryRaw;
  try {
    return window.sessionStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function snapshot(): Stored {
  const raw = readRaw();
  if (raw !== cache.raw) {
    let value: Stored = EMPTY;
    try {
      const parsed = raw ? (JSON.parse(raw) as unknown) : EMPTY;
      if (parsed && typeof parsed === "object") value = parsed as Stored;
    } catch {
      value = EMPTY;
    }
    cache = { raw, value };
  }
  return cache.value;
}

function write(next: Stored) {
  const raw = JSON.stringify(next);
  memoryRaw = raw;
  try {
    window.sessionStorage.setItem(KEY, raw);
  } catch {
    // keep the in-memory copy only
  }
  listeners.forEach((l) => l());
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export const defaultExpanded = (version: FrameworkVersion): string[] => [FUNCTION_ORDER[version][0]];

export function useExpanded(version: FrameworkVersion): ReadonlySet<string> {
  const stored = useSyncExternalStore(subscribe, snapshot, () => EMPTY);
  const list = stored[version];
  return useMemo(() => new Set(list ?? defaultExpanded(version)), [list, version]);
}

function current(version: FrameworkVersion): Set<string> {
  return new Set(snapshot()[version] ?? defaultExpanded(version));
}

export function toggleExpanded(version: FrameworkVersion, id: string, open?: boolean) {
  const set = current(version);
  const next = open ?? !set.has(id);
  if (next === set.has(id)) return;
  if (next) set.add(id);
  else set.delete(id);
  write({ ...snapshot(), [version]: [...set] });
}

export function expandAll(version: FrameworkVersion, ids: string[]) {
  const set = current(version);
  const before = set.size;
  ids.forEach((i) => set.add(i));
  if (set.size !== before) write({ ...snapshot(), [version]: [...set] });
}

/** Test helper. */
export function resetExpansion() {
  memoryRaw = null;
  cache = { raw: null, value: EMPTY };
  try {
    window.sessionStorage.removeItem(KEY);
  } catch {
    // ignore
  }
  listeners.forEach((l) => l());
}
