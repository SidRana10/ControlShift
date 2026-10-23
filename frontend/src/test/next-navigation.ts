import { useMemo, useSyncExternalStore } from "react";

/** In-memory stand-in for next/navigation with a real history stack (push/replace/back). */
let entries: string[] = ["/"];
let index = 0;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

export function resetNavigation(url: string) {
  entries = [url];
  index = 0;
  emit();
}
export const currentUrl = () => entries[index];
export const historyLength = () => entries.length;
export function go(delta: number) {
  index = Math.max(0, Math.min(entries.length - 1, index + delta));
  emit();
}
export function navigate(url: string, mode: "push" | "replace") {
  if (mode === "replace") entries[index] = url;
  else {
    entries = [...entries.slice(0, index + 1), url];
    index = entries.length - 1;
  }
  emit();
}

const subscribe = (cb: () => void) => {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
};
const useHref = () => useSyncExternalStore(subscribe, currentUrl, currentUrl);

export function usePathname() {
  return useHref().split("?")[0];
}
export function useSearchParams() {
  const href = useHref();
  return useMemo(() => new URLSearchParams(href.split("?")[1] ?? ""), [href]);
}
const router = {
  push: (u: string) => navigate(u, "push"),
  replace: (u: string) => navigate(u, "replace"),
  back: () => go(-1),
  forward: () => go(1),
  refresh: () => {},
  prefetch: () => {},
};
export const useRouter = () => router;
