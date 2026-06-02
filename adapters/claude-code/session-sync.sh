#!/usr/bin/env bash
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
exec "$SHARED_AGENTS_HOME/scripts/session-sync.sh"
