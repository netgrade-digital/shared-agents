import { notFound, redirect } from "next/navigation";
import { DocsSidebar } from "@/components/docs-sidebar";
import { MarkdownContent } from "@/components/markdown-content";
import { DOCS_INDEX_SLUG, getDocBySlug, getDocSlugs } from "@/lib/docs";

type PageProps = {
  params: Promise<{ slug: string }>;
};

export async function generateStaticParams() {
  return getDocSlugs()
    .filter((slug) => slug !== DOCS_INDEX_SLUG)
    .map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: PageProps) {
  const { slug } = await params;
  const doc = getDocBySlug(slug);
  if (!doc) return { title: "Not found" };
  return {
    title: `${doc.title} — Shared Agents`,
    description: `Documentation: ${doc.title}`,
  };
}

export default async function DocPage({ params }: PageProps) {
  const { slug } = await params;
  if (slug === DOCS_INDEX_SLUG) redirect("/docs");
  const doc = getDocBySlug(slug);
  if (!doc) notFound();

  return (
    <main className="flex-1">
      <div className="site-container flex flex-col gap-6 py-8 sm:gap-8 sm:py-12 lg:flex-row lg:gap-12">
        <DocsSidebar activeSlug={slug} />
        <div className="min-w-0 flex-1">
          <header className="mb-6 border-b border-border pb-5 sm:mb-8 sm:pb-6">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
              {doc.title}
            </h1>
          </header>
          <MarkdownContent content={doc.content} />
        </div>
      </div>
    </main>
  );
}
