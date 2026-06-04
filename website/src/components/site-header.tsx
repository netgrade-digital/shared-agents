"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { GithubIcon } from "@/components/github-icon";
import { SharedAgentsLogo } from "@/components/shared-agents-logo";
import { GITHUB_REPO } from "@/lib/site";

type SiteHeaderProps = {
  active?: "home" | "docs" | "setup";
};

const NAV = [
  { href: "/#setup", label: "Setup", key: "setup" as const },
  { href: "/docs", label: "Docs", key: "docs" as const },
] as const;

export function SiteHeader({ active }: SiteHeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = useCallback(() => setMenuOpen(false), []);

  useEffect(() => {
    if (!menuOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeMenu();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [menuOpen, closeMenu]);

  const navLinkClass = (isActive: boolean) =>
    isActive
      ? "text-accent"
      : "text-muted transition-colors hover:text-foreground";

  return (
    <header className="site-header sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md">
      <div className="site-container flex h-14 min-h-14 items-center justify-between gap-3">
        <Link
          href="/"
          className="flex min-w-0 items-center gap-2 text-foreground transition-opacity hover:opacity-90 sm:gap-2.5"
          onClick={closeMenu}
        >
          <SharedAgentsLogo className="shrink-0 text-accent" size={32} />
          <span className="truncate font-semibold tracking-tight">
            Shared Agents
          </span>
        </Link>

        <nav
          className="hidden items-center gap-5 text-sm md:flex"
          aria-label="Main"
        >
          {NAV.map(({ href, label, key }) => (
            <Link
              key={key}
              href={href}
              className={navLinkClass(active === key)}
            >
              {label}
            </Link>
          ))}
          <a
            href={GITHUB_REPO}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-9 items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-muted transition-colors hover:border-accent/40 hover:text-accent"
          >
            <GithubIcon className="size-4" />
            GitHub
          </a>
        </nav>

        <button
          type="button"
          className="inline-flex size-11 shrink-0 items-center justify-center rounded-lg border border-border text-foreground transition-colors hover:border-accent/40 hover:text-accent md:hidden"
          aria-expanded={menuOpen}
          aria-controls="mobile-nav"
          aria-label={menuOpen ? "Close menu" : "Open menu"}
          onClick={() => setMenuOpen((o) => !o)}
        >
          {menuOpen ? (
            <X className="size-5" strokeWidth={1.75} />
          ) : (
            <Menu className="size-5" strokeWidth={1.75} />
          )}
        </button>
      </div>

      {menuOpen ? (
        <div
          id="mobile-nav"
          className="fixed inset-0 top-[calc(3.5rem+env(safe-area-inset-top,0px))] z-40 md:hidden"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation"
        >
          <button
            type="button"
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            aria-label="Close menu"
            onClick={closeMenu}
          />
          <nav className="relative border-b border-border bg-background px-4 py-4 shadow-lg">
            <ul className="flex flex-col gap-1">
              {NAV.map(({ href, label, key }) => (
                <li key={key}>
                  <Link
                    href={href}
                    onClick={closeMenu}
                    className={`flex min-h-12 items-center rounded-lg px-4 text-base font-medium ${navLinkClass(active === key)}`}
                  >
                    {label}
                  </Link>
                </li>
              ))}
              <li>
                <a
                  href={GITHUB_REPO}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={closeMenu}
                  className="flex min-h-12 items-center gap-2 rounded-lg px-4 text-base font-medium text-muted transition-colors hover:text-accent"
                >
                  <GithubIcon className="size-5" />
                  GitHub
                </a>
              </li>
            </ul>
          </nav>
        </div>
      ) : null}
    </header>
  );
}
