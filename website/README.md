# Shared Agents — Website

Marketing and onboarding site for [Shared Agents](https://github.com/netgrade-digital/shared-agents). Visual design follows the repo banner (`docs/assets/shared-agents-banner.png`): dark background, cyan accents, feature grid.

## Stack

- [Next.js](https://nextjs.org/) (App Router)
- [Bun](https://bun.sh/) (package manager & runtime)
- [Tailwind CSS](https://tailwindcss.com/) v4
- [Lucide React](https://lucide.dev/) icons

## Develop

```bash
cd website
bun install
bun run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build

```bash
bun run build
```

Local preview (default build, no base path):

```bash
bun run build
bun run preview
```

Open http://localhost:3000

> `next start` is not used — the site is exported as static HTML (`output: "export"`).

## Deploy (GitHub Pages)

On push to `main` (paths: `website/`, `docs/`, `CONTRIBUTING.md`), the workflow [`.github/workflows/deploy-website.yml`](../.github/workflows/deploy-website.yml) builds and deploys to GitHub Pages.

**One-time repo setup**

1. GitHub → **Settings** → **Pages** → **Build and deployment** → Source: **GitHub Actions**
2. After the first successful run, the site is live at  
   **https://netgrade-digital.github.io/shared-agents/**

**Test GitHub Pages build locally**

```bash
bun run build:pages
bun run preview:pages
```

Open **http://localhost:3000/shared-agents/** (the preview script rewrites `/shared-agents/*` like GitHub Pages).

Do **not** use `bunx serve out` for `build:pages` — assets are at `out/_next/` but HTML references `/shared-agents/_next/`, so CSS/JS return 404 without the rewrite.

## Lint

```bash
bun run lint
```

## Documentation pages

`/docs` renders every `*.md` file in the repo’s [`docs/`](../docs/) folder at build time (English, website-oriented). Sidebar categories come from `DOC_SECTIONS` in `src/lib/docs.ts` (new files land in **Other** until assigned). Optional frontmatter:

```yaml
---
section: Reference
order: 10
---
```

Deploy note: build from the monorepo layout (`website/` next to `docs/`).
