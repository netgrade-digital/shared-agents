# Pi

Auto-configured by **`sa install`** when `~/.pi` exists or `pi` is on `PATH` (or `./install.sh` / `./sa install` from repo root).

Re-run **`sa sync`** after team changes (skills + rules) · First-time: **`sa install`** · Status: **`sa check`**

## Global instructions

`sa install` / `sa sync` merge into:

- `~/.pi/agent/AGENTS.md`
- `$PI_CODING_AGENT_DIR/AGENTS.md` when `PI_CODING_AGENT_DIR` is set

| Marker block | Content |
|--------------|---------|
| `<!-- shared-agents:begin/end -->` | Sync + learnings workflow |
| `<!-- shared-agents:team-rules:begin/end -->` | Core + team rules from `$SHARED_AGENTS_HOME/rules/` and `team/rules/*.mdc` |

Your own sections **outside** those markers are never overwritten. The team-rules block is **refreshed on every `sa sync`**.

## Team skills & rules

| Type | Team path | On Pi |
|------|-----------|-------|
| Skills | `team/skills/<name>/SKILL.md` | Symlinks under `~/.agents/skills/` |
| Rules | `team/rules/<slug>.mdc` | Merged into `AGENTS.md` team-rules block |

Pi discovers `~/.agents/skills/` itself. Sync does not also link those skills into `~/.pi/agent/skills/` (same name twice, Pi keeps the first).

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Wizards commit/push by default (`--no-git` to skip). Teammates run **`sa sync`**. Optional rule frontmatter: `targets: [pi, zed, cursor]` — omit for all adapters.

## Sync

No session hook. The agent runs `sync.sh pull` as the first command (from the AGENTS.md block).

In a non-interactive shell the `sa` function from `.bashrc` is absent. The script is `$SHARED_AGENTS_HOME/scripts/sa`.
