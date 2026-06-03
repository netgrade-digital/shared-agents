---
name: shared-agents-knowledge
description: >-
  Sync and use the shared-agents repo (team skills, rules + learnings).
  Use at session start, when loading team knowledge, searching learnings,
  or when the user mentions shared-agents, shared learnings, or team knowledge.
---

# Shared Agents Knowledge

Path: `$SHARED_AGENTS_HOME` (default: `~/.shared-agents`)

## Automatic sync (always — no user action)

**Every session, first step:** run sync before anything else.

```bash
"${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/scripts/sync.sh" pull
```

Pulls **Core** (`~/.shared-agents`) and **Team** (`~/.shared-agents/team/`) when configured.

- Do not ask the user to sync manually.
- Do not skip because "probably up to date".
- Offline/errors: continue with local files; note only if learnings may be stale.

IDE hooks also pull on session start (Cursor `sessionStart`, Claude `SessionStart`). Agent must still sync if hooks may not have run (subagents, headless).

## Retrieve (before non-trivial tasks)

1. Sync (pull) — always first.
2. Read `team/learnings/index.yaml` for `project`, `domain`, `tags`, `versions`.
3. Grep `team/learnings/approved/` for task keywords.
4. Prefer learnings whose `versions` match the project's stack (exact patch or same MAJOR.MINOR.PATCH line); treat `experimental` confidence as hints.
5. Summarize briefly — do not dump the whole repo.

## Capture (after non-trivial tasks — ask first)

**Always ask** after substantive tasks:

> „Soll ich ein Team-Learning in shared-agents anlegen?"

| User says | Action |
|-----------|--------|
| **Yes** / „ja" / „learning speichern" | Write to team `pending/` (see below) |
| **No** | Do nothing |

Also capture when user explicitly asks anytime.

When writing:

1. Activate skill `capture-learning`.
2. Resolve path: `sa pending path YYYY-MM-DD-short-slug` (see [docs/canonical-paths.md](../../docs/canonical-paths.md) — **never** workspace-relative; not in Core-Repo).
3. Never write directly to `approved/`.
4. Remind user: teammate runs **`sa review`** → `approved/` → then all agents can use it.

For shell commands (install, review, pending push): skill **`sa-cli`** or run **`sa help`**.
## Headless agents (OpenClaw)

Wrap commands with entrypoint (sync then exec):

```bash
"$SHARED_AGENTS_HOME/scripts/agent-entrypoint.sh" <your-agent-command>
```

Or first line of agent run: `sync.sh pull`.

## Boundaries

No secrets, API keys, or customer PII in learnings.
