# OpenCode

Auto-configured by **`sa install`** when `~/.config/opencode` exists (or `./install.sh` / `./sa install` from repo root).

Re-run **`sa sync`** after team changes (skills + rules) · First-time: **`sa install`** · Status: **`sa check`**

## Global instructions

`sa install` merges into `~/.config/opencode/AGENTS.md`:

| Marker block | Content |
|--------------|---------|
| `<!-- shared-agents:begin/end -->` | Sync + learnings workflow |
| `<!-- shared-agents:team-rules:begin/end -->` | Core + team rules from `$SHARED_AGENTS_HOME/rules/` and `team/rules/*.mdc` |

Your own content **outside** these markers is preserved. Team-rules block refreshed on every **`sa sync`**.

## Team skills & rules

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Wizards commit/push by default (`--no-git` to skip). Teammates run **`sa sync`**.

## Skills

Symlinked to `~/.config/opencode/skills/` when detected at install time.
