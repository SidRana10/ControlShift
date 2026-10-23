import { splitHighlight } from "@/lib/explorer/hierarchy";

/** Renders text with case-insensitive matches of `q` marked (display only; search is server-side). */
export function Highlight({ text, q }: { text: string; q?: string }) {
  if (!q) return <>{text}</>;
  return (
    <>
      {splitHighlight(text, q).map((p, i) =>
        p.match ? (
          <mark key={i} className="rounded-sm bg-highlight px-px text-inherit">
            {p.text}
          </mark>
        ) : (
          <span key={i}>{p.text}</span>
        ),
      )}
    </>
  );
}
