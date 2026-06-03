#!/usr/bin/env bash
# Print canonical path for a pending learning file (or the pending directory).
set -euo pipefail

SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
PENDING_DIR="$SHARED_AGENTS_HOME/learnings/pending"

if [[ $# -eq 0 ]]; then
  echo "$PENDING_DIR"
  exit 0
fi

slug="$1"
case "$slug" in
  */* | *\\*)
    _py="$(dirname "$0")/sa_ui.py"
    if [[ -f "$_py" ]]; then
      python3 "$_py" --error "learning-path.sh: slug must be a filename only (no directories)" >&2
    else
      echo "learning-path.sh: slug must be a filename only (no directories)" >&2
    fi
    exit 1
    ;;
esac

if [[ "$slug" != *.md ]]; then
  slug="${slug}.md"
fi

echo "$PENDING_DIR/$slug"
