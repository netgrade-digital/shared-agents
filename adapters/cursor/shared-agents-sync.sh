#!/usr/bin/env bash
# Installed to ~/.cursor/hooks/shared-agents-sync.sh by scripts/install.sh
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
exec "$SHARED_AGENTS_HOME/scripts/session-sync.sh"
