import {
  getElement,
  getVersions,
  listElements,
  type ListElementsParams,
} from "@/lib/api/client";
import type {
  ElementDetail,
  ElementList,
  ElementSummary,
  FrameworkVersion,
  VersionList,
} from "@/lib/api/types";

/**
 * Small request cache: identical requests are shared and reused, failed requests are forgotten so
 * Retry really retries. Reference data (about 270 records) is static for the life of the page.
 */
const caches = {
  elements: new Map<FrameworkVersion, Promise<ElementSummary[]>>(),
  versions: { current: null as Promise<VersionList> | null },
  search: new Map<string, Promise<ElementList>>(),
  detail: new Map<string, Promise<ElementDetail>>(),
};

function remember<K, V>(map: Map<K, Promise<V>>, key: K, make: () => Promise<V>): Promise<V> {
  const hit = map.get(key);
  if (hit) return hit;
  const p = make();
  map.set(key, p);
  p.catch(() => {
    if (map.get(key) === p) map.delete(key);
  });
  return p;
}

export const loadElements = (version: FrameworkVersion) =>
  remember(caches.elements, version, async () => (await listElements({ version })).elements);

export function loadVersions(): Promise<VersionList> {
  if (!caches.versions.current) {
    const p = getVersions();
    caches.versions.current = p;
    p.catch(() => {
      if (caches.versions.current === p) caches.versions.current = null;
    });
  }
  return caches.versions.current;
}

export const searchElements = (params: ListElementsParams) =>
  remember(caches.search, JSON.stringify(params), () => listElements(params));

export const loadDetail = (version: FrameworkVersion, id: string) =>
  remember(caches.detail, `${version}/${id}`, () => getElement(version, id));

export function clearCatalogCache() {
  caches.elements.clear();
  caches.versions.current = null;
  caches.search.clear();
  caches.detail.clear();
}
