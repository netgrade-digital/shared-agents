#!/usr/bin/env bash
set -euo pipefail

SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
ACTION="${1:-pull}"

if [[ ! -d "$SHARED_AGENTS_HOME" ]]; then
  echo "Shared agents repo not found at: $SHARED_AGENTS_HOME" >&2
  echo "Run: ~/.shared-agents/scripts/install.sh" >&2
  exit 1
fi

if [[ ! -d "$SHARED_AGENTS_HOME/.git" ]]; then
  # Non-git copy install — nothing to pull
  exit 0
fi

case "$ACTION" in
  pull)
    git -C "$SHARED_AGENTS_HOME" pull --ff-only
    ;;
  status)
    git -C "$SHARED_AGENTS_HOME" status -sb
    ;;
  *)
    echo "Usage: sync.sh [pull|status]" >&2
    exit 1
    ;;
esac
