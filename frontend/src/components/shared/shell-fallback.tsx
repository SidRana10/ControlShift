import { BrandMark } from "./brand-mark";

/**
 * Static stand-in for the application shell while a request-time route (a record deep link)
 * streams in: same sidebar and header geometry, so nothing jumps when the real shell arrives.
 */
export function ShellFallback() {
  return (
    <div className="flex h-dvh overflow-hidden" aria-busy="true" role="status" aria-label="Loading ControlShift">
      <div className="sidebar-dock hidden shrink-0 border-r border-border bg-surface-sunken min-[900px]:block">
        <div className="flex h-14 items-center gap-3 px-5">
          <BrandMark className="shrink-0" />
        </div>
      </div>
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="h-[52px] shrink-0 border-b border-border bg-surface min-[900px]:h-14" />
        <div className="flex-1 bg-surface min-[900px]:ml-0" />
      </div>
    </div>
  );
}
