"use client";

import { useCallback, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { MappingType } from "@/lib/api/types";
import { compareHref, hasSubject, parseCompare, type CompareState } from "@/lib/compare/url";
import { cn } from "@/lib/utils";
import { Inspector, Orientation } from "./inspector";
import { RelationshipIndex } from "./relationship-index";

/**
 * Compare Frameworks: relationship index on the left, inspector on the right (>=900px); below that
 * one screen at a time. All state lives in the URL (see lib/compare/url.ts): selecting a row pushes a
 * history entry, search and filter changes replace the current one.
 */
export function CompareWorkspace() {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const state = useMemo(() => parseCompare(sp), [sp]);
  const inspecting = hasSubject(state);
  void pathname;

  const replace = useCallback((next: CompareState) => router.replace(compareHref(next), { scroll: false }), [router]);
  const subject = { focal: state.focal, ref: state.ref, row: state.row };
  const filters = { q: state.q, type: state.type };

  return (
    <div className="flex h-full min-h-0 flex-col min-[900px]:flex-row">
      <RelationshipIndex
        state={state}
        selectedRow={state.row}
        className={inspecting ? "hidden min-[900px]:flex" : "flex"}
        onSearch={(q) => replace({ ...subject, ...filters, q: q || undefined })}
        onType={(t: MappingType | undefined) => replace({ ...subject, ...filters, type: t })}
        onClear={() => replace(subject)}
      />
      <section
        aria-label="Comparison"
        className={cn(
          "min-h-0 min-w-0 flex-1 overflow-y-auto bg-canvas",
          inspecting ? "block" : "hidden min-[900px]:block",
        )}
      >
        {inspecting ? (
          <Inspector state={state} backHref={compareHref(filters)} />
        ) : (
          <Orientation />
        )}
      </section>
    </div>
  );
}
