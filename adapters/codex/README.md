# Codex CLI (OpenAI)

Auto-configured by **`sa install`** when `~/.codex` exists (or `./install.sh` / `./sa install` from repo root).

Re-run **`sa sync`** after team changes (skills + rules) · First-time: **`sa install`** · Status: **`sa check`**

## Global instructions

`sa install` merges into:

- `~/.codex/AGENTS.md`
- `$CODEX_HOME/AGENTS.md` (if `CODEX_HOME` is set)

| Marker block | Content |
|--------------|---------|
| `<!-- shared-agents:begin/end -->` | Sync + learnings workflow |
| `<!-- shared-agents:team-rules:begin/end -->` | Core + team rules from `$SHARED_AGENTS_HOME/rules/` and `team/rules/*.mdc` |

Your own content **outside** these markers is preserved. Team-rules block refreshed on every **`sa sync`**.

## Team skills & rules

Flat files in the private team repo — no pending/review workflow (unlike learnings):

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Wizards commit/push by default (`--no-git` to skip). Teammates run **`sa sync`**.

Optional rule frontmatter: `targets: [codex, zed, cursor]` — omit for all adapters.

## Sync

No built-in session hook — agent runs `sync.sh pull` as first command (from AGENTS.md block).

## Skills

Symlinked to `~/.codex/skills/` when detected at install time.
