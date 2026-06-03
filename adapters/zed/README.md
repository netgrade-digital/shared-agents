# Zed

Auto-configured by **`sa install`** when `~/.config/zed` exists (or `./install.sh` / `./sa install` from repo root).

Re-run **`sa sync`** after team changes (skills + rules) · First-time: **`sa install`** · Status: **`sa check`**

## Global instructions

Merged into **`~/.config/zed/AGENTS.md`** (applies to all projects):

| Marker block | Content |
|--------------|---------|
| `<!-- shared-agents:begin/end -->` | Sync + learnings workflow |
| `<!-- shared-agents:team-rules:begin/end -->` | Core + team rules from `$SHARED_AGENTS_HOME/rules/` and `team/rules/*.mdc` |

Your own sections **above** those markers (e.g. communication style) are never overwritten. The team-rules block is **refreshed on every `sa sync`** for detected tools.

## Team skills & rules

| Type | Team path | On Zed |
|------|-----------|--------|
| Skills | `team/skills/<name>/SKILL.md` | Symlinks under `~/.agents/skills/` |
| Rules | `team/rules/<slug>.mdc` | Merged into `AGENTS.md` team-rules block |

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Wizards commit/push by default (`--no-git` to skip). Teammates run **`sa sync`**. Optional rule frontmatter: `targets: [zed, cursor]` — omit for all adapters.

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

Team skills available via `@shared-agents-knowledge` and other skill names from `~/.agents/skills/`.

Reference snippet: `AGENTS.md.snippet`
