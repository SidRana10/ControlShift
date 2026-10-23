"use client";

import { useCallback, useMemo } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { MappingType } from "@/lib/api/types";
import { compareHref, hasSubject, parseCompare, type CompareState } from "@/lib/compare/url";
import { loadDetail } from "@/lib/explorer/catalog-cache";
import { useLoader } from "@/lib/explorer/use-loader";
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

  // The index marks the row the inspector shows: ?row=N, else the inspected element's first row
  // (the same default Inspector uses). Shares the cached record request with the inspector.
  const subjectKey = state.focal ? `2.0/${state.focal}` : state.ref ? `1.1/${state.ref}` : null;
  const subjectDetail = useLoader(subjectKey && `detail:${subjectKey}`, () =>
    loadDetail(state.focal ? "2.0" : "1.1", (state.focal ?? state.ref)!),
  );
  const entries = subjectDetail.status === "success" ? subjectDetail.data?.crosswalk.entries : undefined;
  const selectedRow =
    entries && entries.length > 0
      ? (entries.find((e) => e.excel_row === state.row) ?? entries[0]).excel_row
      : state.row;

  const replace = useCallback((next: CompareState) => router.replace(compareHref(next), { scroll: false }), [router]);
  const subject = { focal: state.focal, ref: state.ref, row: state.row };
  const filters = { q: state.q, type: state.type };

  return (
    <div className="flex h-full min-h-0 flex-col min-[900px]:flex-row">
      <RelationshipIndex
        state={state}
        selectedRow={selectedRow}
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
