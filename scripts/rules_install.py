#!/usr/bin/env python3
"""Install team/core rules: Cursor symlinks + AGENTS.md marker merge for all adapters."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

TEAM_RULES_MARKER_BEGIN = "<!-- shared-agents:team-rules:begin -->"
TEAM_RULES_MARKER_END = "<!-- shared-agents:team-rules:end -->"
CORE_KNOWLEDGE_RULE = "shared-agents-knowledge.mdc"
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
LIST_RE = re.compile(r"^\[(.*)\]$")


def expand(path: str | Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


@dataclass(frozen=True)
class ParsedRule:
    path: Path
    rule_id: str
    title: str
    body: str
    targets: tuple[str, ...]
    source_label: str


def _parse_frontmatter(text: str) -> dict[str, str]:
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


def _parse_yaml_list(value: str) -> list[str]:
    value = value.strip()
    match = LIST_RE.match(value)
    if not match:
        return [value.strip().strip("'\"")] if value.strip() else []
    inner = match.group(1).strip()
    if not inner:
        return []
    return [part.strip().strip("'\"") for part in inner.split(",") if part.strip()]


def _rule_body(text: str) -> str:
    match = FM_RE.match(text)
    if match:
        return text[match.end() :].strip()
    return text.strip()


def _rule_source_dirs(repo_home: Path) -> list[Path]:
    from sa_config import rules_source_dirs

    return rules_source_dirs(repo_home) or [repo_home / "rules"]


def collect_parsed_rules(repo_home: Path) -> list[ParsedRule]:
    seen_names: set[str] = set()
    rules: list[ParsedRule] = []
    for src in _rule_source_dirs(repo_home):
        label = "rules" if src.name == "rules" and src.parent.name != "team" else "team/rules"
        for path in sorted(src.glob("*.mdc")):
            if path.name in seen_names:
                continue
            seen_names.add(path.name)
            text = path.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            rule_id = fm.get("id", path.stem).strip() or path.stem
            title = fm.get("title", rule_id).strip() or rule_id
            targets = tuple(t.lower() for t in _parse_yaml_list(fm.get("targets", "")))
            rules.append(
                ParsedRule(
                    path=path,
                    rule_id=rule_id,
                    title=title,
                    body=_rule_body(text),
                    targets=targets,
                    source_label=label,
                )
            )
    # Legacy layout: team/rules/approved/*.mdc (pre flat-dir migration)
    legacy = repo_home / "team" / "rules" / "approved"
    if legacy.is_dir():
        for path in sorted(legacy.glob("*.mdc")):
            if path.name in seen_names:
                continue
            seen_names.add(path.name)
            text = path.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            rule_id = fm.get("id", path.stem).strip() or path.stem
            title = fm.get("title", rule_id).strip() or rule_id
            targets = tuple(t.lower() for t in _parse_yaml_list(fm.get("targets", "")))
            rules.append(
                ParsedRule(
                    path=path,
                    rule_id=rule_id,
                    title=title,
                    body=_rule_body(text),
                    targets=targets,
                    source_label="team/rules/approved (legacy)",
                )
            )
    return rules


def rule_applies(rule: ParsedRule, adapter_id: str, *, for_agents_md: bool = False) -> bool:
    adapter = adapter_id.lower()
    if for_agents_md and rule.path.name == CORE_KNOWLEDGE_RULE:
        return False
    if not rule.targets:
        return True
    return adapter in rule.targets


def rules_for_adapter(repo_home: Path, adapter_id: str, *, for_agents_md: bool = False) -> list[ParsedRule]:
    return [
        rule
        for rule in collect_parsed_rules(repo_home)
        if rule_applies(rule, adapter_id, for_agents_md=for_agents_md)
    ]


def build_team_rules_block(rules: list[ParsedRule]) -> str | None:
    if not rules:
        return None
    sections: list[str] = [
        TEAM_RULES_MARKER_BEGIN,
        "## Team rules (shared-agents)",
        "",
        "Managed by `sa install` — edit `$SHARED_AGENTS_HOME/rules/` or "
        "`$SHARED_AGENTS_HOME/team/rules/` (like skills), not this block.",
        "",
    ]
    for rule in rules:
        sections.extend(
            [
                f"### {rule.title}",
                "",
                f"<!-- shared-agents:rule:{rule.rule_id}:begin -->",
                rule.body,
                f"<!-- shared-agents:rule:{rule.rule_id}:end -->",
                "",
            ]
        )
    sections.append(TEAM_RULES_MARKER_END)
    return "\n".join(sections).rstrip() + "\n"


def team_rules_block(repo_home: Path, adapter_id: str) -> str | None:
    rules = rules_for_adapter(repo_home, adapter_id, for_agents_md=True)
    return build_team_rules_block(rules)


def file_has_marker(path: Path, begin: str) -> bool:
    return path.is_file() and begin in path.read_text(encoding="utf-8")


def merge_marker_block(
    target: Path,
    begin: str,
    end: str,
    block: str,
    *,
    dry_run: bool = False,
) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    if begin in existing and end in existing:
        start = existing.index(begin)
        stop = existing.index(end) + len(end)
        updated = existing[:start].rstrip() + "\n\n" + block + "\n" + existing[stop:].lstrip()
    elif existing.strip():
        updated = existing.rstrip() + "\n\n" + block + "\n"
    else:
        updated = block + "\n"
    if not dry_run:
        target.write_text(updated, encoding="utf-8")


def remove_marker_block(
    target: Path,
    begin: str,
    end: str,
    *,
    dry_run: bool = False,
) -> bool:
    if not target.is_file() or begin not in target.read_text(encoding="utf-8"):
        return False
    text = target.read_text(encoding="utf-8")
    if begin not in text or end not in text:
        return False
    start = text.index(begin)
    stop = text.index(end) + len(end)
    updated = (text[:start].rstrip() + "\n" + text[stop:].lstrip()).strip()
    if dry_run:
        return True
    if updated:
        target.write_text(updated + "\n", encoding="utf-8")
    else:
        target.unlink(missing_ok=True)
    return True


def agents_md_paths(tool: dict, home: str) -> list[Path]:
    paths: list[Path] = []
    for key in ("agents_md", "alt_agents_md"):
        if tool.get(key):
            paths.append(expand(tool[key]))
    for alt in tool.get("alt_rules") or []:
        paths.append(expand(alt))
    env_home = tool.get("env_home")
    if env_home and os.environ.get(env_home):
        paths.append(expand(os.path.join(os.environ[env_home], "AGENTS.md")))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def install_team_rules_to_path(
    target: Path,
    repo_home: Path,
    adapter_id: str,
    *,
    dry_run: bool = False,
) -> str | None:
    block = team_rules_block(repo_home, adapter_id)
    if block:
        if dry_run:
            return f"[dry-run] would merge team rules into {target}"
        merge_marker_block(
            target,
            TEAM_RULES_MARKER_BEGIN,
            TEAM_RULES_MARKER_END,
            block,
            dry_run=False,
        )
        return f"Merged team rules into {target}"
    if file_has_marker(target, TEAM_RULES_MARKER_BEGIN):
        if dry_run:
            return f"[dry-run] would remove team rules block from {target}"
        remove_marker_block(
            target,
            TEAM_RULES_MARKER_BEGIN,
            TEAM_RULES_MARKER_END,
            dry_run=False,
        )
        return f"Removed team rules block from {target}"
    return None


def collect_rule_symlink_pairs(repo_home: Path) -> list[tuple[Path, str]]:
    pairs: list[tuple[Path, str]] = []
    for rule in collect_parsed_rules(repo_home):
        if rule_applies(rule, "cursor"):
            pairs.append((rule.path, rule.source_label))
    return pairs


def check_rules(repo_home: Path, manifest: dict) -> list[str]:
    issues: list[str] = []
    rule_pairs = collect_rule_symlink_pairs(repo_home)
    if not rule_pairs:
        return issues
    for entry in manifest.get("shared", {}).get("rule_dirs", []):
        dest_root = expand(entry["path"])
        if not dest_root.is_dir():
            issues.append(f"Rule dir missing: {dest_root}")
            continue
        for rule, _label in rule_pairs:
            dest = dest_root / rule.name
            if not dest.exists():
                issues.append(f"Rule not linked: {dest}")
            elif dest.is_symlink() and dest.resolve() != rule.resolve():
                issues.append(f"Rule symlink stale: {dest}")
            elif not dest.is_symlink() and dest.is_file():
                issues.append(
                    f"Rule exists as regular file (skipped to preserve edits): {dest}"
                )
    return issues


def symlink_rules(
    repo_home: Path, rule_dirs: list[dict], *, dry_run: bool = False
) -> list[str]:
    messages: list[str] = []
    rule_pairs = collect_rule_symlink_pairs(repo_home)
    if not rule_pairs:
        return messages

    for entry in rule_dirs:
        dest_root = expand(entry["path"])
        if not dry_run:
            dest_root.mkdir(parents=True, exist_ok=True)
        for rule, src_label in rule_pairs:
            dest = dest_root / rule.name
            if dry_run:
                messages.append(
                    f"[dry-run] would link {rule.name} ({src_label}) → {dest_root}"
                )
                continue
            if dest.is_symlink():
                dest.unlink()
            elif dest.exists() and not dest.is_symlink():
                messages.append(
                    f"Skipped rule {rule.name} — {dest} exists (not a symlink; preserving local edits)"
                )
                continue
            dest.symlink_to(rule.resolve())
        if not dry_run and rule_pairs:
            note = entry.get("note", "")
            messages.append(f"Rules → {dest_root}" + (f" ({note})" if note else ""))
    return messages


def _rule_source_roots(repo_home: Path) -> list[Path]:
    roots: list[Path] = []
    core = repo_home / "rules"
    if core.is_dir():
        roots.append(core.resolve())
    team = repo_home / "team" / "rules"
    if team.is_dir():
        roots.append(team.resolve())
    legacy = team / "approved"
    if legacy.is_dir():
        roots.append(legacy.resolve())
    return roots


def symlink_points_to_shared_rules(dest: Path, source_roots: list[Path]) -> bool:
    if not dest.is_symlink():
        return False
    try:
        target = dest.resolve()
    except OSError:
        return False
    for root in source_roots:
        if target == root or root in target.parents:
            return True
    return False


def uninstall_rule_symlinks(
    repo_home: Path, rule_dirs: list[dict], *, dry_run: bool = False
) -> list[str]:
    messages: list[str] = []
    source_roots = _rule_source_roots(repo_home)
    if not source_roots:
        return messages

    seen_dest: set[Path] = set()
    for entry in rule_dirs:
        dest_root = expand(entry["path"])
        if not dest_root.is_dir():
            continue
        for dest in sorted(dest_root.glob("*.mdc")):
            if dest in seen_dest:
                continue
            if not symlink_points_to_shared_rules(dest, source_roots):
                continue
            seen_dest.add(dest)
            if dry_run:
                messages.append(f"[dry-run] would remove rule symlink {dest}")
            else:
                dest.unlink()
                messages.append(f"Removed rule symlink {dest}")
    return messages


def uninstall_team_rules_from_tool(
    tool: dict, repo_home: Path, *, dry_run: bool = False
) -> list[str]:
    messages: list[str] = []
    home = str(repo_home)
    seen: set[Path] = set()
    for path in agents_md_paths(tool, home):
        if path in seen:
            continue
        seen.add(path)
        if dry_run:
            if file_has_marker(path, TEAM_RULES_MARKER_BEGIN):
                messages.append(f"[dry-run] would remove team rules block from {path}")
            continue
        if remove_marker_block(
            path,
            TEAM_RULES_MARKER_BEGIN,
            TEAM_RULES_MARKER_END,
            dry_run=False,
        ):
            messages.append(f"Removed team rules block from {path}")
    return messages
