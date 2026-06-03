#!/usr/bin/env python3
"""Team data repo under $SHARED_AGENTS_HOME/team (nested git, not committed to core)."""

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
from sa_config import TEAM_DIRNAME, core_home, team_dir, team_remote, write_config
from sa_ui import (
    bold,
    bullet_fail,
    bullet_ok,
    bullet_warn,
    cyan,
    green,
    heading,
    plain,
    print_banner,
    red,
    say_info,
    say_success,
    say_warn,
    say_warn_stderr,
    run_cli_main,
    yellow,
)

ID_RE = re.compile(r"^\s+-\s+id:\s+(.+)\s*$", re.MULTILINE)

INDEX_TEMPLATE = """version: 1
learnings:
"""

LEARNINGS_README = """# Team learnings

- `pending/` — agent drafts (after you said yes)
- `approved/` — human-reviewed team knowledge (`sa review`)

Agents read `approved/` + `index.yaml`. Never commit secrets.
"""

TEAM_README = """# Team data (private)

This directory is its own git repository (not part of the public core remote).
Learnings and team-specific skills live here.
"""


def run_git(cwd: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {err}")
    return result


def git_origin_url(repo: Path) -> str | None:
    result = run_git(repo, ["remote", "get-url", "origin"], check=False)
    if result.returncode != 0:
        return None
    url = (result.stdout or "").strip()
    return url or None


def repair_index_yaml(index: Path) -> bool:
    """Fix legacy scaffold `learnings: []` so sa review can append entries."""
    if not index.is_file():
        return False
    text = index.read_text(encoding="utf-8")
    if not re.search(r"^learnings:\s*\[\]\s*$", text, re.MULTILINE):
        return False
    index.write_text(
        re.sub(
            r"^learnings:\s*\[\]\s*$",
            "learnings:",
            text,
            count=1,
            flags=re.MULTILINE,
        ),
        encoding="utf-8",
    )
    return True


def resolve_team_remote(core_home: Path, chosen: str | None = None) -> str | None:
    """Wizard/config value, or git origin when team/ already exists."""
    if chosen and str(chosen).strip():
        return str(chosen).strip()
    td = team_dir(core_home)
    if (td / ".git").is_dir():
        return git_origin_url(td)
    return team_remote(core_home)


def _ensure_dir_gitkeep(directory: Path) -> None:
    """Track empty learnings folders in git (clone/pull keeps pending/ and approved/)."""
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / ".gitkeep"
    if not marker.is_file():
        marker.write_text("", encoding="utf-8")


def scaffold_team_tree(root: Path) -> None:
    learnings = root / "learnings"
    _ensure_dir_gitkeep(learnings / "pending")
    _ensure_dir_gitkeep(learnings / "approved")
    (root / "skills").mkdir(parents=True, exist_ok=True)

    index = root / "learnings" / "index.yaml"
    if not index.is_file():
        index.write_text(INDEX_TEMPLATE, encoding="utf-8")
    else:
        repair_index_yaml(index)

    readme_learn = root / "learnings" / "README.md"
    if not readme_learn.is_file():
        readme_learn.write_text(LEARNINGS_README, encoding="utf-8")

    readme_team = root / "README.md"
    if not readme_team.is_file():
        readme_team.write_text(TEAM_README, encoding="utf-8")

    keep = root / "skills" / ".gitkeep"
    if not keep.is_file():
        keep.touch()


def _has_commits(repo: Path) -> bool:
    r = run_git(repo, ["rev-parse", "HEAD"], check=False)
    return r.returncode == 0


def _remote_empty(remote: str) -> bool:
    r = run_git(Path.cwd(), ["ls-remote", remote, "HEAD"], check=False)
    return r.returncode != 0 or not (r.stdout or "").strip()


def setup_team(
    core_home: Path,
    remote: str | None,
    *,
    dry_run: bool = False,
) -> str:
    """Clone or init team/ and optionally push scaffold. Returns status line."""
    td = team_dir(core_home)

    if not remote:
        origin = git_origin_url(td) if (td / ".git").is_dir() else None
        if origin:
            write_config(core_home, team_remote_url=origin)
            scaffold_team_tree(td)
            maybe_commit_push(
                td,
                message="chore(team): sync config scaffold and index.yaml",
                initial=False,
            )
            return f"Synced team.remote from existing team/ ({origin})"
        write_config(core_home, team_remote_url=None)
        return "Solo mode — learnings under core (no team remote)"

    remote = remote.strip()
    write_config(core_home, team_remote_url=remote)

    if dry_run:
        return f"[dry-run] would setup {TEAM_DIRNAME}/ → {remote}"

    if td.is_dir() and (td / ".git").is_dir():
        run_git(td, ["remote", "set-url", "origin", remote], check=False)
        configure_pull(td)
        run_git(td, ["fetch", "origin"], check=False)
        branch = run_git(td, ["rev-parse", "--abbrev-ref", "HEAD"], check=False)
        br = branch.stdout.strip() if branch.returncode == 0 else "main"
        merge = run_git(td, ["merge", "--ff-only", f"origin/{br}"], check=False)
        if merge.returncode != 0:
            run_git(td, ["pull", "--ff-only", "origin", br], check=False)
        scaffold_team_tree(td)
        maybe_commit_push(
            td,
            message="chore(team): ensure learnings scaffold and index.yaml",
            initial=False,
        )
        write_config(core_home, team_remote_url=git_origin_url(td) or remote)
        return f"Team repo updated: {td}"

    if td.exists() and any(td.iterdir()) and not (td / ".git").is_dir():
        say_warn_stderr(f"Removing non-git {td} to clone team remote")
        import shutil

        shutil.rmtree(td)

    td.parent.mkdir(parents=True, exist_ok=True)

    clone = run_git(core_home, ["clone", remote, TEAM_DIRNAME], check=False)
    if clone.returncode == 0:
        configure_pull(td)
        scaffold_team_tree(td)
        maybe_commit_push(td, message="chore(team): ensure learnings scaffold", initial=False)
        return f"Cloned team repo: {remote}"

    td.mkdir(parents=True, exist_ok=True)
    scaffold_team_tree(td)
    run_git(td, ["init", "-b", "main"], check=True)
    run_git(td, ["remote", "add", "origin", remote], check=False)
    configure_pull(td)
    maybe_commit_push(td, message="chore(team): initial team data scaffold", initial=True)

    if _remote_empty(remote):
        run_git(td, ["push", "-u", "origin", "main"], check=False)
        return f"Initialized and pushed team repo: {remote}"

    push = run_git(td, ["push", "-u", "origin", "main"], check=False)
    if push.returncode == 0:
        return f"Initialized and pushed team repo: {remote}"
    return f"Initialized team repo locally ({remote}) — push when remote is ready"


def configure_pull(repo: Path) -> None:
    run_git(repo, ["config", "pull.rebase", "false"], check=False)
    run_git(repo, ["config", "pull.ff", "only"], check=False)


def maybe_commit_push(repo: Path, *, message: str, initial: bool) -> None:
    run_git(repo, ["add", "-A"], check=False)
    if run_git(repo, ["diff", "--cached", "--quiet"], check=False).returncode == 0:
        return
    run_git(repo, ["commit", "-m", message], check=False)
    if initial or _has_commits(repo):
        run_git(repo, ["push", "-u", "origin", "main"], check=False)


def migrate_legacy_learnings(core_home: Path, *, dry_run: bool = False) -> str:
    """Move $SHARED_AGENTS_HOME/learnings/ → team/learnings/ (one-time)."""
    import shutil

    from sa_config import team_remote, write_config

    legacy = core_home / "learnings"
    if not legacy.is_dir():
        return "Nothing to migrate — no learnings/ under core home"

    has_content = bool(list(legacy.rglob("*.md")))
    index = legacy / "index.yaml"
    if index.is_file() and "id:" in index.read_text(encoding="utf-8"):
        has_content = True
    if not has_content:
        return "learnings/ has no team content — safe to remove the empty folder"

    remote = team_remote(core_home)
    if not remote:
        raise RuntimeError(
            "No team.remote in config.local.yaml — run sa bootstrap and set a team repo URL first"
        )

    td = team_dir(core_home)
    if not (td / ".git").is_dir():
        if dry_run:
            return f"[dry-run] would init team/ from {remote} and move learnings/"
        setup_team(core_home, remote, dry_run=False)

    dest = td / "learnings"
    if dest.exists() and list(dest.rglob("*.md")):
        raise RuntimeError(
            "team/learnings/ already has content — merge manually (see docs/migration-team-data.md)"
        )

    if dry_run:
        return f"[dry-run] would move {legacy} → {dest}"

    if dest.exists():
        shutil.rmtree(dest)
    shutil.move(str(legacy), str(dest))

    if (td / ".git").is_dir():
        maybe_commit_push(
            td,
            message="chore(team): migrate learnings from core home",
            initial=False,
        )

    write_config(core_home, team_remote_url=remote)
    return f"Migrated learnings/ → {dest}"


@dataclass
class TeamVerifyReport:
    team_path: str
    configured_remote: str | None
    git_origin: str | None
    ok: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    stats: dict[str, int | str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.errors

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


def _parse_index_stats(index_path: Path) -> tuple[int, str | None]:
    if not index_path.is_file():
        return 0, "index.yaml missing"
    try:
        text = index_path.read_text(encoding="utf-8")
    except OSError as exc:
        return 0, str(exc)
    if "learnings:" not in text:
        return 0, "index.yaml has no learnings: section"
    ids = ID_RE.findall(text)
    return len(ids), None


def verify_team(home: Path | None = None) -> TeamVerifyReport:
    """Validate team/ layout, git remote, and learnings structure."""
    root = home if home is not None else core_home()
    td = team_dir(root)
    remote = team_remote(root)
    report = TeamVerifyReport(
        team_path=str(td),
        configured_remote=remote,
        git_origin=None,
    )

    legacy = root / "learnings"
    if legacy.is_dir() and (list(legacy.rglob("*.md")) or (legacy / "index.yaml").is_file()):
        report.warnings.append(
            f"Legacy {legacy} still present — run: sa team migrate"
        )

    if not remote:
        report.warnings.append(
            "No team.remote in config.local.yaml (solo mode — learnings may use core/learnings/)"
        )
        if not td.is_dir():
            report.ok.append("Solo mode — team/ not required")
            return report

    if not td.is_dir():
        report.errors.append("team/ missing — run: sa bootstrap")
        return report

    if not (td / ".git").is_dir():
        report.errors.append("team/ is not a git repository — run: sa bootstrap")
        return report

    origin = run_git(td, ["remote", "get-url", "origin"], check=False)
    if origin.returncode == 0:
        report.git_origin = origin.stdout.strip()
        report.ok.append(f"git origin: {report.git_origin}")
        if remote and report.git_origin != remote:
            report.warnings.append(
                f"config team.remote ({remote}) differs from git origin ({report.git_origin})"
            )
        elif report.git_origin and not remote:
            report.warnings.append(
                f"team.remote unset in config.local.yaml but team/ origin is {report.git_origin} "
                "— set team.remote to match"
            )
    else:
        report.warnings.append("team/ has no git origin remote")

    head = run_git(td, ["rev-parse", "HEAD"], check=False)
    if head.returncode != 0:
        report.errors.append("team/ has no commits yet")
    else:
        report.ok.append("git repository has commits")

    learnings = td / "learnings"
    if not learnings.is_dir():
        report.errors.append("team/learnings/ missing")
        return report

    pending = learnings / "pending"
    approved = learnings / "approved"
    index_path = learnings / "index.yaml"

    if not pending.is_dir():
        report.warnings.append("team/learnings/pending/ missing (will be created on first learning)")
    else:
        n_pending = len(list(pending.glob("*.md")))
        report.stats["pending_md"] = n_pending
        report.ok.append(f"pending/: {n_pending} draft(s)")

    if not approved.is_dir():
        report.warnings.append("team/learnings/approved/ missing")
    else:
        n_approved = len(list(approved.glob("**/*.md")))
        report.stats["approved_md"] = n_approved
        report.ok.append(f"approved/: {n_approved} file(s)")

    index_count, index_err = _parse_index_stats(index_path)
    if index_err:
        report.errors.append(f"team/learnings/index.yaml — {index_err}")
    else:
        report.stats["index_entries"] = index_count
        report.ok.append(f"index.yaml: {index_count} entr(y/ies)")

        approved_n = int(report.stats.get("approved_md", 0))
        if index_count > 0 and approved_n == 0:
            report.warnings.append(
                "index.yaml has entries but no approved/*.md — check paths or run sa sync"
            )

    # Legacy layout inside team repo (learnings/*.md at root without pending/)
    loose = [
        p
        for p in learnings.glob("*.md")
        if p.is_file() and p.name.lower() not in {"readme.md"}
    ]
    if loose:
        report.warnings.append(
            f"Markdown directly in team/learnings/ ({len(loose)} file(s)) — prefer pending/ or approved/"
        )

    skills = td / "skills"
    if skills.is_dir():
        n_skills = len([p for p in skills.iterdir() if p.is_dir()])
        report.stats["team_skills"] = n_skills
        if n_skills:
            report.ok.append(f"team/skills/: {n_skills} skill(s)")
        else:
            report.ok.append("team/skills/ (empty — optional)")
    else:
        report.warnings.append("team/skills/ missing (optional for team-only skills)")

    return report


def print_verify_report(report: TeamVerifyReport, *, quiet: bool = False) -> None:
    if quiet and report.passed and not report.has_warnings:
        say_success("Team repo OK")
        return

    print()
    print(heading("Team repo verify"))
    label = green("OK") if report.passed and not report.has_warnings else (
        yellow("WARN") if report.passed else red("FAIL")
    )
    print(f"  {plain('Status:')} {label}")
    print(f"  {plain('Path:')}   {cyan(report.team_path)}")
    if report.configured_remote:
        print(f"  {plain('Config:')} {cyan(report.configured_remote)}")
    print()

    for msg in report.ok:
        bullet_ok(msg)
    for msg in report.warnings:
        bullet_warn(msg)
    for msg in report.errors:
        bullet_fail(msg)

    if report.passed and not report.has_warnings:
        print()
        say_success("Team data repository is ready.")
    elif report.passed:
        print()
        say_warn("Team repo usable — review warnings above.")
    else:
        print()
        say_warn_stderr("Fix errors above, then: sa team verify")


def verify_team_json(report: TeamVerifyReport) -> str:
    return json.dumps(
        {
            "passed": report.passed,
            "team_path": report.team_path,
            "configured_remote": report.configured_remote,
            "git_origin": report.git_origin,
            "ok": report.ok,
            "warnings": report.warnings,
            "errors": report.errors,
            "stats": report.stats,
        },
        indent=2,
    )


def sync_team(core_home: Path, *, quiet: bool = False) -> bool:
    td = team_dir(core_home)
    if not (td / ".git").is_dir():
        return False
    configure_pull(td)
    branch = run_git(td, ["rev-parse", "--abbrev-ref", "HEAD"], check=False)
    br = branch.stdout.strip() if branch.returncode == 0 else "main"
    fetch = run_git(td, ["fetch", "origin"], check=not quiet)
    if fetch.returncode != 0:
        return False
    merge = run_git(td, ["merge", "--ff-only", f"origin/{br}"], check=False)
    if merge.returncode != 0:
        run_git(td, ["pull", "--ff-only", "origin", br], check=False)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Team data repo helpers")
    parser.add_argument("command", choices=["sync", "setup", "migrate", "verify"])
    parser.add_argument("core_home", nargs="?", default=os.environ.get("SHARED_AGENTS_HOME", ""))
    parser.add_argument("--remote", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when warnings are present (not only errors)",
    )
    args = parser.parse_args()

    core = Path(os.path.expanduser(args.core_home or "~/shared-agents"))
    if args.command == "verify":
        if not args.quiet and not args.json:
            print_banner(subtitle="Team data — structure check")
        report = verify_team(core)
        if args.json:
            print(verify_team_json(report))
        else:
            print_verify_report(report, quiet=args.quiet)
        if not report.passed:
            return 1
        if args.strict and report.has_warnings:
            return 1
        return 0

    if args.command == "sync":
        if sync_team(core, quiet=args.quiet):
            if not args.quiet:
                say_info("Team learnings synced.")
        return 0

    if args.command == "migrate":
        try:
            msg = migrate_legacy_learnings(core, dry_run=args.dry_run)
            say_success(msg)
            return 0
        except RuntimeError as exc:
            say_warn_stderr(str(exc))
            return 1

    remote = args.remote.strip() or None
    try:
        msg = setup_team(core, remote, dry_run=args.dry_run)
        say_success(msg)
        return 0
    except RuntimeError as exc:
        say_warn_stderr(str(exc))
        return 1


if __name__ == "__main__":
    run_cli_main(main)
