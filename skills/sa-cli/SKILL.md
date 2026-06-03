---
name: sa-cli
description: >-
  Complete guide to the shared-agents shell CLI (sa). Use when the user asks
  how to run sa, sa help, install, sync, review, pending, unapprove, check,
  uninstall, status, or any shared-agents terminal command. Also use when explaining
  setup, wizard, or troubleshooting the CLI after sa install.
---

# shared-agents CLI (`sa`)

**Canonical live help:** run **`sa`** or **`sa help`** — prefer that over memorizing flags.

```bash
sa                  # help overview (default)
sa help             # same
shared-agents …     # alias
sharedagents …      # alias
```

Without shell aliases (agents, CI, fresh shell):

```bash
"${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/scripts/sa" help
```

Repo root (dev checkout): **`./sa`** · **`./sa install`**

Env: **`SHARED_AGENTS_HOME`** (default `~/.shared-agents`) · Version: **`sa version`**

---

## First-time setup

**Recommended (Core + private team repo + adapters):**

```bash
curl -fsSL https://raw.githubusercontent.com/netgrade-digital/shared-agents/refs/heads/main/scripts/bootstrap.sh | bash
# Piped curl uses /dev/tty for the wizard when possible (TUI or text prompts).
# Force auto-install only: SA_BOOTSTRAP_NON_INTERACTIVE=1 curl … | bash
# or after clone: ./scripts/bootstrap.sh  ·  sa bootstrap
source ~/.bashrc
sa check
sa team verify    # optional but useful after bootstrap
```

**Classic (Core only, then wizard — team repo optional in wizard):**

```bash
git clone git@bitbucket.org:netgrade/shared-agents.git ~/.shared-agents
cd ~/.shared-agents
./sa install
source ~/.bashrc
```

**From dev checkout without `~/.shared-agents` yet:** `./sa install` — wizard runs **before** clone; cancel leaves no `~/.shared-agents`.

**New AI tool installed?** → run **`sa install`** again.

---

## Commands (overview)

| Area | Command | Summary |
|------|---------|---------|
| Info | `sa` · `sa help` | All commands |
| Info | `sa version` | CLI version + HOME |
| Setup | `sa bootstrap` | Full first-time setup (Core + team + adapters) |
| Setup | `sa install` | Setup wizard (default in TTY) |
| Setup | `sa install --non-interactive` | All detected tools, no prompts |
| Setup | `sa install --wizard` | Wizard explicitly |
| Setup | `sa check` | Tool installed vs configured (+ team warnings) |
| Setup | `sa sync` | Pull Core + team; link skills + rules |
| Setup | `sa status` | Open items: review, skills, adapters, team |
| Setup | `sa team verify` | Deep team repo validation |
| Setup | `sa team migrate` | Legacy `learnings/` → `team/learnings/` |
| Setup | `sa uninstall` | Uninstall (y/N) |
| Learnings | `sa review` | Interactive: pending → approved |
| Learnings | `sa review list` | Pending list |
| Learnings | `sa review dry [file]` | Dry-run |
| Learnings | `sa pending push [file]` | Commit + push pending |
| Learnings | `sa pending path [slug]` | Canonical pending path |
| Learnings | `sa unapprove [id\|file]` | Remove from approved |
| Learnings | `sa unapprove list` | Approved list |
| Team content | `sa skill new` | Wizard: `team/skills/<name>/SKILL.md` |
| Team content | `sa skill rm [name]` | Remove team skill |
| Team content | `sa skill list` | List team skills |
| Team content | `sa rule new` | Wizard: `team/rules/<slug>.mdc` |
| Team content | `sa rule rm [slug]` | Remove team rule |
| Team content | `sa rule list` | List team rules |

Alias: **`sa install`** = **`sa setup`**

---

## Status — `sa status`

Shows easy-to-forget work:

| Check | Meaning | Action |
|-------|---------|--------|
| Pending learnings | `team/learnings/pending/` (team repo) | `sa review list` · `sa review` |
| Not pushed yet | Local pending changes | `sa pending push` |
| Team setup | Config / legacy layout | `sa team verify` · `sa team migrate` |
| Skill symlinks | New skill not linked | `sa sync` (or `sa install` first time) |
| Rule symlinks | New rule not linked | `sa sync` (or `sa install` first time) |
| Adapters | Tool present, not configured | `sa install` |

```bash
sa status              # full list (or “all clear ✓”)
sa status --brief      # one line
sa status --quiet      # print only when action needed (exit 1)
sa status --json       # CI / scripts
```

**After `sa sync` (non-quiet):** runs `sa status --quiet` for a short terminal hint.

Cursor/Claude hooks sync quietly (`--quiet`); the **rule** reminds agents to run **`sa status --brief`** and tell you briefly if needed.

**`sa check` vs `sa team verify`:** `check` uses quick `check_team_setup()` warnings; **`sa team verify`** is stricter (folders, index, origin, `--strict`).

---

## Setup — `sa install`

Calls `install.sh` (manifest-driven, idempotent).

### Wizard (recommended, TTY)

```bash
sa install
```

| Step | Controls |
|------|----------|
| Install path | Type path · Enter |
| Agents | `↑↓` · **Space** toggle · `a` all · `d` detected · Enter |
| Team repo URL | Optional private remote for learnings |
| Shell CLI | `←→` / `↑↓` Yes/No · Enter |
| Summary | `↑↓` Run/Cancel · Enter (default: Cancel) |

- **Cursor / VS Code terminal:** often plain text wizard (`SA_WIZARD_PLAIN=1`)
- **foot / alacritty:** TUI with arrow keys

### Quick / CI

```bash
sa install --non-interactive
sa install --non-interactive --tools cursor,claude-code
sa install --dry-run
sa install --dry-run --wizard
```

### Install flags (passed through to `install.sh`)

| Flag | Meaning |
|------|---------|
| `--home DIR` | Target path (default: `~/.shared-agents`) |
| `--source DIR` | Source repo (dev checkout) |
| `--shell-rc FILE` | bashrc for `SHARED_AGENTS_HOME` + `sa` |
| `--tools IDS` | Comma-separated adapter IDs only |
| `--check` | Status instead of install (`sa check`) |
| `--check --json` | JSON for CI |
| `--dry-run` | Preview, no writes |

Low-level: `./install.sh` at repo root — same options.

---

## Check — `sa check`

```bash
sa check
sa check --json
sa install --check    # same
```

| STATUS | Meaning |
|--------|---------|
| `ok` | Tool present + shared-agents configured |
| `missing_tool` | CLI/config not found |
| `not_configured` | Tool present, adapter missing → `sa install` |
| `available` | generic fallback |

Team warnings appear under **Team data:** when relevant.

---

## Sync — `sa sync`

```bash
sa sync
# = scripts/sync.sh pull
#   1) git pull  ~/.shared-agents        (Core — tools, adapters, OSS skills)
#   2) git pull  ~/.shared-agents/team/  (Team — learnings, team skills, team rules)
#   3) sync-links — skill symlinks, rule symlinks, team-rules AGENTS.md/CLAUDE.md blocks
```

- Both repos **ff-only**
- Without `team/` / without `team.remote`: Core only (solo fallback under `core/learnings/`)
- Agents: session start via hook (`session-sync.sh` → `sync.sh pull --quiet`; links refresh quietly)
- Manual: after offline, before review, when a teammate pushed new skills/rules

---

## Learnings workflow

```text
Agent writes pending/  →  sa pending push  →  sa review  →  approved/
```

## Rules (like skills — no review CLI)

Team rules: `$SHARED_AGENTS_HOME/team/rules/*.mdc` (flat). Core: `$SHARED_AGENTS_HOME/rules/`.

After edit: commit/push team repo → teammates **`sa sync`** (links skills + rules automatically).

- **Cursor:** symlinks → `~/.cursor/rules/` (local non-symlink files preserved)
- **Zed, Codex, Claude Code (`~/.claude/CLAUDE.md`), Gemini, Windsurf, …:** merged `<!-- shared-agents:team-rules:begin/end -->` block in each tool's agents file

Optional frontmatter: `targets: [zed, claude-code]` — omit for all adapters.

## Team skills & rules — `sa skill` · `sa rule`

Interactive wizards scaffold files in the **team repo** (private `team/`). No pending/review workflow — commit/push like any team file.

```bash
sa skill new                 # create: slug, title, description, sections
sa skill rm [name]           # remove (picker if name omitted)
sa skill list

sa rule new                  # create: slug, title, description, targets, body
sa rule rm [slug]            # remove (picker if slug omitted)
sa rule list

# Aliases: rm = delete = remove · list = ls

# Non-interactive (CI / scripts):
sa skill new --name my-skill --description "When user asks about …"
sa skill rm my-skill -y
sa rule new --name my-rule --description "…" --targets cursor,zed
sa rule rm my-rule --no-git

# Flags: --dry-run --force (new only) --no-git --push -y
```

Create/remove ends with commit + push to the team repo (**default: yes** — Enter or `y`). Skip git with `n` on the push prompt or **`--no-git`**.

After push: teammates run **`sa sync`**. Optional **`--push`** / **`-y`**: skip prompts.

### Publish pending — `sa pending push`

```bash
sa pending push 2026-06-02-my-slug.md
sa pending push              # unstaged pending/*.md
# flags: --all --dry-run --no-git
```

Commits/pushes **team repo** only when team mode is active.

### Review — `sa review`

```bash
sa review list
sa review dry 2026-06-02-my-slug.md
sa review                    # interactive file picker
sa review 2026-06-02-my-slug.md
```

| Flag | Meaning |
|------|---------|
| `--domain DOMAIN` | Target under `approved/by-domain/` |
| `--dry-run` | Show only |
| `--no-git` | No commit/push |
| `-y` / `--yes` | Skip confirmation |

Moves to `team/learnings/approved/`, updates `index.yaml`, commit + push (team repo only in team mode).

### Resolve path — `sa pending path`

```bash
sa pending path 2026-06-02-my-slug
# → …/team/learnings/pending/2026-06-02-my-slug.md  (with team repo)
```

### Unapprove — `sa unapprove`

```bash
sa unapprove list
sa unapprove fantasy-2026-06-dragon-cache
# wizard: [1] Delete  [2] Move to pending/  [q] Cancel
```

| Flag | Meaning |
|------|---------|
| `--to-pending` | Move to pending/ (non-interactive) |
| `--delete` | Delete file (non-interactive) |
| `--dry-run` · `--no-git` · `-y` | same as review |

Alias: **`sa unapprove`** = **`sa rm`** (remove learning, not uninstall repo)

---

## Uninstall — `sa uninstall`

```bash
sa uninstall
sa uninstall -y
sa uninstall --keep-repo     # adapters only; keep core + team/
sa uninstall --dry-run
```

Removes hooks and skill symlinks (Core **and** team skills). Without `--keep-repo`: deletes `$SHARED_AGENTS_HOME` including `team/` and `config.local.yaml`.

Then: **`source ~/.bashrc`** or new terminal. Fresh setup: **`sa bootstrap`**.

---

## Team repo — `sa team verify`

After bootstrap or when debugging team layout:

```bash
sa team verify
sa team verify --json
sa team verify --strict      # exit 1 on warnings
```

Checks: `team/.git`, `origin` vs `config.local.yaml`, `learnings/index.yaml`, `pending/` / `approved/`, legacy `~/shared-agents/learnings/`.

---

## Migration — `sa team migrate`

If `~/.shared-agents/learnings/` still exists (pre Core/team split):

```bash
sa team migrate --dry-run
sa team migrate
```

See `$SHARED_AGENTS_HOME/docs/migration-team-data.md`.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `sa: command not found` | `source ~/.bashrc` or `"$SHARED_AGENTS_HOME/scripts/sa" help` |
| shared-agents not installed | `sa bootstrap` or `sa install` / `./sa install` |
| Tool `not_configured` | `sa install` |
| Stale learnings | `sa sync` · check hooks / `sa check` |
| Team layout / legacy paths | `sa team verify` · `sa team migrate` |
| Wizard cancelled, half setup | `rm -rf ~/.shared-agents` · `sa bootstrap` again |

---

## Agent instruction

When the user needs CLI help:

1. Run **`sa help`** (live text from `scripts/sa_ui.py`).
2. Use this skill for workflows — do not invent a parallel command list.
3. Paths: **`$SHARED_AGENTS_HOME`** — see skills `shared-agents-knowledge` and `capture-learning`.

More docs: **`$SHARED_AGENTS_HOME/README.md`** · **`docs/canonical-paths.md`**
