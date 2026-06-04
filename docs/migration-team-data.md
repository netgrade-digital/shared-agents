# Migrate team data

If you used Shared Agents **before** the Core/team split and still have learnings under `~/.shared-agents/learnings/`, they are in the wrong place. Team knowledge belongs in your **private team repo** under `team/`.

## Prerequisites

1. `config.local.yaml` with `team.remote` (or run **`sa bootstrap`** again)
2. An empty or new team remote (or be ready to merge)

## Automatic (recommended)

```bash
sa team migrate --dry-run    # preview
sa team migrate              # moves learnings/ → team/learnings/
cd ~/.shared-agents/team && git status
git push                     # if not pushed yet
```

`sa check` and **`sa team verify`** report legacy `learnings/` paths and structure issues.

## Manual

```bash
# 1) Clone or init team repo (if needed)
sa bootstrap   # or set team URL in config.local.yaml

# 2) Move content
mv ~/.shared-agents/learnings ~/.shared-agents/team/learnings

# 3) Commit in team repo
cd ~/.shared-agents/team
git add learnings/
git commit -m "chore(team): migrate learnings from core home"
git push
```

## After migration

- Run **`sa sync`** — Core + team
- Use only **`sa pending path <slug>`** (resolves to `team/learnings/pending/…`)
- The Core dev checkout (`Development/…/shared-agents`) should **not** hold team learnings

## Solo mode (no team remote)

Without `team.remote`, the CLI may still use `core/learnings/` as a fallback. For teams with private knowledge, always set **`team.remote`**.
