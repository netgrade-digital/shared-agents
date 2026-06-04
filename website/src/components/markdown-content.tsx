import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type MarkdownContentProps = {
  content: string;
};

function resolveHref(href: string | undefined): string | undefined {
  if (!href) return href;
  if (href.startsWith("/") || href.startsWith("#") || href.startsWith("http")) {
    return href;
  }
  const mdMatch = href.match(/^(?:\.\/)?(?:docs\/)?([^/]+\.md)$/);
  if (mdMatch) {
    return `/docs/${mdMatch[1].replace(/\.md$/, "")}`;
  }
  return href;
}

export function MarkdownContent({ content }: MarkdownContentProps) {
  return (
    <article className="prose prose-invert prose-sa max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => {
            const resolved = resolveHref(href);
            if (resolved?.startsWith("/") || resolved?.startsWith("#")) {
              return (
                <Link href={resolved} className="text-accent hover:underline">
                  {children}
                </Link>
              );
            }
            return (
              <a
                href={resolved}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:underline"
              >
                {children}
              </a>
            );
          },
          code: ({ className, children }) => {
            const isBlock = className?.includes("language-");
            if (isBlock) {
              return (
                <code className={`${className} font-mono text-sm`}>
                  {children}
                </code>
              );
            }
            return (
              <code className="rounded bg-white/5 px-1.5 py-0.5 font-mono text-sm text-accent">
                {children}
              </code>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </article>
  );
}
