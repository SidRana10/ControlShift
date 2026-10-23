"use client";

import { ChevronDown, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  LEVEL_LABEL,
  categoriesOf,
  functionsOf,
} from "@/lib/explorer/hierarchy";
import { LEVELS, hasFilters, isLevel } from "@/lib/explorer/url";
import { cn } from "@/lib/utils";
import { useExplorer } from "./explorer-provider";

function FilterSelect({
  label,
  value,
  onChange,
  children,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <div className="relative min-w-0 flex-1">
      <select
        aria-label={label}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "h-11 w-full appearance-none truncate rounded-md border border-border-strong bg-surface pr-5 pl-1.5 text-ui-sm min-[900px]:h-7 min-[900px]:pl-2",
          value ? "text-fg-1" : "text-fg-2",
          "disabled:text-fg-4",
        )}
      >
        {children}
      </select>
      <ChevronDown
        aria-hidden="true"
        strokeWidth={1.5}
        className="pointer-events-none absolute top-1/2 right-1 size-3.5 -translate-y-1/2 text-fg-3"
      />
    </div>
  );
}

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <span className="inline-flex h-11 max-w-full items-center gap-1 rounded-md border border-border bg-surface-sunken pl-3 text-caption text-fg-1 min-[900px]:h-6 min-[900px]:pl-2">
      <span className="truncate">{label}</span>
      <button
        type="button"
        aria-label={`Remove filter: ${label}`}
        onClick={onRemove}
        className="flex size-11 shrink-0 items-center justify-center rounded-md text-fg-3 hover:text-fg-1 min-[900px]:size-6"
      >
        <X aria-hidden="true" strokeWidth={1.5} className="size-3" />
      </button>
    </span>
  );
}

/** Level / Function / Category filters for the selected framework, with removable active chips. */
export function FilterBar() {
  const { ctx, elements, updateContext, clearFilters, version } = useExplorer();
  const functions = elements ? functionsOf(elements) : [];
  const categories = elements ? categoriesOf(elements, ctx.fn) : [];
  const fnName = functions.find((f) => f.element_id === ctx.fn);
  const catName = elements?.find((e) => e.element_id === ctx.cat);

  return (
    <div className="mt-2 space-y-2">
      <div className="flex gap-1.5" role="group" aria-label={`Filters for CSF ${version}`}>
        <FilterSelect
          label="Level"
          value={ctx.level ?? ""}
          onChange={(v) => updateContext({ level: isLevel(v) ? v : undefined })}
        >
          <option value="">Level</option>
          {LEVELS.map((l) => (
            <option key={l} value={l}>
              {LEVEL_LABEL[l]}
            </option>
          ))}
        </FilterSelect>
        <FilterSelect
          label="Function"
          value={ctx.fn ?? ""}
          disabled={!elements}
          onChange={(v) => updateContext({ fn: v || undefined })}
        >
          <option value="">Function</option>
          {functions.map((f) => (
            <option key={f.element_id} value={f.element_id}>
              {f.original_id} {f.name}
            </option>
          ))}
        </FilterSelect>
        <FilterSelect
          label="Category"
          value={ctx.cat ?? ""}
          disabled={!elements || ctx.level === "function"}
          onChange={(v) => updateContext({ cat: v || undefined })}
        >
          <option value="">Category</option>
          {categories.map((c) => (
            <option key={c.element_id} value={c.element_id}>
              {c.original_id} {c.name}
            </option>
          ))}
        </FilterSelect>
      </div>
      {hasFilters(ctx) && (
        <div className="flex flex-wrap items-center gap-1.5">
          {ctx.level && (
            <Chip label={`Level: ${LEVEL_LABEL[ctx.level]}`} onRemove={() => updateContext({ level: undefined })} />
          )}
          {ctx.fn && (
            <Chip
              label={`Function: ${ctx.fn}${fnName?.name ? ` ${fnName.name}` : ""}`}
              onRemove={() => updateContext({ fn: undefined })}
            />
          )}
          {ctx.cat && (
            <Chip
              label={`Category: ${ctx.cat}${catName?.name ? ` ${catName.name}` : ""}`}
              onRemove={() => updateContext({ cat: undefined })}
            />
          )}
          <Button variant="ghost" size="sm" className="h-11 px-3 text-caption min-[900px]:h-6 min-[900px]:px-2" onClick={() => clearFilters()}>
            Clear filters
          </Button>
        </div>
      )}
    </div>
  );
}
