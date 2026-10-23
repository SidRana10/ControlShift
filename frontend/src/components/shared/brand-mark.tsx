/** Two offset squares joined by one stroke: the "shift" between framework versions. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <rect x="1" y="1" width="9" height="9" rx="2" fill="var(--cs-v20)" />
      <rect x="10" y="10" width="9" height="9" rx="2" fill="var(--cs-v11)" />
      <path d="M10 5.5h4.5V10" stroke="var(--cs-fg-1)" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
