#!/usr/bin/env python3
"""Review a pending learning and promote it to approved/ + index.yaml."""

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
LIST_RE = re.compile(r"^\[(.*)\]$")
ID_RE = re.compile(r"^\s+-\s+id:\s+(.+)\s*$")


def shared_home() -> Path:
    import os

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


def parse_yaml_list(value: str) -> list[str]:
    value = value.strip()
    match = LIST_RE.match(value)
    if not match:
        return [value] if value else []
    inner = match.group(1).strip()
    if not inner:
        return []
    return [part.strip().strip("'\"") for part in inner.split(",") if part.strip()]


def resolve_pending(path_arg: str | None, home: Path) -> Path | None:
    pending = pending_dir(home)
    if path_arg:
        candidates = [
            Path(path_arg),
            home / path_arg,
            pending / path_arg,
            pending / Path(path_arg).name,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        print(f"File not found: {path_arg}", file=sys.stderr)
        return None

    files = sorted(pending.glob("*.md"))
    if not files:
        print("No pending learnings.")
        return None
    if len(files) == 1:
        return files[0]

    print("Pending learnings:")
    for idx, path in enumerate(files, start=1):
        print(f"  {idx}) {path.name}")
    while True:
        choice = input("Select number (or q): ").strip().lower()
        if choice in {"q", "quit", ""}:
            return None
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(files):
                return files[num - 1]
        print("Invalid choice.")


def pick_domain(frontmatter: dict[str, str], override: str | None) -> str:
    if override:
        return override.strip().strip("/")
    domains = parse_yaml_list(frontmatter.get("domain", ""))
    if domains:
        return re.sub(r"[^\w.-]+", "-", domains[0]).strip("-") or "general"
    return "general"


def index_has_id(index_path: Path, learning_id: str) -> bool:
    if not index_path.is_file():
        return False
    for line in index_path.read_text().splitlines():
        match = ID_RE.match(line)
        if match and match.group(1).strip() == learning_id:
            return True
    return False


def format_index_entry(entry: dict[str, str | list[str]]) -> str:
    domain = entry["domain"]
    tags = entry["tags"]
    domain_yaml = ", ".join(domain)
    tags_yaml = ", ".join(tags)
    return (
        f"  - id: {entry['id']}\n"
        f"    file: {entry['file']}\n"
        f"    project: {entry['project']}\n"
        f"    domain: [{domain_yaml}]\n"
        f"    tags: [{tags_yaml}]\n"
        f"    confidence: {entry['confidence']}\n"
        f"    created: {entry['created']}\n"
    )


def append_index(index_path: Path, entry: dict[str, str | list[str]]) -> None:
    block = format_index_entry(entry)
    if index_path.is_file():
        content = index_path.read_text()
        if not content.endswith("\n"):
            content += "\n"
        index_path.write_text(content + block)
        return

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("version: 1\nlearnings:\n" + block)


def build_index_entry(
    frontmatter: dict[str, str], rel_file: str
) -> dict[str, str | list[str]]:
    learning_id = frontmatter.get("id", "").strip()
    if not learning_id:
        raise SystemExit("Frontmatter missing required field: id")

    project = frontmatter.get("project", "unknown").strip()
    domain = parse_yaml_list(frontmatter.get("domain", "")) or ["general"]
    tags = parse_yaml_list(frontmatter.get("tags", "")) or domain
    confidence = frontmatter.get("confidence", "high").strip() or "high"
    created = frontmatter.get("created", "").strip()
    if not created:
        from datetime import date

        created = date.today().isoformat()

    return {
        "id": learning_id,
        "file": rel_file,
        "project": project,
        "domain": domain,
        "tags": tags,
        "confidence": confidence,
        "created": created,
    }


def promote(
    pending_path: Path,
    home: Path,
    domain: str,
    *,
    dry_run: bool = False,
) -> tuple[Path, dict[str, str | list[str]]]:
    text = pending_path.read_text()
    frontmatter = parse_frontmatter(text)
    entry = build_index_entry(
        frontmatter, f"approved/by-domain/{domain}/{pending_path.name}"
    )

    index_path = home / "learnings" / "index.yaml"
    if index_has_id(index_path, str(entry["id"])):
        raise SystemExit(f"ID already in index.yaml: {entry['id']}")

    dest_dir = home / "learnings" / "approved" / "by-domain" / domain
    dest = dest_dir / pending_path.name
    if dest.exists():
        raise SystemExit(f"Destination already exists: {dest}")

    if dry_run:
        return dest, entry

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pending_path), str(dest))
    append_index(index_path, entry)
    return dest, entry


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
    """Point origin at Bitbucket when it is a local dev checkout path."""
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
    dest: Path,
    pending_path: Path,
    entry: dict[str, str | list[str]],
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

    learning_id = str(entry["id"])
    commit_msg = f"docs(learnings): approve {learning_id}"
    rel_dest = dest.relative_to(home)

    if dry_run:
        print("")
        print("[dry-run] Would run:")
        print("  ensure git remote -> Bitbucket (not local dev checkout)")
        print(f"  git -C {home} add learnings/index.yaml {rel_dest}")
        print(f"  git -C {home} add -u learnings/pending/")
        print(f'  git -C {home} commit -m "{commit_msg}"')
        print(f"  git -C {home} push")
        return 0

    fixed = ensure_git_remote(home)
    if fixed:
        print(fixed)

    ensure_remote = home / "scripts" / "ensure-git-remote.sh"
    if ensure_remote.is_file():
        fix = subprocess.run(
            ["bash", str(ensure_remote), str(home)],
            capture_output=True,
            text=True,
        )
        if fix.stdout.strip():
            print(fix.stdout.strip())

    run_git(home, ["add", "learnings/index.yaml", str(rel_dest)], check=True)
    run_git(home, ["add", "-u", "learnings/pending/"], check=False)

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
    if "denyCurrentBranch" in err or "checked out branch" in err:
        print(
            "Hint: origin points at a local dev checkout. Run:\n"
            f"  bash {home}/scripts/ensure-git-remote.sh\n"
            f"  cd {home} && git push",
            file=sys.stderr,
        )
    else:
        print(f"Retry: cd {home} && git push", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review a pending learning and promote it to approved/."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Pending learning path or filename (interactive picker if omitted)",
    )
    parser.add_argument("--list", action="store_true", help="List pending learnings")
    parser.add_argument("--domain", help="Override destination domain folder")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Approve without confirmation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without moving files or editing index.yaml",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="Skip automatic git commit and push after promote",
    )
    args = parser.parse_args()

    home = shared_home()
    pending = pending_dir(home)

    if args.list:
        files = sorted(pending.glob("*.md"))
        if not files:
            print("No pending learnings.")
            return 0
        for path in files:
            fm = parse_frontmatter(path.read_text())
            learning_id = fm.get("id", path.stem)
            project = fm.get("project", "?")
            print(f"{path.name}\tlearning_id={learning_id}\tproject={project}")
        return 0

    pending_path = resolve_pending(args.file, home)
    if pending_path is None:
        return 1

    text = pending_path.read_text()
    frontmatter = parse_frontmatter(text)
    domain = pick_domain(frontmatter, args.domain)

    print("")
    print(f"Review: {pending_path.name}")
    print(f"Target: learnings/approved/by-domain/{domain}/")
    print("-" * 72)
    print(text.rstrip())
    print("-" * 72)

    if not args.yes and not args.dry_run:
        if not confirm("Approve and promote?"):
            print("Cancelled.")
            return 0

    dest, entry = promote(
        pending_path,
        home,
        domain,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("")
        print("[dry-run] Would move to:", dest)
        print("[dry-run] Would append to learnings/index.yaml:")
        print(format_index_entry(entry).rstrip())
        git_publish(
            home,
            dest,
            pending_path,
            entry,
            dry_run=True,
            no_git=args.no_git,
        )
        return 0

    print("")
    print(f"Promoted: {dest}")
    print(f"Indexed:  {home / 'learnings' / 'index.yaml'}")

    return git_publish(
        home,
        dest,
        pending_path,
        entry,
        dry_run=False,
        no_git=args.no_git,
    )


if __name__ == "__main__":
    raise SystemExit(main())
