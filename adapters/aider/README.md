# Aider

Auto-configured by **`sa install`** when `~/.aider` exists (or `./install.sh` from repo root).

Status: **`sa check`**

## Global instructions

`sa install` merges into `~/.aider/AGENTS.md`.

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
