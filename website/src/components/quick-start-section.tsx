import { InstallTerminal } from "@/components/install-terminal";
import { SetupSteps } from "@/components/setup-steps";
import { BOOTSTRAP_CMD } from "@/lib/site";

export function QuickStartSection() {
  return (
    <section
      id="setup"
      className="site-section relative scroll-mt-[calc(3.5rem+env(safe-area-inset-top,0px))] overflow-hidden border-b border-border/50 sm:py-28"
    >
      <div
        className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-[0.04]"
        aria-hidden
      >
        <svg
          className="h-[min(120%,800px)] w-[min(120%,800px)] text-accent"
          viewBox="0 0 800 800"
          fill="none"
        >
          {[160, 240, 320, 400, 480].map((r) => (
            <circle
              key={r}
              cx="400"
              cy="400"
              r={r}
              stroke="currentColor"
              strokeWidth="0.75"
            />
          ))}
        </svg>
      </div>

      <div className="site-container relative">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-medium uppercase tracking-[0.16em] text-accent sm:text-sm sm:tracking-[0.2em]">
            Get started
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-glow sm:mt-3 sm:text-3xl lg:text-4xl">
            Install in seconds
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-[15px] leading-relaxed text-muted sm:mt-4 sm:text-base">
            Copy the command, run it in your terminal, then type{" "}
            <code className="rounded-md border border-border bg-white/[0.04] px-1.5 py-0.5 font-mono text-xs text-accent sm:px-2 sm:text-sm">
              sa
            </code>{" "}
            to sync skills, rules, and learnings across your team.
          </p>
        </div>

        <div className="mx-auto mt-8 max-w-3xl sm:mt-12">
          <InstallTerminal command={BOOTSTRAP_CMD} />
        </div>

        <SetupSteps />
      </div>
    </section>
  );
}
