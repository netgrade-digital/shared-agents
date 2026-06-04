# Canonical paths

**Single source of truth** for file paths in Shared Agents. Agents and scripts must use these paths — not the Cursor workspace, not a client project root.

Environment variable:

```bash
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
```

Default: `~/.shared-agents`

---

## Required paths

| What | Absolute path | Who writes |
|------|---------------|------------|
| Core skills (OSS) | `$SHARED_AGENTS_HOME/skills/` | Upstream (PR to Core) |
| Team skills | `$SHARED_AGENTS_HOME/team/skills/` | Private team repo |
| Team rules | `$SHARED_AGENTS_HOME/team/rules/` | Private team repo (flat, like skills) |
| Core rules | `$SHARED_AGENTS_HOME/rules/` | Upstream (PR to Core) |
| Learnings index | `$SHARED_AGENTS_HOME/team/learnings/index.yaml` | Human / **`sa review`** |
| Learnings **approved** | `$SHARED_AGENTS_HOME/team/learnings/approved/` | **Humans only** (`sa review`) |
| Learnings **pending** | `$SHARED_AGENTS_HOME/team/learnings/pending/` | **Agents** (after explicit yes) |
| Local config | `$SHARED_AGENTS_HOME/config.local.yaml` | Installer / **`sa bootstrap`** (gitignored) |
| Team data (private) | `$SHARED_AGENTS_HOME/team/` | Separate Git remote — **never** push to Core |
| Sync script | `$SHARED_AGENTS_HOME/scripts/sync.sh` | Hook / agent / **`sa sync`** |
| Adapter manifest | `$SHARED_AGENTS_HOME/adapters/manifest.json` | Maintainers (PR) |
| MCP manifest (draft) | `$SHARED_AGENTS_HOME/mcps/manifest.example.json` | Maintainers (PR) |
| MCP local (gitignored) | `$SHARED_AGENTS_HOME/mcps.local.yaml` | User |

---

## Rule: learnings always use `$SHARED_AGENTS_HOME`

Agents **must** place learning drafts here:

```text
${SHARED_AGENTS_HOME}/team/learnings/pending/YYYY-MM-DD-short-slug.md
```

Resolve via CLI: `sa pending path <slug>` (uses `config.local.yaml` or solo fallback).

Learnings are **not** in the Core repo — only in the private team clone under `team/`. See [Learnings](/docs/learnings).

### Do not

- Commit learnings to the **Cursor workspace** or the **Core repo**
- Write learnings into a dev checkout `Development/…/shared-agents/` when that is **not** `$SHARED_AGENTS_HOME`
- Store learnings in a **client project** (`.cursor/`, `docs/`, project root)
- Use relative paths like `learnings/pending/foo.md` without resolving `$SHARED_AGENTS_HOME`
- Write directly to `learnings/approved/`

### Before writing

1. Resolve the path: `sa pending path <slug>` or `"${SHARED_AGENTS_HOME}/team/learnings/pending/…"`
2. Optionally ensure the target directory exists
3. **Do not** assume workspace root equals `$SHARED_AGENTS_HOME`

### Two clones (typical setup)

| Path | Role |
|------|------|
| `~/.shared-agents/` | **Runtime** — sync, hooks, agents write learnings **here** |
| `~/Development/…/shared-agents/` | **Dev checkout** — Core development (README, scripts, docs) |

Git commits for a learning usually happen in the clone where the file lives (often `~/.shared-agents`). The **write location** is always `$SHARED_AGENTS_HOME`.

```bash
sa pending path 2026-06-02-my-slug
# → /home/you/.shared-agents/team/learnings/pending/2026-06-02-my-slug.md
```

Shell CLI (after **`sa install`**): **`sa`** · `shared-agents` · `sharedagents` — bare **`sa`** runs **`sa help`**.  
Full reference: skill **`sa-cli`** · live help: **`sa help`**

---

## Rule: reading (retrieve)

Before non-trivial tasks:

1. **`sa sync`** — pulls Core + team and links skills & rules
2. Read `$SHARED_AGENTS_HOME/team/learnings/index.yaml`
3. Search `$SHARED_AGENTS_HOME/team/learnings/approved/`

Do not search only inside the IDE workspace.

---

## Rule: rules work like skills (no review workflow)

Team rules live flat in `$SHARED_AGENTS_HOME/team/rules/*.mdc` — **no** `pending/` / `approved/` (only learnings use that).

On **`sa sync`** (daily) or **`sa install`** (first setup):

| Adapter type | Installation |
|--------------|--------------|
| **Cursor** | Symlinks → `~/.cursor/rules/*.mdc` |
| **AGENTS.md / CLAUDE.md** (Zed, Codex, Claude Code, Gemini, Windsurf, …) | Marker block `<!-- shared-agents:team-rules:begin/end -->` |
| **Dedicated target file** (no symlink, Cursor) | **Not overwritten** |

Sources: `$SHARED_AGENTS_HOME/rules/` (Core) + `$SHARED_AGENTS_HOME/team/rules/` (team).

`shared-agents-knowledge.mdc` is **not** duplicated in AGENTS.md/CLAUDE.md tools — those use `<!-- shared-agents:begin -->` (sync/learnings).

Optional frontmatter: `targets: [zed, claude-code, cursor]` — empty means all adapters.

Workflow: add file under `team/rules/` → commit/push → teammates run **`sa sync`**.

**`sa install`** is still required for first-time setup (hooks, base AGENTS.md/CLAUDE.md blocks, new tools).

## Rule: skill symlinks

Installed skills under `~/.agents/skills/` etc. point at `$SHARED_AGENTS_HOME/skills/`. Edit the source under `$SHARED_AGENTS_HOME/skills/` (or a dev checkout synced via pull).

---

## See also

- [Learnings](/docs/learnings) — workflow
- [Repository README](https://github.com/netgrade-digital/shared-agents/blob/main/README.md) — overview
- [sa-cli skill](https://github.com/netgrade-digital/shared-agents/blob/main/skills/sa-cli/SKILL.md) — CLI guide
- [capture-learning skill](https://github.com/netgrade-digital/shared-agents/blob/main/skills/capture-learning/SKILL.md)
