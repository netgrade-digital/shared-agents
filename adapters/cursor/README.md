# Cursor

Auto-configured by **`sa install`** when `~/.cursor` exists (or `./install.sh` / `./sa install` from repo root).

Re-run **`sa install`** to merge updates safely · Status: **`sa check`**

## What gets configured

| Item | Path |
|------|------|
| Rule (always apply) | `~/.cursor/rules/shared-agents-knowledge.mdc` |
| Sync hook script | `~/.cursor/hooks/shared-agents-sync.sh` |
| Session hook | `~/.cursor/hooks.json` → `sessionStart` |

Sync runs **automatically** on every Cursor session — no manual pull.

## Manual reference

Example hooks: `hooks.json.example`
