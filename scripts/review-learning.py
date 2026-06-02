#!/usr/bin/env python3
"""Review a pending learning and promote it to approved/ + index.yaml."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

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
        return 0

    print("")
    print(f"Promoted: {dest}")
    print(f"Indexed:  {home / 'learnings' / 'index.yaml'}")
    print("")
    print("Next: commit + push/PR from shared-agents repo")
    print(f"  cd {home}")
    print("  git add learnings/")
    print(f'  git commit -m "docs(learnings): approve {entry["id"]}"')
    print("  git push")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
