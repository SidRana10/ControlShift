import { cn } from "@/lib/utils";

/** Marks verbatim NIST text or workbook content. Solid, black. */
export function SourceTag({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm bg-ink px-1.5 font-mono text-[10px] leading-[14px] font-medium text-white",
        className,
      )}
    >
      NIST
    </span>
  );
}

/** Marks a ControlShift interpretation (not an official field). Dashed border by design. */
export function DerivedTag({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border border-dashed border-derived-border px-1.5 text-label leading-4 font-medium text-derived",
        className,
      )}
    >
      Derived
    </span>
  );
}
