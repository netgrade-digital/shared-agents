#!/usr/bin/env bash
# Print shell rc file(s) for install/bootstrap/uninstall.
#   detect-shell-rc.sh          primary login-shell rc
#   detect-shell-rc.sh --all    primary, plus fish config when fish is installed
#   detect-shell-rc.sh --known  existing rc files to clean on uninstall
# Respects SHELL_RC for the primary/--all modes (single explicit file).
set -euo pipefail

MODE="primary"
case "${1:-}" in
  --all) MODE="all" ;;
  --known) MODE="known" ;;
  "") ;;
  *) echo "Unknown option: $1" >&2; exit 2 ;;
esac

if [[ -n "${SHELL_RC:-}" && "$MODE" != "known" ]]; then
  printf '%s\n' "$SHELL_RC"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_sa_fallback() {
  local shell fish
  shell="$(basename "${SHELL:-/bin/bash}")"
  if [[ -n "${XDG_CONFIG_HOME:-}" ]]; then
    fish="$XDG_CONFIG_HOME/fish/config.fish"
  else
    fish="$HOME/.config/fish/config.fish"
  fi
  case "$MODE" in
    known)
      local candidate
      for candidate in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile" "$fish"; do
        [[ -f "$candidate" ]] && printf '%s\n' "$candidate"
      done
      ;;
    all)
      case "$shell" in
        zsh)  printf '%s\n' "$HOME/.zshrc" ;;
        bash) printf '%s\n' "$HOME/.bashrc" ;;
        fish) printf '%s\n' "$fish"; return ;;
        *)    printf '%s\n' "$HOME/.profile" ;;
      esac
      if command -v fish >/dev/null 2>&1 || [[ -f "$fish" ]]; then
        printf '%s\n' "$fish"
      fi
      ;;
    *)
      case "$shell" in
        zsh)  printf '%s\n' "$HOME/.zshrc" ;;
        bash) printf '%s\n' "$HOME/.bashrc" ;;
        fish) printf '%s\n' "$fish" ;;
        *)    printf '%s\n' "$HOME/.profile" ;;
      esac
      ;;
  esac
}

if ! python3 - "$SCRIPT_DIR" "$MODE" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from sa_config import default_shell_rc, known_shell_rcs, shell_rc_targets

mode = sys.argv[2]
if mode == "known":
    paths = known_shell_rcs()
elif mode == "all":
    paths = shell_rc_targets(include_fish=True)
else:
    paths = [default_shell_rc()]
for path in paths:
    print(path)
PY
then
  _sa_fallback
fi
