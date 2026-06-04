#!/usr/bin/env python3
"""Interactive wizards to scaffold team skills and rules under $SHARED_AGENTS_HOME/team/."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sa_config import core_home, git_data_home, team_dir, uses_team_data
from sa_ui import (
    bold,
    cyan,
    git_committed,
    git_dry_run,
    git_push_failed,
    git_pushed,
    git_skip_no_git,
    git_skip_not_repo,
    heading,
    list_pick_item,
    list_section,
    plain,
    prompt_line,
    prompt_yes_no,
    run_cli_main,
    say_info,
    say_success,
    say_warn,
    say_warn_stderr,
)

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKIP_ADAPTER_IDS = frozenset({"generic", "openclaw"})


def expand(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def slug_from_name(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.strip().lower())
    slug = slug.strip("-")
    return slug or "untitled"


def title_from_slug(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def validate_slug(slug: str) -> str | None:
    if not slug:
        return "Slug is required."
    if not SLUG_RE.match(slug):
        return "Use lowercase letters, numbers, and hyphens only (e.g. shopware-seo)."
    if slug in {"new", "path", "help"}:
        return f"'{slug}' is reserved."
    return None


def load_adapter_ids(repo_home: Path) -> list[str]:
    manifest = repo_home / "adapters" / "manifest.json"
    if not manifest.is_file():
        return []
    data = json.loads(manifest.read_text(encoding="utf-8"))
    return [
        str(tool["id"])
        for tool in data.get("tools", [])
        if str(tool.get("id", "")) not in SKIP_ADAPTER_IDS
    ]


def ensure_team_tree(core: Path) -> Path:
    from team_data import scaffold_team_tree

    td = team_dir(core)
    if not td.is_dir():
        say_warn_stderr(
            "team/ not found — run sa bootstrap or configure team.remote in config.local.yaml"
        )
        raise SystemExit(1)
    scaffold_team_tree(td)
    return td


def list_team_skills(core: Path) -> list[tuple[str, Path]]:
    base = team_dir(core) / "skills"
    if not base.is_dir():
        return []
    items: list[tuple[str, Path]] = []
    for path in sorted(base.iterdir()):
        if path.is_dir() and (path / "SKILL.md").is_file():
            items.append((path.name, path))
    return items


def list_team_rules(core: Path) -> list[tuple[str, Path]]:
    items: list[tuple[str, Path]] = []
    rules = team_dir(core) / "rules"
    if rules.is_dir():
        for path in sorted(rules.glob("*.mdc")):
            items.append((path.stem, path))
    legacy = rules / "approved"
    if legacy.is_dir():
        for path in sorted(legacy.glob("*.mdc")):
            if not any(slug == path.stem for slug, _ in items):
                items.append((path.stem, path))
    return items


def assert_under_team_skills(core: Path, path: Path) -> None:
    base = (team_dir(core) / "skills").resolve()
    try:
        path.resolve().relative_to(base)
    except ValueError as exc:
        raise SystemExit(
            "Only team skills can be removed (team/skills/) — not Core skills."
        ) from exc


def assert_under_team_rules(core: Path, path: Path) -> None:
    rules = (team_dir(core) / "rules").resolve()
    try:
        path.resolve().relative_to(rules)
    except ValueError as exc:
        raise SystemExit(
            "Only team rules can be removed (team/rules/) — not Core rules."
        ) from exc


def pick_from_list(
    label: str, items: list[tuple[str, Path]]
) -> tuple[str, Path] | None:
    if not items:
        say_warn(f"No team {label} found.")
        return None
    if len(items) == 1:
        return items[0]

    list_section(f"Team {label}:")
    for idx, (slug, path) in enumerate(items, start=1):
        list_pick_item(idx, f"{slug}  ({path})")
    while True:
        choice = prompt_line(f"{cyan('Select number (or q)')}: ").strip().lower()
        if choice in {"q", "quit", ""}:
            return None
        if choice.isdigit():
            num = int(choice)
            if 1 <= num <= len(items):
                return items[num - 1]
        say_warn("Invalid choice.")


def resolve_team_skill(core: Path, name: str | None) -> tuple[str, Path] | None:
    items = list_team_skills(core)
    if not name:
        return pick_from_list("skills", items)

    slug = slug_from_name(name)
    for skill_slug, path in items:
        if skill_slug == slug:
            return skill_slug, path

    candidates = [
        team_dir(core) / "skills" / slug,
        Path(name).expanduser(),
    ]
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "SKILL.md").is_file():
            assert_under_team_skills(core, candidate)
            return candidate.name, candidate.resolve()

    say_warn_stderr(f"Team skill not found: {name}")
    return None


def resolve_team_rule(core: Path, name: str | None) -> tuple[str, Path] | None:
    items = list_team_rules(core)
    if not name:
        return pick_from_list("rules", items)

    slug = slug_from_name(name)
    for rule_slug, path in items:
        if rule_slug == slug:
            return rule_slug, path

    candidates = [
        team_dir(core) / "rules" / f"{slug}.mdc",
        team_dir(core) / "rules" / "approved" / f"{slug}.mdc",
        Path(name).expanduser(),
    ]
    for candidate in candidates:
        if candidate.is_file() and candidate.suffix == ".mdc":
            assert_under_team_rules(core, candidate)
            return candidate.stem, candidate.resolve()

    say_warn_stderr(f"Team rule not found: {name}")
    return None


def existing_skill_slugs(core: Path) -> set[str]:
    slugs: set[str] = set()
    for base in (core / "skills", team_dir(core) / "skills"):
        if not base.is_dir():
            continue
        for path in base.iterdir():
            if path.is_dir() and (path / "SKILL.md").is_file():
                slugs.add(path.name)
    return slugs


def existing_rule_slugs(core: Path) -> set[str]:
    slugs: set[str] = set()
    for base in (core / "rules", team_dir(core) / "rules"):
        if not base.is_dir():
            continue
        for path in base.glob("*.mdc"):
            slugs.add(path.stem)
    legacy = team_dir(core) / "rules" / "approved"
    if legacy.is_dir():
        for path in legacy.glob("*.mdc"):
            slugs.add(path.stem)
    return slugs


def prompt_slug(
    label: str, *, default: str | None = None, taken: set[str] | None = None
) -> str:
    while True:
        answer = prompt_line(f"{label}{f' [{default}]' if default else ''}: ").strip()
        slug = slug_from_name(answer) if answer else (default or "")
        if not slug and default:
            slug = default
        err = validate_slug(slug)
        if err:
            say_warn(err)
            continue
        if taken and slug in taken:
            say_warn(f"Already exists: {slug}")
            continue
        return slug


def prompt_multiline(title: str, *, hint: str | None = None) -> str:
    print()
    print(bold(title))
    print(plain("  Finish with a single '.' on its own line (empty body is ok)."))
    if hint:
        print(plain(f"  {hint}"))
    lines: list[str] = []
    while True:
        line = prompt_line("  ")
        if line.strip() == ".":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def parse_targets(
    raw: str | None, valid: set[str]
) -> tuple[tuple[str, ...] | None, str | None]:
    if not raw or not raw.strip():
        return (), None
    parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
    unknown = [p for p in parts if p not in valid]
    if unknown:
        return None, f"Unknown adapter id(s): {', '.join(unknown)}"
    return tuple(dict.fromkeys(parts)), None


def prompt_targets(valid_ids: list[str]) -> tuple[str, ...]:
    valid = set(valid_ids)
    print()
    print(bold("Adapter targets"))
    print(plain("  Empty = all adapters. Comma-separated ids otherwise."))
    print(plain(f"  Available: {', '.join(valid_ids)}"))
    while True:
        raw = prompt_line("  targets: ").strip()
        if not raw:
            return ()
        targets, err = parse_targets(raw, valid)
        if err:
            say_warn(err)
            say_warn(f"Valid: {', '.join(sorted(valid))}")
            continue
        return targets or ()


def build_skill_markdown(
    *, name: str, title: str, description: str, when_to_use: str, workflow: str
) -> str:
    when_block = when_to_use or "- Describe when agents should load this skill.\n"
    workflow_block = workflow or "1. …\n"
    return f"""---
name: {name}
description: >-
  {description}
---

# {title}

## When to use

{when_block}

## Workflow

{workflow_block}

## Notes

- Team skill — `$SHARED_AGENTS_HOME/team/skills/{name}/`
- Teammates: commit/push team repo, then **`sa sync`**
"""


def build_rule_markdown(
    *,
    title: str,
    description: str,
    body: str,
    targets: tuple[str, ...],
) -> str:
    lines = [
        "---",
        f"description: {description}",
    ]
    if targets:
        lines.append(f"targets: [{', '.join(targets)}]")
    lines.extend(["---", "", f"# {title}", ""])
    if body:
        lines.append(body)
    else:
        lines.extend(
            [
                "## Purpose",
                "",
                "Describe what this rule enforces.",
                "",
                "## Guidelines",
                "",
                "- …",
            ]
        )
    lines.extend(
        [
            "",
            "<!-- Team rule — edit in $SHARED_AGENTS_HOME/team/rules/; teammates run sa sync -->",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def run_git_publish(
    core: Path,
    rel_paths: list[str],
    commit_msg: str,
    *,
    dry_run: bool,
    no_git: bool,
) -> int:
    return run_git_commit(
        core, rel_paths, commit_msg, action="add", dry_run=dry_run, no_git=no_git
    )


def open_in_editor(path: Path) -> int:
    """Open path in $EDITOR (fallback nano → vim → vi). Returns subprocess return code."""
    editor = os.environ.get("EDITOR", "")
    if not editor:
        for fallback in ("nano", "vim", "vi"):
            if shutil.which(fallback):
                editor = fallback
                break
    if not editor:
        say_warn_stderr("No editor found. Set $EDITOR or install nano/vim.")
        return 1
    return subprocess.run([editor, str(path)]).returncode


def remove_path(path: Path, repo: Path, rel: str, *, dry_run: bool) -> None:
    if dry_run:
        say_info(f"[dry-run] would remove {path}")
        return

    if (repo / ".git").is_dir():
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=repo,
            capture_output=True,
        )
        if tracked.returncode == 0:
            cmd = ["git", "rm", "-r", rel] if path.is_dir() else ["git", "rm", rel]
            subprocess.run(cmd, cwd=repo, check=True, capture_output=True, text=True)
            return

    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        path.unlink()


def run_git_delete(
    core: Path,
    paths: list[Path],
    commit_msg: str,
    *,
    dry_run: bool,
    no_git: bool,
) -> int:
    repo = git_data_home(core)
    rel_paths = [p.relative_to(repo).as_posix() for p in paths]

    if dry_run:
        for path, rel in zip(paths, rel_paths, strict=True):
            remove_path(path, repo, rel, dry_run=True)
        if no_git:
            return 0
        git_dry_run(
            [
                *(
                    f"git -C {repo} rm -r {rel}"
                    if path.is_dir()
                    else f"git -C {repo} rm {rel}"
                    for path, rel in zip(paths, rel_paths, strict=True)
                ),
                f'git -C {repo} commit -m "{commit_msg}"',
                f"git -C {repo} push",
            ]
        )
        return 0

    for path, rel in zip(paths, rel_paths, strict=True):
        if not path.exists() and not (repo / ".git").is_dir():
            say_warn_stderr(f"Not found: {path}")
            return 1
        remove_path(path, repo, rel, dry_run=False)

    if no_git:
        git_skip_no_git()
        return 0

    if not (repo / ".git").is_dir():
        git_skip_not_repo(extra="Commit deletion manually in the team repo when ready.")
        return 0

    try:
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo,
            capture_output=True,
        )
        if staged.returncode == 0:
            unstaged = subprocess.run(
                ["git", "diff", "--quiet"],
                cwd=repo,
                capture_output=True,
            )
            if unstaged.returncode == 0:
                say_warn("Nothing to commit — file may already be removed.")
                return 0
            subprocess.run(
                ["git", "add", "-u", *rel_paths],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        git_committed(commit_msg)
        push = subprocess.run(["git", "push"], cwd=repo, capture_output=True, text=True)
        if push.returncode != 0:
            git_push_failed((push.stderr or push.stdout or "").strip())
            return 1
        git_pushed()
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or str(exc)).strip()
        git_push_failed(err)
        return 1
    return 0


def run_git_commit(
    core: Path,
    rel_paths: list[str],
    commit_msg: str,
    *,
    action: str,
    dry_run: bool,
    no_git: bool,
) -> int:
    if no_git:
        git_skip_no_git()
        return 0

    repo = git_data_home(core)
    if not (repo / ".git").is_dir():
        git_skip_not_repo(extra="Commit manually in the team repo when ready.")
        return 0

    if dry_run:
        git_dry_run(
            [
                f"git -C {repo} add {' '.join(rel_paths)}",
                f'git -C {repo} commit -m "{commit_msg}"',
                f"git -C {repo} push",
            ]
        )
        return 0

    try:
        subprocess.run(
            ["git", "add", *rel_paths],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo,
            capture_output=True,
        )
        if staged.returncode == 0:
            say_warn("Nothing staged — file may already be committed.")
            return 0
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        git_committed(commit_msg)
        push = subprocess.run(["git", "push"], cwd=repo, capture_output=True, text=True)
        if push.returncode != 0:
            git_push_failed((push.stderr or push.stdout or "").strip())
            return 1
        git_pushed()
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or str(exc)).strip()
        git_push_failed(err)
        return 1
    return 0


def write_file(path: Path, content: str, *, dry_run: bool) -> None:
    if dry_run:
        say_info(f"[dry-run] would write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def wizard_skill_new(core: Path, args: argparse.Namespace) -> int:
    td = ensure_team_tree(core)
    taken = existing_skill_slugs(core)

    if args.name:
        name = slug_from_name(args.name)
        err = validate_slug(name)
        if err:
            say_warn_stderr(err)
            return 1
        if name in taken:
            say_warn_stderr(f"Skill already exists: {name}")
            return 1
        description = (args.description or "").strip()
        if not description:
            say_warn_stderr("--description is required with --name")
            return 1
        title = (args.title or title_from_slug(name)).strip()
        when_to_use = args.when or ""
        workflow = args.workflow or ""
    else:
        heading("New team skill")
        print(plain(f"Target: {cyan(str(td / 'skills'))}"))
        print()
        name = prompt_slug("Skill slug", taken=taken)
        title_default = title_from_slug(name)
        title = prompt_line(f"Title [{title_default}]: ").strip() or title_default
        while True:
            description = prompt_line("Description (frontmatter, one line): ").strip()
            if description:
                break
            say_warn("Description is required.")
        when_to_use = prompt_multiline(
            "When to use (optional)",
            hint="Trigger phrases, projects, or situations.",
        )
        workflow = prompt_multiline(
            "Workflow (optional)", hint="Numbered steps for agents."
        )

    content = build_skill_markdown(
        name=name,
        title=title,
        description=description,
        when_to_use=when_to_use,
        workflow=workflow,
    )
    dest = td / "skills" / name / "SKILL.md"
    if dest.is_file() and not args.force:
        say_warn_stderr(f"Already exists: {dest} (use --force to overwrite)")
        return 1

    write_file(dest, content, dry_run=args.dry_run)
    if not args.dry_run:
        say_success(f"Created skill: {dest}")

    rel = dest.relative_to(git_data_home(core)).as_posix()
    if should_git_publish(args):
        return run_git_publish(
            core,
            [rel],
            f"feat(skills): add team skill {name}",
            dry_run=args.dry_run,
            no_git=args.no_git,
        )

    if not args.dry_run:
        print(plain(f"Next: edit {dest}, commit in team repo, teammates run sa sync"))
    return 0


def wizard_rule_new(core: Path, args: argparse.Namespace) -> int:
    td = ensure_team_tree(core)
    taken = existing_rule_slugs(core)
    valid_ids = load_adapter_ids(core)

    if args.name:
        slug = slug_from_name(args.name)
        err = validate_slug(slug)
        if err:
            say_warn_stderr(err)
            return 1
        if slug in taken:
            say_warn_stderr(f"Rule already exists: {slug}")
            return 1
        description = (args.description or "").strip()
        if not description:
            say_warn_stderr("--description is required with --name")
            return 1
        title = (args.title or title_from_slug(slug)).strip()
        targets, err = (
            parse_targets(args.targets, set(valid_ids)) if args.targets else ((), None)
        )
        if err:
            say_warn_stderr(err)
            return 1
        body = args.body or ""
    else:
        heading("New team rule")
        print(plain(f"Target: {cyan(str(td / 'rules'))}"))
        print()
        slug = prompt_slug("Rule slug (filename without .mdc)", taken=taken)
        title_default = title_from_slug(slug)
        title = prompt_line(f"Title [{title_default}]: ").strip() or title_default
        while True:
            description = prompt_line("Description (frontmatter): ").strip()
            if description:
                break
            say_warn("Description is required.")
        targets = prompt_targets(valid_ids) if valid_ids else ()
        body = prompt_multiline(
            "Rule body (optional)", hint="Markdown content after the title."
        )

    content = build_rule_markdown(
        title=title,
        description=description,
        body=body,
        targets=targets,
    )
    dest = td / "rules" / f"{slug}.mdc"
    if dest.is_file() and not args.force:
        say_warn_stderr(f"Already exists: {dest} (use --force to overwrite)")
        return 1

    write_file(dest, content, dry_run=args.dry_run)
    if not args.dry_run:
        say_success(f"Created rule: {dest}")

    rel = dest.relative_to(git_data_home(core)).as_posix()
    if should_git_publish(args):
        return run_git_publish(
            core,
            [rel],
            f"feat(rules): add team rule {slug}",
            dry_run=args.dry_run,
            no_git=args.no_git,
        )

    if not args.dry_run:
        print(plain(f"Next: edit {dest}, commit in team repo, teammates run sa sync"))
    return 0


def should_git_publish(args: argparse.Namespace) -> bool:
    if args.no_git:
        return False
    if args.push or args.yes:
        return True
    if args.dry_run:
        return True
    return prompt_yes_no("Commit and push to team repo?", default=True)


def confirm_delete(label: str, slug: str, args: argparse.Namespace) -> bool:
    if args.yes:
        return True
    if args.dry_run:
        return True
    return prompt_yes_no(f"Delete team {label} '{slug}'?", default=True)


def wizard_skill_edit(core: Path, args: argparse.Namespace) -> int:
    ensure_team_tree(core)
    resolved = resolve_team_skill(core, args.name)
    if not resolved:
        return 1
    slug, skill_dir = resolved
    assert_under_team_skills(core, skill_dir)

    target = skill_dir / "SKILL.md"
    before = target.read_text(encoding="utf-8")

    rc = open_in_editor(target)
    if rc != 0:
        say_warn_stderr(f"Editor exited with code {rc}")
        return rc

    after = target.read_text(encoding="utf-8")
    if before == after:
        say_info("No changes made.")
        return 0

    say_success(f"Updated skill: {slug}")

    rel = target.relative_to(git_data_home(core)).as_posix()
    if should_git_publish(args):
        return run_git_publish(
            core,
            [rel],
            f"feat(skills): update team skill {slug}",
            dry_run=args.dry_run,
            no_git=args.no_git,
        )

    if not args.dry_run:
        print(plain(f"Next: commit in team repo, teammates run sa sync"))
    return 0


def wizard_rule_edit(core: Path, args: argparse.Namespace) -> int:
    ensure_team_tree(core)
    resolved = resolve_team_rule(core, args.name)
    if not resolved:
        return 1
    slug, rule_path = resolved
    assert_under_team_rules(core, rule_path)

    before = rule_path.read_text(encoding="utf-8")

    rc = open_in_editor(rule_path)
    if rc != 0:
        say_warn_stderr(f"Editor exited with code {rc}")
        return rc

    after = rule_path.read_text(encoding="utf-8")
    if before == after:
        say_info("No changes made.")
        return 0

    say_success(f"Updated rule: {slug}")

    rel = rule_path.relative_to(git_data_home(core)).as_posix()
    if should_git_publish(args):
        return run_git_publish(
            core,
            [rel],
            f"feat(rules): update team rule {slug}",
            dry_run=args.dry_run,
            no_git=args.no_git,
        )

    if not args.dry_run:
        print(plain(f"Next: commit in team repo, teammates run sa sync"))
    return 0


def cmd_skill_list(core: Path, args: argparse.Namespace) -> int:
    items = list_team_skills(core)
    if not items:
        say_info("No team skills in team/skills/")
        return 0
    list_section("Team skills:")
    for slug, path in items:
        print(f"  {cyan(slug)}  {plain(str(path))}")
    return 0


def cmd_rule_list(core: Path, args: argparse.Namespace) -> int:
    items = list_team_rules(core)
    if not items:
        say_info("No team rules in team/rules/")
        return 0
    list_section("Team rules:")
    for slug, path in items:
        print(f"  {cyan(slug)}  {plain(str(path))}")
    return 0


def wizard_skill_rm(core: Path, args: argparse.Namespace) -> int:
    ensure_team_tree(core)
    resolved = resolve_team_skill(core, args.name)
    if not resolved:
        return 1
    slug, skill_dir = resolved
    assert_under_team_skills(core, skill_dir)

    if not confirm_delete("skill", slug, args):
        say_warn("Cancelled.")
        return 0

    repo = git_data_home(core)
    rel = skill_dir.relative_to(repo).as_posix()

    if should_git_publish(args):
        rc = run_git_delete(
            core,
            [skill_dir],
            f"feat(skills): remove team skill {slug}",
            dry_run=args.dry_run,
            no_git=args.no_git,
        )
        if rc == 0 and not args.dry_run:
            say_success(f"Removed skill: {slug}")
        return rc

    remove_path(skill_dir, repo, rel, dry_run=args.dry_run)
    if not args.dry_run:
        say_success(f"Removed skill: {slug}")
        print(plain("Commit team repo + sa sync so teammates drop symlinks"))
    return 0


def wizard_rule_rm(core: Path, args: argparse.Namespace) -> int:
    ensure_team_tree(core)
    resolved = resolve_team_rule(core, args.name)
    if not resolved:
        return 1
    slug, rule_path = resolved
    assert_under_team_rules(core, rule_path)

    if not confirm_delete("rule", slug, args):
        say_warn("Cancelled.")
        return 0

    repo = git_data_home(core)
    rel = rule_path.relative_to(repo).as_posix()

    if should_git_publish(args):
        rc = run_git_delete(
            core,
            [rule_path],
            f"feat(rules): remove team rule {slug}",
            dry_run=args.dry_run,
            no_git=args.no_git,
        )
        if rc == 0 and not args.dry_run:
            say_success(f"Removed rule: {slug}")
        return rc

    remove_path(rule_path, repo, rel, dry_run=args.dry_run)
    if not args.dry_run:
        say_success(f"Removed rule: {slug}")
        print(plain("Commit team repo + sa sync so teammates refresh rule links"))
    return 0


def add_git_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--home", type=Path, default=None, help="SHARED_AGENTS_HOME")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--no-git", action="store_true", help="Skip commit/push")
    parser.add_argument(
        "--push", action="store_true", help="Commit and push without prompting"
    )
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirm prompts")


def add_create_flags(parser: argparse.ArgumentParser) -> None:
    add_git_flags(parser)
    parser.add_argument("--force", action="store_true", help="Overwrite existing file")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, list, or remove team skills and rules"
    )
    sub = parser.add_subparsers(dest="kind", required=True)

    p_skill = sub.add_parser("skill", help="Team skills")
    skill_sub = p_skill.add_subparsers(dest="command", required=True)
    p_skill_new = skill_sub.add_parser("new", help="Create team/skills/<name>/SKILL.md")
    add_create_flags(p_skill_new)
    p_skill_new.add_argument("--name", help="Skill slug (non-interactive)")
    p_skill_new.add_argument("--title", help="Display title")
    p_skill_new.add_argument("--description", help="Frontmatter description")
    p_skill_new.add_argument("--when", dest="when", help="When-to-use section")
    p_skill_new.add_argument("--workflow", help="Workflow section")

    p_skill_rm = skill_sub.add_parser("rm", help="Remove a team skill")
    add_git_flags(p_skill_rm)
    p_skill_rm.add_argument("name", nargs="?", help="Skill slug (picker if omitted)")

    p_skill_edit = skill_sub.add_parser("edit", help="Edit a team skill")
    add_git_flags(p_skill_edit)
    p_skill_edit.add_argument("name", nargs="?", help="Skill slug (picker if omitted)")

    p_skill_list = skill_sub.add_parser("list", help="List team skills")
    add_git_flags(p_skill_list)

    p_rule = sub.add_parser("rule", help="Team rules")
    rule_sub = p_rule.add_subparsers(dest="command", required=True)
    p_rule_new = rule_sub.add_parser("new", help="Create team/rules/<slug>.mdc")
    add_create_flags(p_rule_new)
    p_rule_new.add_argument("--name", help="Rule slug (non-interactive)")
    p_rule_new.add_argument("--title", help="Display title")
    p_rule_new.add_argument("--description", help="Frontmatter description")
    p_rule_new.add_argument(
        "--targets", help="Comma-separated adapter ids (empty = all)"
    )
    p_rule_new.add_argument("--body", help="Markdown body (non-interactive)")

    p_rule_rm = rule_sub.add_parser("rm", help="Remove a team rule")
    add_git_flags(p_rule_rm)
    p_rule_rm.add_argument("name", nargs="?", help="Rule slug (picker if omitted)")

    p_rule_edit = rule_sub.add_parser("edit", help="Edit a team rule")
    add_git_flags(p_rule_edit)
    p_rule_edit.add_argument("name", nargs="?", help="Rule slug (picker if omitted)")

    p_rule_list = rule_sub.add_parser("list", help="List team rules")
    add_git_flags(p_rule_list)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    core = expand(args.home) if getattr(args, "home", None) else core_home()

    if not uses_team_data(core):
        say_warn_stderr("Team data not configured — run sa bootstrap first.")
        return 1

    handlers = {
        ("skill", "new"): wizard_skill_new,
        ("skill", "rm"): wizard_skill_rm,
        ("skill", "list"): cmd_skill_list,
        ("skill", "edit"): wizard_skill_edit,
        ("rule", "new"): wizard_rule_new,
        ("rule", "rm"): wizard_rule_rm,
        ("rule", "list"): cmd_rule_list,
        ("rule", "edit"): wizard_rule_edit,
    }
    handler = handlers.get((args.kind, args.command))
    if handler:
        return handler(core, args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    run_cli_main(main)
