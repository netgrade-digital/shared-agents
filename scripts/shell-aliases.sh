# shared-agents shell helpers — sourced from ~/.bashrc (see configure-shell-rc.sh)
: "${SHARED_AGENTS_HOME:=$HOME/.shared-agents}"

_sa_install() {
  if [[ -f "$SHARED_AGENTS_HOME/install.sh" ]]; then
    echo "$SHARED_AGENTS_HOME/install.sh"
  else
    echo "$(_sa_bin install.sh)"
  fi
}

_sa_bin() {
  echo "$SHARED_AGENTS_HOME/scripts/$1"
}

_sa_uninstall() {
  if [[ -f "$SHARED_AGENTS_HOME/uninstall.sh" ]]; then
    echo "$SHARED_AGENTS_HOME/uninstall.sh"
  else
    echo "$(_sa_bin uninstall.sh)"
  fi
}

# Learnings review (paths resolve under $SHARED_AGENTS_HOME/learnings/pending/)
sa-review() {
  # Usage: sa-review [file|slug] [--domain DOMAIN] [-y] [--dry-run]
  "$(_sa_bin review-learning.sh)" "$@"
}

sa-review-list() {
  "$(_sa_bin review-learning.sh)" --list
}

sa-review-dry() {
  "$(_sa_bin review-learning.sh)" --dry-run "$@"
}

sa-unapprove() {
  # Usage: sa-unapprove [id|file] [--to-pending] [-y] [--dry-run] [--no-git]
  "$(_sa_bin unapprove-learning.sh)" "$@"
}

sa-unapprove-list() {
  "$(_sa_bin unapprove-learning.sh)" --list
}

sa-learning-path() {
  "$(_sa_bin learning-path.sh)" "$@"
}

# Optional shortcuts
sa-sync() {
  "$(_sa_bin sync.sh)" pull
}

sa-check() {
  "$(_sa_install)" --check
}

sa-uninstall() {
  # Deinstalliert shared-agents (Adapter + Aliase + ~/.shared-agents). Bestätigung: y/N
  # Usage: sa-uninstall [--keep-repo] [--dry-run]  |  -y zum Überspringen
  "$(_sa_uninstall)" "$@"
}
