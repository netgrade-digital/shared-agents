#!/usr/bin/env bash
# Grok imports this hook via Claude compat and kills it at the 5s default timeout.
# When the Grok adapter hook is installed, that hook pulls (60s). Exit here so two
# git pulls do not run at once. Claude Code does not set GROK_HOOK_EVENT.
if [[ -n "${GROK_HOOK_EVENT:-}" ]]; then
  grok_home="${GROK_HOME:-$HOME/.grok}"
  if [[ -f "$grok_home/hooks/shared-agents.json" ]]; then
    exit 0
  fi
fi
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
exec "$SHARED_AGENTS_HOME/scripts/session-sync.sh"
