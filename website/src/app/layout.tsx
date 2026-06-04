import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { PreloaderRoot } from "@/components/preloader-root";
import { getBasePath, getSiteUrl } from "@/lib/deploy";
import "./globals.css";

const siteUrl = getSiteUrl();
const asset = (path: string) => `${getBasePath()}${path}`;

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "Shared Agents — Team skills & learnings for AI assistants",
  description:
    "One install, Git-synced, IDE-agnostic. Team skills, rules, and learnings for Cursor, Claude Code, Zed, Codex, and more.",
  openGraph: {
    title: "Shared Agents",
    description:
      "Team skills and learnings for AI assistants — one install, Git-synced, IDE-agnostic.",
    images: [asset("/shared-agents-banner.png")],
    url: siteUrl,
  },
  icons: {
    icon: asset("/shared-agents.svg"),
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <PreloaderRoot />
        {children}
      </body>
    </html>
  );
}
