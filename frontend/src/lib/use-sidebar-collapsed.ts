"use client";

import { useCallback, useSyncExternalStore } from "react";
import { SIDEBAR_STORAGE_KEY } from "./sidebar-preference";

const listeners = new Set<() => void>();
let memory: boolean | null = null; // used when storage is unavailable

function read(): boolean {
  if (memory !== null) return memory;
  try {
    return window.localStorage.getItem(SIDEBAR_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

/** Mirrors the preference onto <html>; CSS reads it (the inline script in layout.tsx sets it first). */
function applyAttribute() {
  const root = document.documentElement;
  if (read()) root.dataset.sidebar = "collapsed";
  else delete root.dataset.sidebar;
}

function onStorage() {
  memory = null;
  applyAttribute();
  listeners.forEach((l) => l());
}

function subscribe(onChange: () => void) {
  listeners.add(onChange);
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(onChange);
    window.removeEventListener("storage", onStorage);
  };
}

/**
 * Desktop collapse preference, persisted per browser. The returned value is only used for labels;
 * layout comes from the <html data-sidebar> attribute so there is no width jump on load.
 */
export function useSidebarCollapsed(): [boolean, () => void] {
  const collapsed = useSyncExternalStore(subscribe, read, () => false);
  const toggle = useCallback(() => {
    const next = !read();
    memory = next;
    try {
      window.localStorage.setItem(SIDEBAR_STORAGE_KEY, next ? "1" : "0");
    } catch {
      // Storage unavailable (private mode): the preference simply does not persist.
    }
    applyAttribute();
    listeners.forEach((l) => l());
  }, []);
  return [collapsed, toggle];
}
