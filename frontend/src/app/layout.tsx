import type { Metadata, Viewport } from "next";
import { Suspense } from "react";
import { IBM_Plex_Mono, IBM_Plex_Sans, Source_Serif_4 } from "next/font/google";
import { AppShell } from "@/components/layout/app-shell";
import { ShellFallback } from "@/components/shared/shell-fallback";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SIDEBAR_STORAGE_KEY } from "@/lib/sidebar-preference";
import "./globals.css";

// UI text, identifiers, and verbatim NIST text: one typeface per role (spec section 2).
const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});
const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
  display: "swap",
});
const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
  style: ["normal", "italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "ControlShift", template: "%s · ControlShift" },
  description:
    "Version-aware, evidence-grounded exploration of NIST CSF 1.1, CSF 2.0 and the official transition crosswalk.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

// Runs before first paint: reflect a stored "collapsed" preference on <html> so the server-rendered
// sidebar is already the right width. Only this one attribute differs from the server HTML.
const SIDEBAR_INIT = `try{if(localStorage.getItem(${JSON.stringify(SIDEBAR_STORAGE_KEY)})==="1")document.documentElement.dataset.sidebar="collapsed"}catch(e){}`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${plexSans.variable} ${plexMono.variable} ${sourceSerif.variable} h-full`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: SIDEBAR_INIT }} />
      </head>
      <body className="h-full">
        <TooltipProvider delay={300}>
          {/* Routes with runtime params (/explorer/[version]/[id]) read the pathname at request time. */}
          <Suspense fallback={<ShellFallback />}>
            <AppShell>{children}</AppShell>
          </Suspense>
        </TooltipProvider>
      </body>
    </html>
  );
}
