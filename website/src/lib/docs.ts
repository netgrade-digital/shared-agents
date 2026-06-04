import fs from "node:fs";
import path from "node:path";

/** Monorepo root (parent of `website/`). */
export function getRepoRoot(): string {
  return path.resolve(process.cwd(), "..");
}

/** Repo `docs/` — sibling of `website/`. */
export function getDocsRoot(): string {
  return path.join(getRepoRoot(), "docs");
}

/** Additional markdown sources outside `docs/` (slug → file). */
const EXTRA_DOC_SOURCES: Record<string, string> = {
  contributing: "CONTRIBUTING.md",
};

/** Sidebar / index order (unknown slugs sort alphabetically at end). */
export const DOC_ORDER: string[] = [
  "overview",
  "installation",
  "cli-reference",
  "skills-and-rules",
  "learnings",
  "canonical-paths",
  "adapters",
  "team-setup",
  "migration-team-data",
  "shared-mcps",
  "troubleshooting",
  "contributing",
];

export type DocEntry = {
  slug: string;
  title: string;
  description: string;
  section: string;
  order: number;
};

export type DocSection = {
  title: string;
  docs: DocEntry[];
};

function parseFrontmatter(raw: string): {
  body: string;
  section?: string;
  order?: number;
} {
  if (!raw.startsWith("---\n")) return { body: raw };
  const end = raw.indexOf("\n---\n", 4);
  if (end === -1) return { body: raw };

  const fm = raw.slice(4, end);
  const body = raw.slice(end + 5);
  let section: string | undefined;
  let order: number | undefined;

  for (const line of fm.split("\n")) {
    const sectionMatch = line.match(/^section:\s*(.+)$/);
    if (sectionMatch) section = sectionMatch[1].trim().replace(/^["']|["']$/g, "");
    const orderMatch = line.match(/^order:\s*(\d+)$/);
    if (orderMatch) order = Number(orderMatch[1]);
    const sidebarSection = line.match(/^\s+section:\s*(.+)$/);
    if (sidebarSection) section = sidebarSection[1].trim().replace(/^["']|["']$/g, "");
    const sidebarOrder = line.match(/^\s+order:\s*(\d+)$/);
    if (sidebarOrder) order = Number(sidebarOrder[1]);
  }

  return { body, section, order };
}

function defaultSectionForSlug(slug: string): string {
  for (const s of DOC_SECTIONS) {
    if (s.slugs.includes(slug)) return s.title;
  }
  return "Other";
}

function defaultOrderForSlug(slug: string): number {
  const idx = DOC_ORDER.indexOf(slug);
  return idx === -1 ? 999 : idx;
}

function extractTitle(markdown: string, fallback: string): string {
  const match = markdown.match(/^#\s+(.+)$/m);
  return match?.[1]?.trim() ?? fallback;
}

function extractDescription(markdown: string): string {
  const lines = markdown.split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    return trimmed.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").slice(0, 160);
  }
  return "";
}

function humanizeSlug(slug: string): string {
  return slug
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function sortDocs(entries: DocEntry[]): DocEntry[] {
  const order = new Map(DOC_ORDER.map((s, i) => [s, i]));
  return [...entries].sort((a, b) => {
    const ai = order.get(a.slug) ?? 999;
    const bi = order.get(b.slug) ?? 999;
    if (ai !== bi) return ai - bi;
    return a.title.localeCompare(b.title);
  });
}

function readDocFile(filePath: string, slug: string): DocEntry | null {
  if (!fs.existsSync(filePath)) return null;
  const raw = fs.readFileSync(filePath, "utf8");
  const { body, section, order } = parseFrontmatter(raw);
  return {
    slug,
    title: extractTitle(body, humanizeSlug(slug)),
    description: extractDescription(body),
    section: section ?? defaultSectionForSlug(slug),
    order: order ?? defaultOrderForSlug(slug),
  };
}

export function listDocs(): DocEntry[] {
  const root = getDocsRoot();
  const entries: DocEntry[] = [];
  const seen = new Set<string>();

  if (fs.existsSync(root)) {
    for (const e of fs.readdirSync(root, { withFileTypes: true })) {
      if (!e.isFile() || !e.name.endsWith(".md")) continue;
      const slug = e.name.replace(/\.md$/, "");
      const doc = readDocFile(path.join(root, e.name), slug);
      if (doc) {
        entries.push(doc);
        seen.add(slug);
      }
    }
  }

  for (const [slug, rel] of Object.entries(EXTRA_DOC_SOURCES)) {
    if (seen.has(slug)) continue;
    const doc = readDocFile(path.join(getRepoRoot(), rel), slug);
    if (doc) entries.push(doc);
  }

  return sortDocs(entries);
}

export function getDocSlugs(): string[] {
  return listDocs().map((d) => d.slug);
}

export function getDocBySlug(slug: string): {
  slug: string;
  title: string;
  content: string;
} | null {
  const safe = slug.replace(/[^a-z0-9-]/gi, "");
  if (safe !== slug) return null;

  const docsPath = path.join(getDocsRoot(), `${slug}.md`);
  if (fs.existsSync(docsPath)) {
    const raw = fs.readFileSync(docsPath, "utf8");
    const { body } = parseFrontmatter(raw);
    return {
      slug,
      title: extractTitle(body, humanizeSlug(slug)),
      content: body,
    };
  }

  const extraRel = EXTRA_DOC_SOURCES[slug];
  if (extraRel) {
    const extraPath = path.join(getRepoRoot(), extraRel);
    if (fs.existsSync(extraPath)) {
      const raw = fs.readFileSync(extraPath, "utf8");
      const { body } = parseFrontmatter(raw);
      return {
        slug,
        title: extractTitle(body, humanizeSlug(slug)),
        content: body,
      };
    }
  }

  return null;
}

/** Docs home — merged with `/docs` (not listed in sidebar sections). */
export const DOCS_INDEX_SLUG = "overview";

/** Default section → slugs (used when frontmatter has no `section`). */
export const DOC_SECTIONS: { title: string; slugs: string[] }[] = [
  {
    title: "Getting started",
    slugs: ["installation"],
  },
  {
    title: "Daily use",
    slugs: ["cli-reference", "skills-and-rules", "learnings"],
  },
  {
    title: "Reference",
    slugs: ["canonical-paths", "adapters", "team-setup"],
  },
  {
    title: "Advanced",
    slugs: ["migration-team-data", "shared-mcps", "troubleshooting"],
  },
  {
    title: "Community",
    slugs: ["contributing"],
  },
];

const SECTION_ORDER = [
  ...DOC_SECTIONS.map((s) => s.title),
  "Other",
];

/** Group all docs into sections for sidebar + index (auto-includes unlisted docs under Other). */
export function listDocSections(): DocSection[] {
  const docs = listDocs().filter((d) => d.slug !== DOCS_INDEX_SLUG);
  const bySection = new Map<string, DocEntry[]>();

  for (const doc of docs) {
    const list = bySection.get(doc.section) ?? [];
    list.push(doc);
    bySection.set(doc.section, list);
  }

  for (const [, list] of bySection) {
    list.sort((a, b) => a.order - b.order || a.title.localeCompare(b.title));
  }

  const known = new Set(SECTION_ORDER);
  const extraSections = [...bySection.keys()]
    .filter((t) => !known.has(t))
    .sort((a, b) => a.localeCompare(b));

  const orderedTitles = [...SECTION_ORDER, ...extraSections];

  return orderedTitles
    .map((title) => ({
      title,
      docs: bySection.get(title) ?? [],
    }))
    .filter((s) => s.docs.length > 0);
}
