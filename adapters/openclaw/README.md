# OpenClaw / headless agents

No IDE hooks — use the **entrypoint wrapper** so sync never gets skipped.

## Every agent run

```bash
export SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
"$SHARED_AGENTS_HOME/scripts/agent-entrypoint.sh" <your-agent-command> [args...]
```

This runs `sync.sh pull` then execs your command.

## Docker

```dockerfile
ENV SHARED_AGENTS_HOME=/data/shared-agents
ENTRYPOINT ["/data/shared-agents/scripts/agent-entrypoint.sh"]
CMD ["node", "agent.js"]
```

## During run

- Read skills from `$SHARED_AGENTS_HOME/skills/`
- Search `learnings/approved/` before non-trivial steps
- End: write to `learnings/pending/` → branch + PR

## CI / cron

```bash
"$SHARED_AGENTS_HOME/scripts/agent-entrypoint.sh" ./run-pipeline.sh
```

Never start headless agents without the entrypoint.
