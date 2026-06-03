# OpenClaw / headless agents

No IDE hooks — use the **entrypoint wrapper** so sync never gets skipped.

Install shared-agents first: **`sa install`** (or `./install.sh` / `./sa install` from repo root).

## Every agent run

```bash
export SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
"$SHARED_AGENTS_HOME/scripts/agent-entrypoint.sh" <your-agent-command> [args...]
```

This runs `sync.sh pull` (Core + team + skill/rule links) then execs your command.

Manual sync before a run: **`sa sync`**

## Docker

```dockerfile
ENV SHARED_AGENTS_HOME=/data/shared-agents
ENTRYPOINT ["/data/shared-agents/scripts/agent-entrypoint.sh"]
CMD ["node", "agent.js"]
```

## During run

Read directly from `$SHARED_AGENTS_HOME` (headless agents do **not** auto-merge AGENTS.md — load or reference these paths in your runner):

| Content | Paths |
|---------|--------|
| Skills | `skills/` + `team/skills/` |
| Rules | `rules/` + `team/rules/*.mdc` |
| Learnings | `team/learnings/approved/` + `index.yaml` |

Manage team content via CLI:

```bash
sa skill new | sa skill list | sa skill rm [name]
sa rule new  | sa rule list  | sa rule rm [slug]
```

Learnings: `sa pending path` → `sa pending push` → **`sa review`**

## CI / cron

```bash
"$SHARED_AGENTS_HOME/scripts/agent-entrypoint.sh" ./run-pipeline.sh
```

Never start headless agents without the entrypoint.
