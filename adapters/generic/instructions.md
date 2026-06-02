<!-- shared-agents:begin -->
## Team Knowledge (shared-agents)

Repo: /home/quentin/.shared-agents

MANDATORY — first action every new session/thread, without asking:
  /home/quentin/.shared-agents/scripts/sync.sh pull

Before non-trivial work: search /home/quentin/.shared-agents/learnings/approved/ and index.yaml.
Use skill `shared-agents-knowledge` for the full workflow.
After reusable insights: write to /home/quentin/.shared-agents/learnings/pending/ only (skill `capture-learning`) — absolute path under SHARED_AGENTS_HOME, never the Cursor workspace. See /home/quentin/.shared-agents/docs/canonical-paths.md.
No secrets, tokens, or customer data in learnings.

After non-trivial tasks: ALWAYS ask "Soll ich ein Team-Learning anlegen?" — write pending/ only if user says yes.
Copy into your CLI global AGENTS.md / CLAUDE.md / GEMINI.md.
<!-- shared-agents:end -->
