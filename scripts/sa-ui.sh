# shared-agents terminal UI — source from scripts/sa (do not execute directly)
# ASCII logo via sa_ui.py (colors only on logo lines).

SA_UI_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

sa_print_logo() {
  local py="${SA_UI_SCRIPT_DIR}/sa_ui.py"
  if [[ -f "$py" ]] && command -v python3 &>/dev/null; then
    python3 "$py" --logo
    return
  fi
  # fallback without Python
  printf '%s\n' \
    '  ____  _                        _      _                    _       ' \
    ' / ___|| |__   __ _ _ __ ___  __| |    / \   __ _  ___ _ __ | |_ ___ ' \
    ' \___ \| '\''_ \ / _` | '\''__/ _ \/ _` |   / _ \ / _` |/ _ \ '\''_ \| __/ __|' \
    '  ___) | | | | (_| | | |  __/ (_| |  / ___ \ (_| |  __/ | | | |_\__ \' \
    ' |____/|_| |_|\__,_|_|  \___|\__,_| /_/   \_\__, |\___|_| |_|\__|___/' \
    '                                            |___/                     ' \
    '  team skills · learnings · sync'
}

sa_print_header() {
  SA_VERSION="${1:-}" SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME}" \
    python3 "${SA_UI_SCRIPT_DIR}/sa_ui.py" --help 2>/dev/null || {
    sa_print_logo
    echo "  shared-agents CLI  (sa v${1:-})"
    echo
  }
}

_sa_ui_py() {
  python3 "${SA_UI_SCRIPT_DIR}/sa_ui.py" "$@"
}
