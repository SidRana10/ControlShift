import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DerivedTag, GeneratedTag, SourceTag } from "@/components/shared/source-tags";
import { buttonVariants } from "@/components/ui/button";
import { AskStatus } from "@/features/overview/ask-status";
import { FrameworkFacts } from "@/features/overview/framework-facts";
import { NAV_ITEMS } from "@/lib/navigation";

export const metadata: Metadata = { title: "Overview" };

const WORKFLOWS: Record<string, { cta: string; text: string; note: string }> = {
  "/ask": {
    cta: "Ask a question",
    text: "Ask in plain language about CSF 1.1, CSF 2.0 or the crosswalk. Every answer lists the retrieved NIST evidence behind it, and the system declines when the evidence is missing.",
    note: "AI-generated text is labelled and separate from the NIST excerpts.",
  },
  "/explorer": {
    cta: "Browse official records",
    text: "Read every function, category and subcategory of either framework as official NIST text, with source pages, informative references and the crosswalk rows for each record.",
    note: "No language model involved.",
  },
  "/compare": {
    cta: "Compare frameworks",
    text: "Search the official transition workbook and inspect a CSF 2.0 element beside the CSF 1.1 element it references. One-to-many rows and rows with no reference stay visible and separate.",
    note: "No language model involved.",
  },
};

const START: { href: string; label: string; note: string }[] = [
  { href: "/explorer/2.0/GV.SC-03", label: "Inspect GV.SC-03", note: "a CSF 2.0 subcategory with its source page and crosswalk" },
  { href: "/compare?focal=GV.SC-03&row=26", label: "See why GV.SC-03 needs interpretation", note: "workbook rows 25 and 26 point different ways" },
  { href: "/compare?focal=ID.IM-03", label: "Follow a one-to-many relationship", note: "ID.IM-03 appears in seven workbook rows" },
  { href: "/compare?ref=RC.CO-02", label: "Look up a CSF 1.1 control with no crosswalk reference", note: "RC.CO-02; the workbook does not say what that means" },
];

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={id} className="mt-12">
      <h2 id={id} className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
        {title}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

export default function OverviewPage() {
  return (
    <div className="mx-auto w-full max-w-[1080px] px-4 py-8 min-[900px]:px-10 min-[900px]:py-12">
      <section aria-labelledby="intro" className="max-w-[720px]">
        <p className="text-label font-medium tracking-[0.04em] text-fg-3 uppercase">
          NIST Cybersecurity Framework · version-aware research
        </p>
        <h2 id="intro" className="mt-2 text-name-lg font-semibold text-fg-1">
          Read CSF 1.1 and CSF 2.0 against each other, from the official sources.
        </h2>
        <p className="mt-3 text-body text-fg-2">
          The two framework versions are organised differently, and an ID that looks the same in both is
          not the same requirement. ControlShift keeps the official NIST records, the official transition
          workbook that relates them, and AI-written explanations clearly apart, so you can see what NIST
          says, what ControlShift derived from it, and what a model wrote.
        </p>
        <div className="mt-5 flex flex-wrap gap-2">
          <Link href="/ask" className={buttonVariants({ className: "min-h-11 px-4 min-[900px]:min-h-8" })}>
            Ask a question
          </Link>
          <Link href="/explorer" className={buttonVariants({ variant: "outline", className: "min-h-11 px-4 min-[900px]:min-h-8" })}>
            Browse official records
          </Link>
        </div>
      </section>

      <Section id="frameworks" title="What it covers">
        <FrameworkFacts />
      </Section>

      <Section id="workflows" title="Three ways to work">
        <ul className="grid gap-3 min-[900px]:grid-cols-3">
          {NAV_ITEMS.filter((i) => WORKFLOWS[i.href]).map((item) => {
            const Icon = item.icon;
            const w = WORKFLOWS[item.href];
            return (
              <li key={item.href} className="flex">
                <div className="flex w-full flex-col rounded-lg border border-border bg-surface p-4">
                  <h3 className="flex items-center gap-2 text-title-sm font-semibold text-fg-1">
                    <Icon aria-hidden="true" strokeWidth={1.5} className="size-4 text-fg-3" />
                    {item.label}
                  </h3>
                  <p className="mt-2 text-ui-sm text-fg-2">{w.text}</p>
                  <p className="mt-2 text-caption text-fg-3">
                    {w.note}
                    {item.href === "/ask" && (
                      <>
                        {" "}
                        <AskStatus />
                      </>
                    )}
                  </p>
                  <Link
                    href={item.href}
                    className="group mt-auto inline-flex min-h-11 items-center gap-1 pt-3 text-ui font-medium text-cobalt hover:underline min-[900px]:min-h-9"
                  >
                    {w.cta}
                    <ArrowRight aria-hidden="true" strokeWidth={1.5} className="size-4" />
                  </Link>
                </div>
              </li>
            );
          })}
        </ul>
      </Section>

      <Section id="start" title="Start exploring">
        <ul className="max-w-[720px] divide-y divide-border rounded-lg border border-border bg-surface">
          {START.map((s) => (
            <li key={s.href}>
              <Link href={s.href} className="group flex min-h-11 items-center gap-3 px-4 py-2.5 hover:bg-surface-hover">
                <span className="min-w-0 flex-1">
                  <span className="block text-ui font-medium text-cobalt group-hover:underline">{s.label}</span>
                  <span className="block text-caption text-fg-3">{s.note}</span>
                </span>
                <ArrowRight aria-hidden="true" strokeWidth={1.5} className="size-4 shrink-0 text-fg-4 group-hover:text-fg-2" />
              </Link>
            </li>
          ))}
        </ul>
      </Section>

      <Section id="labels" title="How content is labelled">
        <dl className="max-w-[720px] space-y-3 text-ui-sm">
          <div className="flex gap-3">
            <dt className="w-28 shrink-0 pt-0.5"><SourceTag /></dt>
            <dd className="text-fg-2">
              <span className="font-serif text-source text-fg-1">Verbatim text</span> from the NIST framework
              documents or the official transition workbook, shown with its source.
            </dd>
          </div>
          <div className="flex gap-3">
            <dt className="w-28 shrink-0 pt-0.5"><DerivedTag /></dt>
            <dd className="text-fg-2">
              A ControlShift interpretation, such as an ingest label or a summary of how workbook rows
              relate. It is not a NIST field.
            </dd>
          </div>
          <div className="flex gap-3">
            <dt className="w-28 shrink-0 pt-0.5"><GeneratedTag /></dt>
            <dd className="text-fg-2">
              Written by a language model from retrieved evidence, only in Ask ControlShift. Its citations
              are checked for existence and provenance, not for whether the wording is faithful.
            </dd>
          </div>
        </dl>
      </Section>
    </div>
  );
}
