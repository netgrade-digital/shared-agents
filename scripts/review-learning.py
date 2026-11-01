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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import usage  # noqa: E402  (same dir: per-learning usage.yaml init)
from sa_ui import (
    cyan,
    git_committed,
    git_dry_run,
    git_nothing_staged,
    git_note,
    git_push_failed,
    git_pushed,
    git_skip_no_git,
    git_skip_not_repo,
    green,
    heading,
    list_pick_item,
    list_section,
    list_tsv_row,
    menu_option,
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
)

DEFAULT_GIT_REMOTE = "git@bitbucket.org:netgrade/shared-agents.git"

FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
LIST_RE = re.compile(r"^\[(.*)\]$")
ID_RE = re.compile(r"^\s+-\s+id:\s+(.+)\s*$")


def shared_home() -> Path:
    from sa_config import core_home

    return core_home()


def git_home(home: Path | None = None) -> Path:
    from sa_config import git_data_home

    return git_data_home(home)


def pending_dir(home: Path) -> Path:
    from sa_config import pending_dir as sa_pending_dir

    return sa_pending_dir(home)


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


def parse_versions(value: str) -> dict[str, str]:
    """Parse `versions: [shopware:6.6.10, php:8.3.14]` into a dict."""
    result: dict[str, str] = {}
    for item in parse_yaml_list(value):
        if ":" not in item:
            continue
        name, ver = item.split(":", 1)
        name = name.strip()
        ver = ver.strip().strip("'\"")
        if name and ver:
            result[name] = ver
    return result


def format_versions(versions: dict[str, str]) -> str:
    if not versions:
        return "[]"
    inner = ", ".join(f"{k}:{v}" for k, v in sorted(versions.items()))
    return f"[{inner}]"


VERSION_FULL_RE = re.compile(r"^\d+\.\d+\.\d+(?:\.\d+)?$")


def validate_version_strings(versions: dict[str, str]) -> list[str]:
    """Return human-readable warnings for non-conforming version values."""
    warnings: list[str] = []
    for name, ver in versions.items():
        lowered = ver.lower()
        if "x" in lowered or "*" in ver:
            warnings.append(
                f"{name}:{ver} — use full patch (e.g. shopware:6.6.10), not wildcards"
            )
            continue
        if not VERSION_FULL_RE.match(ver):
            warnings.append(
                f"{name}:{ver} — expected MAJOR.MINOR.PATCH (e.g. 6.6.10, 11.31.0)"
            )
    return warnings


STACK_DOMAINS = {
    "shopware",
    "laravel",
    "symfony",
    "vue",
    "nuxt",
    "react",
    "nextjs",
    "php",
    "node",
    "wordpress",
    "magento",
    "typo3",
}


def is_pending_learning(path: Path, pending: Path) -> bool:
    """True only for a markdown file directly in pending/."""
    resolved = path.resolve()
    return (
        resolved.is_file()
        and resolved.parent == pending.resolve()
        and resolved.suffix == ".md"
    )


def resolve_pending(path_arg: str | None, home: Path) -> Path | None:
    pending = pending_dir(home)
    if path_arg:
        candidates = [
            Path(path_arg),
            home / path_arg,
            pending / path_arg,
            pending / Path(path_arg).name,
        ]
        outside = False
        for candidate in candidates:
            if not candidate.is_file():
                continue
            if is_pending_learning(candidate, pending):
                return candidate.resolve()
            outside = True
        if outside:
            say_warn_stderr(f"Not a pending learning: {path_arg}")
        else:
            say_warn_stderr(f"File not found: {path_arg}")
        return None

    files = sorted(pending.glob("*.md"))
    if not files:
        say_warn("No pending learnings.")
        return None
    if len(files) == 1:
        return files[0]

    list_section("Pending learnings:")
    for idx, path in enumerate(files, start=1):
        list_pick_item(idx, path.name)
    while True:
        choice = prompt_line(f"{cyan('Select number (or q)')}: ").strip().lower()
        if choice in {"q", "quit", ""}:
            return None
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(files):
                return files[num - 1]
        say_warn("Invalid choice.")


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


def format_index_entry(entry: dict[str, str | list[str] | dict[str, str]]) -> str:
    domain = entry["domain"]
    tags = entry["tags"]
    versions = entry.get("versions") or {}
    domain_yaml = ", ".join(domain)
    tags_yaml = ", ".join(tags)
    lines = [
        f"  - id: {entry['id']}",
        f"    file: {entry['file']}",
        f"    project: {entry['project']}",
        f"    domain: [{domain_yaml}]",
        f"    tags: [{tags_yaml}]",
        f"    versions: {format_versions(versions)}",
        f"    confidence: {entry['confidence']}",
        f"    created: {entry['created']}",
    ]
    return "\n".join(lines) + "\n"


def append_index(index_path: Path, entry: dict[str, str | list[str]]) -> None:
    block = format_index_entry(entry)
    if index_path.is_file():
        content = index_path.read_text()
        if not content.endswith("\n"):
            content += "\n"
        # Scaffold uses "learnings: []" — replace before appending first entry.
        if re.search(r"^learnings:\s*\[\]\s*$", content, re.MULTILINE):
            content = re.sub(
                r"^learnings:\s*\[\]\s*$",
                "learnings:",
                content,
                count=1,
                flags=re.MULTILINE,
            )
        elif "learnings:" not in content:
            content = content.rstrip() + "\nlearnings:\n"
        index_path.write_text(content + block)
        return

    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("version: 1\nlearnings:\n" + block)


def build_index_entry(
    frontmatter: dict[str, str], rel_file: str
) -> dict[str, str | list[str] | dict[str, str]]:
    learning_id = frontmatter.get("id", "").strip()
    if not learning_id:
        raise SystemExit("Frontmatter missing required field: id")

    project = frontmatter.get("project", "unknown").strip()
    domain = parse_yaml_list(frontmatter.get("domain", "")) or ["general"]
    tags = parse_yaml_list(frontmatter.get("tags", "")) or domain
    versions = parse_versions(frontmatter.get("versions", ""))
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
        "versions": versions,
        "confidence": confidence,
        "created": created,
    }


def warn_missing_versions(
    frontmatter: dict[str, str], domain: str, versions: dict[str, str]
) -> None:
    if versions:
        for msg in validate_version_strings(versions):
            say_warn_stderr(msg)
        return
    domains = {d.lower() for d in parse_yaml_list(frontmatter.get("domain", ""))}
    domains.add(domain.lower())
    if domains & STACK_DOMAINS:
        say_warn_stderr(
            "no versions: in frontmatter — add stack versions when applicable "
            "(e.g. versions: [shopware:6.6.10, php:8.3.14])."
        )


def promote(
    pending_path: Path,
    home: Path,
    domain: str,
    *,
    dry_run: bool = False,
) -> tuple[Path, dict[str, str | list[str]]]:
    text = pending_path.read_text()
    frontmatter = parse_frontmatter(text)
    learning_id = str(frontmatter.get("id") or pending_path.stem).strip()
    # Folder per learning: <id>/learning.md + <id>/usage.yaml (machine-writable)
    entry = build_index_entry(
        frontmatter,
        f"approved/by-domain/{domain}/{learning_id}/learning.md",
    )

    from sa_config import approved_dir, index_path as sa_index_path

    index_path = sa_index_path(home)
    if index_has_id(index_path, str(entry["id"])):
        raise SystemExit(f"ID already in index.yaml: {entry['id']}")

    dest_dir = approved_dir(home) / "by-domain" / domain / learning_id
    dest = dest_dir / "learning.md"
    if dest.exists() or dest_dir.exists():
        raise SystemExit(f"Destination already exists: {dest_dir}")

    if dry_run:
        return dest, entry

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pending_path), str(dest))
    usage.init_usage_file(dest_dir, str(entry["id"]))
    append_index(index_path, entry)
    return dest, entry


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
    """Point origin at Bitbucket when it is a local dev checkout path (core only)."""
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
    dest: Path,
    pending_path: Path,
    entry: dict[str, str | list[str]],
    *,
    dry_run: bool = False,
    no_git: bool = False,
) -> int:
    from sa_config import learnings_label, learnings_prefix_for_git

    repo = git_home(home)
    prefix = learnings_prefix_for_git(home)
    label = learnings_label(home)

    if no_git:
        git_skip_no_git()
        return 0

    if not (repo / ".git").is_dir():
        git_skip_not_repo()
        return 0

    learning_id = str(entry["id"])
    commit_msg = f"docs(learnings): approve {learning_id}"
    rel_dest = dest.relative_to(repo)

    if dry_run:
        git_dry_run(
            [
                "ensure git remote (core only)",
                f"git -C {repo} add {prefix}/index.yaml {rel_dest}",
                f"git -C {repo} add -u {prefix}/pending/",
                f'git -C {repo} commit -m "{commit_msg}"',
                f"git -C {repo} push",
            ]
        )
        return 0

    fixed = ensure_git_remote(repo)
    if fixed:
        git_note(fixed)

    core = shared_home()
    ensure_remote = core / "scripts" / "ensure-git-remote.sh"
    if ensure_remote.is_file() and repo.resolve() == core.resolve():
        fix = subprocess.run(
            ["bash", str(ensure_remote), str(repo)],
            capture_output=True,
            text=True,
        )
        if fix.stdout.strip():
            git_note(fix.stdout.strip())

    run_git(repo, ["add", f"{prefix}/index.yaml", str(rel_dest)], check=True)
    run_git(repo, ["add", "-u", f"{prefix}/pending/"], check=False)

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
    hints: list[str] = []
    if "denyCurrentBranch" in err or "checked out branch" in err:
        hints = [
            "Hint: origin points at a local dev checkout. Run:",
            f"  bash {home}/scripts/ensure-git-remote.sh",
            f"  cd {home} && git push",
        ]
    else:
        hints = [f"Retry: cd {home} && git push"]
    git_push_failed(err, hints=hints)
    return 1


def ask_review_action() -> str | None:
    """Return 'approve', 'reject', or None (cancel, file stays pending)."""
    print()
    print(heading("Review"))
    menu_option("[y]", "Approve and promote")
    menu_option("[r]", "Reject (delete pending + push)")
    menu_option("[n]", "Cancel (keep pending)")
    while True:
        choice = prompt_line(f"{cyan('> ')}").strip().lower()
        if choice in {"y", "yes", "j", "ja"}:
            return "approve"
        if choice in {"r", "reject", "ablehnen", "d", "delete"}:
            return "reject"
        if choice in {"n", "no", "nein", "q", "quit", "a", "abbrechen", ""}:
            return None
        say_warn("Please answer y, r, or n.")


def learning_id_of(path: Path) -> str:
    return parse_frontmatter(path.read_text()).get("id", "").strip() or path.stem


def git_reject(
    home: Path,
    rel: str,
    learning_id: str,
    *,
    dry_run: bool = False,
    no_git: bool = False,
) -> int:
    repo = git_home(home)
    commit_msg = f"docs(learnings): reject {learning_id}"

    if no_git:
        git_skip_no_git()
        return 0
    if not (repo / ".git").is_dir():
        git_skip_not_repo()
        return 0

    if dry_run:
        git_dry_run(
            [
                f"git -C {repo} add -u -- {rel}",
                f'git -C {repo} commit -m "{commit_msg}"',
                f"git -C {repo} push",
            ]
        )
        return 0

    fixed = ensure_git_remote(repo)
    if fixed:
        git_note(fixed)

    run_git(repo, ["add", "-u", "--", rel], check=True)
    staged = run_git(repo, ["diff", "--cached", "--quiet"], check=False)
    if staged.returncode == 0:
        git_nothing_staged("Nothing staged — skipped commit/push.")
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
    git_push_failed(err, hints=[f"Retry: cd {repo} && git push"])
    return 1


def reject_pending(
    pending_path: Path,
    home: Path,
    *,
    dry_run: bool = False,
    no_git: bool = False,
) -> int:
    pending = pending_dir(home)
    if not is_pending_learning(pending_path, pending):
        say_warn_stderr(f"Not a pending learning: {pending_path}")
        return 1

    learning_id = learning_id_of(pending_path)
    repo = git_home(home)
    rel = pending_path.resolve().relative_to(repo.resolve()).as_posix()
    tracked = (
        run_git(repo, ["ls-files", "--error-unmatch", "--", rel], check=False).returncode
        == 0
    )

    if dry_run:
        say_warn(f"[dry-run] Would delete: {pending_path}")
        if not tracked:
            say_warn("[dry-run] Not in git — no commit/push.")
            return 0
        return git_reject(home, rel, learning_id, dry_run=True, no_git=no_git)

    pending_path.unlink()
    say_success(f"Deleted: {pending_path}")
    if not tracked:
        say_warn("Not in git — nothing to commit or push.")
        return 0
    return git_reject(home, rel, learning_id, dry_run=False, no_git=no_git)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review a pending learning: approve into approved/ or reject (delete)."
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
        "--reject",
        action="store_true",
        help="Delete the pending file and push (no prompt)",
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

    if args.reject and args.yes:
        say_warn_stderr("Cannot use --reject and --yes together.")
        return 1

    home = shared_home()
    pending = pending_dir(home)

    if args.list:
        files = sorted(pending.glob("*.md"))
        if not files:
            say_warn("No pending learnings.")
            return 0
        for path in files:
            fm = parse_frontmatter(path.read_text())
            learning_id = fm.get("id", path.stem)
            project = fm.get("project", "?")
            versions = format_versions(parse_versions(fm.get("versions", "")))
            list_tsv_row(
                path.name,
                learning_id=learning_id,
                project=project,
                versions=versions,
            )
        return 0

    pending_path = resolve_pending(args.file, home)
    if pending_path is None:
        return 1

    text = pending_path.read_text()
    frontmatter = parse_frontmatter(text)
    domain = pick_domain(frontmatter, args.domain)
    versions = parse_versions(frontmatter.get("versions", ""))
    warn_missing_versions(frontmatter, domain, versions)

    from sa_config import approved_dir

    _preview_id = str(frontmatter.get("id") or pending_path.stem).strip()
    rel_target = (
        approved_dir(home) / "by-domain" / domain / _preview_id / "learning.md"
    )
    preview_header(
        f"Review: {pending_path.name}",
        Target=str(rel_target.relative_to(git_home(home))),
    )
    preview_body(text)

    action = "approve"
    if args.reject:
        action = "reject"
    elif not args.yes and not args.dry_run:
        action = ask_review_action()
        if action is None:
            say_cancelled()
            return 0

    if action == "reject":
        return reject_pending(
            pending_path,
            home,
            dry_run=args.dry_run,
            no_git=args.no_git,
        )

    dest, entry = promote(
        pending_path,
        home,
        domain,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        say_warn(f"[dry-run] Would move to: {dest}")
        say_warn("[dry-run] Would append to team learnings index.yaml:")
        say_info(format_index_entry(entry).rstrip())
        git_publish(
            home,
            dest,
            pending_path,
            entry,
            dry_run=True,
            no_git=args.no_git,
        )
        return 0

    from sa_config import index_path

    print()
    say_success(f"Promoted: {dest}")
    say_success(f"Indexed:  {index_path(home)}")

    return git_publish(
        home,
        dest,
        pending_path,
        entry,
        dry_run=False,
        no_git=args.no_git,
    )


if __name__ == "__main__":
    run_cli_main(main)
