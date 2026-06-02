# Zed

Auto-configured by **`sa install`** when `~/.config/zed` exists (or `./install.sh` from repo root).

Re-run **`sa install`** after Zed updates · Status: **`sa check`**

## Global instructions

Merged into **`~/.config/zed/AGENTS.md`** (applies to all projects).

Zed has no session hook — the instruction block tells the agent to run sync as the **first shell command** in every new thread.

## Tool permissions

If sync prompts every time:

```json
{
  "agent": {
    "tool_permissions": {
      "default": "allow"
    }
  }
}
```

## Skills

Team skills available via `@shared-agents-knowledge` from `~/.agents/skills/`.

Reference snippet: `AGENTS.md.snippet`
