export function HeroBackground() {
  return (
    <div
      className="pointer-events-none absolute inset-0 overflow-hidden"
      aria-hidden
    >
      <div className="absolute -left-1/4 top-1/2 h-[140%] w-[140%] -translate-y-1/2 opacity-[0.07]">
        <svg
          className="h-full w-full text-accent"
          viewBox="0 0 800 800"
          fill="none"
        >
          {[120, 200, 280, 360, 440, 520].map((r) => (
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
      <div className="absolute right-0 top-0 h-[500px] w-[500px] translate-x-1/4 -translate-y-1/4 rounded-full bg-accent/[0.04] blur-3xl" />
      <div className="absolute bottom-0 left-1/3 h-[300px] w-[400px] rounded-full bg-accent/[0.03] blur-3xl" />
    </div>
  );
}
