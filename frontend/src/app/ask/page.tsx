import type { Metadata } from "next";
import Link from "next/link";
import { Notice } from "@/components/shared/notice";
import { buttonVariants } from "@/components/ui/button";

export const metadata: Metadata = { title: "Ask ControlShift" };

export default function AskPage() {
  return (
    <div className="mx-auto w-full max-w-[720px] px-4 py-8 min-[900px]:px-10 min-[900px]:py-12">
      <Notice variant="info" title="Ask ControlShift is in development">
        <p>
          This workspace will answer questions about NIST CSF 1.1, CSF 2.0 and the official
          crosswalk using retrieved NIST evidence. Each answer will list its citations, show the
          evidence behind them, and say so when the evidence is not sufficient to answer.
        </p>
        <p className="mt-2">
          The interface is not built yet. This page does not send questions to any model, and
          nothing here is a generated answer.
        </p>
      </Notice>
      <p className="mt-6 text-body text-fg-2">
        In the meantime, the official records are available without AI in Control Explorer.
      </p>
      <Link href="/explorer" className={buttonVariants({ variant: "outline", className: "mt-3" })}>
        Open Control Explorer
      </Link>
    </div>
  );
}
