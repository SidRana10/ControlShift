import { cn } from "@/lib/utils";

/** Centered empty / error / not-found content for a region: title, one line, up to two actions. */
export function StateBlock({
  title,
  children,
  actions,
  className,
}: {
  title: string;
  children?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mx-auto flex max-w-[360px] flex-col items-center py-12 text-center", className)}>
      <p className="text-title-sm font-semibold text-fg-1">{title}</p>
      {children && <p className="mt-1 text-caption text-fg-3">{children}</p>}
      {actions && <div className="mt-4 flex flex-wrap justify-center gap-2">{actions}</div>}
    </div>
  );
}
