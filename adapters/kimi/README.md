# Kimi Code CLI

> **Best-effort workaround — not a full integration.**
>
> Kimi does **not** natively load a global instructions file at session start (unlike Claude Code or Cursor). `sa install` creates `~/.kimi/AGENTS.md` anyway, but you must copy its contents into your prompt manually or use a wrapper script. `sa sync` keeps the file up to date so you always have the latest block ready to paste.

Auto-configured by **`sa install`** when `~/.kimi` exists or the `kimi` binary is on `PATH`.

Re-run **`sa sync`** after team changes (skills + rules) · First-time: **`sa install`** · Status: **`sa check`**

## Global instructions

Merged into **`~/.kimi/AGENTS.md`** (applies to all projects):

| Marker block | Content |
|--------------|---------|
| `<!-- shared-agents:begin/end -->` | Sync + learnings workflow |
| `<!-- shared-agents:team-rules:begin/end -->` | Core + team rules from `$SHARED_AGENTS_HOME/rules/` and `team/rules/*.mdc` |

Your own sections **above** those markers (e.g. communication style) are never overwritten. The team-rules block is **refreshed on every `sa sync`** for detected tools.

## How to use the AGENTS.md content

Because Kimi does not read `~/.kimi/AGENTS.md` automatically, pick one of these workflows:

1. **Copy-paste** — open `~/.kimi/AGENTS.md` and paste the `<!-- shared-agents:begin/end -->` block into your first prompt at the start of each session.
2. **Wrapper script** — create a small shell alias or script that reads `~/.kimi/AGENTS.md` and passes it as context to `kimi`.
3. **Project-level** — copy the block into a project `AGENTS.md` or `.kimi/AGENTS.md` if your project setup supports it.

## Team skills & rules

| Type | Team path | On Kimi |
|------|-----------|---------|
| Skills | `team/skills/<name>/SKILL.md` | Not auto-loaded — copy manually from `~/.agents/skills/` if needed |
| Rules | `team/rules/<slug>.mdc` | Merged into `~/.kimi/AGENTS.md` team-rules block |

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Wizards commit/push by default (`--no-git` to skip). Teammates run **`sa sync`**. Optional rule frontmatter: `targets: [kimi, cursor]` — omit for all adapters.

## Sync

No built-in session hook — the AGENTS.md block instructs the user to run `sync.sh pull` as the first command, but Kimi does not execute it automatically. You must trigger `sa sync` manually or copy the updated block before each session.

## Why this is marked "best-effort"

- No native session hook (Cursor `hooks.json`, Claude Code `settings.json`).
- No native global instructions loader (Zed, Codex, Aider load `AGENTS.md` automatically).
- The `~/.kimi/` directory is **not** an official Kimi config path; it is a convention chosen by this project so that `sa install` / `sa sync` have a stable target file.
