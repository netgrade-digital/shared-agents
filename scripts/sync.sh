#!/usr/bin/env bash
set -euo pipefail

SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
ACTION="${1:-pull}"
QUIET=0

if [[ "${2:-}" == "--quiet" || "${1:-}" == "--quiet" ]]; then
  QUIET=1
  if [[ "${1:-}" == "--quiet" ]]; then
    ACTION="${2:-pull}"
  fi
fi

if [[ ! -d "$SHARED_AGENTS_HOME" ]]; then
  echo "Shared agents repo not found at: $SHARED_AGENTS_HOME" >&2
  echo "Run: ~/.shared-agents/scripts/install.sh" >&2
  exit 1
fi

if [[ ! -d "$SHARED_AGENTS_HOME/.git" ]]; then
  exit 0
fi

# Never use global pull.rebase here — breaks with local edits in ~/.shared-agents.
configure_pull() {
  git -C "$SHARED_AGENTS_HOME" config pull.rebase false
  git -C "$SHARED_AGENTS_HOME" config pull.ff only
}

pull_ff() {
  configure_pull
  local branch
  branch="$(git -C "$SHARED_AGENTS_HOME" rev-parse --abbrev-ref HEAD)"
  if [[ "$QUIET" -eq 1 ]]; then
    git -C "$SHARED_AGENTS_HOME" fetch origin --quiet
    git -C "$SHARED_AGENTS_HOME" merge --ff-only "origin/$branch" --quiet
  else
    git -C "$SHARED_AGENTS_HOME" fetch origin
    git -C "$SHARED_AGENTS_HOME" merge --ff-only "origin/$branch"
  fi
}

case "$ACTION" in
  pull)
    pull_ff
    ;;
  status)
    git -C "$SHARED_AGENTS_HOME" status -sb
    ;;
  *)
    echo "Usage: sync.sh [pull|status] [--quiet]" >&2
    exit 1
    ;;
esac
