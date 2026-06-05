#!/usr/bin/env bash
# Remove shared-agents block from shell rc (inverse of configure-shell-rc.sh).
set -euo pipefail

RC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHELL_RC="${1:-${SHELL_RC:-$("$RC_DIR/detect-shell-rc.sh")}}"
DRY_RUN="${DRY_RUN:-0}"
MARKER_BEGIN="# shared-agents team knowledge"
MARKER_END="# shared-agents:shell-end"
SA_UI_PY="${SA_UI_PY:-$RC_DIR/sa_ui.py}"

_sa_out() {
  local kind="$1"
  shift
  if [[ -f "$SA_UI_PY" ]]; then
    python3 "$SA_UI_PY" --out "$kind" "$@" || printf '%s\n' "$*"
  else
    printf '%s\n' "$*"
  fi
}

_sa_dry() {
  if [[ -f "$SA_UI_PY" ]]; then
    python3 "$SA_UI_PY" --dry-run-line "$*" || printf '  %s\n' "$*"
  else
    printf '  %s\n' "$*"
  fi
}

_cleanup_shell_rc() {
  python3 - "$SHELL_RC" "$SA_UI_PY" <<'PY'
import os
import re
import subprocess
import sys
from pathlib import Path

path = Path(sys.argv[1])
ui_py = sys.argv[2] if len(sys.argv) > 2 else ""


def say_success(msg: str) -> None:
    if ui_py and Path(ui_py).is_file():
        subprocess.run(
            [sys.executable, ui_py, "--out", "success", msg],
            check=False,
        )
    else:
        print(msg)


if not path.is_file():
    sys.exit(0)

text = path.read_text()
lines = text.splitlines()

legacy_names = (
    "sa-help", "sa-sync", "sa-check", "sa-review", "sa-review-list", "sa-review-dry",
    "sa-pending-push", "sa-learning-path", "sa-unapprove", "sa-unapprove-list",
    "sa-uninstall", "sa", "shared-agents", "sharedagents", "_sa_cli", "_sa_dispatch",
)
legacy_re = re.compile(
    r"^\s*(?:" + "|".join(re.escape(n) for n in legacy_names) + r")\s*\(\)"
)

out: list[str] = []
skip_until_brace_close = False
brace_depth = 0
removed = 0

for line in lines:
    stripped = line.strip()

    if skip_until_brace_close:
        brace_depth += line.count("{") - line.count("}")
        if brace_depth <= 0:
            skip_until_brace_close = False
            brace_depth = 0
        removed += 1
        continue

    if legacy_re.match(line):
        if "{" in line and "}" not in line:
            skip_until_brace_close = True
            brace_depth = line.count("{") - line.count("}")
        removed += 1
        continue

    if stripped.startswith("#") and re.search(
        r"\bsa-(?:help|sync|review|check|uninstall|pending|unapprove)", stripped
    ):
        removed += 1
        continue

    if "unset -f" in line and "_sa_legacy" in line:
        removed += 1
        continue
    if stripped.startswith("for _sa_legacy in sa-"):
        removed += 1
        continue
    if stripped.startswith("unset _sa_legacy"):
        removed += 1
        continue

    out.append(line)

if removed:
    updated = "\n".join(out).rstrip()
    path.write_text(updated + ("\n" if updated else ""))
    say_success(f"  ✓ Removed {removed} legacy sa / shared-agents line(s) from {path}")
PY
}

if [[ ! -f "$SHELL_RC" ]]; then
  _sa_dry "○ $SHELL_RC not found — nothing to remove"
  exit 0
fi

if grep -qF "$MARKER_END" "$SHELL_RC" 2>/dev/null; then
  if [[ "$DRY_RUN" == "1" ]]; then
    _sa_dry "[dry-run] would remove shared-agents block from $SHELL_RC"
    _sa_dry "[dry-run] would remove legacy sa-* / CLI function lines from $SHELL_RC"
    exit 0
  fi
  python3 - "$SHELL_RC" "$MARKER_BEGIN" "$MARKER_END" "$SA_UI_PY" <<'PY'
import subprocess
import sys
from pathlib import Path

path = Path(sys.argv[1])
begin = sys.argv[2]
end = sys.argv[3]
ui_py = sys.argv[4]


def say(kind: str, msg: str) -> None:
    if Path(ui_py).is_file():
        subprocess.run(
            [sys.executable, ui_py, "--out", kind, msg],
            check=False,
        )
    else:
        print(msg)


text = path.read_text()
if begin in text and end in text:
    start = text.index(begin)
    finish = text.index(end) + len(end)
    updated = (text[:start].rstrip() + "\n" + text[finish:].lstrip()).rstrip()
    path.write_text(updated + ("\n" if updated else ""))
    say("success", f"  ✓ Removed shared-agents block from {path}")
else:
    say("warn", f"  ○ No managed block in {path}")
PY
  _cleanup_shell_rc
  exit 0
fi

if grep -qF 'SHARED_AGENTS_HOME=' "$SHELL_RC" 2>/dev/null; then
  if [[ "$DRY_RUN" == "1" ]]; then
    _sa_dry "[dry-run] would remove legacy SHARED_AGENTS_HOME lines from $SHELL_RC"
    _sa_dry "[dry-run] would remove legacy sa-* / CLI function lines from $SHELL_RC"
    exit 0
  fi
  python3 - "$SHELL_RC" "$SA_UI_PY" <<'PY'
import subprocess
import sys
from pathlib import Path

path = Path(sys.argv[1])
ui_py = sys.argv[2]


def say_success(msg: str) -> None:
    if Path(ui_py).is_file():
        subprocess.run(
            [sys.executable, ui_py, "--out", "success", msg],
            check=False,
        )
    else:
        print(msg)


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
say_success(f"  ✓ Removed legacy shared-agents lines from {path}")
PY
  _cleanup_shell_rc
  exit 0
fi

if [[ "$DRY_RUN" == "1" ]]; then
  _sa_dry "[dry-run] would scan $SHELL_RC for legacy sa-* / CLI function lines"
  exit 0
fi

_cleanup_shell_rc
_sa_dry "○ No shared-agents configuration in $SHELL_RC"
