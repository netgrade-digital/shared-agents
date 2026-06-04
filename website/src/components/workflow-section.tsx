import { BookOpen, GitBranch, RefreshCw, ShieldCheck } from "lucide-react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";

const WORKFLOW = [
  {
    icon: RefreshCw,
    title: "Sync",
    body: "Pull the latest Core and team content. Skills and rules link into every IDE automatically.",
    href: "/docs/cli-reference",
    label: "CLI reference",
  },
  {
    icon: GitBranch,
    title: "Share",
    body: "Team skills and rules live in your private repo — same workflows in Cursor, Claude Code, Zed, and more.",
    href: "/docs/skills-and-rules",
    label: "Skills & rules",
  },
  {
    icon: ShieldCheck,
    title: "Review",
    body: "Agents propose learnings; humans approve with sa review. Only approved knowledge reaches the team.",
    href: "/docs/learnings",
    label: "Learnings",
  },
  {
    icon: BookOpen,
    title: "Explore",
    body: "Installation, adapters, paths, and troubleshooting — everything in the docs.",
    href: "/docs",
    label: "All guides",
  },
] as const;

function WorkflowCard({
  icon: Icon,
  title,
  body,
  href,
  label,
}: {
  icon: LucideIcon;
  title: string;
  body: string;
  href: string;
  label: string;
}) {
  return (
    <article className="flex flex-col rounded-2xl border border-border/80 bg-surface/40 p-5 transition-colors hover:border-accent/30 hover:bg-surface/60 sm:p-6">
      <div className="flex size-10 items-center justify-center rounded-xl border border-accent/30 bg-accent/5 text-accent sm:size-11">
        <Icon className="size-5" strokeWidth={1.5} aria-hidden />
      </div>
      <h3 className="mt-3 text-base font-semibold tracking-tight sm:mt-4 sm:text-lg">
        {title}
      </h3>
      <p className="mt-2 flex-1 text-sm leading-relaxed text-muted">{body}</p>
      <Link
        href={href}
        className="mt-4 inline-flex min-h-10 items-center text-sm font-medium text-accent transition-colors hover:underline"
      >
        {label} →
      </Link>
    </article>
  );
}

export function WorkflowSection() {
  return (
    <section
      id="workflow"
      className="site-section scroll-mt-[calc(3.5rem+env(safe-area-inset-top,0px))]"
    >
      <div className="site-container">
        <div className="max-w-2xl">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-accent sm:text-sm sm:tracking-[0.2em]">
            How it works
          </p>
          <h2 className="mt-2 text-xl font-bold tracking-tight sm:text-2xl lg:text-3xl">
            One workflow for the whole team
          </h2>
          <p className="mt-2 text-[15px] leading-relaxed text-muted sm:mt-3 sm:text-base">
            Install once, then sync, share, and review team knowledge across every
            tool. Command details:{" "}
            <Link
              href="/docs/cli-reference"
              className="text-accent hover:underline"
            >
              CLI reference
            </Link>
            .
          </p>
        </div>

        <div className="mt-8 grid gap-3 sm:mt-10 sm:grid-cols-2 sm:gap-4 lg:grid-cols-4">
          {WORKFLOW.map((item) => (
            <WorkflowCard key={item.title} {...item} />
          ))}
        </div>
      </div>
    </section>
  );
}
