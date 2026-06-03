<!-- shared-agents:begin -->
## Team Knowledge (shared-agents)

Repo: $SHARED_AGENTS_HOME

MANDATORY — first action every new session/thread, without asking:
  $SHARED_AGENTS_HOME/scripts/sync.sh pull

Before non-trivial work: search team learnings (see $SHARED_AGENTS_HOME/docs/canonical-paths.md).
Use skill `shared-agents-knowledge` for the full workflow.
After reusable insights: write pending learnings only (skill `capture-learning`) — use `sa pending path <slug>` for the absolute path.
No secrets, tokens, or customer data in learnings.

After non-trivial tasks: ALWAYS ask "Soll ich ein Team-Learning anlegen?" — write pending/ only if user says yes.
Copy into your CLI global AGENTS.md / CLAUDE.md / GEMINI.md.
<!-- shared-agents:end -->
