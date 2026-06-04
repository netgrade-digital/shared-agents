# Team setup

Team-specific content (learnings, team skills, team rules) lives in a **separate private Git repository**, cloned into:

```text
$SHARED_AGENTS_HOME/team/
```

It is **never** pushed to the public Core repo.

---

## Bootstrap (recommended)

During **`sa bootstrap`** or **`sa install`**, enter your private team remote URL when prompted. The wizard clones or updates `team/` and writes `config.local.yaml`.

```bash
curl -fsSL https://raw.githubusercontent.com/netgrade-digital/shared-agents/refs/heads/main/scripts/bootstrap.sh | bash
source ~/.bashrc
sa team verify
```

---

## Manual configuration

Edit `$SHARED_AGENTS_HOME/config.local.yaml` (gitignored):

```yaml
team:
  remote: git@github.com:your-org/your-team-shared-agents.git
```

Then:

```bash
sa sync
sa team verify
```

---

## Team repository layout

```text
team/
├── learnings/
│   ├── pending/          # agent drafts (not used as knowledge)
│   ├── approved/         # promoted by sa review
│   └── index.yaml        # catalog
├── skills/               # team-only skills
└── rules/                # flat *.mdc
```

---

## Verify team repo

```bash
sa team verify
sa team verify --json
sa team verify --strict    # exit 1 on warnings
```

Checks include:

- `team/.git` present
- `origin` matches `config.local.yaml`
- `learnings/index.yaml`, `pending/`, `approved/`
- Legacy `~/shared-agents/learnings/` or `learnings/` at home root

---

## Solo mode (no team remote)

Without `team.remote`, the CLI may use a solo fallback (`core/learnings/`). For real teams with private knowledge, always configure a team remote.

---

## Legacy migration

If learnings still live at `~/.shared-agents/learnings/` (pre split):

```bash
sa team migrate --dry-run
sa team migrate
```

See [Migrate team data](/docs/migration-team-data).

---

## Daily workflow

| Task | Command |
|------|---------|
| Pull Core + team | `sa sync` |
| Push learning draft | `sa pending push` |
| Approve learning | `sa review` |
| Add team skill/rule | `sa skill new` · `sa rule new` |
| Health check | `sa team verify` · `sa status` |

---

## See also

- [Overview](/docs)
- [Learnings](/docs/learnings)
- [Skills and rules](/docs/skills-and-rules)
- [Canonical paths](/docs/canonical-paths)
