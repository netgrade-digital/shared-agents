/** GitHub Pages project site base path (e.g. `/shared-agents`), empty locally. */
export function getBasePath(): string {
  return process.env.NEXT_PUBLIC_BASE_PATH ?? "";
}

/** Canonical site URL for metadata and OG tags. */
export function getSiteUrl(): string {
  if (process.env.NEXT_PUBLIC_SITE_URL) {
    return process.env.NEXT_PUBLIC_SITE_URL.replace(/\/$/, "");
  }
  const base = getBasePath();
  if (base) {
    return `https://netgrade-digital.github.io${base}`;
  }
  return "http://localhost:3000";
}
