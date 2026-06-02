# Generic / any AI CLI

For tools not yet in [`manifest.json`](../manifest.json).

## Auto-generated file

Every `install.sh` run refreshes:

```
adapters/generic/instructions.md
```

Copy that block into your tool's global config file.

## Common global paths (ecosystem convention)

Many agents follow the **AGENTS.md pattern**:

| Tool family | Typical global path |
|-------------|---------------------|
| Zed | `~/.config/zed/AGENTS.md` |
| Codex CLI | `~/.codex/AGENTS.md` or `$CODEX_HOME/AGENTS.md` |
| OpenCode | `~/.config/opencode/AGENTS.md` |
| Claude Code | `~/.claude/CLAUDE.md` or project `CLAUDE.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` |
| Project-level | `./AGENTS.md`, `./CLAUDE.md`, `.cursorrules` |

## Add first-class support

1. Find the tool's global instructions path (create config dir by launching tool once)
2. Add entry to `adapters/manifest.json`
3. Optional: `adapters/<tool>/README.md`
4. Re-run `install.sh`

## Minimum contract

Every adapter must ensure:

1. **Sync** — `$SHARED_AGENTS_HOME/scripts/sync.sh pull` runs at session start
2. **Read** — agent searches `learnings/approved/` before non-trivial work
3. **Write** — agent can propose to `learnings/pending/` via `capture-learning` skill
