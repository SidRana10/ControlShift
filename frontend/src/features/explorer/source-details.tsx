"use client";

import { useId, useState } from "react";
import { Check, ChevronRight, Copy } from "lucide-react";
import type { Provenance } from "@/lib/api/types";
import { formatBytes } from "@/lib/explorer/crosswalk";
import { cn } from "@/lib/utils";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[6.5rem_1fr] gap-x-3 py-1">
      <dt className="text-caption text-fg-3">{label}</dt>
      <dd className="min-w-0 text-ui-sm break-words text-fg-1">{children}</dd>
    </div>
  );
}

function CopyButton({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      aria-label={copied ? `${label} copied` : `Copy ${label}`}
      onClick={() => {
        void navigator.clipboard?.writeText(value).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        });
      }}
      className="ml-1 inline-flex size-11 items-center justify-center rounded-md text-fg-3 hover:text-fg-1 min-[900px]:size-6"
    >
      {copied ? <Check aria-hidden="true" className="size-3.5" /> : <Copy aria-hidden="true" className="size-3.5" />}
    </button>
  );
}

/**
 * On-demand provenance (spec 9.3), straight from the API: file, section path, pages, document
 * metadata, SHA-256 and chunk id. No links to documents: the backend supplies none.
 */
export function SourceDetails({ provenance, className }: { provenance: Provenance; className?: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const doc = provenance.source_document;
  const chunk = provenance.chunk;
  return (
    <div className={className}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((o) => !o)}
        className="-ml-1 inline-flex min-h-11 items-center gap-1 rounded-md px-1 text-ui-sm font-medium text-fg-2 hover:text-fg-1 min-[900px]:min-h-7"
      >
        <ChevronRight
          aria-hidden="true"
          strokeWidth={1.5}
          className={cn("size-3.5 transition-transform duration-150", open && "rotate-90")}
        />
        Source details
      </button>
      <dl id={id} hidden={!open} className="mt-1 rounded-lg border border-border bg-surface px-3 py-2">
        <Row label="File">
          <span className="font-mono text-id">{doc.source_file}</span>
        </Row>
        <Row label="Section">{chunk.section}</Row>
        <Row label="Printed page">{chunk.printed_page ?? "not recorded"}</Row>
        <Row label="PDF page">{chunk.page}</Row>
        <Row label="Document">
          {doc.kind.toUpperCase()}
          {doc.pages ? ` · ${doc.pages} pages` : ""} · {formatBytes(doc.bytes)}
        </Row>
        <Row label="SHA-256">
          <span className="font-mono text-id break-all">{doc.sha256}</span>
          <CopyButton value={doc.sha256} label="SHA-256" />
        </Row>
        <Row label="Chunk">
          <span className="font-mono text-id break-all">{chunk.chunk_id}</span>
        </Row>
      </dl>
    </div>
  );
}
