#!/usr/bin/env python3
"""Remove an approved learning (index + file). Optional: move back to pending/."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_GIT_REMOTE = "git@bitbucket.org:netgrade/shared-agents.git"

FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
ID_RE = re.compile(r"^\s+-\s+id:\s+(.+)\s*$")


def shared_home() -> Path:
    return Path(os.environ.get("SHARED_AGENTS_HOME", Path.home() / ".shared-agents"))


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


def index_entries(index_path: Path) -> list[tuple[str, str]]:
    if not index_path.is_file():
        return []
    entries: list[tuple[str, str]] = []
    learning_id = ""
    rel_file = ""
    for line in index_path.read_text().splitlines():
        id_match = ID_RE.match(line)
        if id_match:
            if learning_id and rel_file:
                entries.append((learning_id, rel_file))
            learning_id = id_match.group(1).strip()
            rel_file = ""
            continue
        if line.strip().startswith("file:") and learning_id:
            rel_file = line.split(":", 1)[1].strip()
    if learning_id and rel_file:
        entries.append((learning_id, rel_file))
    return entries


def remove_index_entry(index_path: Path, learning_id: str) -> bool:
    if not index_path.is_file():
        return False
    lines = index_path.read_text().splitlines()
    out: list[str] = []
    i = 0
    removed = False
    while i < len(lines):
        match = ID_RE.match(lines[i])
        if match and match.group(1).strip() == learning_id:
            removed = True
            i += 1
            while i < len(lines) and (
                lines[i].startswith("    ") or lines[i].strip() == ""
            ):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    if removed:
        index_path.write_text("\n".join(out).rstrip() + "\n")
    return removed


def approved_path(home: Path, rel_file: str) -> Path:
    rel = rel_file.removeprefix("learnings/").removeprefix("/")
    return home / "learnings" / rel


def find_by_id(home: Path, learning_id: str) -> tuple[str, Path] | None:
    index_path = home / "learnings" / "index.yaml"
    for entry_id, rel_file in index_entries(index_path):
        if entry_id == learning_id:
            path = approved_path(home, rel_file)
            if path.is_file():
                return entry_id, path
    for path in sorted((home / "learnings" / "approved").glob("**/*.md")):
        fm = parse_frontmatter(path.read_text())
        if fm.get("id", "").strip() == learning_id:
            return learning_id, path
    return None


def resolve_target(arg: str | None, home: Path) -> tuple[str, Path] | None:
    if not arg:
        entries = index_entries(home / "learnings" / "index.yaml")
        if not entries:
            print("No approved learnings in index.yaml.")
            return None
        if len(entries) == 1:
            entry_id, rel = entries[0]
            return entry_id, approved_path(home, rel)

        print("Approved learnings:")
        for idx, (entry_id, rel) in enumerate(entries, start=1):
            print(f"  {idx}) {entry_id}  ({Path(rel).name})")
        while True:
            choice = input("Select number (or q): ").strip().lower()
            if choice in {"q", "quit", ""}:
                return None
            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(entries):
                    entry_id, rel = entries[num - 1]
                    return entry_id, approved_path(home, rel)
            print("Invalid choice.")

    arg = arg.strip()
    found = find_by_id(home, arg)
    if found:
        return found

    candidates = [
        Path(arg),
        home / arg,
        home / "learnings" / arg,
        home / "learnings" / "approved" / arg,
    ]
    name = Path(arg).name
    candidates.extend((home / "learnings" / "approved").glob(f"**/{name}"))

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            fm = parse_frontmatter(candidate.read_text())
            entry_id = fm.get("id", candidate.stem).strip()
            return entry_id, candidate.resolve()

    print(f"Learning not found: {arg}", file=sys.stderr)
    return None


def confirm(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
        if answer in {"", "n", "no"}:
            return False
        if answer in {"y", "yes"}:
            return True
        print("Please answer y or n.")


def run_git(
    home: Path, args: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
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


def git_publish(
    home: Path,
    learning_id: str,
    *,
    dry_run: bool = False,
    no_git: bool = False,
) -> int:
    if no_git:
        print("Skipped git commit/push (--no-git).")
        return 0
    if not (home / ".git").is_dir():
        print("Not a git repo — skipped commit/push.")
        return 0

    commit_msg = f"docs(learnings): unapprove {learning_id}"
    if dry_run:
        print("")
        print("[dry-run] Would run:")
        print(f'  git -C {home} add learnings/')
        print(f'  git -C {home} commit -m "{commit_msg}"')
        print(f"  git -C {home} push")
        return 0

    fixed = ensure_git_remote(home)
    if fixed:
        print(fixed)

    run_git(home, ["add", "learnings/"], check=True)
    staged = run_git(home, ["diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        print("Nothing staged under learnings/ — skipped commit/push.")
        return 0

    run_git(home, ["commit", "-m", commit_msg], check=True)
    print(f"Committed: {commit_msg}")

    push = run_git(home, ["push"], check=False)
    if push.returncode == 0:
        out = (push.stdout or push.stderr or "").strip()
        if out:
            print(out)
        print("Pushed to remote.")
        return 0

    err = (push.stderr or push.stdout or "push failed").strip()
    print(f"Commit OK, but push failed: {err}", file=sys.stderr)
    return 1


def unapprove(
    home: Path,
    entry_id: str,
    approved_file: Path,
    *,
    to_pending: bool = False,
    dry_run: bool = False,
) -> Path | None:
    index_path = home / "learnings" / "index.yaml"
    pending_dest: Path | None = None

    if to_pending:
        pending_dest = home / "learnings" / "pending" / approved_file.name
        if pending_dest.exists() and not dry_run:
            raise SystemExit(f"Pending file already exists: {pending_dest}")

    if dry_run:
        action = f"move to {pending_dest}" if to_pending else "delete"
        print(f"[dry-run] Would remove index entry: {entry_id}")
        print(f"[dry-run] Would {action}: {approved_file}")
        return pending_dest

    if not remove_index_entry(index_path, entry_id):
        print(f"Warning: id not in index.yaml: {entry_id}", file=sys.stderr)

    if to_pending:
        pending_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(approved_file), str(pending_dest))
        return pending_dest

    approved_file.unlink()
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove an approved learning from index.yaml and disk."
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Learning id, filename, or path (interactive picker if omitted)",
    )
    parser.add_argument("--list", action="store_true", help="List approved learnings")
    parser.add_argument(
        "--to-pending",
        action="store_true",
        help="Move file to learnings/pending/ instead of deleting",
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    parser.add_argument("--dry-run", action="store_true", help="Show actions only")
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Skip automatic git commit and push",
    )
    args = parser.parse_args()

    home = shared_home()

    if args.list:
        entries = index_entries(home / "learnings" / "index.yaml")
        if not entries:
            print("No approved learnings in index.yaml.")
            return 0
        for entry_id, rel in entries:
            print(f"{Path(rel).name}\tlearning_id={entry_id}\tfile={rel}")
        return 0

    target = resolve_target(args.target, home)
    if target is None:
        return 1

    entry_id, approved_file = target
    if not approved_file.is_file():
        print(f"File not found: {approved_file}", file=sys.stderr)
        return 1

    print("")
    print(f"Unapprove: {entry_id}")
    print(f"File:      {approved_file.relative_to(home)}")
    if args.to_pending:
        print(f"Target:    learnings/pending/{approved_file.name}")
    else:
        print("Target:    delete file")
    print("-" * 72)
    print(approved_file.read_text().rstrip())
    print("-" * 72)

    if not args.yes and not args.dry_run:
        if not confirm("Remove from approved?"):
            print("Cancelled.")
            return 0

    pending_dest = unapprove(
        home,
        entry_id,
        approved_file,
        to_pending=args.to_pending,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        return git_publish(
            home, entry_id, dry_run=True, no_git=args.no_git
        )

    if pending_dest:
        print(f"Moved to pending: {pending_dest}")
    else:
        print(f"Removed: {approved_file}")

    print(f"Updated: {home / 'learnings' / 'index.yaml'}")
    return git_publish(home, entry_id, dry_run=False, no_git=args.no_git)


if __name__ == "__main__":
    raise SystemExit(main())
