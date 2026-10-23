import type { Metadata } from "next";

export const metadata: Metadata = { title: "Control Explorer" };

// /explorer/{version}/{element_id}: the record pane is rendered by ExplorerWorkspace in the layout,
// which reads the version and ID from the URL.
export default function RecordPage() {
  return null;
}
