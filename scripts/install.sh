#!/usr/bin/env bash
# shared-agents setup: install repo, configure detected AI CLIs, verify status.
# Open-source friendly — no network calls, manifest-driven (adapters/manifest.json).
set -euo pipefail

VERSION="0.1.0"
REPO_SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
SHELL_RC="${SHELL_RC:-$HOME/.bashrc}"
MODE="install"
DRY_RUN=0
CHECK_JSON=0
NON_INTERACTIVE=0
FORCE_WIZARD=0
TOOLS=""

usage() {
  cat <<EOF
shared-agents install.sh v${VERSION}

Usage:
  install.sh [options]              Install / update repo + configure tools
  install.sh --wizard               Interactive TUI (↑↓ Space Enter)
  install.sh --non-interactive      Configure all detected tools (CI/scripts)
  --check         Check which AI tools are installed vs configured
  --check --json  Same as check, JSON output (for CI/scripts)
  --dry-run       Show what install would do (no writes)

Options:
  --source DIR    Repo to install from (default: parent of scripts/)
  --home DIR      Install path (default: ~/.shared-agents)
  --shell-rc FILE Shell rc for SHARED_AGENTS_HOME (default: ~/.bashrc)
  --tools IDS     Comma-separated tool ids (e.g. cursor,claude-code)
  -h, --help      Show this help

After install, verify with:  install.sh --check
Registry: adapters/manifest.json
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check"; shift ;;
    --json) CHECK_JSON=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --wizard) FORCE_WIZARD=1; shift ;;
    --non-interactive) NON_INTERACTIVE=1; shift ;;
    --tools) TOOLS="$2"; shift 2 ;;
    --source) REPO_SOURCE="$2"; shift 2 ;;
    --home) SHARED_AGENTS_HOME="$2"; shift 2 ;;
    --shell-rc) SHELL_RC="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

export SHARED_AGENTS_HOME

fix_git_remote() {
  local home="$1"
  local script="$home/scripts/ensure-git-remote.sh"
  if [[ ! -f "$script" ]]; then
    script="$REPO_SOURCE/scripts/ensure-git-remote.sh"
  fi
  if [[ -f "$script" ]]; then
    bash "$script" "$home"
  fi
}

run_check() {
  local repo="${SHARED_AGENTS_HOME}"
  if [[ ! -d "$repo" ]]; then
    repo="$REPO_SOURCE"
  fi
  local args=(check "$repo")
  [[ $CHECK_JSON -eq 1 ]] && args+=(--json)
  python3 "$repo/scripts/install-adapters.py" "${args[@]}"
}

if [[ "$MODE" == "check" ]]; then
  run_check
  exit $?
fi

use_wizard=0
if [[ $NON_INTERACTIVE -eq 0 && ( $FORCE_WIZARD -eq 1 || ( -t 0 && -t 1 ) ) ]]; then
  use_wizard=1
fi

# --- install path ---
mkdir -p "$(dirname "$SHARED_AGENTS_HOME")"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN: repo sync skipped"
elif [[ "$REPO_SOURCE" == "$SHARED_AGENTS_HOME" ]]; then
  echo "Installing from live path: $SHARED_AGENTS_HOME"
elif [[ -d "$SHARED_AGENTS_HOME/.git" ]]; then
  echo "Updating existing install at $SHARED_AGENTS_HOME"
  git -C "$SHARED_AGENTS_HOME" config pull.rebase false
  git -C "$SHARED_AGENTS_HOME" config pull.ff only
  bash "$SHARED_AGENTS_HOME/scripts/sync.sh" pull 2>/dev/null || \
    git -C "$SHARED_AGENTS_HOME" pull --ff-only --no-rebase
elif [[ -e "$SHARED_AGENTS_HOME" && ! -d "$SHARED_AGENTS_HOME/.git" ]]; then
  echo "Updating copy at $SHARED_AGENTS_HOME from $REPO_SOURCE"
  cp -a "$REPO_SOURCE/." "$SHARED_AGENTS_HOME/"
elif [[ -d "$REPO_SOURCE/.git" ]]; then
  echo "Cloning $REPO_SOURCE -> $SHARED_AGENTS_HOME"
  git clone "$REPO_SOURCE" "$SHARED_AGENTS_HOME"
  if [[ $DRY_RUN -eq 0 ]]; then
    fix_git_remote "$SHARED_AGENTS_HOME"
  fi
else
  echo "Copying $REPO_SOURCE -> $SHARED_AGENTS_HOME"
  mkdir -p "$SHARED_AGENTS_HOME"
  cp -a "$REPO_SOURCE/." "$SHARED_AGENTS_HOME/"
fi

chmod +x "$SHARED_AGENTS_HOME/scripts/"*.sh 2>/dev/null || true
chmod +x "$SHARED_AGENTS_HOME/scripts/sa" 2>/dev/null || true
chmod +x "$SHARED_AGENTS_HOME/sa" 2>/dev/null || true
chmod +x "$SHARED_AGENTS_HOME/scripts/install-adapters.py" 2>/dev/null || true

if [[ $DRY_RUN -eq 0 && -d "$SHARED_AGENTS_HOME/.git" ]]; then
  fix_git_remote "$SHARED_AGENTS_HOME"
  git -C "$SHARED_AGENTS_HOME" config pull.rebase false
  git -C "$SHARED_AGENTS_HOME" config pull.ff only
fi

if [[ $use_wizard -eq 1 ]]; then
  WIZARD_ARGS=(wizard "$SHARED_AGENTS_HOME" --home "$SHARED_AGENTS_HOME" --shell-rc "$SHELL_RC")
  [[ $DRY_RUN -eq 1 ]] && WIZARD_ARGS+=(--dry-run)
  python3 "$SHARED_AGENTS_HOME/scripts/install-adapters.py" "${WIZARD_ARGS[@]}"
else
  if [[ $DRY_RUN -eq 0 ]]; then
    DRY_RUN="$DRY_RUN" bash "$SHARED_AGENTS_HOME/scripts/configure-shell-rc.sh" \
      "$SHARED_AGENTS_HOME" "$SHELL_RC"
  else
    DRY_RUN=1 bash "$SHARED_AGENTS_HOME/scripts/configure-shell-rc.sh" \
      "$SHARED_AGENTS_HOME" "$SHELL_RC"
  fi

  INSTALL_ARGS=(install "$SHARED_AGENTS_HOME")
  [[ $DRY_RUN -eq 1 ]] && INSTALL_ARGS+=(--dry-run)
  [[ -n "$TOOLS" ]] && INSTALL_ARGS+=(--tools "$TOOLS")
  INSTALL_ARGS+=(--non-interactive)

  python3 "$SHARED_AGENTS_HOME/scripts/install-adapters.py" "${INSTALL_ARGS[@]}"

  if [[ $DRY_RUN -eq 0 ]]; then
    echo ""
    run_check
  fi
fi

if [[ $DRY_RUN -eq 0 && -d "$SHARED_AGENTS_HOME/.git" ]]; then
  fix_git_remote "$SHARED_AGENTS_HOME"
  git -C "$SHARED_AGENTS_HOME" config pull.rebase false
  git -C "$SHARED_AGENTS_HOME" config pull.ff only
fi

cat <<EOF

Install OK.

CLI:  sa help   (auch: shared-agents help · sharedagents help)

Befehle (nach source ~/.bashrc oder neuem Terminal):
  sa sync              Neueste Learnings pullen
  sa review            Learning reviewen / approven
  sa pending push      Pending ans Team pushen
  sa unapprove         Learning aus approved entfernen
  sa check             Adapter-Status
  sa uninstall         Deinstallieren (y/N)

Docs:     $SHARED_AGENTS_HOME/README.md
Check:    sa check
Wizard:   sa install --wizard
Remove:   sa uninstall
EOF
