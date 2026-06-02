# Codex CLI (OpenAI)

Auto-configured when `~/.codex` exists.

## Global instructions

`install.sh` merges the shared-agents block into:

- `~/.codex/AGENTS.md`
- `$CODEX_HOME/AGENTS.md` (if `CODEX_HOME` is set)

## Sync

No built-in session hook — agent runs `sync.sh pull` as first command (from AGENTS.md block).

## Skills

Symlinked to `~/.codex/skills/` if that directory exists after install.
