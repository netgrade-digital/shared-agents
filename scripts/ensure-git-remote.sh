#!/usr/bin/env bash
# Ensure ~/.shared-agents pushes to Bitbucket, not a local dev checkout.
set -euo pipefail

REPO_HOME="${1:-${SHARED_AGENTS_HOME:-$HOME/.shared-agents}}"
DEFAULT_REMOTE="git@bitbucket.org:netgrade/shared-agents.git"

if [[ ! -d "$REPO_HOME/.git" ]]; then
  exit 0
fi

current="$(git -C "$REPO_HOME" remote get-url origin 2>/dev/null || true)"
if [[ -z "$current" ]]; then
  exit 0
fi

# Already a network remote — nothing to do.
if [[ "$current" == git@* || "$current" == https://* || "$current" == ssh://* ]]; then
  exit 0
fi

canonical="${SHARED_AGENTS_GIT_REMOTE:-$DEFAULT_REMOTE}"

# Local path remote: try upstream of that checkout (e.g. dev clone → Bitbucket).
local_path="${current#file://}"
if [[ -d "$local_path/.git" ]]; then
  upstream="$(git -C "$local_path" remote get-url origin 2>/dev/null || true)"
  if [[ "$upstream" == git@* || "$upstream" == https://* || "$upstream" == ssh://* ]]; then
    canonical="$upstream"
  fi
fi

git -C "$REPO_HOME" remote set-url origin "$canonical"
echo "Fixed git origin: $current -> $canonical"
