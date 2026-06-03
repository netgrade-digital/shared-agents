---
name: capture-learning
description: >-
  Create a team learning after user confirms. Use when the user says "learning
  speichern", "ja" to creating a learning, "capture learning", or "team learning".
  After non-trivial tasks, only write after explicit user approval.
---

# Capture Learning

Write team learnings to **`pending/`** — drafts awaiting human review.

## Ask first (required)

After non-trivial tasks, the agent must **ask**:

> „Soll ich ein Team-Learning in shared-agents anlegen?"

**Only write if the user says yes.** Never silently write to pending.

## When content is worth capturing

Propose when **all** apply:

- Insight is reusable beyond this session
- Would help a teammate or future agent
- No secrets or customer-specific data

Skip when trivial, already documented, or user said no.

## Where to write (pending only)

**Canonical path only** — see [docs/canonical-paths.md](../../docs/canonical-paths.md).

```bash
# Resolve before write (never use workspace-relative paths):
sa pending path YYYY-MM-DD-short-slug
# Or: "$SHARED_AGENTS_HOME/scripts/learning-path.sh" YYYY-MM-DD-short-slug
```

### Mandatory

1. Write **only** under the path from `sa pending path` (typically `$SHARED_AGENTS_HOME/team/learnings/pending/`).
2. Use the **absolute** path in the Write/edit tool — not paths from the open project or Core dev checkout.
3. **Do not** commit learnings into the public Core-Repo.

### Forbidden

- `Development/Work/shared-agents/learnings/` (Core has no learnings)
- Customer project repos (`.cursor/`, project `docs/`, etc.)
- `approved/` (human/PR only)

**Never write to `approved/`** — that is human/PR territory.

## File format

```markdown
---
id: project-YYYY-MM-short-slug
project: project-name
domain: [tag1, tag2]
tags: [keyword1, keyword2]
versions: [shopware:6.6.10, php:8.3.14]
confidence: high
source: task
created: YYYY-MM-DD
author: github-or-name
---

## Kontext
What problem or situation triggered this.

## Erkenntnis
The reusable insight in 1–3 sentences.

## Anwendung
Concrete steps or rule of thumb for next time.

## Links
- path/to/file or PR URL (optional)
```

### Versions (required when a stack applies)

Always set **`versions:`** for framework/runtime-specific learnings. Use `[]` only when no stack version is relevant (e.g. pure process/infra docs).

Format: list of `name:version` pairs (compatible with flat frontmatter parsing):

```yaml
versions: [shopware:6.6.10, php:8.3.14]
versions: [laravel:11.31.0, php:8.3.14]
versions: [vue:3.4.27, node:20.18.1]
versions: []   # no stack — OK for shared-agents workflow, MCP setup, etc.
```

**Version format (mandatory for stack entries):**

- **Full patch level** — `6.6.10`, not `6.6.x` or `6.6`
- **Minimum `MAJOR.MINOR.PATCH`** (three numeric segments), e.g. `11.31.0`, `3.4.27`
- **Fourth segment** only when the product publishes it (e.g. Shopware `6.6.10.0`); trailing `.0` may be dropped → `6.6.10`
- **No wildcards** (`x`, `*`) — always the version the insight was verified against

Common keys: `shopware`, `laravel`, `symfony`, `vue`, `nuxt`, `react`, `nextjs`, `php`, `node`, `wordpress`, `typo3`, `magento`.

**How to determine:** read from the project (`composer.json`, `composer.lock`, `package.json`, Shopware Admin/CLI `bin/console --version`). Use the exact version from the environment where the learning was validated.

## After writing — mandatory publish

After creating the file, **always** push pending for team review:

```bash
"$SHARED_AGENTS_HOME/scripts/publish-pending-learning.sh" YYYY-MM-DD-short-slug.md
```

Or: `sa pending push <datei>`

This commits + pushes **only** the team repo (`team/learnings/pending/`) — teammates run `sa sync` and `sa review`.

## After writing — tell the user

1. File is in **`pending/`** — **not** team knowledge for agents yet (not in `approved/`).
2. After publish: teammates can **`sa sync`** → **`sa review`**.
3. Only **`approved/`** after review becomes team truth.

## pending vs approved

| | pending/ | approved/ |
|---|----------|-----------|
| Who writes | Agent (after user says yes) | Human via `sa review` |
| Git | Auto commit+push via `sa pending push` | Auto commit+push via `sa review` |
| Used by agents | **No** | **Yes** |
| Purpose | Draft for team review | Team truth |
