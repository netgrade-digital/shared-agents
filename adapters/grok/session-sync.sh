#!/usr/bin/env bash
# Grok SessionStart hook. Timeout lives on the hook entry (default Grok timeout is 5s).
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
exec "$SHARED_AGENTS_HOME/scripts/session-sync.sh"
