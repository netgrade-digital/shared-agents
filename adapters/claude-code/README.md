# Claude Code

Auto-configured by **`sa install`** when `~/.claude` exists (or `./install.sh` / `./sa install` from repo root).

Re-run **`sa sync`** after team changes (skills + rules) · First-time: **`sa install`** · Status: **`sa check`**

## What gets configured

| Item | Path |
|------|------|
| Session hook | `~/.claude/settings.json` → `hooks.SessionStart` |
| Team knowledge block | `~/.claude/CLAUDE.md` → `<!-- shared-agents:begin/end -->` |
| Team rules block | `~/.claude/CLAUDE.md` → `<!-- shared-agents:team-rules:begin/end -->` |
| Skills | Symlinked to `~/.claude/skills/` |

Hook runs `adapters/claude-code/session-sync.sh` → `sync.sh pull` (Core + Team + skill/rule links) on every session start.

Your own content in `CLAUDE.md` **outside** the marker blocks is never overwritten.

## Rules vs Cursor

Claude Code has **no** `~/.cursor/rules/` — rules are merged as markdown into **`CLAUDE.md`**, same pattern as Zed's `AGENTS.md`. Cursor additionally gets `.mdc` symlinks.

Sources: `$SHARED_AGENTS_HOME/rules/` + `$SHARED_AGENTS_HOME/team/rules/*.mdc` — team-rules block refreshed on every **`sa sync`**.

## Team skills & rules

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Wizards commit/push by default (`--no-git` to skip). Teammates run **`sa sync`**.

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

Re-run **`sa install`** to merge marker blocks safely.
