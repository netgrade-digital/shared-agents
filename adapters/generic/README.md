# Generic / any AI CLI

For tools not yet in [`manifest.json`](../manifest.json).

## Auto-generated file

Every **`sa install`** run refreshes:

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
| Kimi Code CLI | `~/.kimi/AGENTS.md` (best-effort — not auto-loaded) |
| Project-level | `./AGENTS.md`, `./CLAUDE.md`, `.cursorrules` |

## Add first-class support

1. Find the tool's global instructions path (create config dir by launching tool once)
2. Add entry to `adapters/manifest.json`
3. Optional: `adapters/<tool>/README.md`
4. Re-run **`sa install`** (or `./install.sh`)

## Minimum contract

Every adapter must ensure:

1. **Sync** — `sa sync` (or `sync.sh pull`) at session start or manually — pulls Core + team, links skills + rules
2. **Read** — agent searches `$SHARED_AGENTS_HOME/team/learnings/approved/` before non-trivial work
3. **Write learnings** — skill `capture-learning` + `sa pending path` → `sa review` (team repo only)
4. **Rules** — on **`sa sync`**: merge `team/rules/*.mdc` into AGENTS.md/CLAUDE.md blocks, or symlinks (Cursor); first-time blocks via **`sa install`**

## Team skills & rules (CLI)

Same for all tools — content lives in the private team repo:

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Wizards commit/push by default. Teammates run **`sa sync`**.
