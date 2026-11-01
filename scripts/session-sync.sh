#!/usr/bin/env bash
# Session hook: pull latest learnings. Fail-open (never block the tool).
# One pull at a time. A second hook waits, then runs (the pull is then a no-op
# if the first finished). Stdout stays empty so Grok does not treat it as hook JSON.
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"

if [[ ! -d "$SHARED_AGENTS_HOME/.git" ]]; then
  exit 0
fi

python3 - "$SHARED_AGENTS_HOME" <<'PY'
import fcntl, hashlib, os, subprocess, sys, time

home = sys.argv[1]
key = hashlib.sha256(home.encode()).hexdigest()[:16]
lock_path = f"/tmp/shared-agents-session-sync-{key}.lock"
sync_sh = os.path.join(home, "scripts", "sync.sh")
with open(lock_path, "a", encoding="utf-8") as lock:
    deadline = time.time() + 50
    while True:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.time() >= deadline:
                sys.exit(0)
            time.sleep(0.2)
    subprocess.call(
        ["bash", sync_sh, "pull", "--quiet"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
sys.exit(0)
PY
exit 0
