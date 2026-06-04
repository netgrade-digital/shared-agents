import Image from "next/image";

const LOGO_SRC = `${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/shared-agents.svg`;

type SharedAgentsLogoProps = {
  className?: string;
  size?: number;
  /** Slow rotation (preloader) */
  animated?: boolean;
  priority?: boolean;
};

export function SharedAgentsLogo({
  className = "",
  size = 72,
  animated = false,
  priority = false,
}: SharedAgentsLogoProps) {
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center ${
        animated ? "logo-ring-spin" : ""
      } ${className}`}
      style={{ width: size, height: size }}
    >
      <Image
        src={LOGO_SRC}
        alt=""
        width={size}
        height={size}
        priority={priority}
        className="size-full object-contain"
        aria-hidden
      />
    </span>
  );
}
