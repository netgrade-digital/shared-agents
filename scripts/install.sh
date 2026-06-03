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
BOOTSTRAP=0
TOOLS=""

usage() {
  cat <<EOF
shared-agents install.sh v${VERSION}

Usage:
  install.sh [options]              Install / update (TTY → Setup-Wizard)
  install.sh --wizard               Wizard explizit (wie Default in Terminal)
  install.sh --non-interactive      Ohne Wizard — alle erkannten Tools
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
    --bootstrap) BOOTSTRAP=1; FORCE_WIZARD=1; shift ;;
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

on_interrupt() {
  echo ""
  echo "Abgebrochen (Ctrl+C)."
  exit 130
}
trap on_interrupt INT

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

adapters_py() {
  if [[ "$REPO_SOURCE" != "$SHARED_AGENTS_HOME" && -f "$REPO_SOURCE/scripts/install-adapters.py" ]]; then
    echo "$REPO_SOURCE/scripts/install-adapters.py"
  elif [[ -f "$SHARED_AGENTS_HOME/scripts/install-adapters.py" ]]; then
    echo "$SHARED_AGENTS_HOME/scripts/install-adapters.py"
  else
    echo "$REPO_SOURCE/scripts/install-adapters.py"
  fi
}

sync_installer_from_source() {
  if [[ "$REPO_SOURCE" == "$SHARED_AGENTS_HOME" || $DRY_RUN -eq 1 ]]; then
    return 0
  fi
  if [[ ! -d "$REPO_SOURCE/scripts" ]]; then
    return 0
  fi
  echo "Sync installer scripts from source checkout → $SHARED_AGENTS_HOME"
  cp -a "$REPO_SOURCE/scripts/." "$SHARED_AGENTS_HOME/scripts/"
  [[ -f "$REPO_SOURCE/install.sh" ]] && cp -f "$REPO_SOURCE/install.sh" "$SHARED_AGENTS_HOME/install.sh"
  [[ -f "$REPO_SOURCE/sa" ]] && cp -f "$REPO_SOURCE/sa" "$SHARED_AGENTS_HOME/sa"
  [[ -f "$REPO_SOURCE/uninstall.sh" ]] && cp -f "$REPO_SOURCE/uninstall.sh" "$SHARED_AGENTS_HOME/uninstall.sh"
  chmod +x "$SHARED_AGENTS_HOME/scripts/"*.sh 2>/dev/null || true
  chmod +x "$SHARED_AGENTS_HOME/scripts/sa" 2>/dev/null || true
  chmod +x "$SHARED_AGENTS_HOME/sa" 2>/dev/null || true
  chmod +x "$SHARED_AGENTS_HOME/install.sh" 2>/dev/null || true
}

run_check() {
  local repo="${SHARED_AGENTS_HOME}"
  if [[ ! -d "$repo" ]]; then
    repo="$REPO_SOURCE"
  fi
  local py
  py="$(adapters_py)"
  local args=(check "$repo")
  [[ $CHECK_JSON -eq 1 ]] && args+=(--json)
  python3 "$py" "${args[@]}"
}

if [[ "$MODE" == "check" ]]; then
  run_check
  exit $?
fi

if [[ $BOOTSTRAP -eq 1 && $DRY_RUN -eq 0 ]]; then
  BW="$(adapters_py)"
  BW="${BW%/install-adapters.py}/bootstrap_wizard.py"
  if [[ -f "$BW" ]]; then
    exec python3 "$BW" \
      --source "$REPO_SOURCE" \
      --home "$SHARED_AGENTS_HOME" \
      --shell-rc "$SHELL_RC" \
      ${SHARED_AGENTS_CORE_REMOTE:+--core-remote "$SHARED_AGENTS_CORE_REMOTE"} \
      "$@"
  fi
fi

use_wizard=0
if [[ $NON_INTERACTIVE -eq 1 ]]; then
  use_wizard=0
elif [[ $FORCE_WIZARD -eq 1 ]] || [[ -t 0 && -t 1 ]]; then
  # Interaktiver Wizard (TUI in foot/alacritty, Text in Cursor-Terminal)
  use_wizard=1
fi

# Curses-TUI hängt oft in Cursor/VS-Code-Terminals — Text-Wizard ist stabiler.
if [[ $use_wizard -eq 1 && -z "${SA_WIZARD_PLAIN:-}" ]]; then
  case "${TERM_PROGRAM:-}" in
    Cursor|vscode|Code)
      export SA_WIZARD_PLAIN=1
      echo "Hinweis: Text-Wizard (IDE-Terminal). Für TUI: foot/alacritty + unset SA_WIZARD_PLAIN"
      ;;
  esac
fi

FRESH_INSTALL=0
DID_CLONE=0
WIZARD_CHOICES=""
WIZARD_PY="$(adapters_py)"

needs_bootstrap=0
if [[ "$REPO_SOURCE" != "$SHARED_AGENTS_HOME" && ! -d "$SHARED_AGENTS_HOME/.git" ]]; then
  needs_bootstrap=1
  FRESH_INSTALL=1
fi

# Erst-Install + Wizard: UI zuerst — bei Abbruch wird nichts geklont.
if [[ $use_wizard -eq 1 && $needs_bootstrap -eq 1 && $DRY_RUN -eq 0 ]]; then
  WIZARD_CHOICES="$(mktemp /tmp/shared-agents-wizard.XXXXXX)"
  cleanup_wizard_choices() { rm -f "$WIZARD_CHOICES"; }
  trap cleanup_wizard_choices EXIT INT

  echo ""
  echo "Setup-Wizard — $SHARED_AGENTS_HOME wird erst nach deiner Bestätigung angelegt."
  echo ""
  if ! python3 "$WIZARD_PY" wizard "$REPO_SOURCE" \
      --home "$SHARED_AGENTS_HOME" \
      --shell-rc "$SHELL_RC" \
      --collect-only \
      --choices-file "$WIZARD_CHOICES"; then
    echo ""
    echo "Abgebrochen — nichts installiert."
    exit 1
  fi
  SHARED_AGENTS_HOME="$(python3 -c "import json; print(json.load(open('$WIZARD_CHOICES'))['home'])")"
  export SHARED_AGENTS_HOME
  if [[ "$REPO_SOURCE" != "$SHARED_AGENTS_HOME" && ! -d "$SHARED_AGENTS_HOME/.git" ]]; then
    needs_bootstrap=1
  else
    needs_bootstrap=0
  fi
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
  DID_CLONE=1
  FRESH_INSTALL=1
  if [[ $DRY_RUN -eq 0 ]]; then
    fix_git_remote "$SHARED_AGENTS_HOME"
  fi
else
  echo "Copying $REPO_SOURCE -> $SHARED_AGENTS_HOME"
  mkdir -p "$SHARED_AGENTS_HOME"
  cp -a "$REPO_SOURCE/." "$SHARED_AGENTS_HOME/"
  FRESH_INSTALL=1
fi

sync_installer_from_source

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
  if [[ -n "$WIZARD_CHOICES" && -f "$WIZARD_CHOICES" ]]; then
    if ! python3 "$WIZARD_PY" wizard "$SHARED_AGENTS_HOME" \
        --shell-rc "$SHELL_RC" \
        --apply-only \
        --choices-file "$WIZARD_CHOICES"; then
      echo ""
      echo "Setup fehlgeschlagen."
      if [[ $DID_CLONE -eq 1 && -d "$SHARED_AGENTS_HOME" ]]; then
        echo "Entferne unvollständiges $SHARED_AGENTS_HOME …"
        rm -rf "$SHARED_AGENTS_HOME"
      fi
      exit 1
    fi
    rm -f "$WIZARD_CHOICES"
    trap - EXIT INT
  else
    WIZARD_ARGS=(wizard "$SHARED_AGENTS_HOME" --home "$SHARED_AGENTS_HOME" --shell-rc "$SHELL_RC")
    [[ $DRY_RUN -eq 1 ]] && WIZARD_ARGS+=(--dry-run)
    if ! python3 "$WIZARD_PY" "${WIZARD_ARGS[@]}"; then
      echo ""
      echo "Install abgebrochen — kein vollständiges Setup."
      exit 1
    fi
  fi
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

  python3 "$(adapters_py)" "${INSTALL_ARGS[@]}"

  if [[ $DRY_RUN -eq 0 ]]; then
    echo ""
    run_check
    if ! grep -qF "shared-agents:shell-end" "$SHELL_RC" 2>/dev/null; then
      DRY_RUN=0 bash "$SHARED_AGENTS_HOME/scripts/configure-shell-rc.sh" \
        "$SHARED_AGENTS_HOME" "$SHELL_RC" || true
    fi
  fi
fi

if [[ $DRY_RUN -eq 0 && -d "$SHARED_AGENTS_HOME/.git" ]]; then
  fix_git_remote "$SHARED_AGENTS_HOME"
  git -C "$SHARED_AGENTS_HOME" config pull.rebase false
  git -C "$SHARED_AGENTS_HOME" config pull.ff only
fi

_sa_ui_sh="$SHARED_AGENTS_HOME/scripts/sa-ui.sh"
[[ -f "$_sa_ui_sh" ]] || _sa_ui_sh="$REPO_SOURCE/scripts/sa-ui.sh"
if [[ -f "$_sa_ui_sh" ]]; then
  # shellcheck source=sa-ui.sh
  source "$_sa_ui_sh"
  echo
  sa_print_logo
  echo
fi

_sa_ui_py="${SHARED_AGENTS_HOME}/scripts/sa_ui.py"
[[ -f "$_sa_ui_py" ]] || _sa_ui_py="$REPO_SOURCE/scripts/sa_ui.py"
if [[ -f "$_sa_ui_py" ]]; then
  SHARED_AGENTS_HOME="$SHARED_AGENTS_HOME" SHELL_RC="$SHELL_RC" \
    python3 "$_sa_ui_py" --install-footer
else
  cat <<EOF

Install OK.

CLI:  sa help   (auch: shared-agents help · sharedagents help)

Wichtig — Shell neu laden:
  source $SHELL_RC

Befehle danach:
  sa sync              Neueste Learnings pullen
  sa review            Learning reviewen / approven
  sa pending push      Pending ans Team pushen
  sa unapprove         Learning aus approved entfernen
  sa check             Adapter-Status
  sa uninstall         Deinstallieren (y/N)

Docs:     $SHARED_AGENTS_HOME/README.md
Check:    sa check
Wizard:   sa install
Schnell:  sa install --non-interactive
Remove:   sa uninstall
EOF
fi
