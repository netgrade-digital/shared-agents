import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronRight, FileText } from "lucide-react";
import { DocsSidebar } from "@/components/docs-sidebar";
import { MarkdownContent } from "@/components/markdown-content";
import { DOCS_INDEX_SLUG, getDocBySlug, listDocSections } from "@/lib/docs";

export const metadata = {
  title: "Overview — Shared Agents",
  description:
    "What Shared Agents is, how it works, and links to all documentation guides.",
};

function DocCard({
  slug,
  title,
  description,
}: {
  slug: string;
  title: string;
  description: string;
}) {
  return (
    <li>
      <Link
        href={`/docs/${slug}`}
        className="group flex items-start gap-3 rounded-xl border border-border bg-surface/40 p-4 transition-colors hover:border-accent/40 hover:bg-surface/70 active:bg-surface/70 sm:gap-4 sm:p-5"
      >
        <FileText
          className="mt-0.5 size-5 shrink-0 text-accent"
          strokeWidth={1.5}
        />
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-foreground group-hover:text-accent">
            {title}
          </p>
          {description ? (
            <p className="mt-1 line-clamp-2 text-sm text-muted">
              {description}
            </p>
          ) : null}
        </div>
        <ChevronRight
          className="size-5 shrink-0 text-muted transition-transform group-hover:translate-x-0.5 group-hover:text-accent"
          strokeWidth={1.75}
        />
      </Link>
    </li>
  );
}

export default function DocsIndexPage() {
  const overview = getDocBySlug(DOCS_INDEX_SLUG);
  if (!overview) notFound();

  const sections = listDocSections();

  return (
    <main className="flex-1">
      <div className="site-container flex flex-col gap-6 py-8 sm:gap-8 sm:py-12 lg:flex-row lg:gap-12">
        <DocsSidebar defaultMenuOpen />
        <div className="min-w-0 flex-1">
          <header className="mb-6 border-b border-border pb-5 sm:mb-8 sm:pb-6">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              {overview.title}
            </h1>
          </header>
          <MarkdownContent content={overview.content} />

          <div className="mt-14 border-t border-border pt-12">
            <h2 className="text-xl font-semibold tracking-tight">All guides</h2>
            <p className="mt-2 text-sm text-muted">
              Browse by topic or use the sidebar.
            </p>

            <div className="mt-8 space-y-10">
              {sections.map((section) => (
                <section key={section.title}>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-accent">
                    {section.title}
                  </h3>
                  <ul className="mt-4 space-y-3">
                    {section.docs.map((doc) => (
                      <DocCard
                        key={doc.slug}
                        slug={doc.slug}
                        title={doc.title}
                        description={doc.description}
                      />
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
