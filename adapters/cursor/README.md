# Cursor

Auto-configured by `install.sh` when `~/.cursor` exists.

## What install.sh sets up

| Item | Path |
|------|------|
| Rule (always apply) | `~/.cursor/rules/shared-agents-knowledge.mdc` |
| Sync hook script | `~/.cursor/hooks/shared-agents-sync.sh` |
| Session hook | `~/.cursor/hooks.json` → `sessionStart` |

Sync runs **automatically** on every Cursor session — no manual pull.

## Manual reference

Example hooks: `hooks.json.example`
