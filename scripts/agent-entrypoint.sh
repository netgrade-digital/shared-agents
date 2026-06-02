#!/usr/bin/env bash
# OpenClaw / headless agent entrypoint — sync before any work.
set -euo pipefail

SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"

if [[ ! -d "$SHARED_AGENTS_HOME/.git" ]]; then
  echo "shared-agents repo missing at $SHARED_AGENTS_HOME" >&2
  exit 1
fi

"$SHARED_AGENTS_HOME/scripts/sync.sh" pull

if [[ $# -gt 0 ]]; then
  exec "$@"
fi
