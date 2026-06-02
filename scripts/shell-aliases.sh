# shared-agents shell helpers — sourced from ~/.bashrc (see configure-shell-rc.sh)
: "${SHARED_AGENTS_HOME:=$HOME/.shared-agents}"

_sa_bin() {
  echo "$SHARED_AGENTS_HOME/scripts/$1"
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

sa-learning-path() {
  "$(_sa_bin learning-path.sh)" "$@"
}

# Optional shortcuts
sa-sync() {
  "$(_sa_bin sync.sh)" pull
}

sa-check() {
  "$(_sa_bin install.sh)" --check
}
