# Windsurf

Auto-configured when `~/.codeium/windsurf` exists.

## Global instructions

`install.sh` merges into:

- `~/.codeium/windsurf/AGENTS.md`
- `~/.codeium/windsurf/memories/global_rules.md` (if file/dir exists)

## Sync

Agent runs sync as first action — allow terminal commands for `sync.sh pull`.

## Project rules

Project `.windsurfrules` / `AGENTS.md` still apply for repo-specific context.
