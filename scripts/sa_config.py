"""Load config.local.yaml and resolve core vs team data paths (stdlib only)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

CONFIG_FILENAME = "config.local.yaml"
TEAM_DIRNAME = "team"
CONFIG_VERSION = 1


def expand(path: str | Path) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


def core_home() -> Path:
    return expand(os.environ.get("SHARED_AGENTS_HOME", "~/shared-agents"))


def config_path(core: Path | None = None) -> Path:
    root = core or core_home()
    return root / CONFIG_FILENAME


def _parse_yaml(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {"version": 1, "team": {}, "core": {}}
    section: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.endswith(":") and not line.startswith("-"):
            section = line[:-1].strip()
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if value in {"null", "~", ""}:
            value = ""
        if section == "team" and key == "remote":
            out.setdefault("team", {})["remote"] = value or None
        elif section == "core" and key == "remote":
            out.setdefault("core", {})["remote"] = value or None
    return out


def load_config(core: Path | None = None) -> dict[str, Any] | None:
    path = config_path(core)
    if not path.is_file():
        return None
    try:
        return _parse_yaml(path.read_text(encoding="utf-8"))
    except OSError:
        return None


def team_remote(core: Path | None = None) -> str | None:
    cfg = load_config(core)
    if not cfg:
        return None
    team = cfg.get("team")
    if not isinstance(team, dict):
        return None
    remote = str(team.get("remote", "")).strip()
    return remote or None


def team_dir(core: Path | None = None) -> Path:
    return (core or core_home()) / TEAM_DIRNAME


def uses_team_data(core: Path | None = None) -> bool:
    root = core or core_home()
    if team_remote(root):
        return True
    td = team_dir(root)
    return (td / ".git").is_dir() or (td / "learnings").is_dir()


def learnings_root(core: Path | None = None) -> Path:
    root = core or core_home()
    if uses_team_data(root):
        return team_dir(root) / "learnings"
    return root / "learnings"


def skills_dirs(core: Path | None = None) -> list[Path]:
    root = core or core_home()
    dirs: list[Path] = []
    core_skills = root / "skills"
    if core_skills.is_dir():
        dirs.append(core_skills)
    team_skills = team_dir(root) / "skills"
    if team_skills.is_dir():
        dirs.append(team_skills)
    return dirs


def git_data_home(core: Path | None = None) -> Path:
    """Git repo root for learnings commit/push."""
    root = core or core_home()
    td = team_dir(root)
    if (td / ".git").is_dir():
        return td
    if team_remote(root):
        return td
    return root


def pending_dir(core: Path | None = None) -> Path:
    return learnings_root(core) / "pending"


def approved_dir(core: Path | None = None) -> Path:
    return learnings_root(core) / "approved"


def index_path(core: Path | None = None) -> Path:
    return learnings_root(core) / "index.yaml"


def write_config(
    core: Path,
    *,
    team_remote_url: str | None,
    core_remote: str | None = None,
) -> Path:
    lines = [
        f"version: {CONFIG_VERSION}",
        "core:",
        f"  home: {core}",
    ]
    if core_remote:
        lines.append(f"  remote: {core_remote}")
    lines.append("team:")
    if team_remote_url:
        lines.append(f"  remote: {team_remote_url}")
    else:
        lines.append("  remote: null")
    path = config_path(core)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def learnings_prefix_for_git(core: Path | None = None) -> str:
    """Path prefix under git_data_home for learnings/ in git commands."""
    root = core or core_home()
    data = git_data_home(root)
    lr = learnings_root(root)
    try:
        rel = lr.relative_to(data)
        return rel.as_posix()
    except ValueError:
        return "learnings"


def learnings_label(core: Path | None = None) -> str:
    """Human-readable learnings path for CLI messages (from $SHARED_AGENTS_HOME)."""
    root = core or core_home()
    prefix = learnings_prefix_for_git(root)
    if uses_team_data(root):
        return f"team/{prefix}/"
    return f"{prefix}/"


def check_team_setup(core: Path | None = None) -> list[str]:
    """Warnings for team/ layout, config, and legacy learnings/ in core home."""
    root = core or core_home()
    issues: list[str] = []
    remote = team_remote(root)
    td = team_dir(root)
    legacy = root / "learnings"

    if remote:
        if not td.is_dir():
            issues.append(
                "team.remote in config.local.yaml but team/ missing — run: sa bootstrap"
            )
        elif not (td / ".git").is_dir():
            issues.append(
                "team.remote set but team/ is not a git repository — run: sa bootstrap"
            )

    if legacy.is_dir():
        legacy_md = list(legacy.rglob("*.md"))
        index = legacy / "index.yaml"
        has_index_entries = False
        if index.is_file() and "id:" in index.read_text(encoding="utf-8"):
            has_index_entries = True
        if legacy_md or has_index_entries:
            issues.append(
                "Legacy learnings/ under $SHARED_AGENTS_HOME — run: sa team migrate "
                "(see docs/migration-team-data.md)"
            )
    return issues


def is_team_git_repo(repo: Path, core: Path | None = None) -> bool:
    root = core or core_home()
    try:
        return repo.resolve() == git_data_home(root).resolve() and uses_team_data(root)
    except OSError:
        return False
