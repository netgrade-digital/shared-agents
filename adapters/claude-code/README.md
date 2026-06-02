# Claude Code

Auto-configured by `install.sh` when `~/.claude` exists.

## What install.sh sets up

| Item | Path |
|------|------|
| Session hook | `~/.claude/settings.json` → `hooks.SessionStart` |
| Skills | Symlinked to `~/.claude/skills/` |

Hook runs `adapters/claude-code/session-sync.sh` → `git pull` on every session start.

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

Re-run `install.sh` to merge safely.
