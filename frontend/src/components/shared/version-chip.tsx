import { cn } from "@/lib/utils";
import type { FrameworkVersion } from "@/lib/api/types";

const STYLES: Record<FrameworkVersion, string> = {
  "2.0": "bg-v20-soft border-v20-border text-v20",
  "1.1": "bg-v11-soft border-v11-border text-v11",
};

/** Version identity chip. Version ink is used for identity only, never for status. */
export function VersionChip({
  version,
  className,
}: {
  version: FrameworkVersion;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 font-mono text-label leading-4 font-medium",
        STYLES[version],
        className,
      )}
    >
      {version}
    </span>
  );
}
