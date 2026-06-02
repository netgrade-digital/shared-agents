#!/usr/bin/env bash
# Remove shared-agents block from shell rc (inverse of configure-shell-rc.sh).
set -euo pipefail

SHELL_RC="${1:-${SHELL_RC:-$HOME/.bashrc}}"
DRY_RUN="${DRY_RUN:-0}"

MARKER_BEGIN="# shared-agents team knowledge"
MARKER_END="# shared-agents:shell-end"

if [[ ! -f "$SHELL_RC" ]]; then
  echo "  ○ $SHELL_RC not found — nothing to remove"
  exit 0
fi

if grep -qF "$MARKER_END" "$SHELL_RC" 2>/dev/null; then
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [dry-run] would remove shared-agents block from $SHELL_RC"
    exit 0
  fi
  python3 - "$SHELL_RC" "$MARKER_BEGIN" "$MARKER_END" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
begin = sys.argv[2]
end = sys.argv[3]
text = path.read_text()
if begin in text and end in text:
    start = text.index(begin)
    finish = text.index(end) + len(end)
    updated = (text[:start].rstrip() + "\n" + text[finish:].lstrip()).rstrip()
    path.write_text(updated + ("\n" if updated else ""))
    print(f"  ✓ Removed shared-agents block from {path}")
else:
    print(f"  ○ No managed block in {path}")
PY
  exit 0
fi

if grep -qF 'SHARED_AGENTS_HOME=' "$SHELL_RC" 2>/dev/null; then
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [dry-run] would remove legacy SHARED_AGENTS_HOME lines from $SHELL_RC"
    exit 0
  fi
  python3 - "$SHELL_RC" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
lines = path.read_text().splitlines()
out = []
skip_aliases = False
for line in lines:
    if "shared-agents" in line.lower() and line.strip().startswith("#"):
        continue
    if line.strip().startswith("export SHARED_AGENTS_HOME="):
        continue
    if "shell-aliases.sh" in line:
        skip_aliases = True
        continue
    if skip_aliases:
        if line.strip() == "fi":
            skip_aliases = False
        continue
    out.append(line)
path.write_text("\n".join(out).rstrip() + ("\n" if out else ""))
print(f"  ✓ Removed legacy shared-agents lines from {path}")
PY
  exit 0
fi

echo "  ○ No shared-agents configuration in $SHELL_RC"
