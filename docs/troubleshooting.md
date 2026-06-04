# Troubleshooting

Common issues and fixes when using Shared Agents.

---

## `sa: command not found`

```bash
source ~/.bashrc
# or
"${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/scripts/sa" help
```

Re-run **`sa install`** if bashrc was not updated.

---

## Shared Agents not installed

```bash
sa bootstrap
# or from dev checkout:
./sa install --home "$HOME/.shared-agents"
```

---

## Tool shows `not_configured` in `sa check`

The AI tool is installed but adapters are missing:

```bash
sa install
sa check
```

Install a new IDE/CLI later? Run **`sa install`** again.

---

## Stale skills, rules, or learnings

```bash
sa sync
sa status
```

Confirm session hooks are configured (`sa check`). Cursor: `~/.cursor/hooks.json` · Claude Code: `~/.claude/settings.json`.

---

## Cursor rule symlink blocked

A rule exists as a regular file instead of a symlink:

```bash
sa doctor
sa doctor --fix
```

Backups land in `$SHARED_AGENTS_HOME/.doctor-backups/`.

---

## Team layout warnings

```bash
sa team verify
sa team migrate --dry-run   # if legacy learnings/ at home root
```

See [Team setup](/docs/team-setup) and [Migrate team data](/docs/migration-team-data).

---

## Wizard cancelled / half-finished install

```bash
rm -rf ~/.shared-agents
sa bootstrap
```

Or fix manually with `sa install` after cleaning partial state.

---

## Pending learnings not visible to teammates

1. `sa pending push` — commit + push team repo
2. Teammate runs `sa sync`
3. Human runs `sa review` to promote to `approved/`

Agents only read **approved** learnings.

---

## Wrong path for learning drafts

Always resolve before writing:

```bash
sa pending path 2026-06-02-my-slug
```

See [Canonical paths](/docs/canonical-paths).

---

## Dev checkout vs runtime home

| Path | Role |
|------|------|
| `~/.shared-agents/` | Runtime — agents write learnings **here** |
| `~/Development/…/shared-agents/` | Dev checkout — edit Core, run `./sa sync` |

Do not assume the Cursor workspace is `$SHARED_AGENTS_HOME`.

---

## Still stuck?

- `sa help` — live command list
- `sa status` — what needs attention
- [CLI reference](/docs/cli-reference)
- [GitHub issues](https://github.com/netgrade-digital/shared-agents/issues)
