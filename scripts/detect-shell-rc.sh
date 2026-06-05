#!/usr/bin/env bash
# Print the default shell rc file for the current user's login shell.
# Respects SHELL_RC when set. Used by install/bootstrap/uninstall scripts.
set -euo pipefail

if [[ -n "${SHELL_RC:-}" ]]; then
  printf '%s\n' "$SHELL_RC"
  exit 0
fi

case "$(basename "${SHELL:-/bin/bash}")" in
  zsh)  printf '%s\n' "$HOME/.zshrc" ;;
  bash) printf '%s\n' "$HOME/.bashrc" ;;
  *)    printf '%s\n' "$HOME/.profile" ;;
esac
