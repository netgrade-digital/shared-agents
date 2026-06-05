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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sa_config import default_shell_rc  # noqa: E402
from sa_ui import (
    TAGLINE,
    bold,
    cyan,
    green,
    is_tty as ui_is_tty,
    plain,
    print_banner as ui_print_banner,
    highlight_paths,
    print_dry_run_line,
    prompt_line,
    prompt_yes_no,
    red,
    run_cli_main,
    yellow,
)

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
    from sa_config import index_path, learnings_root, pending_dir

    extra = f"\n{tool_note.strip()}" if tool_note.strip() else ""
    root = expand(home)
    lr = learnings_root(root)
    pending = pending_dir(root)
    index = index_path(root)
    return f"""{MARKER_BEGIN}
## Team Knowledge (shared-agents)

Repo: {home}

MANDATORY — first action every new session/thread, without asking:
  {home}/scripts/sync.sh pull

Before non-trivial work: search {lr}/approved/ and {index.name} ({index.parent}/).
Use skill `shared-agents-knowledge` for the full workflow.
After reusable insights: write to {pending}/ only (skill `capture-learning`) — absolute path under SHARED_AGENTS_HOME, never the Cursor workspace. See {home}/docs/canonical-paths.md.
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
    rules_block = tool.get("rules") or {}
    if rules_block.get("dest"):
        paths.append(expand(rules_block["dest"]))
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


def check_cursor_configured(tool: dict, repo_home: Path) -> tuple[bool, str]:
    from rules_install import check_rules
    sync = tool["sync"]
    hook = expand(sync["script_dest"])
    hooks_json = expand(sync["hooks_json"])
    hook_ok = hook.is_file() and os.access(hook, os.X_OK)
    json_ok = False
    if hooks_json.is_file():
        data = json.loads(hooks_json.read_text())
        session = data.get("hooks", {}).get("sessionStart", [])
        json_ok = any(h.get("command") == sync["hook_command"] for h in session)

    rule_ok = True
    rule_parts: list[str] = []
    rule_issues = check_rules(repo_home, {"shared": {"rule_dirs": [{"path": "~/.cursor/rules"}]}})
    blocking = [i for i in rule_issues if "regular file" not in i]
    if blocking:
        rule_ok = False
        rule_parts.append("rule symlinks missing or stale")

    ok = hook_ok and json_ok and rule_ok
    parts = []
    if not hook_ok:
        parts.append("hook script missing")
    if not json_ok:
        parts.append("sessionStart hook not registered")
    if not rule_ok:
        parts.extend(rule_parts)
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


def check_tool(tool: dict, home: str, repo_home: Path | None = None) -> ToolReport:
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
        root = repo_home or expand(home)
        configured, msg = check_cursor_configured(tool, root)
    elif tid == "claude-code":
        configured, msg = check_claude_configured(tool, home)
        if configured and (tool.get("agents_md") or tool.get("alt_agents_md")):
            md_ok, md_msg = check_agents_md_configured(tool, home)
            if not md_ok:
                configured, msg = md_ok, md_msg
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


def _skill_source_dirs(repo_home: Path) -> list[Path]:
    from sa_config import skills_dirs

    return skills_dirs(repo_home) or [repo_home / "skills"]


def check_skills(repo_home: Path, manifest: dict) -> list[str]:
    issues = []
    sources = _skill_source_dirs(repo_home)
    skills: list[Path] = []
    for src in sources:
        skills.extend(sorted(p for p in src.glob("*/") if p.is_dir()))
    if not skills:
        issues.append("No skills/ in core or team/")
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
    from rules_install import check_rules

    repo_ok, repo_msg = check_repo(home)
    manifest = load_manifest(repo_home) if repo_ok else {"tools": [], "shared": {"skill_dirs": [], "rule_dirs": []}}
    reports = [check_tool(t, home, repo_home) for t in manifest.get("tools", [])]
    skill_issues = check_skills(repo_home, manifest) if repo_ok else []
    rule_issues = check_rules(repo_home, manifest) if repo_ok else []
    from sa_config import check_team_setup

    team_issues = check_team_setup(expand(home)) if repo_ok else []

    if as_json:
        payload = {
            "version": VERSION,
            "shared_agents_home": home,
            "repo_ok": repo_ok,
            "repo_message": repo_msg,
            "skill_issues": skill_issues,
            "rule_issues": rule_issues,
            "team_issues": team_issues,
            "tools": [asdict(r) for r in reports],
        }
        print(json.dumps(payload, indent=2))
        return 0 if repo_ok else 1

    print(f"{bold('shared-agents check')} {green(f'v{VERSION}')}")
    print(f"{plain('SHARED_AGENTS_HOME=')}{cyan(home)}")
    repo_label = green("OK") if repo_ok else red("MISSING")
    print(f"Repo: {repo_label} — {plain(repo_msg)}\n")

    col_id = 14
    print(bold(f"{'TOOL':<{col_id}} {'INSTALLED':<10} {'CONFIGURED':<12} STATUS"))
    print("-" * 60)
    for r in reports:
        inst = green("yes") if r.installed else plain("no")
        conf = green("yes") if r.configured else plain("no")
        print(f"{r.id:<{col_id}} {inst:<10} {conf:<12} {_status_colored(r.status.value)}")
    print()

    for r in reports:
        if r.status == Status.OK or r.status == Status.AVAILABLE:
            continue
        hint = r.detect_path or (", ".join(r.detect_bins) if r.detect_bins else "—")
        print(f"  [{cyan(r.id)}] {plain(r.message)}")
        if hint:
            print(f"         {plain('detect:')} {cyan(hint)}")
        if r.docs:
            print(f"         {plain('docs:')}   {cyan(r.docs)}")

    if skill_issues:
        print(bold("\nSkill links:"))
        for issue in skill_issues:
            print(f"  {yellow('!')} {plain(issue)}")

    if rule_issues:
        print(bold("\nRule links:"))
        for issue in rule_issues:
            print(f"  {yellow('!')} {plain(issue)}")

    if team_issues:
        print(bold("\nTeam data:"))
        for issue in team_issues:
            print(f"  {yellow('!')} {plain(issue)}")
        print(plain("  → sa team verify · sa team migrate · docs/migration-team-data.md"))

    needs_install = any(r.installed and not r.configured for r in reports)
    missing = sum(1 for r in reports if r.status == Status.MISSING_TOOL)
    if needs_install:
        print(f"\n{plain('→ Run:')} {green(f'{home}/install.sh')}")
    if missing:
        print(plain(f"→ {missing} tool(s) not installed on this machine (expected if unused)"))

    return 0 if repo_ok else 1


def _status_colored(value: str) -> str:
    if value == "ok":
        return green(value)
    if value in {"not_configured", "partial"}:
        return yellow(value)
    if value == "missing_tool":
        return red(value)
    return plain(value)


def _print_action(msg: str) -> None:
    if msg.startswith("[dry-run]"):
        print_dry_run_line(msg, symbol="✓")
    else:
        print(f"  {green('✓')} {highlight_paths(msg)}")


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
    seen: set[str] = set()
    skill_pairs: list[tuple[Path, str]] = []
    for src in _skill_source_dirs(repo_home):
        for skill in sorted(p for p in src.glob("*/") if p.is_dir()):
            if skill.name in seen:
                continue
            seen.add(skill.name)
            skill_pairs.append((skill, src.name))

    for entry in skill_dirs:
        dest_root = expand(entry["path"])
        if not dry_run:
            dest_root.mkdir(parents=True, exist_ok=True)
        for skill, src_label in skill_pairs:
            dest = dest_root / skill.name
            if dry_run:
                messages.append(f"[dry-run] would link {skill.name} ({src_label}) → {dest_root}")
                continue
            if dest.is_symlink():
                dest.unlink()
            elif dest.exists() and not dest.is_symlink():
                continue
            dest.symlink_to(skill.resolve())
        if not dry_run and skill_pairs:
            note = entry.get("note", "")
            messages.append(f"Skills → {dest_root}" + (f" ({note})" if note else ""))
    return messages


def install_cursor(repo_home: Path, tool: dict, dry_run: bool) -> list[str]:
    if dry_run:
        return ["[dry-run] would configure Cursor (sessionStart hook)"]
    sync = tool["sync"]
    dest_hook = expand(sync["script_dest"])
    dest_hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo_home / sync["script_src"], dest_hook)
    dest_hook.chmod(0o755)
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
        "If they agree, use capture-learning and sa pending path — write only under "
        "$SHARED_AGENTS_HOME/team/learnings/pending/. "
        "If they decline or the task was trivial (typo, formatting, pure Q&A), do nothing."
    )
    stop = data["hooks"].setdefault("stop", [])
    if not any(h.get("type") == "prompt" and "Team-Learning" in h.get("prompt", "") for h in stop):
        stop.insert(0, {"type": "prompt", "prompt": stop_prompt, "loop_limit": 1})
    hooks_path.parent.mkdir(parents=True, exist_ok=True)
    hooks_path.write_text(json.dumps(data, indent=2) + "\n")
    return [
        f"Cursor: sessionStart hook ({dest_hook})",
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


def install_agents_md_tool(
    repo_home: Path, home: str, tool: dict, dry_run: bool
) -> list[str]:
    from rules_install import agents_md_paths, install_team_rules_to_path

    block = agents_block(home, tool.get("note", ""))
    paths = agents_md_paths(tool, home)
    messages = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        if dry_run:
            messages.append(f"[dry-run] would merge block into {path}")
            extra = install_team_rules_to_path(
                path, repo_home, tool["id"], dry_run=True
            )
            if extra:
                messages.append(extra)
        else:
            merge_agents_md(path, block)
            messages.append(f"{tool['name']}: merged block into {path}")
            extra = install_team_rules_to_path(
                path, repo_home, tool["id"], dry_run=False
            )
            if extra:
                messages.append(f"{tool['name']}: {extra}")
    return messages


def install_tool(repo_home: Path, home: str, tool: dict, dry_run: bool) -> list[str]:
    tid = tool["id"]
    if tid == "cursor":
        return install_cursor(repo_home, tool, dry_run)
    if tid == "claude-code":
        messages = install_claude(home, tool, dry_run)
        if tool.get("agents_md") or tool.get("alt_agents_md") or tool.get("alt_rules"):
            messages.extend(install_agents_md_tool(repo_home, home, tool, dry_run))
        return messages
    if tool.get("agents_md") or tool.get("alt_agents_md") or tool.get("alt_rules"):
        return install_agents_md_tool(repo_home, home, tool, dry_run)
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
    from rules_install import symlink_rules

    os.environ["SHARED_AGENTS_HOME"] = home
    manifest = load_manifest(repo_home)
    print(f"{bold('Installing adapters')} {green(f'v{VERSION}')} ({cyan(home)})")
    if dry_run:
        print(yellow("DRY RUN — no files will be modified\n"))

    messages = symlink_skills(repo_home, manifest["shared"]["skill_dirs"], dry_run=dry_run)
    messages.extend(
        symlink_rules(repo_home, manifest["shared"].get("rule_dirs", []), dry_run=dry_run)
    )
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

    print(bold("Actions:"))
    for msg in messages:
        _print_action(msg)
    if configured:
        print(bold("\nConfigured:"))
        for name in configured:
            print(f"  {green('•')} {plain(name)}")
    if missing:
        print(bold("\nNot installed (selected but missing on this machine):"))
        for name in missing:
            print(f"  {red('✗')} {plain(name)}")
    if skipped:
        print(bold("\nSkipped (tool not detected):"))
        for name in skipped:
            print(f"  {yellow('○')} {plain(name)}")

    print(f"\n{plain('Verify:')} {green('./install.sh --check')}")
    return 0


def run_sync_links(
    repo_home: Path,
    home: str,
    *,
    quiet: bool = False,
    dry_run: bool = False,
) -> int:
    """After sa sync pull: refresh skill symlinks, rule symlinks, and AGENTS.md team-rules blocks."""
    from rules_install import agents_md_paths, install_team_rules_to_path, symlink_rules

    os.environ["SHARED_AGENTS_HOME"] = home
    if not (repo_home / "adapters" / "manifest.json").is_file():
        return 0

    manifest = load_manifest(repo_home)
    messages: list[str] = []
    messages.extend(
        symlink_skills(repo_home, manifest["shared"]["skill_dirs"], dry_run=dry_run)
    )
    messages.extend(
        symlink_rules(repo_home, manifest["shared"].get("rule_dirs", []), dry_run=dry_run)
    )

    seen_paths: set[Path] = set()
    for tool in installable_tools(manifest):
        installed, _, _ = tool_is_installed(tool)
        if not installed:
            continue
        if tool["id"] == "cursor":
            continue
        if not (tool.get("agents_md") or tool.get("alt_agents_md") or tool.get("alt_rules")):
            continue
        for path in agents_md_paths(tool, home):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            extra = install_team_rules_to_path(
                path, repo_home, tool["id"], dry_run=dry_run
            )
            if extra:
                messages.append(f"{tool['name']}: {extra}")

    if not messages:
        return 0

    if quiet and not dry_run:
        return 0

    if dry_run:
        print(bold("Sync links (dry run):"))
    elif not quiet:
        print(bold("Skills + rules:"))

    for msg in messages:
        _print_action(msg)
    return 0


# --- wizard ---


def is_tty() -> bool:
    return ui_is_tty()


def stdin_interactive() -> bool:
    """True when prompts can read from the user (not curl | bash)."""
    return sys.stdin.isatty()


def prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            answer = prompt_line(f"{text}{suffix}: ").strip()
        except EOFError:
            print()
            raise SystemExit(130)
        if answer:
            return answer
        if default is not None:
            return default
        print("Please enter a value.")


def confirm(text: str, default: bool = True) -> bool:
    return prompt_yes_no(text, default=default)


def print_banner() -> None:
    ui_print_banner(subtitle=f"Setup Wizard — {TAGLINE}")


def tool_status_label(report: ToolReport) -> str:
    if report.status == Status.OK:
        return green("configured")
    if report.installed:
        return yellow("needs setup")
    return plain("not installed")


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


def default_detected_tool_ids(reports: list[tuple[dict, ToolReport]]) -> set[str]:
    return {tool["id"] for tool, report in reports if report.installed}


def wizard_select_tools(reports: list[tuple[dict, ToolReport]]) -> set[str]:
    selected = default_detected_tool_ids(reports)
    if not reports:
        return set()

    if not stdin_interactive():
        print(
            plain(
                f"  Non-interactive stdin: configuring {len(selected)} detected tool(s) "
                "(run ./scripts/bootstrap.sh or sa bootstrap in a terminal for the full wizard)."
            )
        )
        for tool, report in reports:
            if tool["id"] in selected:
                print(f"    • {tool['name']} ({tool_status_plain(report)})")
        print()
        return selected

    while True:
        print(bold("Select AI tools"))
        print(plain("  Toggle with number · all · detected · none · Enter to continue"))
        print()
        for idx, (tool, report) in enumerate(reports, start=1):
            mark = "x" if tool["id"] in selected else " "
            status = tool_status_label(report)
            name = tool["name"]
            print(f"  [{idx}] [{mark}] {name:<24} {status}")
        print()
        choice = prompt_line("> ").strip().lower()
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


def prompt_team_remote() -> str | None:
    print(bold("Step 2/5 — Team data (private repo)"))
    print(plain("  Separate git repo for learnings + team skills."))
    print(plain("  Leave empty for solo (learnings only under core/)."))
    if not stdin_interactive():
        return None
    url = prompt("  Team remote URL (or empty)", "")
    url = url.strip()
    return url or None


def run_wizard_plain(
    repo_home: Path,
    home: str,
    reports: list[tuple[dict, ToolReport]],
    *,
    dry_run: bool,
    shell_rc: Path | None,
    ask_team: bool = True,
    bootstrap: bool = False,
) -> tuple[str, str | None, set[str], bool, bool] | None:
    """Returns (home, team_remote, selected, add_shell, run_setup) or None if cancelled."""
    subtitle = "Bootstrap Wizard" if bootstrap else f"Setup Wizard — {TAGLINE}"
    ui_print_banner(subtitle=subtitle)

    print(bold("Step 1/5 — Install location"))
    print(f"  Repo:  {repo_home}")
    default_home = home
    if stdin_interactive():
        home_input = prompt("  SHARED_AGENTS_HOME", default_home)
        home = os.path.expanduser(os.path.expandvars(home_input))
    else:
        home = default_home
    print()

    team_remote: str | None = None
    if ask_team:
        team_remote = prompt_team_remote()
        print()

    print(bold("Step 3/5 — Select AI tools"))
    selected = wizard_select_tools(reports)
    print()
    if not selected:
        print("No tools selected — skills will still be linked.")
    print()

    print(bold(cyan("Step 4/5 — Shell environment")))
    add_shell = True
    shell_rc_path = shell_rc or default_shell_rc()
    rc_text = shell_rc_path.read_text() if shell_rc_path.is_file() else ""
    has_home = "SHARED_AGENTS_HOME=" in rc_text
    has_cli = "shell-aliases.sh" in rc_text
    if has_home and has_cli:
        print(f"  ✓ {shell_rc_path} already configured (SHARED_AGENTS_HOME + CLI)")
        add_shell = False
    elif has_home and not has_cli:
        print(f"  → {shell_rc_path} has SHARED_AGENTS_HOME — will add CLI (sa)")
        add_shell = True
    elif stdin_interactive():
        add_shell = confirm(
            f"  Add SHARED_AGENTS_HOME + sa CLI to {shell_rc_path}?",
            True,
        )
    print()

    print(bold("Step 5/5 — Summary"))
    print(f"  Install path: {home}")
    if team_remote:
        print(f"  Team data:    {team_remote}")
    else:
        print("  Team data:    solo (core learnings only)")
    print(f"  Skills:       link core + team skills")
    if selected:
        print("  Configure:")
        for tool, report in reports:
            if tool["id"] in selected:
                print(f"    • {tool['name']} ({tool_status_label(report)})")
    else:
        print("  Configure:    (none)")
    print()
    if not stdin_interactive():
        print(plain("  Non-interactive stdin: running setup."))
        return home, team_remote, selected, add_shell, True
    if not confirm("Run setup now?", False):
        return None
    return home, team_remote, selected, add_shell, True


@dataclass
class SavedWizardChoices:
    home: str
    selected_tools: list[str]
    add_shell: bool
    team_remote: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "home": self.home,
                "team_remote": self.team_remote,
                "selected_tools": sorted(self.selected_tools),
                "add_shell": self.add_shell,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, text: str) -> SavedWizardChoices:
        data = json.loads(text)
        tr = data.get("team_remote")
        return cls(
            home=data["home"],
            selected_tools=list(data.get("selected_tools", [])),
            add_shell=bool(data.get("add_shell", True)),
            team_remote=tr if tr else None,
        )


def resolve_manifest_repo(repo_home: Path, home: str) -> Path:
    if (repo_home / "adapters" / "manifest.json").is_file():
        return repo_home
    alt = expand(home)
    if (alt / "adapters" / "manifest.json").is_file():
        return alt
    raise FileNotFoundError("manifest.json not found in repo_home or SHARED_AGENTS_HOME")


def gather_wizard_choices(
    repo_home: Path,
    home: str,
    *,
    shell_rc: Path | None,
    ask_team: bool = False,
    bootstrap: bool = False,
) -> SavedWizardChoices | None:
    from sa_config import config_path

    if not ask_team and not bootstrap:
        ask_team = not config_path(expand(home)).is_file()

    repo_ok, repo_msg = check_repo(str(repo_home))
    if not repo_ok:
        repo_ok, repo_msg = check_repo(home)
    if not repo_ok:
        print(f"Repo error: {repo_msg}", file=sys.stderr)
        return None

    manifest_repo = resolve_manifest_repo(repo_home, home)
    manifest = load_manifest(manifest_repo)
    reports = [
        (tool, check_tool(tool, home, manifest_repo))
        for tool in installable_tools(manifest)
    ]

    shell_rc_path = shell_rc or default_shell_rc()
    shell_rc_str = str(shell_rc_path)

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
        try:
            result = run_wizard_tui(
                default_home=home,
                rows=tool_rows,
                shell_rc=shell_rc_str,
                shell_state=shell_state,
                bootstrap=bootstrap,
                ask_team=ask_team,
            )
        except WizardTuiFailed as exc:
            print(f"  → {exc} — using text prompts.", file=sys.stderr)
            result = None
            wizard_result = run_wizard_plain(
                repo_home,
                home,
                reports,
                dry_run=False,
                shell_rc=shell_rc_path,
                ask_team=ask_team,
                bootstrap=bootstrap,
            )
            if wizard_result is None:
                return None
            ph, team_remote, selected, add_shell, _ = wizard_result
            return SavedWizardChoices(ph, sorted(selected), add_shell, team_remote)

        if result is None or not result.run_setup:
            return None
        return SavedWizardChoices(
            result.home,
            sorted(result.selected_tools),
            result.add_shell,
            result.team_remote,
        )

    wizard_result = run_wizard_plain(
        repo_home,
        home,
        reports,
        dry_run=False,
        shell_rc=shell_rc_path,
        ask_team=ask_team,
        bootstrap=bootstrap,
    )
    if wizard_result is None:
        return None
    ph, team_remote, selected, add_shell, _ = wizard_result
    return SavedWizardChoices(ph, sorted(selected), add_shell, team_remote)


def apply_wizard_choices(
    repo_home: Path,
    choices: SavedWizardChoices,
    *,
    dry_run: bool,
    shell_rc: Path | None,
    skip_team_setup: bool = False,
) -> int:
    home = os.path.expanduser(os.path.expandvars(choices.home))
    os.environ["SHARED_AGENTS_HOME"] = home
    shell_rc_path = shell_rc or default_shell_rc()
    selected = set(choices.selected_tools)

    if not skip_team_setup and not dry_run:
        from sa_config import write_config
        from team_data import resolve_team_remote, setup_team

        team_url = resolve_team_remote(expand(home), choices.team_remote)
        write_config(expand(home), team_remote_url=team_url)
        if team_url:
            try:
                msg = setup_team(expand(home), team_url, dry_run=False)
                print(f"  {green('✓')} {highlight_paths(msg)}")
            except RuntimeError as exc:
                print(f"  ! {exc}", file=sys.stderr)
                return 1

    if choices.add_shell:
        if not configure_shell_rc(shell_rc_path, home, dry_run, repo_home=repo_home):
            print("Warning: shell CLI was not configured.", file=sys.stderr)
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


def run_wizard(
    repo_home: Path,
    home: str,
    *,
    dry_run: bool = False,
    shell_rc: Path | None = None,
    collect_only: bool = False,
    apply_only: bool = False,
    choices_file: Path | None = None,
) -> int:
    if collect_only and apply_only:
        print("Use either --collect-only or --apply-only, not both.", file=sys.stderr)
        return 1

    if collect_only:
        if choices_file is None:
            print("--choices-file required with --collect-only", file=sys.stderr)
            return 1
        choices = gather_wizard_choices(repo_home, home, shell_rc=shell_rc)
        if choices is None:
            return 1
        choices_file.write_text(choices.to_json() + "\n")
        return 0

    if apply_only:
        if choices_file is None or not choices_file.is_file():
            print("--choices-file required with --apply-only", file=sys.stderr)
            return 1
        choices = SavedWizardChoices.from_json(choices_file.read_text())
        return apply_wizard_choices(
            repo_home,
            choices,
            dry_run=dry_run,
            shell_rc=shell_rc,
        )

    choices = gather_wizard_choices(repo_home, home, shell_rc=shell_rc)
    if choices is None:
        return 1
    return apply_wizard_choices(
        repo_home,
        choices,
        dry_run=dry_run,
        shell_rc=shell_rc,
    )


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
    p_wizard.add_argument(
        "--collect-only",
        action="store_true",
        help="Wizard UI only — write choices JSON (no clone/install)",
    )
    p_wizard.add_argument(
        "--apply-only",
        action="store_true",
        help="Apply choices JSON after clone",
    )
    p_wizard.add_argument(
        "--choices-file",
        type=Path,
        default=None,
        help="JSON file for --collect-only / --apply-only",
    )

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

    p_sync_links = sub.add_parser(
        "sync-links",
        help="Refresh skill/rule symlinks after sa sync (no full adapter install)",
    )
    p_sync_links.add_argument("repo_home", type=Path, help="Path to shared-agents repo")
    p_sync_links.add_argument("--quiet", action="store_true", help="No output when successful")
    p_sync_links.add_argument("--dry-run", action="store_true", help="Preview only")

    args = parser.parse_args()
    repo_home = args.repo_home.resolve()
    default_home = os.environ.get("SHARED_AGENTS_HOME", str(expand("~/.shared-agents")))

    if args.command == "check":
        home = default_home
        return run_check(repo_home, home, args.json)

    if args.command == "sync-links":
        home = default_home
        return run_sync_links(
            repo_home,
            home,
            quiet=args.quiet,
            dry_run=args.dry_run,
        )

    if args.command == "wizard":
        home = args.home or default_home
        shell_rc = expand(args.shell_rc) if args.shell_rc else None
        return run_wizard(
            repo_home,
            home,
            dry_run=args.dry_run,
            shell_rc=shell_rc,
            collect_only=args.collect_only,
            apply_only=args.apply_only,
            choices_file=args.choices_file,
        )

    home = default_home
    tool_ids = parse_tool_ids(args.tools)
    return run_install(repo_home, home, dry_run=args.dry_run, tool_ids=tool_ids)


if __name__ == "__main__":
    run_cli_main(main)
