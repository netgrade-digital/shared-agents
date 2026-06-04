import Link from "next/link";
import { GithubIcon } from "@/components/github-icon";
import { SharedAgentsLogo } from "@/components/shared-agents-logo";
import { DOCS_INDEX_SLUG, listDocs } from "@/lib/docs";
import { GITHUB_REPO, LEGAL, NETGRADE_URL } from "@/lib/site";

const FOOTER_GUIDE_SLUGS = [
  "installation",
  "cli-reference",
  "learnings",
  "contributing",
] as const;

export function SiteFooter() {
  const docsBySlug = new Map(
    listDocs()
      .filter((d) => d.slug !== DOCS_INDEX_SLUG)
      .map((d) => [d.slug, d]),
  );
  const footerGuides = FOOTER_GUIDE_SLUGS.map((slug) => docsBySlug.get(slug)).filter(
    (d): d is NonNullable<typeof d> => d != null,
  );

  return (
    <footer className="border-t border-border bg-surface/30 pb-[env(safe-area-inset-bottom,0px)]">
      <div className="site-container py-10 sm:py-14">
        <div className="grid gap-8 sm:grid-cols-2 sm:gap-10 lg:grid-cols-4">
          <div className="space-y-3 sm:space-y-4 lg:col-span-1">
            <Link href="/" className="inline-flex items-center gap-2.5">
              <SharedAgentsLogo className="text-accent" size={28} />
              <span className="font-semibold">Shared Agents</span>
            </Link>
            <p className="max-w-xs text-sm leading-relaxed text-muted">
              Team skills, rules, and learnings for AI assistants — one install,
              Git-synced, IDE-agnostic.
            </p>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Product
            </h3>
            <ul className="mt-3 space-y-2 text-sm sm:mt-4 sm:space-y-2.5">
              <li>
                <Link
                  href="/"
                  className="inline-flex min-h-9 items-center text-foreground/80 transition-colors hover:text-accent"
                >
                  Home
                </Link>
              </li>
              <li>
                <Link
                  href="/#setup"
                  className="inline-flex min-h-9 items-center text-foreground/80 transition-colors hover:text-accent"
                >
                  Quick start
                </Link>
              </li>
              <li>
                <Link
                  href="/docs"
                  className="inline-flex min-h-9 items-center text-foreground/80 transition-colors hover:text-accent"
                >
                  Documentation
                </Link>
              </li>
              <li>
                <Link
                  href="/#workflow"
                  className="inline-flex min-h-9 items-center text-foreground/80 transition-colors hover:text-accent"
                >
                  How it works
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Project
            </h3>
            <ul className="mt-3 space-y-2 text-sm sm:mt-4 sm:space-y-2.5">
              <li>
                <a
                  href={GITHUB_REPO}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex min-h-9 items-center gap-1.5 text-foreground/80 transition-colors hover:text-accent"
                >
                  <GithubIcon className="size-3.5" />
                  Repository
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">
              Guides
            </h3>
            <ul className="mt-3 space-y-2 text-sm sm:mt-4 sm:space-y-2.5">
              {footerGuides.map((doc) => (
                <li key={doc.slug}>
                  <Link
                    href={`/docs/${doc.slug}`}
                    className="inline-flex min-h-9 items-center text-foreground/80 transition-colors hover:text-accent"
                  >
                    {doc.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-border pt-6 text-sm text-muted sm:mt-12 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between sm:gap-4 sm:pt-8">
          <p className="leading-relaxed">
            Crafted with ❤️ by{" "}
            <a
              href={NETGRADE_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-9 items-center font-medium text-foreground/90 transition-colors hover:text-accent"
            >
              Netgrade
            </a>
          </p>
          <p className="flex flex-wrap gap-x-4 gap-y-0">
            <a
              href={LEGAL.impressum}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-9 items-center transition-colors hover:text-accent"
            >
              Impressum
            </a>
            <a
              href={LEGAL.datenschutz}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-9 items-center transition-colors hover:text-accent"
            >
              Datenschutz
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
