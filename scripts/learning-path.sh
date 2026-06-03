#!/usr/bin/env bash
# Print canonical path for a pending learning file (or the pending directory).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "${SCRIPT_DIR}/learning_path.py" "$@"
