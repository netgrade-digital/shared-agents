#!/usr/bin/env bash
# Remove shared-agents from this machine (adapters + optional repo delete).
set -euo pipefail

_sa_on_cancel() {
  echo
  echo "Cancelled."
  exit 130
}
trap _sa_on_cancel INT

VERSION="0.1.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
SHELL_RC="${SHELL_RC:-$("$SCRIPT_DIR/detect-shell-rc.sh")}"
DRY_RUN=0
YES=0
KEEP_REPO=0

usage() {
  cat <<EOF
shared-agents uninstall.sh v${VERSION}

Usage:
  uninstall.sh [options]

Removes IDE/CLI adapters, shell CLI (sa), and optionally deletes the local install
(core checkout, team/ learnings repo, config.local.yaml).

Options:
  --home DIR       SHARED_AGENTS_HOME (default: ~/.shared-agents)
  --shell-rc FILE  Shell rc to clean (default: auto-detect)
  --keep-repo      Remove adapters only — keep ~/.shared-agents checkout
  --dry-run        Show what would be removed
  -y, --yes        Bestätigung überspringen (non-interactive)
  -h, --help       Show this help

Nach Install (überall im Terminal):  sa uninstall
                                      shared-agents uninstall
Oder im Repo:                         ./uninstall.sh

After uninstall, re-install with: sa bootstrap  (or ./scripts/bootstrap.sh)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --home) SHARED_AGENTS_HOME="$2"; shift 2 ;;
    --shell-rc) SHELL_RC="$2"; shift 2 ;;
    --keep-repo) KEEP_REPO=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -y|--yes) YES=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

export SHARED_AGENTS_HOME

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SA_UI_PY="$SCRIPT_DIR/sa_ui.py"
[[ -f "$SA_UI_PY" ]] || SA_UI_PY="$SHARED_AGENTS_HOME/scripts/sa_ui.py"

_sa() {
  if [[ -f "$SA_UI_PY" ]]; then
    SA_KEEP_REPO="$KEEP_REPO" SHELL_RC="$SHELL_RC" SA_DRY_RUN="$DRY_RUN" \
      SHARED_AGENTS_HOME="$SHARED_AGENTS_HOME" python3 "$SA_UI_PY" "$@"
  fi
}

if [[ ! -d "$SHARED_AGENTS_HOME" ]]; then
  _sa --out warn "Nothing to uninstall — $SHARED_AGENTS_HOME does not exist." || true
  echo "Nothing to uninstall — $SHARED_AGENTS_HOME does not exist."
  exit 0
fi

_sa --uninstall-intro

if [[ $YES -eq 0 && $DRY_RUN -eq 0 ]]; then
  _sa --out plain "Entfernt Hooks, Core- + Team-Skill-Symlinks, Shell-CLI (sa)" || true
  if [[ $KEEP_REPO -eq 0 ]]; then
    _sa --out plain "und löscht $SHARED_AGENTS_HOME inkl. team/ + config.local.yaml." || true
  else
    _sa --out plain "— Core + team/ unter $SHARED_AGENTS_HOME bleiben (--keep-repo)." || true
  fi
  read -r -p "shared-agents deinstallieren? [y/N] " confirm
  if [[ ! "$confirm" =~ ^[yYjJ]([aA][eE]?[sS]?)?$ ]]; then
    _sa --out warn "Abgebrochen." || true
    exit 1
  fi
fi

run() {
  if [[ $DRY_RUN -eq 1 ]]; then
    DRY_RUN=1 "$@"
  else
    "$@"
  fi
}

_sa --uninstall-step "Step 1/3 — Tool adapters"
_adapters_py="$SCRIPT_DIR/uninstall-adapters.py"
[[ -f "$_adapters_py" ]] || _adapters_py="$SHARED_AGENTS_HOME/scripts/uninstall-adapters.py"
if [[ -f "$_adapters_py" ]]; then
  args=(python3 "$_adapters_py" "$SHARED_AGENTS_HOME")
  [[ $DRY_RUN -eq 1 ]] && args+=(--dry-run)
  "${args[@]}"
else
  _sa --out warn "  ! uninstall-adapters.py missing — skip" || true
fi
echo ""

_sa --uninstall-step "Step 2/3 — Shell environment"
_remove_rc="$SCRIPT_DIR/remove-shell-rc.sh"
[[ -f "$_remove_rc" ]] || _remove_rc="$SHARED_AGENTS_HOME/scripts/remove-shell-rc.sh"
if [[ -f "$_remove_rc" ]]; then
  export SA_UI_PY
  run bash "$_remove_rc" "$SHELL_RC"
else
  _sa --out warn "  ! remove-shell-rc.sh missing — skip" || true
fi
echo ""

_sa --uninstall-step "Step 3/3 — Local repo"
if [[ $KEEP_REPO -eq 1 ]]; then
  _sa --dry-run-line "  ○ Keeping $SHARED_AGENTS_HOME (--keep-repo)"
elif [[ $DRY_RUN -eq 1 ]]; then
  _sa --dry-run-line "[dry-run] would delete $SHARED_AGENTS_HOME"
else
  if [[ -d "$SHARED_AGENTS_HOME/.git" ]]; then
    dirty="$(git -C "$SHARED_AGENTS_HOME" status --porcelain 2>/dev/null || true)"
    if [[ -n "$dirty" ]]; then
      _sa --error "  Warning: uncommitted changes in core checkout" || true
    fi
  fi
  if [[ -d "$SHARED_AGENTS_HOME/team/.git" ]]; then
    dirty_team="$(git -C "$SHARED_AGENTS_HOME/team" status --porcelain 2>/dev/null || true)"
    if [[ -n "$dirty_team" ]]; then
      _sa --error "  Warning: uncommitted changes in team/ (private learnings)" || true
    fi
  fi
  rm -rf "$SHARED_AGENTS_HOME"
  _sa --out success "  ✓ Deleted $SHARED_AGENTS_HOME" || true
fi

_sa --uninstall-footer
