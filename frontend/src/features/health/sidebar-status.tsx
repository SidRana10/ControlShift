"use client";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { useHealth } from "./health-provider";

const LABEL = { checking: "Checking API…", online: "API online", unreachable: "API unreachable" };
const DOT = { checking: "bg-fg-4", online: "bg-v20", unreachable: "bg-error" };

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-fg-3">{label}</dt>
      <dd className="text-right font-mono text-id text-fg-1">{value}</dd>
    </div>
  );
}

/**
 * Sidebar footer: reflects the real /health result. Shows only fields that endpoint returns
 * (never secrets). Text hides in the rail via `.rail-hide` (the button keeps an aria-label); the dot always stays visible.
 */
export function SidebarStatus({ docked }: { docked: boolean }) {
  const h = useHealth();
  const text = LABEL[h.status];
  const llmOff = h.status === "online" && !h.health.llm.configured;

  return (
    <Popover>
      <PopoverTrigger
        aria-label={`${text}. Show API status details`}
        className="mx-2 flex min-h-8 items-center gap-2.5 rounded-md py-1.5 pr-2 pl-3 text-left text-ui-sm text-fg-2 hover:bg-surface-hover active:bg-surface-pressed"
      >
        <span aria-hidden="true" className="flex size-4 shrink-0 items-center justify-center">
          <span className={cn("size-2 rounded-full", DOT[h.status])} />
        </span>
        <span className={cn("min-w-0 leading-4", docked && "rail-hide")}>
          <span className={cn("block", h.status === "unreachable" && "text-error")}>{text}</span>
          {llmOff && <span className="block text-caption text-fg-3">LLM not configured</span>}
        </span>
      </PopoverTrigger>
      <PopoverContent side="right" align="end" sideOffset={8} className="w-72">
        <p className="text-ui-sm font-semibold text-fg-1">{text}</p>
        {h.status === "online" ? (
          <dl className="space-y-1.5 text-ui-sm">
            <Row label="Chunks" value={h.health.database.chunks} />
            <Row label="Elements" value={h.health.database.elements} />
            <Row label="Crosswalk rows" value={h.health.database.crosswalk_rows} />
            <Row label="Retrieval mode" value={h.health.retrieval.mode} />
            <Row
              label="LLM"
              value={
                h.health.llm.configured
                  ? [h.health.llm.provider, h.health.llm.model].filter(Boolean).join(" · ")
                  : "not configured"
              }
            />
          </dl>
        ) : (
          <p className="text-ui-sm text-fg-3">
            {h.status === "checking"
              ? "Contacting the ControlShift API…"
              : "The ControlShift API did not respond. Records cannot be loaded until it is running."}
          </p>
        )}
      </PopoverContent>
    </Popover>
  );
}
