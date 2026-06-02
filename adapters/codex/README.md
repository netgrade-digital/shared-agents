# Codex CLI (OpenAI)

Auto-configured by **`sa install`** when `~/.codex` exists (or `./install.sh` from repo root).

Status: **`sa check`**

## Global instructions

`sa install` merges the shared-agents block into:

- `~/.codex/AGENTS.md`
- `$CODEX_HOME/AGENTS.md` (if `CODEX_HOME` is set)

## Sync

No built-in session hook — agent runs `sync.sh pull` as first command (from AGENTS.md block).

## Skills

Symlinked to `~/.codex/skills/` if that directory exists after install.
