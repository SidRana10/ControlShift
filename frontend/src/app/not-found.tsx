import type { Metadata } from "next";
import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export const metadata: Metadata = { title: "Page not found" };

// The shell header already provides the page's h1 ("Page not found") for unknown routes.
export default function NotFound() {
  return (
    <div className="mx-auto w-full max-w-[720px] px-4 py-8 min-[900px]:px-10 min-[900px]:py-12">
      <h2 className="text-name-lg font-semibold text-fg-1">This page doesn&apos;t exist</h2>
      <p className="mt-2 text-body text-fg-2">
        The address may be mistyped, or the page may have moved. Use the navigation to open one of
        the ControlShift sections, or return to the overview.
      </p>
      <Link href="/" className={buttonVariants({ variant: "outline", className: "mt-6" })}>
        Back to Overview
      </Link>
    </div>
  );
}
