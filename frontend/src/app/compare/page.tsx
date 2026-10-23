import type { Metadata } from "next";
import { Suspense } from "react";
import { CompareWorkspace } from "@/features/compare/compare-workspace";

export const metadata: Metadata = { title: "Compare Frameworks" };

export default function ComparePage() {
  return (
    <Suspense fallback={<div className="h-full bg-surface" aria-busy="true" />}>
      <CompareWorkspace />
    </Suspense>
  );
}
