#!/usr/bin/env python3
"""Commit and push a pending learning so teammates can review it."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_GIT_REMOTE = "git@bitbucket.org:netgrade/shared-agents.git"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def shared_home() -> Path:
    return Path(os.environ.get("SHARED_AGENTS_HOME", Path.home() / ".shared-agents"))


def pending_dir(home: Path) -> Path:
    return home / "learnings" / "pending"


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FM_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def resolve_pending(path_arg: str | None, home: Path) -> list[Path]:
    pending = pending_dir(home)
    if path_arg:
        candidates = [
            Path(path_arg),
            home / path_arg,
            pending / path_arg,
            pending / Path(path_arg).name,
        ]
        for candidate in candidates:
            if candidate.is_file() and candidate.suffix == ".md":
                return [candidate.resolve()]
        print(f"File not found: {path_arg}", file=sys.stderr)
        return []

    changed = pending_changes(home)
    if changed:
        return changed

    files = sorted(p for p in pending.glob("*.md") if p.is_file())
    if not files:
        print("No pending learnings to publish.", file=sys.stderr)
        return []
    if len(files) == 1:
        return [files[0]]
    print("Multiple pending files — specify one or use --all:")
    for path in files:
        fm = parse_frontmatter(path.read_text())
        print(f"  {path.name}\tlearning_id={fm.get('id', path.stem)}")
    return []


def pending_changes(home: Path) -> list[Path]:
    if not (home / ".git").is_dir():
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "learnings/pending/"],
        cwd=home,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    paths: list[Path] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.endswith(".md"):
            continue
        rel = line[3:].strip()
        path = home / rel
        if path.is_file():
            paths.append(path)
    return sorted(paths)


def run_git(
    home: Path, args: list[str], *, check: bool = True
) -> subprocess.CompletedResult[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=home,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise SystemExit(f"git {' '.join(args)} failed: {err}")
    return result


def ensure_git_remote(home: Path) -> str | None:
    current = run_git(home, ["remote", "get-url", "origin"], check=False)
    if current.returncode != 0:
        return None
    url = current.stdout.strip()
    if url.startswith(("git@", "https://", "ssh://")):
        return None
    canonical = os.environ.get("SHARED_AGENTS_GIT_REMOTE", DEFAULT_GIT_REMOTE)
    local_path = url.removeprefix("file://")
    local_repo = Path(local_path)
    if local_repo.is_dir() and (local_repo / ".git").is_dir():
        upstream = run_git(local_repo, ["remote", "get-url", "origin"], check=False)
        if upstream.returncode == 0:
            up = upstream.stdout.strip()
            if up.startswith(("git@", "https://", "ssh://")):
                canonical = up
    run_git(home, ["remote", "set-url", "origin", canonical], check=True)
    return f"Fixed git origin: {url} -> {canonical}"


def publish(
    home: Path,
    files: list[Path],
    *,
    dry_run: bool = False,
    no_git: bool = False,
) -> int:
    if not files:
        return 1

    labels: list[str] = []
    rel_paths: list[str] = []
    for path in files:
        fm = parse_frontmatter(path.read_text())
        labels.append(fm.get("id", path.stem))
        rel_paths.append(str(path.relative_to(home)))

    commit_msg = f"docs(learnings): pending {', '.join(labels)}"

    if no_git:
        print("Skipped git commit/push (--no-git).")
        return 0

    if not (home / ".git").is_dir():
        print("Not a git repo — skipped commit/push.")
        print("Teammates cannot review until committed to remote.")
        return 1

    if dry_run:
        print("[dry-run] Would run:")
        print(f"  git -C {home} add {' '.join(rel_paths)}")
        print(f'  git -C {home} commit -m "{commit_msg}"')
        print(f"  git -C {home} push")
        return 0

    fixed = ensure_git_remote(home)
    if fixed:
        print(fixed)

    run_git(home, ["add", *rel_paths], check=True)
    staged = run_git(home, ["diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        print("Nothing new to commit — pending already published.")
        return 0

    run_git(home, ["commit", "-m", commit_msg], check=True)
    print(f"Committed: {commit_msg}")

    push = run_git(home, ["push"], check=False)
    if push.returncode == 0:
        out = (push.stdout or push.stderr or "").strip()
        if out:
            print(out)
        print("Pushed — teammates can sa-sync and sa-review.")
        return 0

    err = (push.stderr or push.stdout or "push failed").strip()
    print(f"Commit OK, but push failed: {err}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Commit and push pending learning(s) for team review."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Pending file or slug (default: unstaged pending/*.md)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Publish all pending/*.md with uncommitted changes",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-git", action="store_true")
    args = parser.parse_args()

    home = shared_home()
    if args.all:
        files = pending_changes(home) or sorted(pending_dir(home).glob("*.md"))
        files = [p for p in files if p.is_file()]
    else:
        files = resolve_pending(args.file, home)

    if not files:
        return 1

    for path in files:
        print(f"Publish pending: {path.relative_to(home)}")

    return publish(home, files, dry_run=args.dry_run, no_git=args.no_git)


if __name__ == "__main__":
    raise SystemExit(main())
