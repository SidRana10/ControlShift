"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, askQuestion } from "@/lib/api/client";
import type { FrameworkVersion } from "@/lib/api/types";
import type { AskResult } from "@/lib/ask/types";

export type AskState =
  | { status: "idle" }
  | { status: "loading"; question: string }
  | { status: "success"; result: AskResult }
  | { status: "error"; error: ApiError; question: string };

/**
 * One in-flight question at a time. A new `submit` aborts the previous request, and every
 * completion is checked against the latest request id, so a slow earlier response can never
 * replace a newer question's state. `submit` is a no-op while a request is loading.
 */
export function useAsk() {
  const [state, setState] = useState<AskState>({ status: "idle" });
  const latest = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const loading = useRef(false);

  useEffect(() => () => controller.current?.abort(), []);

  const submit = useCallback((question: string, version?: FrameworkVersion) => {
    if (loading.current) return;
    const id = ++latest.current;
    const ctl = new AbortController();
    controller.current = ctl;
    loading.current = true;
    setState({ status: "loading", question });
    askQuestion({ question, ...(version ? { version } : {}) }, ctl.signal)
      .then((result) => {
        if (id === latest.current) setState({ status: "success", result });
      })
      .catch((err: unknown) => {
        if (id !== latest.current || ctl.signal.aborted) return;
        const error =
          err instanceof ApiError
            ? err
            : new ApiError("unexpected", "The API returned an unexpected response.");
        setState({ status: "error", error, question });
      })
      .finally(() => {
        if (id === latest.current) loading.current = false;
      });
  }, []);

  /** Aborts any in-flight request and returns to the initial state (Clear and Cancel). */
  const reset = useCallback(() => {
    latest.current++;
    controller.current?.abort();
    loading.current = false;
    setState({ status: "idle" });
  }, []);

  return { state, submit, reset };
}
