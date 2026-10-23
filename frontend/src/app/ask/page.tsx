import type { Metadata } from "next";
import { AskWorkspace } from "@/features/ask/ask-workspace";

export const metadata: Metadata = { title: "Ask ControlShift" };

export default function AskPage() {
  return <AskWorkspace />;
}
