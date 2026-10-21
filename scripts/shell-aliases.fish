# shared-agents shell — sourced from fish config (see configure-shell-rc.sh)
if not set -q SHARED_AGENTS_HOME
    set -gx SHARED_AGENTS_HOME "$HOME/.shared-agents"
end

function _sa_cli
    if not test -f "$SHARED_AGENTS_HOME/scripts/sa"
        echo "shared-agents not installed at: $SHARED_AGENTS_HOME" >&2
        echo "Fix: sa bootstrap   (or: curl -fsSL …/scripts/bootstrap.sh | bash)" >&2
        echo "Or:  git clone <core-remote> ~/.shared-agents && ~/.shared-agents/scripts/bootstrap.sh" >&2
        return 127
    end
    "$SHARED_AGENTS_HOME/scripts/sa" $argv
end

function sa --description "shared-agents CLI"
    _sa_cli $argv
end

function shared-agents --description "shared-agents CLI"
    _sa_cli $argv
end

function sharedagents --description "shared-agents CLI"
    _sa_cli $argv
end
