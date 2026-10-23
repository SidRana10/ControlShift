"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/client";

export type LoaderResult<T> = {
  status: "idle" | "loading" | "success" | "error";
  /** Latest successful data, kept while a new key loads so lists do not blank between requests. */
  data: T | undefined;
  error: ApiError | undefined;
  reload: () => void;
};

interface Settled<T> {
  key: string;
  attempt: number;
  data: T | undefined;
  error: ApiError | undefined;
}

/**
 * Loads `loader()` whenever `key` changes (null = idle). A response is stored together with the key
 * it answers, and only a response for the current key is reported as settled, so a slow earlier
 * request can never overwrite newer results.
 */
export function useLoader<T>(key: string | null, loader: () => Promise<T>): LoaderResult<T> {
  const [settled, setSettled] = useState<Settled<T> | null>(null);
  const [lastData, setLastData] = useState<T | undefined>(undefined);
  const [attempt, setAttempt] = useState(0);
  const loaderRef = useRef(loader);

  useEffect(() => {
    loaderRef.current = loader;
  });

  useEffect(() => {
    if (key === null) return;
    let live = true;
    loaderRef
      .current()
      .then((data) => {
        if (!live) return;
        setSettled({ key, attempt, data, error: undefined });
        setLastData(data);
      })
      .catch((err: unknown) => {
        if (!live) return;
        const error =
          err instanceof ApiError
            ? err
            : new ApiError("unexpected", "The API returned an unexpected response.");
        setSettled({ key, attempt, data: undefined, error });
      });
    return () => {
      live = false;
    };
  }, [key, attempt]);

  const reload = useCallback(() => setAttempt((n) => n + 1), []);

  if (key === null) return { status: "idle", data: undefined, error: undefined, reload };
  if (!settled || settled.key !== key || settled.attempt !== attempt) {
    return { status: "loading", data: lastData, error: undefined, reload };
  }
  if (settled.error) return { status: "error", data: lastData, error: settled.error, reload };
  return { status: "success", data: settled.data, error: undefined, reload };
}
