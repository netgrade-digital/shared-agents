#!/usr/bin/env python3
"""
shared-agents adapter installer and status checker.

Usage:
  install-adapters.py install REPO_HOME
  install-adapters.py check REPO_HOME [--json]
  install-adapters.py check REPO_HOME --json

Open-source friendly: no network, no secrets, manifest-driven (adapters/manifest.json).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from shutil import which

MARKER_BEGIN = "<!-- shared-agents:begin -->"
MARKER_END = "<!-- shared-agents:end -->"
VERSION = "0.1.0"


def claude_session_hook_command(entry: object) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        for hook in entry.get("hooks", []):
            if hook.get("type") == "command" and hook.get("command"):
                return hook["command"]
    return None


def claude_session_hook(hook_cmd: str) -> dict:
    return {
        "hooks": [
            {
                "type": "command",
                "command": hook_cmd,
            }
        ]
    }


def claude_session_has_hook(session: list, hook_cmd: str) -> bool:
    return any(claude_session_hook_command(entry) == hook_cmd for entry in session)


def normalize_claude_session_hooks(session: list) -> list:
    normalized: list = []
    for entry in session:
        cmd = claude_session_hook_command(entry)
        if cmd is None:
            normalized.append(entry)
            continue
        if isinstance(entry, str):
            normalized.append(claude_session_hook(cmd))
        else:
            normalized.append(entry)
    return normalized


class Status(str, Enum):
    OK = "ok"
    MISSING_TOOL = "missing_tool"
    NOT_CONFIGURED = "not_configured"
    PARTIAL = "partial"
    AVAILABLE = "available"  # e.g. openclaw entrypoint — no install detection


@dataclass
class ToolReport:
    id: str
    name: str
    installed: bool
    configured: bool
    status: Status
    detect_path: str | None
    detect_bins: list[str]
    bins_found: list[str]
    config_paths: list[str]
    docs: str
    message: str


def expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path)))


def load_manifest(repo_home: Path) -> dict:
    path = repo_home / "adapters" / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")
    return json.loads(path.read_text())


def agents_block(home: str, tool_note: str = "") -> str:
    extra = f"\n{tool_note.strip()}" if tool_note.strip() else ""
    return f"""{MARKER_BEGIN}
## Team Knowledge (shared-agents)

Repo: {home}

MANDATORY — first action every new session/thread, without asking:
  {home}/scripts/sync.sh pull

Before non-trivial work: search {home}/learnings/approved/ and index.yaml.
Use skill `shared-agents-knowledge` for the full workflow.
After reusable insights: write to {home}/learnings/pending/ only (skill `capture-learning`) — absolute path under SHARED_AGENTS_HOME, never the Cursor workspace. See {home}/docs/canonical-paths.md.
No secrets, tokens, or customer data in learnings.

After non-trivial tasks: ALWAYS ask "Soll ich ein Team-Learning anlegen?" — write pending/ only if user says yes.{extra}
{MARKER_END}
"""


def file_has_marker(path: Path) -> bool:
    return path.is_file() and MARKER_BEGIN in path.read_text()


def tool_config_paths(tool: dict, home: str) -> list[Path]:
    paths: list[Path] = []
    sync = tool.get("sync") or {}
    for key in ("agents_md", "alt_agents_md", "settings_json", "hooks_json"):
        if sync.get(key):
            paths.append(expand(sync[key]))
        if tool.get(key):
            paths.append(expand(tool[key]))
    for rule in (tool.get("rules") or {}).get("copy", []):
        paths.append(expand(rule["dest"]))
    if sync.get("script_dest"):
        paths.append(expand(sync["script_dest"]))
    env_home = tool.get("env_home")
    if env_home and os.environ.get(env_home):
        paths.append(expand(os.path.join(os.environ[env_home], "AGENTS.md")))
    for alt in tool.get("alt_rules") or []:
        paths.append(expand(alt))
    # dedupe preserve order
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def tool_is_installed(tool: dict) -> tuple[bool, list[str], list[str]]:
    detect_bins = list(tool.get("detect_bins") or [])
    bins_found = [b for b in detect_bins if which(b)]
    detect_path = tool.get("detect")
    path_exists = bool(detect_path and expand(detect_path).exists())

    if tool.get("detect") is None:
        # openclaw / generic — not "installed" in CLI sense
        return False, detect_bins, bins_found

    # installed if config dir exists OR any declared binary is on PATH
    installed = path_exists or bool(bins_found)
    return installed, detect_bins, bins_found


def check_cursor_configured(tool: dict) -> tuple[bool, str]:
    sync = tool["sync"]
    hook = expand(sync["script_dest"])
    hooks_json = expand(sync["hooks_json"])
    rule_dest = expand(tool["rules"]["copy"][0]["dest"])
    hook_ok = hook.is_file() and os.access(hook, os.X_OK)
    json_ok = False
    if hooks_json.is_file():
        data = json.loads(hooks_json.read_text())
        session = data.get("hooks", {}).get("sessionStart", [])
        json_ok = any(h.get("command") == sync["hook_command"] for h in session)
    rule_ok = rule_dest.is_file()
    ok = hook_ok and json_ok and rule_ok
    parts = []
    if not hook_ok:
        parts.append("hook script missing")
    if not json_ok:
        parts.append("sessionStart hook not registered")
    if not rule_ok:
        parts.append("rule missing")
    return ok, "; ".join(parts) if parts else "ok"


def check_claude_configured(tool: dict, home: str) -> tuple[bool, str]:
    sync = tool["sync"]
    settings_path = expand(sync["settings_json"])
    hook_cmd = sync["hook_command"].replace("$SHARED_AGENTS_HOME", home)
    if not settings_path.is_file():
        return False, f"{settings_path} missing"
    data = json.loads(settings_path.read_text())
    session = data.get("hooks", {}).get("SessionStart", [])
    if claude_session_has_hook(session, hook_cmd):
        return True, "ok"
    return False, "SessionStart hook not registered"


def check_agents_md_configured(tool: dict, home: str) -> tuple[bool, str]:
    paths = []
    for key in ("agents_md", "alt_agents_md"):
        if tool.get(key):
            paths.append(expand(tool[key]))
    env_home = tool.get("env_home")
    if env_home and os.environ.get(env_home):
        paths.append(expand(os.path.join(os.environ[env_home], "AGENTS.md")))
    if not paths:
        return False, "no agents_md paths in manifest"
    configured = [p for p in paths if file_has_marker(p)]
    if configured:
        return True, f"marker in {configured[0]}"
    return False, f"marker missing in {paths[0]}"


def check_tool(tool: dict, home: str) -> ToolReport:
    tid = tool["id"]
    detect_path = tool.get("detect")
    installed, detect_bins, bins_found = tool_is_installed(tool)
    config_paths = [str(p) for p in tool_config_paths(tool, home)]
    docs = tool.get("docs", "")

    if tid in ("generic",):
        return ToolReport(
            id=tid,
            name=tool["name"],
            installed=False,
            configured=False,
            status=Status.AVAILABLE,
            detect_path=None,
            detect_bins=detect_bins,
            bins_found=bins_found,
            config_paths=config_paths,
            docs=docs,
            message="Use adapters/generic/instructions.md for unsupported CLIs",
        )

    if tid == "openclaw":
        entry = expand(home) / "scripts" / "agent-entrypoint.sh"
        ep_ok = entry.is_file() and os.access(entry, os.X_OK)
        return ToolReport(
            id=tid,
            name=tool["name"],
            installed=True,
            configured=ep_ok,
            status=Status.OK if ep_ok else Status.NOT_CONFIGURED,
            detect_path=str(entry),
            detect_bins=[],
            bins_found=[],
            config_paths=[str(entry)],
            docs=docs,
            message="Wrap agent runs with agent-entrypoint.sh" if ep_ok else "entrypoint missing",
        )

    if not installed:
        return ToolReport(
            id=tid,
            name=tool["name"],
            installed=False,
            configured=False,
            status=Status.MISSING_TOOL,
            detect_path=str(expand(detect_path)) if detect_path else None,
            detect_bins=detect_bins,
            bins_found=bins_found,
            config_paths=config_paths,
            docs=docs,
            message="Tool not detected — install CLI, then re-run install.sh",
        )

    if tid == "cursor":
        configured, msg = check_cursor_configured(tool)
    elif tid == "claude-code":
        configured, msg = check_claude_configured(tool, home)
    elif tool.get("agents_md") or tool.get("alt_agents_md"):
        configured, msg = check_agents_md_configured(tool, home)
    else:
        configured, msg = False, "unknown adapter type"

    status = Status.OK if configured else Status.NOT_CONFIGURED
    return ToolReport(
        id=tid,
        name=tool["name"],
        installed=True,
        configured=configured,
        status=status,
        detect_path=str(expand(detect_path)) if detect_path else None,
        detect_bins=detect_bins,
        bins_found=bins_found,
        config_paths=config_paths,
        docs=docs,
        message=msg,
    )


def check_repo(home: str) -> tuple[bool, str]:
    root = expand(home)
    if not root.is_dir():
        return False, f"SHARED_AGENTS_HOME not found: {root}"
    manifest = root / "adapters" / "manifest.json"
    sync = root / "scripts" / "sync.sh"
    if not manifest.is_file():
        return False, "manifest.json missing"
    if not sync.is_file():
        return False, "sync.sh missing"
    return True, "ok"


def check_skills(repo_home: Path, manifest: dict) -> list[str]:
    issues = []
    skills = sorted(p for p in repo_home.glob("skills/*/") if p.is_dir())
    if not skills:
        issues.append("No skills/ in repo")
        return issues
    for entry in manifest["shared"]["skill_dirs"]:
        dest_root = expand(entry["path"])
        if not dest_root.is_dir():
            issues.append(f"Skill dir missing: {dest_root}")
            continue
        for skill in skills:
            dest = dest_root / skill.name
            if not dest.exists():
                issues.append(f"Skill not linked: {dest}")
            elif dest.is_symlink() and dest.resolve() != skill.resolve():
                issues.append(f"Skill symlink stale: {dest}")
    return issues


def run_check(repo_home: Path, home: str, as_json: bool) -> int:
    repo_ok, repo_msg = check_repo(home)
    manifest = load_manifest(repo_home) if repo_ok else {"tools": [], "shared": {"skill_dirs": []}}
    reports = [check_tool(t, home) for t in manifest.get("tools", [])]
    skill_issues = check_skills(repo_home, manifest) if repo_ok else []

    if as_json:
        payload = {
            "version": VERSION,
            "shared_agents_home": home,
            "repo_ok": repo_ok,
            "repo_message": repo_msg,
            "skill_issues": skill_issues,
            "tools": [asdict(r) for r in reports],
        }
        print(json.dumps(payload, indent=2))
        return 0 if repo_ok else 1

    print(f"shared-agents check v{VERSION}")
    print(f"SHARED_AGENTS_HOME={home}")
    print(f"Repo: {'OK' if repo_ok else 'MISSING'} — {repo_msg}\n")

    col_id = 14
    print(f"{'TOOL':<{col_id}} {'INSTALLED':<10} {'CONFIGURED':<12} STATUS")
    print("-" * 60)
    for r in reports:
        inst = "yes" if r.installed else "no"
        conf = "yes" if r.configured else "no"
        print(f"{r.id:<{col_id}} {inst:<10} {conf:<12} {r.status.value}")
    print()

    for r in reports:
        if r.status == Status.OK or r.status == Status.AVAILABLE:
            continue
        hint = r.detect_path or (", ".join(r.detect_bins) if r.detect_bins else "—")
        print(f"  [{r.id}] {r.message}")
        if hint:
            print(f"         detect: {hint}")
        if r.docs:
            print(f"         docs:   {r.docs}")

    if skill_issues:
        print("\nSkill links:")
        for issue in skill_issues:
            print(f"  ! {issue}")

    needs_install = any(r.installed and not r.configured for r in reports)
    missing = sum(1 for r in reports if r.status == Status.MISSING_TOOL)
    if needs_install:
        print(f"\n→ Run: {home}/install.sh")
    if missing:
        print(f"→ {missing} tool(s) not installed on this machine (expected if unused)")

    return 0 if repo_ok else 1


# --- install (unchanged logic, refactored) ---


def merge_agents_md(target: Path, block: str, dry_run: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text() if target.is_file() else ""
    if MARKER_BEGIN in existing and MARKER_END in existing:
        start = existing.index(MARKER_BEGIN)
        end = existing.index(MARKER_END) + len(MARKER_END)
        updated = existing[:start].rstrip() + "\n\n" + block + "\n" + existing[end:].lstrip()
    elif existing.strip():
        updated = existing.rstrip() + "\n\n" + block + "\n"
    else:
        updated = block + "\n"
    if not dry_run:
        target.write_text(updated)


def symlink_skills(repo_home: Path, skill_dirs: list[dict], dry_run: bool = False) -> list[str]:
    messages = []
    skills = sorted(p for p in repo_home.glob("skills/*/") if p.is_dir())
    for entry in skill_dirs:
        dest_root = expand(entry["path"])
        if not dry_run:
            dest_root.mkdir(parents=True, exist_ok=True)
        for skill in skills:
            dest = dest_root / skill.name
            if dry_run:
                messages.append(f"[dry-run] would link {skill.name} → {dest_root}")
                continue
            if dest.is_symlink():
                dest.unlink()
            elif dest.exists():
                continue
            dest.symlink_to(skill.resolve())
        if not dry_run:
            note = entry.get("note", "")
            messages.append(f"Skills → {dest_root}" + (f" ({note})" if note else ""))
    return messages


def install_cursor(repo_home: Path, tool: dict, dry_run: bool) -> list[str]:
    if dry_run:
        return ["[dry-run] would configure Cursor (rule + sessionStart hook)"]
    sync = tool["sync"]
    dest_hook = expand(sync["script_dest"])
    dest_hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo_home / sync["script_src"], dest_hook)
    dest_hook.chmod(0o755)
    for rule in tool.get("rules", {}).get("copy", []):
        dest = expand(rule["dest"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo_home / rule["src"], dest)
    hooks_path = expand(sync["hooks_json"])
    entry = {"command": sync["hook_command"], "timeout": 30}
    data = {"version": 1, "hooks": {}}
    if hooks_path.is_file():
        data = json.loads(hooks_path.read_text())
    session = data.setdefault("hooks", {}).setdefault("sessionStart", [])
    if not any(h.get("command") == entry["command"] for h in session):
        session.insert(0, entry)
    stop_prompt = (
        "The agent session is ending. If this session completed a non-trivial task "
        "(feature, bugfix, refactor, multi-file change, non-obvious fix), you MUST ask "
        "the user in German: 'Soll ich ein Team-Learning in shared-agents anlegen?' "
        "If they agree, use capture-learning and write to learnings/pending/ only. "
        "If they decline or the task was trivial (typo, formatting, pure Q&A), do nothing."
    )
    stop = data["hooks"].setdefault("stop", [])
    if not any(h.get("type") == "prompt" and "Team-Learning" in h.get("prompt", "") for h in stop):
        stop.insert(0, {"type": "prompt", "prompt": stop_prompt, "loop_limit": 1})
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(json.dumps(data, indent=2) + "\n")
    return [
        f"Cursor: rule + sessionStart hook ({dest_hook})",
        "Cursor: stop hook (ask for learning after big tasks)",
    ]


def install_claude(home: str, tool: dict, dry_run: bool) -> list[str]:
    if dry_run:
        return ["[dry-run] would configure Claude Code SessionStart hook"]
    sync = tool["sync"]
    settings_path = expand(sync["settings_json"])
    hook_cmd = sync["hook_command"].replace("$SHARED_AGENTS_HOME", home)
    data = {}
    if settings_path.is_file():
        data = json.loads(settings_path.read_text())
    session = data.setdefault("hooks", {}).setdefault("SessionStart", [])
    session[:] = normalize_claude_session_hooks(session)
    if not claude_session_has_hook(session, hook_cmd):
        session.insert(0, claude_session_hook(hook_cmd))
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(data, indent=2) + "\n")
    return [f"Claude Code: SessionStart hook in {settings_path}"]


def install_agents_md_tool(home: str, tool: dict, dry_run: bool) -> list[str]:
    block = agents_block(home, tool.get("note", ""))
    paths: list[Path] = []
    for key in ("agents_md", "alt_agents_md"):
        if tool.get(key):
            paths.append(expand(tool[key]))
    for alt in tool.get("alt_rules") or []:
        paths.append(expand(alt))
    env_home = tool.get("env_home")
    if env_home and os.environ.get(env_home):
        paths.append(expand(os.path.join(os.environ[env_home], "AGENTS.md")))
    messages = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        if dry_run:
            messages.append(f"[dry-run] would merge block into {path}")
        else:
            merge_agents_md(path, block)
            messages.append(f"{tool['name']}: merged block into {path}")
    return messages


def install_tool(repo_home: Path, home: str, tool: dict, dry_run: bool) -> list[str]:
    tid = tool["id"]
    if tid == "cursor":
        return install_cursor(repo_home, tool, dry_run)
    if tid == "claude-code":
        return install_claude(home, tool, dry_run)
    if tool.get("agents_md") or tool.get("alt_agents_md") or tool.get("alt_rules"):
        return install_agents_md_tool(home, tool, dry_run)
    return []


def installable_tools(manifest: dict) -> list[dict]:
    return [
        t
        for t in manifest.get("tools", [])
        if t["id"] not in ("generic", "openclaw")
    ]


def parse_tool_ids(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    return {part.strip() for part in raw.split(",") if part.strip()}


def run_install(
    repo_home: Path,
    home: str,
    dry_run: bool,
    *,
    tool_ids: set[str] | None = None,
) -> int:
    os.environ["SHARED_AGENTS_HOME"] = home
    manifest = load_manifest(repo_home)
    print(f"Installing adapters v{VERSION} (SHARED_AGENTS_HOME={home})")
    if dry_run:
        print("DRY RUN — no files will be modified\n")

    messages = symlink_skills(repo_home, manifest["shared"]["skill_dirs"], dry_run=dry_run)
    configured: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []

    for tool in installable_tools(manifest):
        tid = tool["id"]
        if tool_ids is not None and tid not in tool_ids:
            continue
        installed, _, _ = tool_is_installed(tool)
        if not installed:
            if tool_ids is not None and tid in tool_ids:
                missing.append(tool["name"])
            else:
                skipped.append(tool["name"])
            continue
        messages.extend(install_tool(repo_home, home, tool, dry_run))
        configured.append(tool["name"])

    generic = repo_home / "adapters" / "generic" / "instructions.md"
    if not dry_run:
        generic.parent.mkdir(parents=True, exist_ok=True)
        generic.write_text(
            agents_block(home, "Copy into your CLI global AGENTS.md / CLAUDE.md / GEMINI.md.")
        )

    print("Actions:")
    for msg in messages:
        print(f"  ✓ {msg}")
    if configured:
        print("\nConfigured:")
        for name in configured:
            print(f"  • {name}")
    if missing:
        print("\nNot installed (selected but missing on this machine):")
        for name in missing:
            print(f"  ✗ {name}")
    if skipped:
        print("\nSkipped (tool not detected):")
        for name in skipped:
            print(f"  ○ {name}")

    print("\nVerify: ./install.sh --check")
    return 0


# --- wizard ---


def is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not is_tty():
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    return _c("1", text)


def dim(text: str) -> str:
    return _c("2", text)


def green(text: str) -> str:
    return _c("32", text)


def yellow(text: str) -> str:
    return _c("33", text)


def cyan(text: str) -> str:
    return _c("36", text)


def prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            answer = input(f"{text}{suffix}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(130)
        if answer:
            return answer
        if default is not None:
            return default
        print("Please enter a value.")


def confirm(text: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        try:
            answer = input(f"{text} [{hint}]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(130)
        if not answer:
            return default
        if answer in {"y", "yes", "j", "ja"}:
            return True
        if answer in {"n", "no", "nein"}:
            return False
        print("Please answer y or n.")


def print_banner() -> None:
    line = "═" * 58
    print()
    print(cyan(f"╔{line}╗"))
    print(cyan("║") + bold("  shared-agents Setup Wizard".ljust(58)) + cyan("║"))
    print(cyan(f"╚{line}╝"))
    print(dim("  Team skills + learnings for your AI tools"))
    print()


def tool_status_label(report: ToolReport) -> str:
    if report.status == Status.OK:
        return green("configured")
    if report.installed:
        return yellow("needs setup")
    return dim("not installed")


def configure_shell_rc(shell_rc: Path, home: str, dry_run: bool, repo_home: Path | None = None) -> bool:
    script = expand(home) / "scripts" / "configure-shell-rc.sh"
    if not script.is_file() and repo_home is not None:
        script = expand(str(repo_home)) / "scripts" / "configure-shell-rc.sh"
    if not script.is_file():
        print(f"  ! configure-shell-rc.sh not found under {home}")
        return False
    env = os.environ.copy()
    env["DRY_RUN"] = "1" if dry_run else "0"
    result = subprocess.run(
        ["bash", str(script), home, str(shell_rc)],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.returncode != 0 and result.stderr.strip():
        print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode == 0


def wizard_select_tools(reports: list[tuple[dict, ToolReport]]) -> set[str]:
    selected = {tool["id"] for tool, report in reports if report.installed}
    if not reports:
        return set()

    while True:
        print(bold("Step 2/4 — Select AI tools"))
        print(dim("  Toggle with number · all · detected · none · Enter to continue"))
        print()
        for idx, (tool, report) in enumerate(reports, start=1):
            mark = "x" if tool["id"] in selected else " "
            status = tool_status_label(report)
            name = tool["name"]
            print(f"  [{idx}] [{mark}] {name:<24} {status}")
        print()
        choice = input("> ").strip().lower()
        if choice in {"", "done", "ok", "weiter"}:
            break
        if choice in {"all", "a"}:
            selected = {tool["id"] for tool, _ in reports}
            continue
        if choice in {"detected", "d", "installed"}:
            selected = {tool["id"] for tool, report in reports if report.installed}
            continue
        if choice in {"none", "n"}:
            selected = set()
            continue
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(reports):
                tid = reports[num - 1][0]["id"]
                if tid in selected:
                    selected.remove(tid)
                else:
                    selected.add(tid)
            else:
                print("Invalid number.")
            continue
        ids = parse_tool_ids(choice.replace(" ", ","))
        if ids:
            valid = {tool["id"] for tool, _ in reports}
            unknown = ids - valid
            if unknown:
                print(f"Unknown tool id(s): {', '.join(sorted(unknown))}")
                continue
            selected = ids
            continue
        print("Use: number, all, detected, none, or Enter.")

    return selected


def tool_status_plain(report: ToolReport) -> str:
    if report.status == Status.OK:
        return "configured"
    if report.installed:
        return "needs setup"
    return "not installed"


def run_wizard_plain(
    repo_home: Path,
    home: str,
    reports: list[tuple[dict, ToolReport]],
    *,
    dry_run: bool,
    shell_rc: Path | None,
) -> tuple[str, set[str], bool, bool] | None:
    """Returns (home, selected, add_shell, run_setup) or None if cancelled."""
    print_banner()

    print(bold("Step 1/4 — Install location"))
    print(f"  Repo:  {repo_home}")
    default_home = home
    if is_tty():
        home_input = prompt("  SHARED_AGENTS_HOME", default_home)
        home = os.path.expanduser(os.path.expandvars(home_input))
    else:
        home = default_home
    print()

    selected = wizard_select_tools(reports)
    print()
    if not selected:
        print("No tools selected — skills will still be linked.")
    print()

    print(bold("Step 3/4 — Shell environment"))
    add_shell = True
    shell_rc_path = shell_rc or expand("~/.bashrc")
    rc_text = shell_rc_path.read_text() if shell_rc_path.is_file() else ""
    has_home = "SHARED_AGENTS_HOME=" in rc_text
    has_cli = "shell-aliases.sh" in rc_text
    if has_home and has_cli:
        print(f"  ✓ {shell_rc_path} already configured (SHARED_AGENTS_HOME + CLI)")
        add_shell = False
    elif has_home and not has_cli:
        print(f"  → {shell_rc_path} has SHARED_AGENTS_HOME — will add CLI (sa)")
        add_shell = True
    elif is_tty():
        add_shell = confirm(
            f"  Add SHARED_AGENTS_HOME + sa CLI to {shell_rc_path}?",
            True,
        )
    print()

    print(bold("Step 4/4 — Summary"))
    print(f"  Install path: {home}")
    print(f"  Skills:       link all team skills")
    if selected:
        print("  Configure:")
        for tool, report in reports:
            if tool["id"] in selected:
                print(f"    • {tool['name']} ({tool_status_label(report)})")
    else:
        print("  Configure:    (none)")
    print()
    if not confirm("Run setup now?", False):
        return None
    return home, selected, add_shell, True


def run_wizard(
    repo_home: Path,
    home: str,
    *,
    dry_run: bool = False,
    shell_rc: Path | None = None,
) -> int:
    repo_ok, repo_msg = check_repo(str(repo_home))
    if not repo_ok:
        repo_ok, repo_msg = check_repo(home)
    if not repo_ok:
        print(f"Repo error: {repo_msg}", file=sys.stderr)
        return 1

    manifest = load_manifest(repo_home if (repo_home / "adapters" / "manifest.json").is_file() else expand(home))
    reports = [
        (tool, check_tool(tool, home))
        for tool in installable_tools(manifest)
    ]

    shell_rc_path = shell_rc or expand("~/.bashrc")
    shell_rc_str = str(shell_rc_path)

    choices: tuple[str, set[str], bool, bool] | None = None

    try:
        from wizard_tui import (
            ToolRow,
            WizardTuiFailed,
            detect_shell_rc_state,
            run_wizard_tui,
            tui_available,
        )
    except ImportError:
        tui_available = lambda: False  # type: ignore[misc, assignment]
        run_wizard_tui = None  # type: ignore[assignment]
        WizardTuiFailed = Exception  # type: ignore[misc, assignment]

    if tui_available() and run_wizard_tui is not None:
        tool_rows = [
            ToolRow(
                tool_id=tool["id"],
                name=tool["name"],
                status=tool_status_plain(report),
                installed=report.installed,
            )
            for tool, report in reports
        ]
        shell_state = detect_shell_rc_state(shell_rc_str)
        tui_failed = False
        try:
            result = run_wizard_tui(
                default_home=home,
                rows=tool_rows,
                shell_rc=shell_rc_str,
                shell_state=shell_state,
            )
        except WizardTuiFailed as exc:
            print(f"  → {exc} — using text prompts.", file=sys.stderr)
            tui_failed = True
            result = None

        if result is not None:
            if not result.run_setup:
                print("Cancelled.")
                return 1
            choices = (result.home, result.selected_tools, result.add_shell, True)
        elif tui_failed:
            choices = run_wizard_plain(
                repo_home,
                home,
                reports,
                dry_run=dry_run,
                shell_rc=shell_rc_path,
            )
            if choices is None:
                print("Cancelled.")
                return 1
        else:
            print("Cancelled.")
            return 1
    else:
        choices = run_wizard_plain(
            repo_home,
            home,
            reports,
            dry_run=dry_run,
            shell_rc=shell_rc_path,
        )
        if choices is None:
            print("Cancelled.")
            return 1

    home, selected, add_shell, _run = choices
    os.environ["SHARED_AGENTS_HOME"] = home

    if add_shell:
        if not configure_shell_rc(shell_rc_path, home, dry_run, repo_home=repo_home):
            print("Warning: shell CLI was not configured — run: sa install --wizard", file=sys.stderr)
            return 1

    print()
    run_install(repo_home, home, dry_run, tool_ids=selected)
    if not dry_run:
        print()
        run_check(repo_home, home, as_json=False)
        print()
        print(f"Shell CLI:  source {shell_rc_path}")
        print("            (or open a new terminal)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install or check shared-agents adapters for AI CLIs.",
        prog="install-adapters.py",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_wizard = sub.add_parser("wizard", help="Interactive setup wizard")
    p_wizard.add_argument("repo_home", type=Path, help="Path to shared-agents repo")
    p_wizard.add_argument(
        "--home",
        default=None,
        help="SHARED_AGENTS_HOME (default: env or ~/.shared-agents)",
    )
    p_wizard.add_argument(
        "--shell-rc",
        default=None,
        help="Shell rc file for SHARED_AGENTS_HOME export",
    )
    p_wizard.add_argument("--dry-run", action="store_true", help="Show actions without writing")

    p_install = sub.add_parser("install", help="Configure AI tools")
    p_install.add_argument("repo_home", type=Path, help="Path to shared-agents repo")
    p_install.add_argument("--dry-run", action="store_true", help="Show actions without writing")
    p_install.add_argument(
        "--tools",
        default=None,
        help="Comma-separated tool ids (default: all detected)",
    )
    p_install.add_argument(
        "--non-interactive",
        action="store_true",
        help="Install all detected tools without prompts",
    )

    p_check = sub.add_parser("check", help="Report installed vs configured tools")
    p_check.add_argument("repo_home", type=Path, help="Path to shared-agents repo")
    p_check.add_argument("--json", action="store_true", help="Machine-readable output")

    args = parser.parse_args()
    repo_home = args.repo_home.resolve()
    default_home = os.environ.get("SHARED_AGENTS_HOME", str(expand("~/.shared-agents")))

    if args.command == "check":
        home = default_home
        return run_check(repo_home, home, args.json)

    if args.command == "wizard":
        home = args.home or default_home
        shell_rc = expand(args.shell_rc) if args.shell_rc else None
        return run_wizard(repo_home, home, dry_run=args.dry_run, shell_rc=shell_rc)

    home = default_home
    tool_ids = parse_tool_ids(args.tools)
    return run_install(repo_home, home, dry_run=args.dry_run, tool_ids=tool_ids)


if __name__ == "__main__":
    raise SystemExit(main())
