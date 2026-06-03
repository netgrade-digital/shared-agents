#!/usr/bin/env python3
"""Diagnose and repair common shared-agents setup issues (symlinks, links, adapters)."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sa_config import core_home
from sa_ui import (
    bold,
    cyan,
    green,
    heading,
    magenta,
    plain,
    print_logo,
    prompt_yes_no,
    run_cli_main,
    say_info,
    say_success,
    say_warn,
    say_warn_stderr,
    yellow,
)

RULE_BLOCKING_RE = re.compile(
    r"^Rule exists as regular file \(skipped to preserve edits\): (.+)$"
)
RULE_MISSING_RE = re.compile(r"^Rule not linked: (.+)$")
RULE_STALE_RE = re.compile(r"^Rule symlink stale: (.+)$")
SKILL_MISSING_RE = re.compile(r"^Skill not linked: (.+)$")
SKILL_STALE_RE = re.compile(r"^Skill symlink stale: (.+)$")


@dataclass
class DoctorPlan:
    sync_links: bool = False
    blocking_rules: list[tuple[Path, Path]] = field(default_factory=list)
    manual_skill_issues: list[str] = field(default_factory=list)
    manual_rule_issues: list[str] = field(default_factory=list)
    adapters_need_install: list[str] = field(default_factory=list)
    team_issues: list[str] = field(default_factory=list)
    pending_learnings: list[str] = field(default_factory=list)

    @property
    def auto_fixable(self) -> bool:
        return self.sync_links or bool(self.blocking_rules)

    @property
    def has_issues(self) -> bool:
        return (
            self.auto_fixable
            or bool(self.manual_skill_issues)
            or bool(self.manual_rule_issues)
            or bool(self.adapters_need_install)
            or bool(self.team_issues)
            or bool(self.pending_learnings)
        )


def scripts_dir(home: Path) -> Path:
    here = Path(__file__).resolve().parent
    if (here / "install-adapters.py").is_file():
        return here
    return home / "scripts"


def load_status_report(home: Path) -> dict:
    status_py = scripts_dir(home) / "sa-status.py"
    if not status_py.is_file():
        return {}
    env = {**os.environ, "SHARED_AGENTS_HOME": str(home)}
    result = subprocess.run(
        [sys.executable, str(status_py), "--json"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if not result.stdout.strip():
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def build_plan(home: Path) -> DoctorPlan:
    report = load_status_report(home)
    plan = DoctorPlan(
        adapters_need_install=list(report.get("tools_need_install") or []),
        team_issues=list(report.get("team_issues") or []),
        pending_learnings=list(report.get("pending_learnings") or []),
    )

    for msg in report.get("skill_issues") or []:
        if SKILL_MISSING_RE.match(msg) or SKILL_STALE_RE.match(msg):
            plan.sync_links = True
        else:
            plan.manual_skill_issues.append(msg)

    for msg in report.get("rule_issues") or []:
        blocking = RULE_BLOCKING_RE.match(msg)
        if blocking:
            dest = Path(blocking.group(1)).expanduser()
            source = rule_source_for(home, dest)
            if source:
                plan.blocking_rules.append((dest, source))
            else:
                plan.manual_rule_issues.append(msg)
            continue
        if RULE_MISSING_RE.match(msg) or RULE_STALE_RE.match(msg):
            plan.sync_links = True
        else:
            plan.manual_rule_issues.append(msg)

    return plan


def rule_source_for(repo_home: Path, dest: Path) -> Path | None:
    from rules_install import collect_parsed_rules

    for rule in collect_parsed_rules(repo_home):
        if rule.path.name == dest.name:
            return rule.path
    return None


def format_plan(plan: DoctorPlan) -> str:
    if not plan.has_issues:
        return green("shared-agents doctor: all clear ✓")

    lines: list[str] = [bold(cyan("shared-agents doctor")), ""]

    if plan.sync_links:
        lines.append(magenta("Auto-fix:"))
        lines.append(plain("  • Refresh skill symlinks, rule symlinks, AGENTS.md team-rules blocks"))
        lines.append("")

    if plan.blocking_rules:
        lines.append(magenta(f"Auto-fix with backup ({len(plan.blocking_rules)}):"))
        for dest, source in plan.blocking_rules:
            lines.append(f"  • {yellow(dest.name)} — regular file at {dest}")
            lines.append(plain(f"    → symlink to {source}"))
        lines.append(plain("  Backups: $SHARED_AGENTS_HOME/.doctor-backups/"))
        lines.append("")

    if plan.adapters_need_install:
        lines.append(magenta(f"Manual — adapter ({len(plan.adapters_need_install)}):"))
        for item in plan.adapters_need_install:
            lines.append(f"  • {item}")
        lines.append(plain("  → sa install"))
        lines.append("")

    if plan.team_issues:
        lines.append(magenta(f"Manual — team ({len(plan.team_issues)}):"))
        for issue in plan.team_issues:
            lines.append(f"  • {yellow(issue)}")
        lines.append(plain("  → sa team verify · sa bootstrap"))
        lines.append("")

    if plan.pending_learnings:
        lines.append(magenta(f"Manual — learnings ({len(plan.pending_learnings)}):"))
        for name in plan.pending_learnings:
            lines.append(f"  • {yellow(name)}")
        lines.append(plain("  → sa review"))
        lines.append("")

    if plan.manual_skill_issues or plan.manual_rule_issues:
        lines.append(magenta("Manual:"))
        for msg in plan.manual_skill_issues + plan.manual_rule_issues:
            lines.append(f"  • {msg}")

    return "\n".join(lines).rstrip()


def run_sync_links(home: Path, *, dry_run: bool) -> list[str]:
    py = scripts_dir(home) / "install-adapters.py"
    if not py.is_file():
        return ["install-adapters.py not found"]
    env = {**os.environ, "SHARED_AGENTS_HOME": str(home)}
    args = [sys.executable, str(py), "sync-links", str(home)]
    if dry_run:
        args.append("--dry-run")
    result = subprocess.run(args, capture_output=True, text=True, env=env, check=False)
    out = (result.stdout or "").strip()
    if out:
        return out.splitlines()
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "sync-links failed").strip()
        return [f"! {err}"]
    return []


def apply_fixes(
    home: Path,
    plan: DoctorPlan,
    *,
    dry_run: bool,
    replace_blocking: bool,
) -> None:
    backup_dir = home / ".doctor-backups"

    if replace_blocking and plan.blocking_rules:
        heading("Rule symlinks")
        from rules_install import backup_and_symlink

        for dest, source in plan.blocking_rules:
            msg, differs = backup_and_symlink(
                dest, source, backup_dir, dry_run=dry_run
            )
            if msg.startswith("[dry-run]"):
                say_info(msg)
            else:
                say_success(msg)
            if differs and not dry_run:
                say_warn(f"Review backup: {backup_dir / dest.name}")

    if plan.sync_links or replace_blocking:
        heading("Sync links")
        for line in run_sync_links(home, dry_run=dry_run):
            if line.startswith("!"):
                say_warn(line)
            elif line.startswith("[dry-run]") or line.startswith("  ✓") or "Skills" in line or "Merged" in line:
                print(line if line.startswith("  ") else f"  {line}")
            elif line:
                say_info(line)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose and repair shared-agents symlink / link issues."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply fixes (sync-links; blocking rule files → backup + symlink)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview fixes only")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation for --fix",
    )
    args = parser.parse_args()

    home = core_home()
    if not home.is_dir():
        say_warn_stderr(f"shared-agents not found: {home}")
        say_warn_stderr("Run: sa install")
        return 1

    plan = build_plan(home)

    if not args.fix:
        if plan.has_issues:
            print_logo()
            print()
        print(format_plan(plan))
        if plan.auto_fixable:
            print()
            print(plain("Run: ") + green("sa doctor --fix"))
        return 1 if plan.has_issues else 0

    if not plan.auto_fixable:
        print(format_plan(plan))
        if plan.has_issues:
            say_warn("Nothing auto-fixable — see manual items above.")
            return 1
        say_success("Nothing to fix.")
        return 0

    replace_blocking = bool(plan.blocking_rules)
    if not args.yes and not args.dry_run:
        print(format_plan(plan))
        print()
        if not prompt_yes_no("Apply fixes?", default=True):
            say_warn("Cancelled.")
            return 0

    apply_fixes(
        home,
        plan,
        dry_run=args.dry_run,
        replace_blocking=replace_blocking,
    )

    if args.dry_run:
        return 0

    remaining = build_plan(home)
    if remaining.auto_fixable:
        say_warn("Some auto-fixable issues remain — run sa doctor --fix again.")
        return 1
    if remaining.has_issues:
        print()
        print(format_plan(remaining))
        return 1
    say_success("Doctor: all auto-fixable issues resolved ✓")
    return 0


if __name__ == "__main__":
    run_cli_main(main)
