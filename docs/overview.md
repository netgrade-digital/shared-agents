# Overview

Shared Agents gives your team **one Git-synced home** for AI assistant knowledge: skills (workflows), rules (instructions), and learnings (institutional memory). It works across Cursor, Claude Code, Zed, Codex, and other tools without locking you to a single vendor.

## The problem

Teams use many AI tools. Each session starts cold — no shared workflows, no memory of past bugs or decisions, and knowledge trapped in chats or private notes.

## The solution

| Piece | What it is | Where it lives |
|-------|------------|----------------|
| **Core** | Open-source CLI (`sa`), adapters, shared skills & rules | Public GitHub repo |
| **Team** | Learnings, team rules, team-only skills | **Private** Git remote → `~/.shared-agents/team/` |
| **Local install** | Your machine’s runtime copy | `~/.shared-agents` (or `$SHARED_AGENTS_HOME`) |

After bootstrap, teammates run **`sa sync`** to pull Core + team content and link skills/rules into each IDE.

## Core concepts

### Skills

Repeatable agent workflows (Markdown under `skills/`). Example: `sa-cli`, `capture-learning`, `shopware-workflow`.

- **Core skills** — public, contributed via PR
- **Team skills** — private, `sa skill new` → `team/skills/<name>/SKILL.md`

### Rules

Shared instructions per tool. Cursor uses `.mdc` symlinks; other tools get merged blocks in `AGENTS.md` / `CLAUDE.md`.

- **Core rules** — `rules/*.mdc`
- **Team rules** — flat `team/rules/*.mdc` (no review workflow)

### Learnings

What the team already figured out (bugs, stack quirks, decisions). Human-in-the-loop:

1. Agent drafts → `team/learnings/pending/` (after you say yes)
2. Human approves → **`sa review`** → `approved/`
3. Agents read only **approved** learnings

See [Learnings](/docs/learnings).

## Architecture

```text
  GitHub (Core)              Your private remote (Team)
        │                              │
        └────────── sa sync ───────────┘
                        │
                        ▼
              ~/.shared-agents  ──►  Cursor · Claude Code · Zed · …
```

## Repository layout

```text
shared-agents/
├── skills/           # Core skills
├── rules/            # Core rules
├── adapters/         # Per-tool wiring (manifest.json)
├── scripts/          # sa CLI, sync, bootstrap
├── docs/             # This documentation (website + repo)
└── team/             # Private data (separate Git remote)
    ├── learnings/    # pending/ + approved/
    ├── rules/        # flat *.mdc
    └── skills/
```

## Quick commands

| Task | Command |
|------|---------|
| First-time setup | See [Installation](/docs/installation) |
| Pull latest + link skills/rules | `sa sync` |
| Adapter health | `sa check` |
| Full CLI reference | [CLI reference](/docs/cli-reference) or `sa help` |

## Next steps

1. [Install Shared Agents](/docs/installation)
2. [Set up your team repo](/docs/team-setup)
3. [Configure adapters](/docs/adapters) for your IDEs
4. [Contributing](/docs/contributing) if you improve Core
