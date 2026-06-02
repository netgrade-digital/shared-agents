#!/usr/bin/env bash
# Idempotent: SHARED_AGENTS_HOME + source shell-aliases.sh in shell rc.
set -euo pipefail

SHARED_AGENTS_HOME="${1:?usage: configure-shell-rc.sh HOME [SHELL_RC]}"
SHELL_RC="${2:-${SHELL_RC:-$HOME/.bashrc}}"
DRY_RUN="${DRY_RUN:-0}"

MARKER_BEGIN="# shared-agents team knowledge"
MARKER_END="# shared-agents:shell-end"

block() {
  cat <<EOF

${MARKER_BEGIN} (managed by install.sh)
export SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME}"
if [[ -f "\$SHARED_AGENTS_HOME/scripts/shell-aliases.sh" ]]; then
  # sa | shared-agents | sharedagents — CLI (sa help)
  source "\$SHARED_AGENTS_HOME/scripts/shell-aliases.sh"
fi
${MARKER_END}
EOF
}

if [[ -f "$SHELL_RC" ]] && grep -qF "$MARKER_END" "$SHELL_RC" 2>/dev/null; then
  if grep -qF "export SHARED_AGENTS_HOME=" "$SHELL_RC" 2>/dev/null; then
    echo "  ✓ $SHELL_RC already has shared-agents shell block"
    exit 0
  fi
fi

# Legacy: only export line, no aliases — upgrade
if [[ -f "$SHELL_RC" ]] && grep -qF 'SHARED_AGENTS_HOME=' "$SHELL_RC" 2>/dev/null; then
  if ! grep -qF 'shell-aliases.sh' "$SHELL_RC" 2>/dev/null; then
    upgrade=$(cat <<'UP'

if [[ -f "$SHARED_AGENTS_HOME/scripts/shell-aliases.sh" ]]; then
  source "$SHARED_AGENTS_HOME/scripts/shell-aliases.sh"
fi
UP
)
    if [[ "$DRY_RUN" == "1" ]]; then
      echo "  [dry-run] would append shell-aliases source to $SHELL_RC"
      exit 0
    fi
    printf '%s\n' "$upgrade" >> "$SHELL_RC"
    echo "  ✓ Added shell-aliases source to $SHELL_RC"
    exit 0
  fi
  echo "  ✓ $SHELL_RC already configured"
  exit 0
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "  [dry-run] would append shared-agents block to $SHELL_RC"
  exit 0
fi

mkdir -p "$(dirname "$SHELL_RC")"
block >> "$SHELL_RC"
echo "  ✓ Added SHARED_AGENTS_HOME + CLI (sa) to $SHELL_RC"
