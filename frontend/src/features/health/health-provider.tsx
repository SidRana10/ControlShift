"use client";

import { createContext, useContext, useMemo } from "react";
import { getHealth } from "@/lib/api/client";
import type { HealthResponse } from "@/lib/api/types";
import { useApi } from "@/lib/api/use-api";

export type HealthState =
  | { status: "checking" }
  | { status: "online"; health: HealthResponse }
  | { status: "unreachable" };

const HealthContext = createContext<HealthState>({ status: "checking" });

const POLL_MS = 30_000;

/** One /health poll for the whole shell; the sidebar status reads it. */
export function HealthProvider({ children }: { children: React.ReactNode }) {
  const { state } = useApi(getHealth, POLL_MS);
  const value = useMemo<HealthState>(() => {
    if (state.status === "success") return { status: "online", health: state.data };
    if (state.status === "error") return { status: "unreachable" };
    return { status: "checking" };
  }, [state]);
  return <HealthContext.Provider value={value}>{children}</HealthContext.Provider>;
}

export const useHealth = () => useContext(HealthContext);
