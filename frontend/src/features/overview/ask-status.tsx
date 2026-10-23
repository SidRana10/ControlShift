"use client";

import { useHealth } from "@/features/health/health-provider";

/** Tells the visitor, from the real /health result, whether Ask will generate answers here. */
export function AskStatus() {
  const h = useHealth();
  if (h.status === "unreachable") return <span className="text-error">API unreachable</span>;
  if (h.status === "online" && !h.health.llm.configured) {
    return <span>No language model is configured on this server, so Ask returns the retrieved evidence only.</span>;
  }
  return null;
}
