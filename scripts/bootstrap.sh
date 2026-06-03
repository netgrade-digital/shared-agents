#!/usr/bin/env bash
# shared-agents bootstrap — one-shot setup (curl-friendly).
# Usage: curl -fsSL …/scripts/bootstrap.sh | bash
#    or: ./scripts/bootstrap.sh
set -euo pipefail

DEFAULT_CORE_REMOTE="${SHARED_AGENTS_CORE_REMOTE:-${SHARED_AGENTS_GIT_REMOTE:-git@github.com:netgrade-digital/shared-agents.git}}"
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
SHELL_RC="${SHELL_RC:-$HOME/.bashrc}"

if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
  SCRIPT_DIR=""
fi

_sa_ui() {
  local py="${SCRIPT_DIR}/sa_ui.py"
  [[ -f "$py" ]] || py="$SHARED_AGENTS_HOME/scripts/sa_ui.py"
  if [[ -f "$py" ]]; then
    python3 "$py" "$@" 2>/dev/null || true
  fi
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    _sa_ui --error "Missing dependency: $1" "Install git and python3, then retry." || \
      echo "Missing dependency: $1" >&2
    exit 1
  fi
}

need_cmd git
need_cmd python3

# Curl pipe: no script on disk — ensure core checkout, then run wizard from ~/.shared-agents.
if [[ -z "$SCRIPT_DIR" || ! -f "$SCRIPT_DIR/bootstrap_wizard.py" ]]; then
  mkdir -p "$(dirname "$SHARED_AGENTS_HOME")"
  if [[ -d "$SHARED_AGENTS_HOME/.git" ]]; then
    echo "Updating shared-agents core → $SHARED_AGENTS_HOME"
    git -C "$SHARED_AGENTS_HOME" config pull.rebase false 2>/dev/null || true
    git -C "$SHARED_AGENTS_HOME" config pull.ff only 2>/dev/null || true
    git -C "$SHARED_AGENTS_HOME" pull --ff-only --no-rebase 2>/dev/null || true
  elif [[ ! -f "$SHARED_AGENTS_HOME/scripts/bootstrap_wizard.py" ]]; then
    echo "Cloning shared-agents core → $SHARED_AGENTS_HOME"
    git clone --depth 1 "$DEFAULT_CORE_REMOTE" "$SHARED_AGENTS_HOME"
  fi
  SCRIPT_DIR="$SHARED_AGENTS_HOME/scripts"
fi

export SHARED_AGENTS_HOME
export SHARED_AGENTS_CORE_REMOTE="${SHARED_AGENTS_CORE_REMOTE:-$DEFAULT_CORE_REMOTE}"

if [[ -z "${SA_WIZARD_PLAIN:-}" ]]; then
  case "${TERM_PROGRAM:-}" in
    Cursor|vscode|Code) export SA_WIZARD_PLAIN=1 ;;
  esac
fi

BOOTSTRAP_EXTRA=()
if [[ ! -t 0 ]]; then
  BOOTSTRAP_EXTRA+=(--non-interactive)
fi

exec python3 "$SCRIPT_DIR/bootstrap_wizard.py" \
  --source "$(dirname "$SCRIPT_DIR")" \
  --home "$SHARED_AGENTS_HOME" \
  --shell-rc "$SHELL_RC" \
  --core-remote "$SHARED_AGENTS_CORE_REMOTE" \
  "${BOOTSTRAP_EXTRA[@]}" \
  "$@"
