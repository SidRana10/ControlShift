import { AlertCircle, CircleDashed, Info, Split } from "lucide-react";
import { cn } from "@/lib/utils";

const VARIANTS = {
  info: { icon: Info, box: "bg-neutral-notice-soft", edge: "bg-neutral-notice", tone: "text-fg-2" },
  "no-reference": {
    icon: CircleDashed,
    box: "bg-neutral-notice-soft",
    edge: "bg-neutral-notice",
    tone: "text-fg-2",
  },
  ambiguous: { icon: Split, box: "bg-ambiguous-soft", edge: "bg-ambiguous", tone: "text-ambiguous" },
  error: { icon: AlertCircle, box: "bg-error-soft", edge: "bg-error", tone: "text-error" },
} as const;

export type NoticeVariant = keyof typeof VARIANTS;

/** Inline notice: soft fill, 3px left edge in the variant colour, icon + title + body. */
export function Notice({
  variant = "info",
  title,
  children,
  actions,
  className,
}: {
  variant?: NoticeVariant;
  title: string;
  children?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  const v = VARIANTS[variant];
  const Icon = v.icon;
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={cn("relative rounded-lg py-3 pr-4 pl-5", v.box, className)}
    >
      <span aria-hidden="true" className={cn("absolute inset-y-0 left-0 w-[3px] rounded-l-lg", v.edge)} />
      <div className="flex gap-3">
        <Icon aria-hidden="true" className={cn("mt-0.5 size-4 shrink-0", v.tone)} strokeWidth={1.5} />
        <div className="min-w-0 flex-1">
          <p className="text-title-sm font-semibold text-fg-1">{title}</p>
          {children && <div className="mt-1 text-body text-fg-2">{children}</div>}
          {actions && <div className="mt-3 flex flex-wrap gap-2">{actions}</div>}
        </div>
      </div>
    </div>
  );
}
