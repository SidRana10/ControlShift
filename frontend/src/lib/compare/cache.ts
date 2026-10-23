import { listCrosswalk, type CrosswalkParams } from "@/lib/api/client";
import type { CrosswalkList } from "@/lib/api/types";

/** Identical /crosswalk requests are shared; failures are forgotten so Retry really retries. */
const cache = new Map<string, Promise<CrosswalkList>>();

export function loadCrosswalk(params: CrosswalkParams): Promise<CrosswalkList> {
  const key = JSON.stringify(params);
  const hit = cache.get(key);
  if (hit) return hit;
  const p = listCrosswalk(params);
  cache.set(key, p);
  p.catch(() => {
    if (cache.get(key) === p) cache.delete(key);
  });
  return p;
}

export const clearCrosswalkCache = () => cache.clear();
