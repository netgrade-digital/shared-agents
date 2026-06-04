# Skills and rules

Shared Agents distributes **skills** (agent workflows) and **rules** (standing instructions) from Core and your private team repo into each supported IDE.

## Skills

Skills live as `SKILL.md` files in directories under:

| Source | Path | Visibility |
|--------|------|------------|
| Core | `$SHARED_AGENTS_HOME/skills/<name>/` | Public GitHub |
| Team | `$SHARED_AGENTS_HOME/team/skills/<name>/` | Private team repo |

After **`sa sync`**, symlinks point tool skill dirs (e.g. `~/.agents/skills`, `~/.claude/skills`) at these folders.

### Create a team skill

```bash
sa skill new                 # interactive wizard
sa skill list
sa skill rm [name]           # picker if name omitted

# Non-interactive
sa skill new --name my-skill --description "When user asks about …"
sa skill rm my-skill -y --no-git
```

Wizard writes `team/skills/<name>/SKILL.md`, then offers commit + push to the team remote.

### Core skills (contributors)

Add under `skills/<name>/SKILL.md` in the public repo. Keep content **OSS-safe** (no secrets, no client-specific paths). See [Contributing](/docs/contributing).

---

## Rules

| Source | Path | Format |
|--------|------|--------|
| Core | `$SHARED_AGENTS_HOME/rules/` | `.mdc` files |
| Team | `$SHARED_AGENTS_HOME/team/rules/` | flat `*.mdc` |

**No pending/review workflow** for rules (unlike learnings). Edit → commit/push team repo → teammates **`sa sync`**.

### How rules reach each tool

| Adapter type | Delivery |
|--------------|----------|
| **Cursor** | Symlinks → `~/.cursor/rules/` |
| **AGENTS.md / CLAUDE.md tools** | Merged `<!-- shared-agents:team-rules:begin/end -->` block |
| **Dedicated target file** (Cursor) | Existing non-symlink files are **not** overwritten |

Optional frontmatter in team rules:

```yaml
targets: [zed, claude-code, cursor]
```

Empty `targets` = all adapters.

### Create a team rule

```bash
sa rule new                  # slug, title, description, targets, body
sa rule list
sa rule rm [slug]

sa rule new --name my-rule --description "…" --targets cursor,zed
sa rule rm my-rule --no-git
```

---

## Sync vs install

| Command | Skills & rules |
|---------|----------------|
| **`sa sync`** | Pull Git + refresh symlinks / marker blocks (daily) |
| **`sa install`** | First-time hooks, base `<!-- shared-agents:begin -->` blocks, new tool |

Run **`sa install`** when you add a new AI tool. Run **`sa sync`** after teammates push team content.

---

## Repair

If Cursor rules exist as regular files instead of symlinks:

```bash
sa doctor --fix
```

---

## See also

- [Overview](/docs)
- [Adapters](/docs/adapters)
- [Canonical paths](/docs/canonical-paths)
- [CLI reference](/docs/cli-reference)
