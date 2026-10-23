import { GitCompareArrows, LayoutGrid, Library, MessageSquareText } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  /** Header title for the route. */
  title: string;
  icon: LucideIcon;
  /** Small tag shown beside the label when the destination is not complete. */
  tag?: string;
}

/** Order and icons are fixed by docs/frontend-design-spec.md section 4. */
export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Overview", title: "Overview", icon: LayoutGrid },
  { href: "/ask", label: "Ask ControlShift", title: "Ask ControlShift", icon: MessageSquareText },
  { href: "/explorer", label: "Control Explorer", title: "Control Explorer", icon: Library },
  {
    href: "/compare",
    label: "Compare Frameworks",
    title: "Compare Frameworks",
    icon: GitCompareArrows,
    tag: "Soon",
  },
];

export function isActive(href: string, pathname: string): boolean {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function titleFor(pathname: string): string {
  return NAV_ITEMS.find((i) => isActive(i.href, pathname))?.title ?? "Page not found";
}
