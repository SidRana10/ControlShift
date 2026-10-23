"use client";

import { Radio } from "@base-ui/react/radio";
import { RadioGroup } from "@base-ui/react/radio-group";
import type { FrameworkVersion } from "@/lib/api/types";
import { VERSIONS } from "@/lib/explorer/url";
import { cn } from "@/lib/utils";
import { useExplorer } from "./explorer-provider";

const INK: Record<FrameworkVersion, string> = {
  "2.0": "data-checked:shadow-[inset_0_-2px_0_var(--cs-v20)]",
  "1.1": "data-checked:shadow-[inset_0_-2px_0_var(--cs-v11)]",
};

/**
 * Framework version selector: a single-selection radio group styled as a segmented control.
 * Exactly one version is always selected; arrow keys move and select (Base UI radio behaviour).
 */
export function VersionToggle() {
  const { version, setVersion } = useExplorer();
  return (
    <RadioGroup
      aria-label="Framework version"
      value={version}
      onValueChange={(v) => void setVersion(v as FrameworkVersion)}
      className="inline-flex items-center gap-0.5 rounded-full bg-surface-sunken p-0.5"
    >
      {VERSIONS.map((v) => (
        <Radio.Root
          key={v}
          value={v}
          className={cn(
            "relative inline-flex h-6 cursor-pointer items-center rounded-full border border-transparent px-3 text-ui-sm font-medium whitespace-nowrap text-fg-2 select-none",
            "after:absolute after:inset-x-0 after:-inset-y-3 after:content-['']",
            "hover:text-fg-1 data-checked:border-border data-checked:bg-surface data-checked:text-fg-1",
            INK[v],
          )}
        >
          CSF {v}
        </Radio.Root>
      ))}
    </RadioGroup>
  );
}
