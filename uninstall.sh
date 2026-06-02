#!/usr/bin/env bash
# Run from repo root: ./uninstall.sh [-y] [--keep-repo]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$ROOT/scripts/uninstall.sh" "$@"
