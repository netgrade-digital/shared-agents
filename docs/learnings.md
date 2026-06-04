# Learnings

Learnings are your team’s **institutional memory** for AI assistants: bugs you fixed, stack quirks, architecture decisions. They live in the **private team repo**, not in public Core.

---

## Paths

```text
${SHARED_AGENTS_HOME}/team/learnings/pending/YYYY-MM-DD-short-slug.md
${SHARED_AGENTS_HOME}/team/learnings/approved/…
${SHARED_AGENTS_HOME}/team/learnings/index.yaml
```

Resolve before writing:

```bash
sa pending path 2026-06-02-my-slug
```

| Folder | Who writes | Agents use as knowledge |
|--------|------------|-------------------------|
| `pending/` | Agent (after explicit user yes) | **No** |
| `approved/` | Human via **`sa review`** | **Yes** |

---

## Workflow

```text
Agent drafts pending/  →  sa pending push  →  sa review  →  approved/
```

```bash
# Agent (after user approves creating a learning)
# Write to path from: sa pending path <slug>

sa pending push <file>     # commit + push draft to team remote
sa review list
sa review <file>           # promote → approved/ + update index.yaml + push
sa sync                    # teammates pull approved content
```

### Review

```bash
sa review                  # interactive file picker
sa review 2026-06-02-my-slug.md
sa review dry <file>       # preview only
```

| Flag | Meaning |
|------|---------|
| `--domain DOMAIN` | Target under `approved/by-domain/` |
| `--dry-run` | Show actions only |
| `--no-git` | No commit/push |
| `-y` / `--yes` | Skip confirmation |

### Unapprove or fix mistakes

```bash
sa unapprove list
sa unapprove <id-or-file>
# interactive: [1] Delete  [2] Move to pending/  [q] Cancel
```

Flags: `--to-pending`, `--delete`, `--dry-run`, `--no-git`, `-y`

---

## Index file

`team/learnings/index.yaml` catalogs approved learnings (ids, domains, titles). Updated by **`sa review`**.

Agents should read the index and search `approved/` before non-trivial tasks (after **`sa sync`**).

---

## Agent rules

1. **Never** write to `approved/` directly
2. **Never** put learnings in the Core repo or client project
3. Always use **`sa pending path`** or explicit `$SHARED_AGENTS_HOME/team/learnings/pending/…`
4. Ask the user before creating a draft; use skill **`capture-learning`**
5. Only **approved** learnings count as team knowledge

See [Canonical paths](/docs/canonical-paths).

---

## Checks & migration

```bash
sa team verify
sa status                  # pending items needing review
```

Legacy layout at `~/.shared-agents/learnings/`: [Migrate team data](/docs/migration-team-data) · `sa team migrate`

---

## Related

- [Team setup](/docs/team-setup)
- [CLI reference](/docs/cli-reference) — `sa review`, `sa pending`, `sa unapprove`
- [capture-learning skill](https://github.com/netgrade-digital/shared-agents/blob/main/skills/capture-learning/SKILL.md)
