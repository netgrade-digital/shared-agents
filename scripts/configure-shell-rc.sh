#!/usr/bin/env bash
# Idempotent: SHARED_AGENTS_HOME + source shell-aliases.sh in shell rc.
set -euo pipefail

SHARED_AGENTS_HOME="${1:?usage: configure-shell-rc.sh HOME [SHELL_RC]}"
CFG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHELL_RC="${2:-${SHELL_RC:-$("$CFG_DIR/detect-shell-rc.sh")}}"
DRY_RUN="${DRY_RUN:-0}"

_sa_ui_out() {
  local kind="$1"
  shift
  local py="$CFG_DIR/sa_ui.py"
  if [[ -f "$py" ]]; then
    python3 "$py" --out "$kind" "$*" 2>/dev/null && return 0
  fi
  printf '%s\n' "$*"
}

MARKER_BEGIN="# shared-agents team knowledge"
MARKER_END="# shared-agents:shell-end"

_is_fish_rc() {
  local base
  base="$(basename "$SHELL_RC")"
  [[ "$base" == "config.fish" || "$SHELL_RC" == *.fish ]]
}

if _is_fish_rc; then
  ALIAS_FILE="shell-aliases.fish"
else
  ALIAS_FILE="shell-aliases.sh"
fi

block() {
  if _is_fish_rc; then
    cat <<EOF

${MARKER_BEGIN} (managed by install.sh)
set -gx SHARED_AGENTS_HOME "${SHARED_AGENTS_HOME}"
if test -f "\$SHARED_AGENTS_HOME/scripts/shell-aliases.fish"
    # sa | shared-agents | sharedagents — CLI (sa help)
    source "\$SHARED_AGENTS_HOME/scripts/shell-aliases.fish"
end
${MARKER_END}
EOF
    return
  fi
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
  if grep -qF "$ALIAS_FILE" "$SHELL_RC" 2>/dev/null; then
    _sa_ui_out ok "  ✓ $SHELL_RC already has shared-agents shell block"
    exit 0
  fi
fi

# Legacy: only SHARED_AGENTS_HOME line, no matching aliases — upgrade
if [[ -f "$SHELL_RC" ]] && grep -qF 'SHARED_AGENTS_HOME=' "$SHELL_RC" 2>/dev/null; then
  if ! grep -qF "$ALIAS_FILE" "$SHELL_RC" 2>/dev/null && ! grep -qF "$MARKER_END" "$SHELL_RC" 2>/dev/null; then
    if _is_fish_rc; then
      upgrade=$(cat <<'UP'

if test -f "$SHARED_AGENTS_HOME/scripts/shell-aliases.fish"
    source "$SHARED_AGENTS_HOME/scripts/shell-aliases.fish"
end
UP
)
    else
      upgrade=$(cat <<'UP'

if [[ -f "$SHARED_AGENTS_HOME/scripts/shell-aliases.sh" ]]; then
  source "$SHARED_AGENTS_HOME/scripts/shell-aliases.sh"
fi
UP
)
    fi
    if [[ "$DRY_RUN" == "1" ]]; then
      _sa_ui_out warn "  [dry-run] would append shell-aliases source to $SHELL_RC"
      exit 0
    fi
    printf '%s\n' "$upgrade" >> "$SHELL_RC"
    _sa_ui_out success "  ✓ Added shell-aliases source to $SHELL_RC"
    exit 0
  fi
  if grep -qF "$ALIAS_FILE" "$SHELL_RC" 2>/dev/null; then
    _sa_ui_out success "  ✓ $SHELL_RC already configured"
    exit 0
  fi
fi

if [[ "$DRY_RUN" == "1" ]]; then
  _sa_ui_out warn "  [dry-run] would append shared-agents block to $SHELL_RC"
  exit 0
fi

mkdir -p "$(dirname "$SHELL_RC")"
block >> "$SHELL_RC"
_sa_ui_out success "  ✓ Added SHARED_AGENTS_HOME + CLI (sa) to $SHELL_RC"
