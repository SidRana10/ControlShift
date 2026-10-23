import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DerivedTag, SourceTag } from "@/components/shared/source-tags";
import { NAV_ITEMS } from "@/lib/navigation";

export const metadata: Metadata = { title: "Overview" };

const STATUS: Record<string, { tag: string; text: string }> = {
  "/ask": {
    tag: "AI-assisted",
    text: "Ask questions about CSF 1.1, CSF 2.0 and the crosswalk, answered from retrieved NIST evidence with citations.",
  },
  "/explorer": {
    tag: "Official records",
    text: "Browse and search the official CSF 1.1 and CSF 2.0 records, with provenance and the crosswalk rows for each.",
  },
  "/compare": {
    tag: "Official crosswalk",
    text: "Browse the official transition workbook rows and inspect a CSF 2.0 element beside the CSF 1.1 element it references.",
  },
};

export default function OverviewPage() {
  return (
    <div className="mx-auto w-full max-w-[1080px] px-4 py-8 min-[900px]:px-10 min-[900px]:py-12">
      <section className="max-w-[680px]">
        <h2 className="text-name-lg font-semibold text-fg-1">
          Version-aware answers from the NIST Cybersecurity Framework
        </h2>
        <p className="mt-3 text-body text-fg-2">
          ControlShift covers NIST CSF 1.1, NIST CSF 2.0 and the official NIST transition crosswalk
          between them. Official records can be read directly, without any language model. Where AI
          is used to explain them, every statement must point back to retrieved evidence, and the
          system declines to answer when evidence is missing.
        </p>
      </section>

      <section aria-labelledby="sections" className="mt-10 max-w-[680px]">
        <h2 id="sections" className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
          Sections
        </h2>
        <ul className="mt-2 divide-y divide-border rounded-lg border border-border bg-surface">
          {NAV_ITEMS.filter((i) => i.href !== "/").map((item) => {
            const Icon = item.icon;
            const s = STATUS[item.href];
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="group flex items-start gap-3 px-4 py-3 hover:bg-surface-hover"
                >
                  <Icon aria-hidden="true" strokeWidth={1.5} className="mt-0.5 size-4 shrink-0 text-fg-3" />
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2">
                      <span className="text-ui font-medium text-fg-1">{item.label}</span>
                      <span className="rounded-sm bg-surface-sunken px-1.5 text-caption text-fg-3">
                        {s.tag}
                      </span>
                    </span>
                    <span className="mt-0.5 block text-ui-sm text-fg-2">{s.text}</span>
                  </span>
                  <ArrowRight
                    aria-hidden="true"
                    strokeWidth={1.5}
                    className="mt-0.5 size-4 shrink-0 text-fg-4 group-hover:text-fg-2"
                  />
                </Link>
              </li>
            );
          })}
        </ul>
      </section>

      <section aria-labelledby="labels" className="mt-10 max-w-[680px]">
        <h2 id="labels" className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
          How content is labelled
        </h2>
        <dl className="mt-2 space-y-3 text-ui-sm">
          <div className="flex gap-3">
            <dt className="w-16 shrink-0 pt-0.5">
              <SourceTag />
            </dt>
            <dd className="text-fg-2">
              <span className="font-serif text-source text-fg-1">Verbatim text</span> from the NIST
              framework documents or the official transition workbook, shown with its source.
            </dd>
          </div>
          <div className="flex gap-3">
            <dt className="w-16 shrink-0 pt-0.5">
              <DerivedTag />
            </dt>
            <dd className="text-fg-2">
              A ControlShift interpretation, such as a summary of how workbook rows relate. It is
              not a field of the NIST workbook.
            </dd>
          </div>
          <div className="flex gap-3">
            <dt className="w-16 shrink-0" />
            <dd className="text-fg-3">
              AI-generated explanations will carry their own label when they are available in Ask
              ControlShift.
            </dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
