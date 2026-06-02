#!/usr/bin/env bash
# Review a pending learning and promote it to approved/ + index.yaml
set -euo pipefail

SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/review-learning.py" "$@"
