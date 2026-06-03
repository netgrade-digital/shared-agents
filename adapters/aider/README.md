# Aider

Auto-configured by **`sa install`** when `~/.aider` exists (or `./install.sh` / `./sa install` from repo root).

Re-run **`sa sync`** after team changes (skills + rules) · First-time: **`sa install`** · Status: **`sa check`**

## Global instructions

`sa install` merges into `~/.aider/AGENTS.md`:

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

## Alternative: --read flag

Add to `~/.aider.conf.yml` or alias:

```yaml
read:
  - ~/.shared-agents/adapters/aider/instructions.md
```

Or run:

```bash
aider --read "$SHARED_AGENTS_HOME/adapters/generic/instructions.md"
```

## Sync

First message in session should trigger sync, or add to aider startup script:

```bash
"$SHARED_AGENTS_HOME/scripts/sync.sh" pull && aider
```

Or use the shared CLI: `sa sync` before starting aider.
