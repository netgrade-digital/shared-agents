# Continue.dev

Auto-configured by **`sa install`** when `~/.continue` exists (or `./install.sh` from repo root).

Status: **`sa check`**

## Global instructions

`sa install` merges into `~/.continue/AGENTS.md`.

## Project rules

Continue also supports project-level `.continuerules` — use for repo-specific rules only.

## Sync

Agent runs `$SHARED_AGENTS_HOME/scripts/sync.sh pull` at session start.
