# CLI reference

**Live help:** run **`sa`** or **`sa help`** — always prefer that over memorizing flags.

```bash
sa                  # help overview (default)
sa help             # same
shared-agents …     # alias
sharedagents …      # alias
```

Without shell aliases:

```bash
"${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/scripts/sa" help
```

Environment: **`SHARED_AGENTS_HOME`** (default `~/.shared-agents`) · Version: **`sa version`**

---

## Command overview

| Area | Command | Summary |
|------|---------|---------|
| Info | `sa` · `sa help` | All commands |
| Info | `sa version` | CLI version + HOME |
| Setup | `sa bootstrap` | Full first-time setup |
| Setup | `sa install` | Setup wizard |
| Setup | `sa install --non-interactive` | All detected tools, no prompts |
| Setup | `sa check` | Installed vs configured |
| Setup | `sa sync` | Pull Core + team; link skills & rules |
| Setup | `sa status` | Pending reviews, skills, adapters |
| Setup | `sa doctor` | Diagnose symlink / rule issues |
| Setup | `sa doctor --fix` | Repair + relink |
| Setup | `sa team verify` | Deep team repo validation |
| Setup | `sa team migrate` | Legacy `learnings/` → `team/learnings/` |
| Setup | `sa uninstall` | Remove adapters / full uninstall |
| Learnings | `sa review` | Interactive pending → approved |
| Learnings | `sa review list` | List pending |
| Learnings | `sa pending push [file]` | Commit + push pending |
| Learnings | `sa pending path [slug]` | Canonical pending path |
| Learnings | `sa unapprove [id\|file]` | Remove from approved |
| Team | `sa skill new` · `sa skill list` · `sa skill rm` | Team skills |
| Team | `sa rule new` · `sa rule list` · `sa rule rm` | Team rules |

---

## `sa sync`

```bash
sa sync
# = scripts/sync.sh pull
#   1) git pull  ~/.shared-agents        (Core)
#   2) git pull  ~/.shared-agents/team/  (Team)
#   3) sync-links — skills, rules, AGENTS.md/CLAUDE.md blocks
```

- Both repos use **fast-forward only**
- Without team remote: Core only (solo fallback)
- Runs quietly on IDE session hooks where configured
- Run manually after offline work or when a teammate pushed skills/rules

---

## `sa status`

```bash
sa status              # full list
sa status --brief      # one line
sa status --quiet      # only when action needed (exit 1)
sa status --json       # CI / scripts
```

| Check | Meaning | Action |
|-------|---------|--------|
| Pending learnings | Files in `pending/` | `sa review` |
| Not pushed | Local pending changes | `sa pending push` |
| Team setup | Config / legacy layout | `sa team verify` |
| Skill symlinks | New skill not linked | `sa sync` · `sa doctor --fix` |
| Rule symlinks | File blocks symlink | `sa doctor --fix` |
| Adapters | Tool present, not configured | `sa install` |

---

## `sa doctor`

```bash
sa doctor
sa doctor --fix
sa doctor --fix -y
sa doctor --fix --dry-run
```

Backups: `$SHARED_AGENTS_HOME/.doctor-backups/`. Does not replace the learnings review workflow.

---

## `sa check`

```bash
sa check
sa check --json
```

| STATUS | Meaning |
|--------|---------|
| `ok` | Tool present + Shared Agents configured |
| `missing_tool` | CLI/config not found |
| `not_configured` | Tool present, adapter missing → `sa install` |
| `available` | Generic fallback |

---

## Learnings commands

```bash
sa pending path 2026-06-02-my-slug
sa pending push 2026-06-02-my-slug.md
sa review list
sa review                    # interactive picker
sa review 2026-06-02-my-slug.md
sa unapprove list
sa unapprove <id>
```

Review flags: `--domain`, `--dry-run`, `--no-git`, `-y`

Unapprove: `--to-pending`, `--delete`, `--dry-run`, `-y`

Details: [Learnings](/docs/learnings)

---

## Team skills & rules

```bash
sa skill new
sa skill list
sa skill rm [name]

sa rule new
sa rule list
sa rule rm [slug]
```

Create/remove wizards **commit + push by default** (Enter = yes; `--no-git` to skip).

Details: [Skills and rules](/docs/skills-and-rules)

---

## Install flags

Passed through to `install.sh`:

| Flag | Meaning |
|------|---------|
| `--home DIR` | Target path |
| `--source DIR` | Source repo (dev checkout) |
| `--shell-rc FILE` | bashrc for `sa` |
| `--tools IDS` | Comma-separated adapter IDs |
| `--check` | Status only |
| `--dry-run` | Preview, no writes |

---

## See also

- [Installation](/docs/installation)
- [Skills and rules](/docs/skills-and-rules)
- [Canonical paths](/docs/canonical-paths)
- [Troubleshooting](/docs/troubleshooting)
- Full skill: [sa-cli on GitHub](https://github.com/netgrade-digital/shared-agents/blob/main/skills/sa-cli/SKILL.md)
