import type { AnchorHTMLAttributes } from "react";
import { navigate } from "./next-navigation";

/** Minimal next/link: a real anchor that pushes onto the in-memory history. */
export default function Link({
  href,
  onClick,
  ...rest
}: { href: string } & AnchorHTMLAttributes<HTMLAnchorElement>) {
  return (
    <a
      href={href}
      onClick={(e) => {
        onClick?.(e);
        if (e.defaultPrevented || e.button !== 0) return;
        e.preventDefault();
        navigate(href, "push");
      }}
      {...rest}
    />
  );
}
