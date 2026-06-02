#!/usr/bin/env bash
# Cursor/Claude sessionStart hook — pull latest learnings. Fail-open (never block IDE).
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"

if [[ ! -d "$SHARED_AGENTS_HOME/.git" ]]; then
  exit 0
fi

git -C "$SHARED_AGENTS_HOME" pull --ff-only --quiet 2>/dev/null || true
exit 0
