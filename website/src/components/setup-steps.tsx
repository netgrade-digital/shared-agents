import { CheckCircle2, RefreshCw, Terminal } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type Step = {
  num: number;
  icon: LucideIcon;
  title: string;
  body: string;
  cmd: string;
};

const STEPS: Step[] = [
  {
    num: 1,
    icon: Terminal,
    title: "Run installer",
    body: "Core, team repo, and tool adapters in one wizard.",
    cmd: "curl … | bash",
  },
  {
    num: 2,
    icon: RefreshCw,
    title: "Reload shell",
    body: "Load PATH and the sa command.",
    cmd: "source ~/.bashrc",
  },
  {
    num: 3,
    icon: CheckCircle2,
    title: "Verify",
    body: "Check adapters and symlinks.",
    cmd: "sa check",
  },
];

export function SetupSteps() {
  return (
    <div className="mt-10 sm:mt-16">
      <ol className="relative grid gap-8 sm:gap-10 md:grid-cols-3 md:gap-6">
        <span
          className="absolute left-[16.67%] right-[16.67%] top-5 hidden h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent md:block"
          aria-hidden
        />

        {STEPS.map((step) => {
          const Icon = step.icon;
          return (
            <li
              key={step.num}
              className="relative flex flex-col items-center text-center"
            >
              <div className="relative z-10 flex size-10 items-center justify-center rounded-full border-2 border-accent/50 bg-background font-mono text-sm font-semibold text-accent shadow-[0_0_20px_-4px_rgba(0,229,255,0.5)]">
                {step.num}
              </div>

              <div className="mt-4 flex size-9 items-center justify-center rounded-lg border border-border/80 bg-surface/60 text-accent sm:mt-5">
                <Icon className="size-4" strokeWidth={1.75} aria-hidden />
              </div>

              <h3 className="mt-3 text-base font-semibold tracking-tight">
                {step.title}
              </h3>
              <p className="mt-1.5 max-w-[260px] px-2 text-sm leading-relaxed text-muted">
                {step.body}
              </p>

              <code className="mt-3 inline-block max-w-full truncate rounded-lg border border-border/80 bg-black/50 px-3 py-2 font-mono text-xs text-accent/95 sm:mt-4">
                {step.cmd}
              </code>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
