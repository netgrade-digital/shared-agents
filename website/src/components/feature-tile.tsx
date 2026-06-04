import type { LucideIcon } from "lucide-react";

type FeatureTileProps = {
  icon: LucideIcon;
  label: string;
  value: string;
};

export function FeatureTile({ icon: Icon, label, value }: FeatureTileProps) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-transparent p-3 transition-colors hover:border-border hover:bg-white/[0.02] sm:gap-4">
      <div className="flex size-9 shrink-0 items-center justify-center text-accent sm:size-10">
        <Icon className="size-5 sm:size-6" strokeWidth={1.5} aria-hidden />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-muted sm:text-sm">{label}</p>
        <p className="text-sm font-semibold tracking-tight text-foreground sm:text-base">
          {value}
        </p>
      </div>
    </div>
  );
}
