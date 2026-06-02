# Continue.dev

Auto-configured when `~/.continue` exists.

## Global instructions

`install.sh` merges into `~/.continue/AGENTS.md`.

## Project rules

Continue also supports project-level `.continuerules` — use for repo-specific rules only.

## Sync

Agent runs `$SHARED_AGENTS_HOME/scripts/sync.sh pull` at session start.
