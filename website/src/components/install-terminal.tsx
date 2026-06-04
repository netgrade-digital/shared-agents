"use client";

import { Check, Copy } from "lucide-react";
import { useCallback, useState } from "react";

type InstallTerminalProps = {
  command: string;
};

function highlightCommand(cmd: string) {
  const pipeIdx = cmd.indexOf(" | ");
  if (pipeIdx === -1) {
    return <span className="text-foreground/95">{cmd}</span>;
  }
  const curlPart = cmd.slice(0, pipeIdx);
  const pipePart = cmd.slice(pipeIdx);
  return (
    <>
      <span className="text-foreground/95">{curlPart}</span>
      <span className="text-accent">{pipePart}</span>
    </>
  );
}

export function InstallTerminal({ command }: InstallTerminalProps) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2200);
    } catch {
      /* clipboard unavailable */
    }
  }, [command]);

  return (
    <div className="install-terminal overflow-hidden rounded-xl border border-white/[0.08] shadow-[0_0_60px_-24px_rgba(0,229,255,0.4)] sm:rounded-2xl">
      <div className="flex flex-col gap-3 border-b border-white/[0.06] bg-[#0c0c10] px-3 py-3 min-[420px]:flex-row min-[420px]:items-center min-[420px]:justify-between sm:gap-4 sm:px-5">
        <div className="flex min-w-0 items-center gap-2.5 sm:gap-3">
          <div className="flex shrink-0 gap-1.5" aria-hidden>
            <span className="size-2.5 rounded-full bg-[#ff5f57]" />
            <span className="size-2.5 rounded-full bg-[#febc2e]" />
            <span className="size-2.5 rounded-full bg-[#28c840]" />
          </div>
          <span className="truncate font-mono text-[11px] text-muted sm:text-xs">
            install — shared-agents
          </span>
        </div>
        <button
          type="button"
          onClick={copy}
          className="inline-flex h-11 w-full shrink-0 items-center justify-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.04] px-3 text-xs font-medium text-foreground/90 transition-colors hover:border-accent/40 hover:bg-accent/10 hover:text-accent min-[420px]:h-9 min-[420px]:w-auto"
        >
          {copied ? (
            <>
              <Check className="size-3.5" strokeWidth={2.5} />
              Copied
            </>
          ) : (
            <>
              <Copy className="size-3.5" strokeWidth={2} />
              Copy
            </>
          )}
        </button>
      </div>

      <div className="relative bg-[#030306] px-3 py-4 sm:px-5 sm:py-6">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px)",
            backgroundSize: "100% 28px",
          }}
          aria-hidden
        />
        <div className="relative overflow-hidden rounded-lg border border-white/[0.05] bg-black/60 sm:rounded-xl">
          <div className="overflow-x-auto p-3 [-webkit-overflow-scrolling:touch] [scrollbar-color:rgba(0,229,255,0.35)_transparent] [scrollbar-width:thin] sm:p-5">
            <p className="whitespace-nowrap font-mono text-[11px] leading-relaxed sm:text-[13px]">
              <span className="text-[#7ee787]">$</span>{" "}
              {highlightCommand(command)}
            </p>
          </div>
          <div
            className="pointer-events-none absolute inset-y-0 right-0 w-10 bg-gradient-to-l from-black/80 to-transparent sm:w-16"
            aria-hidden
          />
        </div>
      </div>
    </div>
  );
}
