#!/usr/bin/env bash
# Run from repo root after clone: ./install.sh [--wizard]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/scripts/install.sh" --source "$ROOT" "$@"
