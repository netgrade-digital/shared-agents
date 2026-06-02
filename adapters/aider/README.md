# Aider

Auto-configured when `~/.aider` exists.

## Global instructions

`install.sh` merges into `~/.aider/AGENTS.md`.

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
