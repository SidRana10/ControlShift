import type { Metadata } from "next";
import Link from "next/link";
import { Notice } from "@/components/shared/notice";
import { buttonVariants } from "@/components/ui/button";

export const metadata: Metadata = { title: "Compare Frameworks" };

export default function ComparePage() {
  return (
    <div className="mx-auto w-full max-w-[720px] px-4 py-8 min-[900px]:px-10 min-[900px]:py-12">
      <Notice variant="info" title="Compare Frameworks is coming soon">
        <p>
          This view will let you inspect the official relationships between CSF 1.1 and CSF 2.0:
          one-to-many mappings, conceptually new elements, and entries that need interpretation.
        </p>
        <p className="mt-2">
          It depends on an API for listing the full crosswalk, which does not exist yet. No
          comparison data is shown on this page.
        </p>
      </Notice>
      <Link href="/explorer" className={buttonVariants({ variant: "outline", className: "mt-6" })}>
        Open Control Explorer
      </Link>
    </div>
  );
}
