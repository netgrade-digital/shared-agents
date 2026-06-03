#!/usr/bin/env bash
set -euo pipefail

SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
SYNC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="${1:-pull}"
QUIET=0

if [[ "${2:-}" == "--quiet" || "${1:-}" == "--quiet" ]]; then
  QUIET=1
  if [[ "${1:-}" == "--quiet" ]]; then
    ACTION="${2:-pull}"
  fi
fi

_sa_ui_py() {
  if [[ -f "$SYNC_DIR/sa_ui.py" ]]; then
    echo "$SYNC_DIR/sa_ui.py"
  else
    echo "$SHARED_AGENTS_HOME/scripts/sa_ui.py"
  fi
}

_sa_status_py() {
  if [[ -f "$SYNC_DIR/sa-status.py" ]]; then
    echo "$SYNC_DIR/sa-status.py"
  else
    echo "$SHARED_AGENTS_HOME/scripts/sa-status.py"
  fi
}

if [[ ! -d "$SHARED_AGENTS_HOME" ]]; then
  python3 "$(_sa_ui_py)" --error \
    "Shared agents repo not found at: $SHARED_AGENTS_HOME" \
    "Run: sa install" 2>/dev/null || {
    echo "Shared agents repo not found at: $SHARED_AGENTS_HOME" >&2
    echo "Run: sa install" >&2
  }
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

show_status_reminder() {
  local py
  py="$(_sa_status_py)"
  [[ -f "$py" ]] || return 0
  python3 "$py" --quiet 2>/dev/null || true
}

sync_team_data() {
  local py="$SHARED_AGENTS_HOME/scripts/team_data.py"
  [[ -f "$py" ]] || return 0
  if [[ "$QUIET" -eq 1 ]]; then
    python3 "$py" sync "$SHARED_AGENTS_HOME" --quiet 2>/dev/null || true
  else
    python3 "$py" sync "$SHARED_AGENTS_HOME" 2>/dev/null || true
  fi
}

case "$ACTION" in
  pull)
    pull_ff
    sync_team_data
    if [[ "$QUIET" -eq 0 ]]; then
      python3 "$(_sa_ui_py)" --sync-ok 2>/dev/null || echo "Core + team learnings synced."
      show_status_reminder
    fi
    ;;
  status)
    echo "core ($SHARED_AGENTS_HOME):"
    git -C "$SHARED_AGENTS_HOME" status -sb
    if [[ -d "$SHARED_AGENTS_HOME/team/.git" ]]; then
      echo ""
      echo "team ($SHARED_AGENTS_HOME/team):"
      git -C "$SHARED_AGENTS_HOME/team" status -sb
    fi
    ;;
  *)
    python3 "$(_sa_ui_py)" --error "Usage: sync.sh [pull|status] [--quiet]" 2>/dev/null || {
      echo "Usage: sync.sh [pull|status] [--quiet]" >&2
    }
    exit 1
    ;;
esac
