#!/usr/bin/env bash
# Back-compat wrapper — prefer review-learning.sh for interactive review
set -euo pipefail

SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PENDING_FILE="${1:-}"
DOMAIN="${2:-}"

if [[ -z "$PENDING_FILE" ]]; then
  cat <<EOF >&2
Usage: promote-learning.sh PENDING_FILE [domain]

Prefer the interactive command:
  review-learning.sh [PENDING_FILE]

This wrapper approves immediately (-y). Domain overrides frontmatter when set.
EOF
  exit 1
fi

args=(-y "$PENDING_FILE")
if [[ -n "$DOMAIN" ]]; then
  args+=(--domain "$DOMAIN")
fi

exec python3 "$SCRIPT_DIR/review-learning.py" "${args[@]}"
