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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sa_ui import (
    arrow_line,
    cyan,
    menu_option,
    git_committed,
    git_dry_run,
    git_nothing_staged,
    git_note,
    git_push_failed,
    git_pushed,
    git_skip_no_git,
    git_skip_not_repo,
    heading,
    list_pick_item,
    list_section,
    list_tsv_row,
    plain,
    preview_body,
    preview_header,
    UserCancelled,
    prompt_line,
    run_cli_main,
    say_cancelled,
    say_info,
    say_success,
    say_warn_stderr,
    say_warn,
    yellow,
)

DEFAULT_GIT_REMOTE = "git@bitbucket.org:netgrade/shared-agents.git"

FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
ID_RE = re.compile(r"^\s+-\s+id:\s+(.+)\s*$")


def shared_home() -> Path:
    from sa_config import core_home

    return core_home()


def git_repo_home(home: Path) -> Path:
    from sa_config import git_data_home

    return git_data_home(home)


def learnings_base(home: Path) -> Path:
    from sa_config import learnings_root

    return learnings_root(home)


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
    rel = rel_file.removeprefix("learnings/").lstrip("/")
    return learnings_base(home) / rel


def find_by_id(home: Path, learning_id: str) -> tuple[str, Path] | None:
    index_path = learnings_base(home) / "index.yaml"
    for entry_id, rel_file in index_entries(index_path):
        if entry_id == learning_id:
            path = approved_path(home, rel_file)
            if path.is_file():
                return entry_id, path
    for path in sorted((learnings_base(home) / "approved").glob("**/*.md")):
        fm = parse_frontmatter(path.read_text())
        if fm.get("id", "").strip() == learning_id:
            return learning_id, path
    return None


def resolve_target(arg: str | None, home: Path) -> tuple[str, Path] | None:
    if not arg:
        entries = index_entries(learnings_base(home) / "index.yaml")
        if not entries:
            say_warn("No approved learnings in index.yaml.")
            return None
        if len(entries) == 1:
            entry_id, rel = entries[0]
            return entry_id, approved_path(home, rel)

        list_section("Approved learnings:")
        for idx, (entry_id, rel) in enumerate(entries, start=1):
            list_pick_item(idx, f"{entry_id}  ({Path(rel).name})")
        while True:
            choice = prompt_line(f"{cyan('Select number (or q)')}: ").strip().lower()
            if choice in {"q", "quit", ""}:
                return None
            if choice.isdigit():
                num = int(choice)
                if 1 <= num <= len(entries):
                    entry_id, rel = entries[num - 1]
                    return entry_id, approved_path(home, rel)
            say_warn("Invalid choice.")

    arg = arg.strip()
    found = find_by_id(home, arg)
    if found:
        return found

    lb = learnings_base(home)
    candidates = [
        Path(arg),
        home / arg,
        lb / arg,
        lb / "approved" / arg,
    ]
    name = Path(arg).name
    candidates.extend((lb / "approved").glob(f"**/{name}"))

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            fm = parse_frontmatter(candidate.read_text())
            entry_id = fm.get("id", candidate.stem).strip()
            return entry_id, candidate.resolve()

    say_warn_stderr(f"Learning not found: {arg}")
    return None


def ask_disposition() -> str | None:
    """Interactive wizard: delete vs move to pending."""
    print()
    print(heading("Was soll mit der Datei passieren?"))
    menu_option("[1]", "Löschen")
    menu_option("[2]", "Nach pending/ verschieben (Entwurf)")
    menu_option("[q]", "Abbrechen")
    while True:
        choice = prompt_line(f"{cyan('> ')}").strip().lower()
        if choice in {"1", "delete", "löschen", "l", "d"}:
            return "delete"
        if choice in {"2", "pending", "p", "pending/"}:
            return "pending"
        if choice in {"q", "quit", "a", "abbrechen", ""}:
            return None
        say_warn("Bitte 1, 2 oder q.")


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
    from sa_config import is_team_git_repo

    if is_team_git_repo(home):
        return None
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
    from sa_config import learnings_label, learnings_prefix_for_git

    repo = git_repo_home(home)
    prefix = learnings_prefix_for_git(home)
    label = learnings_label(home)

    if no_git:
        git_skip_no_git()
        return 0
    if not (repo / ".git").is_dir():
        git_skip_not_repo()
        return 0

    commit_msg = f"docs(learnings): unapprove {learning_id}"
    if dry_run:
        git_dry_run(
            [
                f"git -C {repo} add {prefix}/",
                f'git -C {repo} commit -m "{commit_msg}"',
                f"git -C {repo} push",
            ]
        )
        return 0

    fixed = ensure_git_remote(repo)
    if fixed:
        git_note(fixed)

    run_git(repo, ["add", f"{prefix}/"], check=True)
    staged = run_git(repo, ["diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        git_nothing_staged(f"Nothing staged under {label} — skipped commit/push.")
        return 0

    run_git(repo, ["commit", "-m", commit_msg], check=True)
    git_committed(commit_msg)

    push = run_git(repo, ["push"], check=False)
    if push.returncode == 0:
        out = (push.stdout or push.stderr or "").strip()
        if out:
            say_info(out)
        git_pushed()
        return 0

    err = (push.stderr or push.stdout or "push failed").strip()
    git_push_failed(err)
    return 1


def unapprove(
    home: Path,
    entry_id: str,
    approved_file: Path,
    *,
    to_pending: bool = False,
    dry_run: bool = False,
) -> Path | None:
    index_path = learnings_base(home) / "index.yaml"
    pending_dest: Path | None = None

    if to_pending:
        pending_dest = learnings_base(home) / "pending" / approved_file.name
        if pending_dest.exists() and not dry_run:
            raise SystemExit(f"Pending file already exists: {pending_dest}")

    if dry_run:
        action = f"move to {pending_dest}" if to_pending else "delete"
        say_warn(f"[dry-run] Would remove index entry: {entry_id}")
        say_warn(f"[dry-run] Would {action}: {approved_file}")
        return pending_dest

    if not remove_index_entry(index_path, entry_id):
        say_warn_stderr(f"id not in index.yaml: {entry_id}")

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
        help="Move to pending/ (non-interactive; skips wizard)",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete file (non-interactive; skips wizard)",
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
    from sa_config import learnings_label

    label = learnings_label(home)

    if args.list:
        entries = index_entries(learnings_base(home) / "index.yaml")
        if not entries:
            say_warn("No approved learnings in index.yaml.")
            return 0
        for entry_id, rel in entries:
            list_tsv_row(Path(rel).name, learning_id=entry_id, file=rel)
        return 0

    target = resolve_target(args.target, home)
    if target is None:
        return 1

    entry_id, approved_file = target
    if not approved_file.is_file():
        say_warn_stderr(f"File not found: {approved_file}")
        return 1

    preview_header(
        f"Unapprove: {entry_id}",
        File=str(approved_file.relative_to(home)),
    )
    preview_body(approved_file.read_text())

    to_pending: bool | None = None
    if args.to_pending and args.delete:
        say_warn_stderr("Cannot use --to-pending and --delete together.")
        return 1
    if args.to_pending:
        to_pending = True
    elif args.delete:
        to_pending = False
    elif args.dry_run:
        to_pending = False
        say_warn("[dry-run] Wizard would ask: [1] Delete  [2] Move to pending/")
    elif args.yes:
        to_pending = False
    else:
        disposition = ask_disposition()
        if disposition is None:
            say_cancelled()
            return 0
        to_pending = disposition == "pending"

    if to_pending:
        arrow_line(f"{label}pending/{approved_file.name}")
    else:
        arrow_line("Delete file")

    pending_dest = unapprove(
        home,
        entry_id,
        approved_file,
        to_pending=to_pending,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        return git_publish(
            home, entry_id, dry_run=True, no_git=args.no_git
        )

    if pending_dest:
        say_success(f"Moved to pending: {pending_dest}")
    else:
        say_success(f"Removed: {approved_file}")

    say_success(f"Updated: {learnings_base(home) / 'index.yaml'}")
    return git_publish(home, entry_id, dry_run=False, no_git=args.no_git)


if __name__ == "__main__":
    run_cli_main(main)
