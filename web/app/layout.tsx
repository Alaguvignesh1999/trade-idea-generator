import type { Metadata } from "next";
import { IBM_Plex_Sans, JetBrains_Mono, Space_Grotesk } from "next/font/google";

import "./globals.css";

const headline = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-headline",
});

const body = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"],
});

const data = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-data",
});

export const metadata: Metadata = {
  title: "Trade Idea Generator",
  description: "Read-only market snapshots, trade ideas, action boards, and backtests.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${headline.variable} ${body.variable} ${data.variable}`} style={{ fontFamily: "var(--font-body)" }}>
        {children}
      </body>
    </html>
  );
}
