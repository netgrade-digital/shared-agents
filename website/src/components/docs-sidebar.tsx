import Link from "next/link";
import { ChevronDown } from "lucide-react";
import { DOCS_INDEX_SLUG, listDocSections } from "@/lib/docs";

type DocsSidebarProps = {
  activeSlug?: string;
  /** Open mobile menu by default (e.g. on /docs overview) */
  defaultMenuOpen?: boolean;
};

function DocsNav({ activeSlug }: { activeSlug?: string }) {
  const sections = listDocSections();
  const isOverview = !activeSlug || activeSlug === DOCS_INDEX_SLUG;

  return (
    <>
      <Link
        href="/docs"
        className={`mb-4 block rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
          isOverview
            ? "bg-accent/10 text-accent"
            : "text-muted hover:bg-white/5 hover:text-foreground"
        }`}
      >
        Overview
      </Link>

      <div className="space-y-6">
        {sections.map((section) => (
          <div key={section.title}>
            <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-muted/90">
              {section.title}
            </p>
            <ul className="space-y-0.5">
              {section.docs.map((doc) => (
                <li key={doc.slug}>
                  <Link
                    href={`/docs/${doc.slug}`}
                    className={`block rounded-lg px-3 py-2.5 text-sm transition-colors ${
                      activeSlug === doc.slug
                        ? "bg-accent/10 font-medium text-accent"
                        : "text-muted hover:bg-white/5 hover:text-foreground"
                    }`}
                  >
                    {doc.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
}

export function DocsSidebar({
  activeSlug,
  defaultMenuOpen = false,
}: DocsSidebarProps) {
  return (
    <aside className="w-full shrink-0 lg:w-60">
      <details
        className="group mb-6 rounded-xl border border-border bg-surface/40 lg:hidden"
        open={defaultMenuOpen}
      >
        <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-medium text-foreground [&::-webkit-details-marker]:hidden">
          <span>Documentation menu</span>
          <ChevronDown
            className="size-4 shrink-0 text-muted transition-transform group-open:rotate-180"
            aria-hidden
          />
        </summary>
        <nav className="max-h-[min(60vh,420px)] overflow-y-auto overscroll-contain border-t border-border/60 px-2 py-3 [scrollbar-width:thin]">
          <DocsNav activeSlug={activeSlug} />
        </nav>
      </details>

      <nav className="sticky top-[calc(3.5rem+env(safe-area-inset-top,0px))] hidden max-h-[calc(100dvh-5.5rem)] overflow-y-auto pr-2 lg:block [scrollbar-width:thin]">
        <DocsNav activeSlug={activeSlug} />
      </nav>
    </aside>
  );
}
