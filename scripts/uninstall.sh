#!/usr/bin/env bash
# Remove shared-agents from this machine (adapters + optional repo delete).
set -euo pipefail

VERSION="0.1.0"
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
SHELL_RC="${SHELL_RC:-$HOME/.bashrc}"
DRY_RUN=0
YES=0
KEEP_REPO=0

usage() {
  cat <<EOF
shared-agents uninstall.sh v${VERSION}

Usage:
  uninstall.sh [options]

Removes IDE/CLI adapters, shell aliases, and optionally deletes the local repo.

Options:
  --home DIR       SHARED_AGENTS_HOME (default: ~/.shared-agents)
  --shell-rc FILE  Shell rc to clean (default: ~/.bashrc)
  --keep-repo      Remove adapters only — keep ~/.shared-agents checkout
  --dry-run        Show what would be removed
  -y, --yes        Bestätigung überspringen (non-interactive)
  -h, --help       Show this help

Nach Install (überall im Terminal):  sa-uninstall
Oder im Repo:                         ./uninstall.sh

After uninstall, re-install with: ./install.sh --wizard
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

if [[ ! -d "$SHARED_AGENTS_HOME" ]]; then
  echo "Nothing to uninstall — $SHARED_AGENTS_HOME does not exist."
  exit 0
fi

echo "shared-agents uninstall"
echo "  HOME:      $SHARED_AGENTS_HOME"
echo "  Shell rc:  $SHELL_RC"
if [[ $KEEP_REPO -eq 1 ]]; then
  echo "  Repo:      keep (adapters only)"
else
  echo "  Repo:      DELETE $SHARED_AGENTS_HOME"
fi
echo ""

if [[ $YES -eq 0 && $DRY_RUN -eq 0 ]]; then
  echo "Entfernt Cursor/Claude-Hooks, Skill-Symlinks, Shell-Aliase"
  if [[ $KEEP_REPO -eq 0 ]]; then
    echo "und löscht $SHARED_AGENTS_HOME vollständig."
  else
    echo "— Git-Checkout unter $SHARED_AGENTS_HOME bleibt erhalten (--keep-repo)."
  fi
  read -r -p "shared-agents deinstallieren? [y/N] " confirm
  if [[ ! "$confirm" =~ ^[yYjJ]([aA][eE]?[sS]?)?$ ]]; then
    echo "Abgebrochen."
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

echo "Step 1/3 — Tool adapters"
if [[ -f "$SHARED_AGENTS_HOME/scripts/uninstall-adapters.py" ]]; then
  args=(python3 "$SHARED_AGENTS_HOME/scripts/uninstall-adapters.py" "$SHARED_AGENTS_HOME")
  [[ $DRY_RUN -eq 1 ]] && args+=(--dry-run)
  "${args[@]}"
else
  echo "  ! uninstall-adapters.py missing — skip"
fi
echo ""

echo "Step 2/3 — Shell environment"
if [[ -f "$SHARED_AGENTS_HOME/scripts/remove-shell-rc.sh" ]]; then
  run bash "$SHARED_AGENTS_HOME/scripts/remove-shell-rc.sh" "$SHELL_RC"
else
  echo "  ! remove-shell-rc.sh missing — skip"
fi
echo ""

echo "Step 3/3 — Local repo"
if [[ $KEEP_REPO -eq 1 ]]; then
  echo "  ○ Keeping $SHARED_AGENTS_HOME (--keep-repo)"
elif [[ $DRY_RUN -eq 1 ]]; then
  echo "  [dry-run] would delete $SHARED_AGENTS_HOME"
else
  if [[ -d "$SHARED_AGENTS_HOME/.git" ]]; then
    dirty="$(git -C "$SHARED_AGENTS_HOME" status --porcelain 2>/dev/null || true)"
    if [[ -n "$dirty" ]]; then
      echo "  Warning: uncommitted changes in $SHARED_AGENTS_HOME" >&2
    fi
  fi
  rm -rf "$SHARED_AGENTS_HOME"
  echo "  ✓ Deleted $SHARED_AGENTS_HOME"
fi

echo ""
if [[ $DRY_RUN -eq 1 ]]; then
  echo "Dry run complete — no changes made."
else
  echo "Uninstall complete."
  echo "Re-install: git clone … ~/.shared-agents && cd ~/.shared-agents && ./install.sh --wizard"
fi
