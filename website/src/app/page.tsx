import { Code2, Link2, ShieldCheck, Star, Zap } from "lucide-react";
import { FeatureTile } from "@/components/feature-tile";
import { HeroBackground } from "@/components/hero-background";
import { QuickStartSection } from "@/components/quick-start-section";
import { WorkflowSection } from "@/components/workflow-section";
import { SharedAgentsLogo } from "@/components/shared-agents-logo";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { GITHUB_REPO } from "@/lib/site";

const FEATURES = [
  { icon: Zap, label: "Speed", value: "Top Performance" },
  {
    icon: ShieldCheck,
    label: "Privacy First",
    value: "Team data stays private",
  },
  { icon: Code2, label: "Developer Experience", value: "Exceptional" },
  { icon: Link2, label: "Tool Agnostic", value: "Works everywhere" },
] as const;

const PILLARS = [
  {
    title: "Skills",
    body: "Repeatable workflows for agents — how your team works.",
  },
  {
    title: "Rules",
    body: "Shared instructions per tool (Cursor .mdc, AGENTS.md, CLAUDE.md).",
  },
  {
    title: "Learnings",
    body: "Institutional memory: bugs, stack quirks, decisions — reviewed by humans.",
  },
] as const;

export default function Home() {
  return (
    <>
      <SiteHeader active="home" />
      <main className="flex-1">
        <section className="relative border-b border-border/50">
          <HeroBackground />
          <div className="site-container relative grid gap-10 py-10 sm:gap-12 sm:py-16 lg:grid-cols-2 lg:items-center lg:gap-16 lg:py-24">
            <div className="animate-fade-up space-y-5 sm:space-y-6">
              <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:items-start sm:gap-5 sm:text-left">
                <SharedAgentsLogo
                  className="shrink-0 text-glow"
                  size={72}
                  priority
                />
                <div className="space-y-2 sm:pt-1">
                  <h1 className="text-3xl font-bold tracking-tight sm:text-4xl lg:text-5xl">
                    Shared Agents
                  </h1>
                  <p className="text-base text-muted sm:max-w-md sm:text-lg">
                    Team skills and learnings for AI assistants
                  </p>
                </div>
              </div>
              <p className="text-center text-[15px] leading-relaxed text-muted sm:text-left sm:text-base sm:max-w-lg">
                One install, Git-synced, IDE-agnostic. Give Cursor, Claude Code,
                Zed, Codex, and the rest the same skills, rules, and team memory
                — without locking into a single vendor.
              </p>
              <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                <a
                  href="#setup"
                  className="inline-flex h-12 w-full items-center justify-center rounded-full bg-accent px-6 text-sm font-semibold text-black transition-opacity hover:opacity-90 sm:h-11 sm:w-auto"
                >
                  Get started
                </a>
                <a
                  href={GITHUB_REPO}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-full border border-border px-6 text-sm font-medium text-foreground transition-colors hover:border-accent/50 hover:text-accent sm:h-11 sm:w-auto"
                >
                  <Star className="size-4" strokeWidth={1.75} />
                  Star on GitHub
                </a>
              </div>
            </div>

            <div className="animate-fade-up animate-fade-up-delay-1 grid grid-cols-1 gap-0.5 sm:grid-cols-2 sm:gap-1">
              {FEATURES.map((f) => (
                <FeatureTile key={f.label} {...f} />
              ))}
            </div>
          </div>
        </section>

        <section className="site-section border-b border-border/50">
          <div className="site-container">
            <h2 className="animate-fade-up text-xl font-bold tracking-tight sm:text-2xl lg:text-3xl">
              Why this exists
            </h2>
            <p className="animate-fade-up animate-fade-up-delay-1 mt-3 max-w-2xl text-[15px] leading-relaxed text-muted sm:mt-4 sm:text-base">
              Teams use many AI tools. Each session starts cold — no shared
              workflows, no institutional memory. Shared Agents is one place for
              skills, rules, and learnings; everyone syncs the same content, and
              sensitive team data stays in your private repo.
            </p>

            <div className="animate-fade-up animate-fade-up-delay-2 mt-8 grid gap-4 sm:mt-12 sm:grid-cols-3 sm:gap-6">
              {PILLARS.map((p) => (
                <article
                  key={p.title}
                  className="rounded-xl border border-border bg-surface/50 p-5 transition-colors hover:border-accent/30 sm:p-6"
                >
                  <h3 className="text-base font-semibold text-accent sm:text-lg">
                    {p.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">
                    {p.body}
                  </p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <QuickStartSection />

        <WorkflowSection />
      </main>
      <SiteFooter />
    </>
  );
}
