"use client";

import { useEffect, useState } from "react";
import { SharedAgentsLogo } from "@/components/shared-agents-logo";

const MIN_VISIBLE_MS = 1600;
const EXIT_MS = 680;

/** Real sync steps — product vocabulary, not decorative filler */
const SYNC_STEPS = [
  { label: "sa sync", detail: "pull team repo" },
  { label: "skills", detail: "~/.agents/skills" },
  { label: "rules", detail: "team/rules" },
  { label: "learnings", detail: "index.yaml" },
  { label: "ready", detail: "" },
] as const;

export function Preloader() {
  const [phase, setPhase] = useState<"visible" | "exit" | "hidden">("visible");
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (phase !== "visible") return;

    const id = window.setInterval(() => {
      setStepIndex((i) => (i + 1) % SYNC_STEPS.length);
    }, 420);

    return () => window.clearInterval(id);
  }, [phase]);

  useEffect(() => {
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    let exited = false;
    const start = Date.now();

    const finish = () => {
      if (exited) return;
      exited = true;
      const elapsed = Date.now() - start;
      const wait = Math.max(0, MIN_VISIBLE_MS - elapsed);
      window.setTimeout(() => {
        setPhase("exit");
        window.setTimeout(() => {
          document.body.style.overflow = prevOverflow;
          setPhase("hidden");
        }, EXIT_MS);
      }, wait);
    };

    if (document.readyState === "complete") {
      finish();
    } else {
      window.addEventListener("load", finish, { once: true });
    }

    const fallback = window.setTimeout(finish, 3400);
    return () => {
      document.body.style.overflow = prevOverflow;
      window.removeEventListener("load", finish);
      window.clearTimeout(fallback);
    };
  }, []);

  if (phase === "hidden") return null;

  const step = SYNC_STEPS[stepIndex];
  const exiting = phase === "exit";

  return (
    <div
      className={`preloader-root fixed inset-0 z-[100] flex items-center justify-center bg-background ${
        exiting ? "preloader-root--exit" : ""
      }`}
      aria-hidden={exiting}
      aria-busy={!exiting}
      role="status"
    >
      <div className="preloader-field pointer-events-none absolute inset-0" aria-hidden>
        <div className="preloader-field-rings" />
        <div className="preloader-field-grid" />
        <div className="preloader-field-glow" />
      </div>

      <div
        className={`preloader-stage relative z-10 flex flex-col items-center ${
          exiting ? "preloader-stage--exit" : ""
        }`}
      >
        <div className="preloader-logo-stage relative">
          <div className="preloader-halo" aria-hidden />
          <div className="preloader-ring preloader-ring--a" aria-hidden />
          <div className="preloader-ring preloader-ring--b" aria-hidden />
          <SharedAgentsLogo
            className="preloader-logo relative z-10 max-sm:scale-[0.73] max-sm:origin-center"
            size={120}
            priority
          />
        </div>

        <div className="preloader-copy mt-8 text-center sm:mt-10">
          <p className="text-[10px] font-medium uppercase tracking-[0.22em] text-muted/80 sm:text-[11px] sm:tracking-[0.32em]">
            Shared Agents
          </p>
          <p
            className="preloader-status mt-4 font-mono text-sm tabular-nums text-foreground"
            aria-live="polite"
          >
            <span className="text-accent">{step.label}</span>
            {step.detail ? (
              <span className="text-muted"> · {step.detail}</span>
            ) : null}
          </p>
        </div>

        <div className="preloader-track mt-8" aria-hidden>
          {SYNC_STEPS.map((s, i) => (
            <span
              key={s.label}
              className={`preloader-tick ${
                i <= stepIndex ? "preloader-tick--on" : ""
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
