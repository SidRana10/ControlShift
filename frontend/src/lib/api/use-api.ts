"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "./client";

export type ApiState<T> =
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; error: ApiError };

/**
 * Runs `fetcher` on mount (and on `reload`), aborting the in-flight request on unmount.
 * `intervalMs` re-fetches quietly in the background; the previous result stays visible meanwhile.
 */
export function useApi<T>(fetcher: (signal: AbortSignal) => Promise<T>, intervalMs?: number) {
  const [state, setState] = useState<ApiState<T>>({ status: "loading" });
  const fetcherRef = useRef(fetcher);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    fetcherRef.current = fetcher;
  });

  useEffect(() => {
    const controller = new AbortController();
    fetcherRef
      .current(controller.signal)
      .then((data) => setState({ status: "success", data }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const error =
          err instanceof ApiError
            ? err
            : new ApiError("unexpected", "The API returned an unexpected response.");
        setState({ status: "error", error });
      });
    return () => controller.abort();
  }, [tick]);

  useEffect(() => {
    if (!intervalMs) return;
    const id = setInterval(() => setTick((t) => t + 1), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  const reload = useCallback(() => {
    setState({ status: "loading" });
    setTick((t) => t + 1);
  }, []);

  return { state, reload };
}
