# GitHub Copilot

Auto-configured by **`sa install`** when `~/.copilot` exists (or `./install.sh` from repo root).

Status: **`sa check`**

## Global instructions

`sa install` merges into (first existing path wins):

- `~/.config/github-copilot/AGENTS.md`
- `~/.copilot/AGENTS.md`

## Project instructions

Repos can use `.github/copilot-instructions.md` for project-specific rules.

## Sync

Agent runs sync at session start via merged instruction block.
