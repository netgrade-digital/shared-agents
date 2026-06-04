"use client";

import { Check, Copy } from "lucide-react";
import { useCallback, useState } from "react";

type CopyCommandProps = {
  command: string;
  label?: string;
};

export function CopyCommand({ command, label = "Copy" }: CopyCommandProps) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(command);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  }, [command]);

  return (
    <div className="group relative rounded-xl border border-border bg-surface/80 glow-accent">
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-2.5">
        <span className="font-mono text-xs text-muted">terminal</span>
        <button
          type="button"
          onClick={copy}
          className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs text-muted transition-colors hover:bg-white/5 hover:text-accent"
          aria-label={copied ? "Copied" : label}
        >
          {copied ? (
            <>
              <Check className="size-3.5 text-accent" strokeWidth={2} />
              <span className="text-accent">Copied</span>
            </>
          ) : (
            <>
              <Copy className="size-3.5" strokeWidth={2} />
              <span>{label}</span>
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-4 font-mono text-sm leading-relaxed text-foreground/90">
        <code>{command}</code>
      </pre>
    </div>
  );
}
