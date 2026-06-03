#!/usr/bin/env python3
"""Inbox-style reminders: pending learnings, skill symlinks, adapter gaps."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sa_ui import bold, cyan, green, magenta, plain, print_logo, run_cli_main, yellow


@dataclass
class StatusReport:
    shared_agents_home: str
    pending_learnings: list[str] = field(default_factory=list)
    pending_unpublished: list[str] = field(default_factory=list)
    skill_issues: list[str] = field(default_factory=list)
    rule_issues: list[str] = field(default_factory=list)
    team_issues: list[str] = field(default_factory=list)
    tools_need_install: list[str] = field(default_factory=list)

    @property
    def has_action(self) -> bool:
        return bool(
            self.pending_learnings
            or self.pending_unpublished
            or self.skill_issues
            or self.rule_issues
            or self.team_issues
            or self.tools_need_install
        )


def shared_home() -> Path:
    from sa_config import core_home

    return core_home()


def pending_files(home: Path) -> list[str]:
    from sa_config import pending_dir

    pending = pending_dir(home)
    if not pending.is_dir():
        return []
    return sorted(p.name for p in pending.glob("*.md") if p.is_file())


def pending_unpublished(home: Path) -> list[str]:
    from sa_config import git_data_home, learnings_prefix_for_git

    repo = git_data_home(home)
    prefix = learnings_prefix_for_git(home)
    if not (repo / ".git").is_dir():
        return []
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", f"{prefix}/pending/"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    names: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        part = line[3:].strip() if len(line) > 3 else line
        if part.endswith(".md"):
            names.append(Path(part).name)
    return sorted(set(names))


def load_check(home: Path) -> tuple[list[str], list[str], list[str]]:
    script = home / "scripts" / "install-adapters.py"
    if not script.is_file():
        return [], [], []
    env = {**os.environ, "SHARED_AGENTS_HOME": str(home)}
    result = subprocess.run(
        [sys.executable, str(script), "check", str(home), "--json"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if result.returncode != 0 and not result.stdout.strip():
        return [], [], []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return [], [], []
    skill_issues = list(payload.get("skill_issues") or [])
    rule_issues = list(payload.get("rule_issues") or [])
    tools: list[str] = []
    for tool in payload.get("tools") or []:
        if tool.get("installed") and tool.get("status") == "not_configured":
            tools.append(f"{tool.get('id', '?')}: {tool.get('message', 'not configured')}")
    return skill_issues, rule_issues, tools


def collect(home: Path) -> StatusReport:
    from sa_config import check_team_setup

    pending = pending_files(home)
    unpublished = pending_unpublished(home)
    skill_issues, rule_issues, tools = load_check(home)
    team_issues = check_team_setup(home)
    return StatusReport(
        shared_agents_home=str(home),
        pending_learnings=pending,
        pending_unpublished=unpublished,
        skill_issues=skill_issues,
        rule_issues=rule_issues,
        team_issues=team_issues,
        tools_need_install=tools,
    )


def format_human(report: StatusReport) -> str:
    lines: list[str] = []
    if not report.has_action:
        return green("shared-agents: all clear ✓")

    lines.append(bold(cyan("shared-agents — open items")))
    lines.append("")

    if report.pending_learnings:
        lines.append(magenta(f"Learnings to review ({len(report.pending_learnings)}):"))
        for name in report.pending_learnings:
            suffix = plain(" (not pushed yet)") if name in report.pending_unpublished else ""
            lines.append(f"  • {yellow(name)}{suffix}")
        lines.append(plain("  → sa review list · sa review <file>"))
        lines.append("")

    if report.pending_unpublished:
        only_unpub = [
            n for n in report.pending_unpublished if n not in report.pending_learnings
        ]
        if only_unpub:
            lines.append(magenta("Pending not on remote yet:"))
            for name in only_unpub:
                lines.append(f"  • {yellow(name)}")
            lines.append(plain("  → sa pending push <file>"))
            lines.append("")

    if report.team_issues:
        lines.append(magenta(f"Team data ({len(report.team_issues)}):"))
        for issue in report.team_issues:
            lines.append(f"  • {yellow(issue)}")
        lines.append(
            plain("  → sa team verify · sa team migrate · sa bootstrap · docs/migration-team-data.md")
        )
        lines.append("")

    if report.skill_issues:
        lines.append(magenta(f"Skills / Symlinks ({len(report.skill_issues)}):"))
        for issue in report.skill_issues:
            lines.append(f"  • {issue}")
        lines.append(plain("  → sa doctor --fix  (or sa sync for missing links only)"))
        lines.append("")

    if report.rule_issues:
        lines.append(magenta(f"Rules / Symlinks ({len(report.rule_issues)}):"))
        for issue in report.rule_issues:
            lines.append(f"  • {issue}")
        lines.append(plain("  → sa doctor --fix  (backup + symlink for local rule files)"))
        lines.append("")

    if report.tools_need_install:
        lines.append(magenta(f"Adapter ({len(report.tools_need_install)}):"))
        for item in report.tools_need_install:
            lines.append(f"  • {item}")
        lines.append(plain("  → sa install"))
        lines.append("")

    return "\n".join(lines).rstrip()


def format_brief(report: StatusReport) -> str:
    if not report.has_action:
        return green("shared-agents: all clear")
    parts: list[str] = []
    if report.pending_learnings:
        parts.append(
            f"{len(report.pending_learnings)} learning(s) to review"
        )
    if report.pending_unpublished:
        parts.append(f"{len(report.pending_unpublished)} pending unpubl.")
    if report.team_issues:
        parts.append(f"{len(report.team_issues)} Team-Setup")
    if report.skill_issues:
        parts.append(f"{len(report.skill_issues)} Skill-Link(s)")
    if report.rule_issues:
        parts.append(f"{len(report.rule_issues)} Rule-Link(s)")
    if report.tools_need_install:
        parts.append(f"{len(report.tools_need_install)} Adapter")
    return yellow("shared-agents: ") + ", ".join(parts) + plain(" — sa status")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show actionable shared-agents reminders (learnings, skills, adapters)."
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print nothing when all clear; exit 1 when action needed",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="One-line summary",
    )
    args = parser.parse_args()

    home = shared_home()
    if not home.is_dir():
        if args.quiet:
            return 0
        print(f"shared-agents not found: {home}", file=sys.stderr)
        print("Run: sa install", file=sys.stderr)
        return 1

    report = collect(home)

    if args.json:
        payload = asdict(report)
        payload["has_action"] = report.has_action
        print(json.dumps(payload, indent=2))
        return 1 if report.has_action else 0

    if args.quiet and not report.has_action:
        return 0

    if args.brief:
        print(format_brief(report))
        return 1 if report.has_action else 0

    if args.quiet and report.has_action:
        print(format_brief(report))
        return 1

    if report.has_action:
        print_logo()
        print()
    print(format_human(report))
    return 1 if report.has_action else 0


if __name__ == "__main__":
    run_cli_main(main)
