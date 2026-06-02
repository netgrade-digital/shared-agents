# GitHub Copilot

Auto-configured when `~/.copilot` exists.

## Global instructions

`install.sh` merges into (first existing path wins):

- `~/.config/github-copilot/AGENTS.md`
- `~/.copilot/AGENTS.md`

## Project instructions

Repos can use `.github/copilot-instructions.md` for project-specific rules.

## Sync

Agent runs sync at session start via merged instruction block.
