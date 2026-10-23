"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { NAV_ITEMS, isActive } from "@/lib/navigation";
import { cn } from "@/lib/utils";

/**
 * The four destinations. `docked` items visually hide their labels in the rail (`.rail-sr`, still
 * the accessible name, including the "Soon" tag) and show a tooltip instead; `showTooltips` is true only while the docked sidebar is actually a rail.
 */
export function SidebarNav({
  docked,
  showTooltips = false,
  onNavigate,
}: {
  docked: boolean;
  showTooltips?: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary" className="flex flex-col gap-0.5 px-2 py-2">
      {NAV_ITEMS.map((item) => {
        const active = isActive(item.href, pathname);
        const Icon = item.icon;
        const link = (
          <Link
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex h-11 items-center gap-2 rounded-md pr-1.5 pl-3 text-ui-sm font-medium min-[900px]:h-8",
              active
                ? "bg-surface text-fg-1 shadow-[0_0_0_1px_var(--cs-border)]"
                : "text-fg-2 hover:bg-surface-hover hover:text-fg-1 active:bg-surface-pressed",
            )}
          >
            <Icon
              aria-hidden="true"
              strokeWidth={1.5}
              className={cn("size-4 shrink-0", active ? "text-fg-1" : "text-fg-3")}
            />
            <span className={cn("min-w-0 flex-1 truncate", docked && "rail-sr")}>{item.label}</span>
            {item.tag && (
              <span
                className={cn(
                  "rounded-sm bg-surface-hover px-1 text-label font-normal text-fg-3",
                  docked && "rail-sr",
                )}
              >
                {item.tag}
              </span>
            )}
          </Link>
        );
        if (!showTooltips) return <div key={item.href}>{link}</div>;
        return (
          <Tooltip key={item.href}>
            <TooltipTrigger render={link} />
            <TooltipContent side="right" sideOffset={8}>
              {item.label}
              {item.tag ? ` (${item.tag})` : ""}
            </TooltipContent>
          </Tooltip>
        );
      })}
    </nav>
  );
}
