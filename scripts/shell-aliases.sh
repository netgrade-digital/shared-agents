# shared-agents shell — sourced from ~/.bashrc (see configure-shell-rc.sh)
: "${SHARED_AGENTS_HOME:=$HOME/.shared-agents}"

# Drop legacy sa-* wrappers from older installs
for _sa_legacy in sa-help sa-sync sa-check sa-review sa-review-list sa-review-dry \
  sa-pending-push sa-learning-path sa-unapprove sa-unapprove-list sa-uninstall; do
  unset -f "$_sa_legacy" 2>/dev/null || true
done
unset _sa_legacy

_sa_cli() {
  "$SHARED_AGENTS_HOME/scripts/sa" "$@"
}

sa() { _sa_cli "$@"; }
shared-agents() { _sa_cli "$@"; }
sharedagents() { _sa_cli "$@"; }
