import type { Metadata } from "next";
import { ExplorerIntro } from "@/features/explorer/explorer-intro";

export const metadata: Metadata = { title: "Control Explorer" };

export default function ExplorerPage() {
  return <ExplorerIntro />;
}
