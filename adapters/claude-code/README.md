# Claude Code

Auto-configured by **`sa install`** when `~/.claude` exists (or `./install.sh` from repo root).

Re-run **`sa install`** to merge safely · Status: **`sa check`**

## What gets configured

| Item | Path |
|------|------|
| Session hook | `~/.claude/settings.json` → `hooks.SessionStart` |
| Skills | Symlinked to `~/.claude/skills/` |

Hook runs `adapters/claude-code/session-sync.sh` → `sync.sh pull` (Core + Team) on every session start.

## Manual hook command

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash \"$HOME/.shared-agents/adapters/claude-code/session-sync.sh\""
          }
        ]
      }
    ]
  }
}
```

Re-run **`sa install`** to merge safely.
