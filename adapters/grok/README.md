# Grok Build (xAI)

Auto-configured by **`sa install`** when `~/.grok` exists or `grok` is on `PATH`.

Re-run **`sa sync`** after team changes (skills + rules). First-time: **`sa install`**. Status: **`sa check`**.

Checked against Grok Build 1.0 (`grok inspect`).

## What gets configured

| Item | Path |
|------|------|
| Session hook | `~/.grok/hooks/shared-agents.json` → `hooks.SessionStart` (timeout 60s) |
| Team knowledge block | `~/.grok/AGENTS.md` → `<!-- shared-agents:begin/end -->` |
| Team rules block | `~/.grok/AGENTS.md` → `<!-- shared-agents:team-rules:begin/end -->` |
| Skills | Already loaded from `~/.agents/skills`. No second link dir. |

`$GROK_HOME` replaces `~/.grok` when that variable is set (same pattern as `$CODEX_HOME`).

Your own text in `AGENTS.md` **outside** the marker blocks is kept. **`sa sync`** refreshes the team-rules block.

## Why the hook timeout is 60s

Grok's default hook timeout is **5 seconds**. `sa sync` pulls Core and the team repo. A 5s kill can stop that pull halfway. The Grok hook sets `"timeout": 60`.

Grok also imports `~/.claude/settings.json` hooks. That Claude hook has no timeout, so Grok would kill it at 5s and it could race the Grok hook. `adapters/claude-code/session-sync.sh` exits immediately when Grok runs it and `~/.grok/hooks/shared-agents.json` exists. Claude Code itself is unchanged (`GROK_HOOK_EVENT` is not set there).

`scripts/session-sync.sh` holds a lock in `/tmp` so two hooks cannot `git pull` the same repo at once.

## Claude instruction files stay on

`sa install` does not change `[compat.claude]`. Grok still reads:

- `~/.claude/CLAUDE.md`
- `<repo>/.claude/CLAUDE.md`
- repo-root `CLAUDE.md` and `AGENTS.md`

`sa` also writes the team-rules block into `~/.grok/AGENTS.md` and into `~/.claude/CLAUDE.md`. With both tools installed, that block is in the Grok prompt twice. That is only the shared-agents text. Other Claude instructions still load.

An older install of this adapter may have set `[compat.claude] agents = false` between `# shared-agents:grok-compat:begin` and `# shared-agents:grok-compat:end`. The next `sa install` removes that block and leaves the rest of `config.toml` alone.

## Skills

Grok discovers `~/.agents/skills` as user skills (same directory Cursor and Pi use). A second copy under `~/.grok/skills` would list each skill twice or hide one of them. Sync does not add that directory.

If a future Grok build stops scanning `~/.agents/skills`, add:

```toml
[skills]
paths = ["~/.agents/skills"]
```

## Rules Grok does not read

- `~/.cursor/rules/*.mdc` (Grok's Cursor rules scan looks for `*.md`)
- Cursor `hooks.json` (Grok reports those hooks and does not run them)

Native `AGENTS.md` plus the SessionStart hook cover both.

## Team skills and rules

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Optional rule frontmatter: `targets: [grok, cursor]` — omit for all adapters.

## Check

```bash
grok inspect
sa check
```

`grok inspect` should list `~/.grok/AGENTS.md` as a global instruction and a `session_start` hook whose source is `~/.grok/hooks/shared-agents.json`. `~/.claude/CLAUDE.md` stays listed while Claude compat is on.
