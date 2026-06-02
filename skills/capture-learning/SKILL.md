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
PENDING="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/learnings/pending/YYYY-MM-DD-short-slug.md
# Or:
"$SHARED_AGENTS_HOME/scripts/learning-path.sh" YYYY-MM-DD-short-slug
```

### Mandatory

1. Write **only** under `$SHARED_AGENTS_HOME/learnings/pending/` (default: `~/.shared-agents/learnings/pending/`).
2. Use the **absolute** path in the Write/edit tool — not `learnings/pending/…` from the open project.
3. **Do not** write to the Cursor workspace or dev checkout unless it is the same directory as `$SHARED_AGENTS_HOME` (verify with `realpath` or `learning-path.sh`).

### Forbidden

- `Development/Work/shared-agents/learnings/pending/` when `$SHARED_AGENTS_HOME` is `~/.shared-agents`
- Customer project repos (`.cursor/`, project `docs/`, etc.)
- `learnings/approved/` (human/PR only)

**Never write to `approved/`** — that is human/PR territory.

## File format

```markdown
---
id: project-YYYY-MM-short-slug
project: project-name
domain: [tag1, tag2]
tags: [keyword1, keyword2]
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

## After writing — tell the user

1. File is in **`pending/`** — not team knowledge yet.
2. Next steps for humans:
   - Review + approve: `scripts/review-learning.sh learnings/pending/<file>.md`
   - Commit + PR → merge to `main`
3. After merge + sync, all agents find it in **`approved/`**.

## pending vs approved

| | pending/ | approved/ |
|---|----------|-----------|
| Who writes | Agent (after user says yes) | Human via PR |
| Used by agents | **No** | **Yes** |
| Purpose | Draft / proposal | Team truth |
