# Cursor

Auto-configured by **`sa install`** when `~/.cursor` exists (or `./install.sh` / `./sa install` from repo root).

Re-run **`sa sync`** after team changes (auto-links skills + rules) · First-time: **`sa install`** · Status: **`sa check`**

## What gets configured

| Item | Path |
|------|------|
| Core rule | `~/.cursor/rules/shared-agents-knowledge.mdc` (symlink → `$SHARED_AGENTS_HOME/rules/`) |
| Team rules | `~/.cursor/rules/*.mdc` (symlinks from `team/rules/` + core `rules/`) |
| Sync hook script | `~/.cursor/hooks/shared-agents-sync.sh` |
| Session hook | `~/.cursor/hooks.json` → `sessionStart` |

Sync runs **automatically** on every Cursor session — no manual pull.

Existing rule files that are **not** symlinks are left untouched (local overrides preserved).

## Team skills & rules

Cursor uses native `.mdc` symlinks — **not** AGENTS.md rule blocks.

| Type | Team path | On Cursor |
|------|-----------|-----------|
| Skills | `team/skills/<name>/` | Symlinks under `~/.agents/skills/` etc. |
| Rules | `team/rules/*.mdc` | Symlinks under `~/.cursor/rules/` |

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Wizards commit/push by default (`--no-git` to skip). Teammates run **`sa sync`** for new symlinks.

Sources: `$SHARED_AGENTS_HOME/rules/` (core) + `$SHARED_AGENTS_HOME/team/rules/` (team).

Optional frontmatter: `targets: [cursor, zed]` — omit for all adapters.

## Manual reference

Example hooks: `hooks.json.example`
