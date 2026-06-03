#!/usr/bin/env python3
"""Remove shared-agents adapter configuration from installed AI tools."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sa_ui import bullet_ok, heading, plain, print_dry_run_line, run_cli_main, say_warn

MARKER_BEGIN = "<!-- shared-agents:begin -->"
MARKER_END = "<!-- shared-agents:end -->"


def expand(path: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(path)))


def load_manifest(repo_home: Path) -> dict:
    return json.loads((repo_home / "adapters" / "manifest.json").read_text())


def installable_tools(manifest: dict) -> list[dict]:
    return [t for t in manifest.get("tools", []) if t["id"] not in ("generic", "openclaw")]


def tool_is_installed(tool: dict) -> bool:
    from shutil import which

    detect_bins = list(tool.get("detect_bins") or [])
    if any(which(b) for b in detect_bins):
        return True
    detect_path = tool.get("detect")
    return bool(detect_path and expand(detect_path).exists())


def unmerge_agents_md(target: Path, dry_run: bool) -> str | None:
    if not target.is_file():
        return None
    text = target.read_text()
    if MARKER_BEGIN not in text or MARKER_END not in text:
        return None
    start = text.index(MARKER_BEGIN)
    end = text.index(MARKER_END) + len(MARKER_END)
    updated = (text[:start].rstrip() + "\n" + text[end:].lstrip()).strip()
    if dry_run:
        return f"[dry-run] would remove marker block from {target}"
    if updated:
        target.write_text(updated + "\n")
    else:
        target.unlink(missing_ok=True)
    return f"Removed marker block from {target}"


def uninstall_rules(repo_home: Path, rule_dirs: list[dict], dry_run: bool) -> list[str]:
    from rules_install import uninstall_rule_symlinks

    return uninstall_rule_symlinks(repo_home, rule_dirs, dry_run=dry_run)


def _skill_source_roots(repo_home: Path) -> list[Path]:
    """Core skills + team skills (same sources as install-adapters symlink_skills)."""
    roots: list[Path] = []
    core = repo_home / "skills"
    if core.is_dir():
        roots.append(core.resolve())
    team = repo_home / "team" / "skills"
    if team.is_dir():
        roots.append(team.resolve())
    return roots


def _symlink_points_to_shared_agents(dest: Path, source_roots: list[Path]) -> bool:
    if not dest.is_symlink():
        return False
    try:
        target = dest.resolve()
    except OSError:
        return False
    for root in source_roots:
        if target == root or root in target.parents:
            return True
    return False


def uninstall_skills(repo_home: Path, skill_dirs: list[dict], dry_run: bool) -> list[str]:
    messages: list[str] = []
    source_roots = _skill_source_roots(repo_home)
    if not source_roots:
        return messages

    seen_dest: set[Path] = set()
    for entry in skill_dirs:
        dest_root = expand(entry["path"])
        if not dest_root.is_dir():
            continue
        for dest in sorted(dest_root.iterdir()):
            if dest in seen_dest:
                continue
            if not _symlink_points_to_shared_agents(dest, source_roots):
                continue
            seen_dest.add(dest)
            if dry_run:
                messages.append(f"[dry-run] would remove skill symlink {dest}")
            else:
                dest.unlink()
                messages.append(f"Removed skill symlink {dest}")
    return messages


def uninstall_cursor(repo_home: Path, tool: dict, dry_run: bool) -> list[str]:
    messages: list[str] = []
    sync = tool["sync"]
    hook_path = expand(sync["script_dest"])
    hooks_path = expand(sync["hooks_json"])

    if hook_path.is_file():
        if dry_run:
            messages.append(f"[dry-run] would remove {hook_path}")
        else:
            hook_path.unlink()
            messages.append(f"Removed {hook_path}")

    if not hooks_path.is_file():
        return messages

    data = json.loads(hooks_path.read_text())
    hooks = data.get("hooks", {})
    hook_cmd = sync["hook_command"]
    session = hooks.get("sessionStart", [])
    new_session = [h for h in session if h.get("command") != hook_cmd]
    if len(new_session) != len(session):
        hooks["sessionStart"] = new_session
        if dry_run:
            messages.append(f"[dry-run] would remove sessionStart hook from {hooks_path}")
        else:
            messages.append(f"Removed sessionStart hook from {hooks_path}")

    stop = hooks.get("stop", [])
    new_stop = [
        h
        for h in stop
        if not (
            h.get("type") == "prompt"
            and "Team-Learning" in h.get("prompt", "")
            and "shared-agents" in h.get("prompt", "").lower()
        )
    ]
    if len(new_stop) != len(stop):
        hooks["stop"] = new_stop
        if dry_run:
            messages.append(f"[dry-run] would remove stop hook from {hooks_path}")
        else:
            messages.append(f"Removed stop hook from {hooks_path}")

    if not dry_run:
        hooks_path.write_text(json.dumps(data, indent=2) + "\n")
    return messages


def claude_session_hook_command(entry: object) -> str | None:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        for hook in entry.get("hooks", []):
            if hook.get("type") == "command" and hook.get("command"):
                return hook["command"]
    return None


def uninstall_claude(home: str, tool: dict, dry_run: bool) -> list[str]:
    messages: list[str] = []
    sync = tool["sync"]
    settings_path = expand(sync["settings_json"])
    if not settings_path.is_file():
        return messages
    hook_cmd = sync["hook_command"].replace("$SHARED_AGENTS_HOME", home)
    data = json.loads(settings_path.read_text())
    session = data.get("hooks", {}).get("SessionStart", [])
    new_session = [e for e in session if claude_session_hook_command(e) != hook_cmd]
    if len(new_session) == len(session):
        return messages
    data.setdefault("hooks", {})["SessionStart"] = new_session
    if dry_run:
        messages.append(f"[dry-run] would remove SessionStart hook from {settings_path}")
    else:
        settings_path.write_text(json.dumps(data, indent=2) + "\n")
        messages.append(f"Removed SessionStart hook from {settings_path}")
    return messages


def uninstall_agents_md_tool(repo_home: Path, tool: dict, dry_run: bool) -> list[str]:
    from rules_install import agents_md_paths, uninstall_team_rules_from_tool

    messages: list[str] = []
    home = str(repo_home)
    seen: set[Path] = set()
    for path in agents_md_paths(tool, home):
        if path in seen:
            continue
        seen.add(path)
        msg = unmerge_agents_md(path, dry_run)
        if msg:
            messages.append(msg)
    messages.extend(uninstall_team_rules_from_tool(tool, repo_home, dry_run=dry_run))
    return messages


def uninstall_tool(repo_home: Path, home: str, tool: dict, dry_run: bool) -> list[str]:
    tid = tool["id"]
    if tid == "cursor":
        return uninstall_cursor(repo_home, tool, dry_run)
    if tid == "claude-code":
        messages = uninstall_claude(home, tool, dry_run)
        if tool.get("agents_md") or tool.get("alt_agents_md") or tool.get("alt_rules"):
            messages.extend(uninstall_agents_md_tool(repo_home, tool, dry_run))
        return messages
    if tool.get("agents_md") or tool.get("alt_agents_md") or tool.get("alt_rules"):
        return uninstall_agents_md_tool(repo_home, tool, dry_run)
    return []


def run_uninstall(repo_home: Path, home: str, dry_run: bool) -> int:
    manifest = load_manifest(repo_home)
    messages: list[str] = []
    messages.extend(
        uninstall_skills(repo_home, manifest["shared"]["skill_dirs"], dry_run=dry_run)
    )
    messages.extend(
        uninstall_rules(repo_home, manifest["shared"].get("rule_dirs", []), dry_run=dry_run)
    )
    for tool in installable_tools(manifest):
        if not tool_is_installed(tool):
            continue
        messages.extend(uninstall_tool(repo_home, home, tool, dry_run))

    generic = repo_home / "adapters" / "generic" / "instructions.md"
    if generic.is_file():
        if dry_run:
            messages.append(f"[dry-run] would remove {generic}")
        else:
            generic.unlink()
            messages.append(f"Removed {generic}")

    if not messages:
        say_warn("Nothing to remove (no configured tools detected).")
        return 0

    print(heading("Removed / would remove:"))
    for msg in messages:
        if msg.startswith("[dry-run]"):
            print_dry_run_line(msg, symbol="○")
        else:
            bullet_ok(msg)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Uninstall shared-agents tool adapters.")
    parser.add_argument("repo_home", type=Path, nargs="?", help="SHARED_AGENTS_HOME")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    home = Path(
        args.repo_home
        or os.environ.get("SHARED_AGENTS_HOME", Path.home() / ".shared-agents")
    )
    if not home.is_dir():
        raise SystemExit(f"Not found: {home}")
    return run_uninstall(home, str(home), args.dry_run)


if __name__ == "__main__":
    run_cli_main(main)
