#!/usr/bin/env python3
"""Learning usage tracking: machine-written usage events, no review workflow.

Layout (per approved learning):
  learnings/approved/by-domain/<domain>/<id>/learning.md   (human-gated, sa review)
  learnings/approved/by-domain/<domain>/<id>/usage.yaml    (machine-writable)

Events (5 types, 2 report domains):
  knowledge : opened (1 per task), used, not_used, outdated (+ note)
  telemetry : read (raw file reads, never mixed into knowledge metrics)

Flow:
  sa learning report  -> local buffer learnings/.usage-local.yaml (zero git)
  sa learning push    -> append to per-learning usage.yaml, single commit, push
  sa learning status  -> aggregates + flags (rule candidates, orphans, unresolved)
  sa learning migrate -> one-time: flat approved/*.md -> <id>/learning.md + usage.yaml

usage.yaml is line-based YAML: event lines are JSON (valid YAML flow maps),
so no PyYAML dependency. Totals are always computed from events + summary;
nothing is incremented in place.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sa_config import (
    approved_dir,
    core_home,
    git_data_home,
    index_path,
    learnings_root,
)
from sa_ui import (
    bold,
    cyan,
    plain,
    say_info,
    say_success,
    say_warn,
    say_warn_stderr,
    run_cli_main,
)

EVENTS = ("read", "opened", "used", "not_used", "outdated")
VERDICTS = ("used", "not_used", "outdated")
UNRESOLVED_DAYS = 7
RULE_CANDIDATE_OPENED = 15
RULE_CANDIDATE_MACHINES = 5
LOW_FIT_VERDICTS = 5

SECRET_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"password\s*[:=]",
        r"api[_-]?key\s*[:=]",
        r"secret\s*[:=]",
        r"access[_-]?token\s*[:=]",
        r"AKIA[0-9A-Z]{16}",
        r"ghp_[A-Za-z0-9]{20,}",
        r"sk-[A-Za-z0-9]{20,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    )
]

USAGE_VERSION = 1
MACHINE_WRITABLE = ("usage.yaml", "usage-orphan.yaml")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def this_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def event_month(ts: str) -> str:
    return (ts or "")[:7]


def machine_id(agent: str | None) -> str:
    host = socket.gethostname().split(".")[0] or "unknown"
    return f"{host}-{agent}" if agent else host


def secret_hit(event: dict) -> str | None:
    for field in ("note", "task", "project"):
        value = str(event.get(field) or "")
        if not value:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                return field
    return None


def run_git(
    cwd: Path,
    args: list[str],
    *,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )
    if check and result.returncode != 0:
        err = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {err}")
    return result


# ---------------------------------------------------------------- paths


def lr_root(home: Path) -> Path:
    return learnings_root(home)


def buffer_path(home: Path) -> Path:
    return lr_root(home) / ".usage-local.yaml"


def orphan_path(home: Path) -> Path:
    return lr_root(home) / "usage-orphan.yaml"


def repo_home(home: Path) -> Path:
    return git_data_home(home)


def is_git_repo(home: Path) -> bool:
    return (repo_home(home) / ".git").is_dir()


def ensure_gitignore(home: Path) -> bool:
    """Keep the machine-written local buffer out of the team repo (retroactive
    for existing teams; new teams get it from the scaffold)."""
    if not is_git_repo(home):
        return False
    gi = repo_home(home) / ".gitignore"
    entry = ".usage-local.yaml"
    try:
        text = gi.read_text(encoding="utf-8") if gi.is_file() else ""
    except OSError:
        return False
    if any(line.strip() == entry for line in text.splitlines()):
        return False
    gi.write_text((text + "\n" if text and not text.endswith("\n") else text) + entry + "\n", encoding="utf-8")
    return True


# ------------------------------------------------------------- index.yaml

def index_entries(home: Path) -> list[tuple[str, str]]:
    """(id, file-rel-to-learnings-root) pairs from index.yaml."""
    path = index_path(home)
    if not path.is_file():
        return []
    entries: list[tuple[str, str]] = []
    current_id: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s+-\s+id:\s*(\S+)", line)
        if m:
            current_id = m.group(1)
            continue
        m = re.match(r"^\s+file:\s*(\S+)", line)
        if m and current_id:
            entries.append((current_id, m.group(1)))
            current_id = None
    return entries


def find_usage_path(home: Path, learning_id: str) -> Path | None:
    """usage.yaml path for a learning id (None when unknown or unmigrated).
    Only the folder layout (<id>/learning.md) is resolvable; flat legacy
    files have no per-learning folder, so their events are quarantined
    until `sa learning migrate` runs."""
    for entry_id, rel in index_entries(home):
        if entry_id == learning_id:
            if not rel.endswith("/learning.md"):
                return None
            learning_md = lr_root(home) / rel
            if learning_md.is_file():
                return learning_md.parent / "usage.yaml"
    return None


def unmigrated_count(home: Path) -> int:
    """Approved index entries still on the flat legacy layout."""
    n = 0
    for _id, rel in index_entries(home):
        if not rel.endswith("/learning.md"):
            n += 1
    return n


# -------------------------------------------------------------- usage files


def _usage_file(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines() if path.is_file() else []


def read_events(path: Path) -> list[dict]:
    """Event dicts from a usage/buffer file (lines under `events:`)."""
    events: list[dict] = []
    in_events = False
    for line in _usage_file(path):
        if re.match(r"^events:\s*$", line):
            in_events = True
            continue
        if in_events:
            line_s = line.strip()
            if line_s.startswith("- "):
                try:
                    events.append(json.loads(line_s[2:]))
                except json.JSONDecodeError:
                    continue
            elif line_s and not line_s.startswith("#"):
                in_events = False
    return events


def _parse_summary_block(lines: list[str]) -> dict[str, dict]:
    """Parse a `summary:` block (JSON bucket lines, legacy plain-kv fallback)."""
    summary: dict[str, dict] = {}
    in_summary = False
    for line in lines:
        if re.match(r"^summary:\s*$", line):
            in_summary = True
            continue
        if in_summary:
            m = re.match(r'^\s*"(\d{4}-\d{2})":\s*(\{.*\})\s*$', line)
            if m:
                month, body = m.groups()
                try:
                    summary[month] = json.loads(body)
                except json.JSONDecodeError:
                    counts = {}
                    for part in body.strip("{}").split(","):
                        if ":" in part:
                            k, v = part.split(":", 1)
                            try:
                                counts[k.strip()] = int(v.strip())
                            except ValueError:
                                pass
                    summary[month] = counts
            elif line.strip() and not line.startswith("  "):
                in_summary = False
    return summary


def read_summary(path: Path) -> dict[str, dict]:
    """Month -> bucket {event: n, last_used?, machines?} from `summary:`."""
    return _parse_summary_block(_usage_file(path))


def _summary_from_text(text: str) -> dict[str, dict]:
    return _parse_summary_block(text.splitlines())


def _merge_summary_buckets(a: dict[str, dict], b: dict[str, dict]) -> dict[str, dict]:
    """Union of two summary blocks: sum counts, max last_used, union machines."""
    out: dict[str, dict] = {}
    for month in set(a) | set(b):
        ba, bb = a.get(month, {}), b.get(month, {})
        bucket: dict = {k: int(ba.get(k, 0) or 0) + int(bb.get(k, 0) or 0) for k in EVENTS}
        last_used = max(str(ba.get("last_used") or ""), str(bb.get("last_used") or ""))
        if last_used:
            bucket["last_used"] = last_used
        machines = sorted(
            {str(x) for x in (ba.get("machines") or [])}
            | {str(x) for x in (bb.get("machines") or [])}
        )
        if machines:
            bucket["machines"] = machines
        out[month] = bucket
    return out


def write_usage_file(path: Path, *, learning_id: str, events: list[dict],
                     summary: dict[str, dict[str, int]],
                     tracking_since: str | None = None,
                     last_compact: str | None = None) -> None:
    lines = [f"version: {USAGE_VERSION}", f"id: {learning_id}"]
    if tracking_since:
        lines.append(f"tracking_since: {tracking_since}")
    if last_compact:
        lines.append(f"last_compact: {last_compact}")
    if summary:
        lines.append("summary:")
        for month in sorted(summary):
            lines.append(f'  "{month}": {json.dumps(summary[month], ensure_ascii=False)}')
    lines.append("events:")
    for event in events:
        lines.append(f"  - {json.dumps(event, ensure_ascii=False)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def init_usage_file(folder: Path, learning_id: str) -> Path:
    path = folder / "usage.yaml"
    if not path.is_file():
        write_usage_file(
            path,
            learning_id=learning_id,
            events=[],
            summary={},
            tracking_since=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        )
    return path


def _buffer_events(path: Path) -> list[dict]:
    return read_events(path)


def _write_buffer(path: Path, events: list[dict]) -> None:
    if not events:
        if path.is_file():
            path.unlink()
        return
    lines = [f"version: {USAGE_VERSION}", "events:"]
    for event in events:
        lines.append(f"  - {json.dumps(event, ensure_ascii=False)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ report


def cmd_report(args: argparse.Namespace) -> int:
    home = Path(args.home) if args.home else core_home()
    learning_id = args.id
    event = args.event
    if event not in EVENTS:
        say_warn_stderr(f"Unknown event: {event} (allowed: {', '.join(EVENTS)})")
        return 1
    if event == "outdated" and not args.note:
        say_warn_stderr("outdated requires --note (what is stale?)")
        return 1

    entry = {
        "ts": now_iso(),
        "eid": uuid.uuid4().hex[:8],
        "learning": learning_id,
        "event": event,
        "machine": machine_id(args.agent),
    }
    if args.project:
        entry["project"] = args.project
    if args.task:
        entry["task"] = args.task
    if args.note:
        entry["note"] = args.note

    hit = secret_hit(entry)
    if hit:
        say_warn_stderr(
            f"Blocked usage event ({hit} looks like a secret). Not recorded. eid={entry['eid']}"
        )
        return 1

    # opened: max 1 per (learning, task) — skip when task unknown.
    # Stored per-learning events carry no `learning` field (push strips it),
    # so dedupe against the learning's own file by task, and the buffer by id.
    if event == "opened" and args.task:
        target = find_usage_path(home, learning_id)
        if target is not None:
            for old in read_events(target):
                if old.get("event") == "opened" and old.get("task") == args.task:
                    say_info(f"opened already recorded for task '{args.task}' — skipped")
                    return 0
        for old in read_events(buffer_path(home)):
            if (
                old.get("learning") == learning_id
                and old.get("event") == "opened"
                and old.get("task") == args.task
            ):
                say_info(f"opened already recorded for task '{args.task}' — skipped")
                return 0

    path = buffer_path(home)
    events = _buffer_events(path)
    events.append(entry)
    _write_buffer(path, events)
    say_success(
        f"usage: buffered {event} {learning_id} ({path.name}, "
        f"{len(events)} pending — flushed by sa sync / sa learning push)"
    )
    return 0


# -------------------------------------------------------------------- push


def compact_usage(path: Path, *, quiet: bool = False) -> bool:
    """Move raw events of finished months into the summary block."""
    if not path.is_file():
        return False
    lines = _usage_file(path)
    header: dict[str, str] = {}
    for line in lines:
        m = re.match(r"^(version|id|tracking_since|last_compact):\s*(\S+)", line)
        if m:
            header[m.group(1)] = m.group(2)
    events = read_events(path)
    summary = read_summary(path)
    month = this_month()
    old = [e for e in events if event_month(str(e.get("ts", ""))) != month]
    if not old:
        return False
    new_buckets: dict[str, dict] = {}
    for e_month in {event_month(str(e.get("ts", ""))) for e in old}:
        month_events = [
            e for e in old if event_month(str(e.get("ts", ""))) == e_month
        ]
        bucket: dict = {k: 0 for k in EVENTS}
        for e in month_events:
            name = str(e.get("event", ""))
            if name in bucket:
                bucket[name] += 1
        used_ts = sorted(
            str(e.get("ts", "")) for e in month_events if e.get("event") == "used"
        )
        if used_ts:
            bucket["last_used"] = used_ts[-1]
        machines = sorted({str(e.get("machine", "?")) for e in month_events})
        if machines:
            bucket["machines"] = machines
        new_buckets[e_month] = bucket
    summary = _merge_summary_buckets(summary, new_buckets)
    keep = [e for e in events if e not in old]
    write_usage_file(
        path,
        learning_id=header.get("id", ""),
        events=keep,
        summary=summary,
        tracking_since=header.get("tracking_since"),
        last_compact=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )
    if not quiet:
        say_info(f"compact: {len(old)} old event(s) -> summary in {path}")
    return True


def _all_usage_files(home: Path) -> list[Path]:
    return sorted((approved_dir(home) / "by-domain").glob("*/*/usage.yaml"))


def _repo_remote(repo: Path) -> bool:
    remote = run_git(repo, ["remote", "get-url", "origin"], check=False)
    return remote.returncode == 0 and bool(remote.stdout.strip())


def _repo_ahead(repo: Path) -> int:
    """Local commits not yet on origin/<branch> (0 when no upstream)."""
    branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"], check=False)
    name = branch.stdout.strip() if branch.returncode == 0 else ""
    if not name or name == "HEAD":
        return 0
    rev = run_git(repo, ["rev-list", "--count", f"origin/{name}..HEAD"], check=False)
    if rev.returncode != 0:
        return 0
    return int(rev.stdout.strip() or 0)


def _push_with_rebase(repo: Path) -> bool:
    """Push; on rejection rebase (union-resolve append-only conflicts) and retry."""
    push = run_git(repo, ["push"], check=False)
    if push.returncode == 0:
        return True
    rebase = run_git(repo, ["pull", "--rebase"], check=False)
    if rebase.returncode == 0:
        return run_git(repo, ["push"], check=False).returncode == 0
    if _auto_resolve_usage_conflicts(repo) and run_git(
        repo, ["rebase", "--continue"], check=False, env={"GIT_EDITOR": "true"}
    ).returncode == 0:
        # Append-only conflict: union-resolved (eid dedup), continue.
        return run_git(repo, ["push"], check=False).returncode == 0
    run_git(repo, ["rebase", "--abort"], check=False)
    return False


def cmd_push(args: argparse.Namespace) -> int:
    home = Path(args.home) if args.home else core_home()
    quiet = args.quiet
    buf = buffer_path(home)
    pending = _buffer_events(buf)

    repo = repo_home(home) if is_git_repo(home) and not args.no_git else None
    has_remote = bool(repo) and _repo_remote(repo)

    if not pending:
        # Publish leftover local usage commits (previous push failed).
        if repo and has_remote and _repo_ahead(repo) > 0:
            if _push_with_rebase(repo):
                if not quiet:
                    say_success("usage: published leftover local commit(s)")
            else:
                say_warn_stderr("usage: leftover local commit, push failed — retry sa learning push")
                return 1
        elif not quiet:
            say_info("usage: nothing to push (buffer empty)")
        return 0

    # Events stay in the buffer until they are persisted to the on-disk files.
    orph = orphan_path(home)
    prev_orphans = read_events(orph)
    orph_pending = list(prev_orphans)
    changed: list[Path] = []

    by_learning: dict[str, list[dict]] = {}
    for entry in pending:
        target = find_usage_path(home, str(entry.get("learning", "")))
        if target is None:
            orph_pending.append(entry)
            continue
        by_learning.setdefault(str(entry.get("learning", "")), []).append(entry)

    if len(orph_pending) > len(prev_orphans):
        write_usage_file(orph, learning_id="(orphan)", events=orph_pending, summary={})
        changed.append(orph)

    for learning_id, entries in by_learning.items():
        path = find_usage_path(home, learning_id)
        if path is None:
            continue
        if not path.is_file():
            path = init_usage_file(path.parent, learning_id)
        known_ids = {str(e.get("eid")) for e in read_events(path)}
        fresh = [e for e in entries if str(e.get("eid")) not in known_ids]
        if not fresh:
            continue
        events = read_events(path) + [
            {k: v for k, v in e.items() if k != "learning"} for e in fresh
        ]
        write_usage_file(
            path,
            learning_id=learning_id,
            events=events,
            summary=read_summary(path),
            tracking_since=_header_value(path, "tracking_since"),
        )
        compact_usage(path, quiet=True)
        changed.append(path)

    if not changed:
        # Events already in local files; still publish a leftover commit.
        if repo and has_remote and _repo_ahead(repo) > 0:
            if _push_with_rebase(repo):
                _write_buffer(buf, [])
                if not quiet:
                    say_success("usage: all events already on remote (eid dedup); leftover commit pushed")
                return 0
            say_warn_stderr("usage: push failed — events stay in buffer, retry sa learning push")
            return 1
        _write_buffer(buf, [])
        if not quiet:
            say_info("usage: all events already on remote (eid dedup)")
        return 0

    exit_code = 0
    if repo:
        if ensure_gitignore(home):
            changed.append(repo / ".gitignore")
        for p in changed:
            run_git(repo, ["add", str(p)], check=False)
        staged = run_git(repo, ["diff", "--cached", "--quiet"], check=False)
        if staged.returncode != 0:
            msg = f"chore(learnings): usage events ({len(pending)} buffered)"
            run_git(repo, ["commit", "-m", msg], check=False)
            if has_remote:
                if not _push_with_rebase(repo):
                    say_warn_stderr(
                        "usage: committed locally, remote not updated — events stay in buffer, retry sa learning push"
                    )
                    exit_code = 1
            else:
                if not quiet:
                    say_info("usage: no git remote — committed locally only")
    # Keep the buffer until the events are published, so a failed push is
    # retried on the next sa sync / sa learning push (eid dedup is idempotent).
    if exit_code == 0 or not has_remote:
        _write_buffer(buf, [])
    if not quiet:
        if exit_code == 0:
            say_success(f"usage: pushed {len(pending)} event(s) to {len(changed)} file(s)")
        else:
            say_warn(f"usage: {len(pending)} event(s) committed locally, remote not updated (see warnings)")
    return exit_code


def _events_from_text(text: str) -> list[dict]:
    events: list[dict] = []
    in_events = False
    for line in text.splitlines():
        if re.match(r"^events:\s*$", line):
            in_events = True
            continue
        if in_events:
            s = line.strip()
            if s.startswith("- "):
                try:
                    events.append(json.loads(s[2:]))
                except json.JSONDecodeError:
                    pass
            elif s and not s.startswith("  "):
                in_events = False
    return events


def _auto_resolve_usage_conflicts(repo: Path) -> bool:
    """Rebase conflict on append-only usage files: keep the union of events
    (dedup by eid) and merge both summary blocks, so two machines appending
    to the same file never lose data."""
    res = run_git(repo, ["diff", "--name-only", "--diff-filter=U"], check=False)
    if res.returncode != 0:
        return False
    conflicted = [l for l in res.stdout.splitlines() if l.strip()]
    for rel in conflicted:
        # Only machine-written usage files may be union-resolved; anything
        # else (e.g. index.yaml) must not be rewritten in usage format.
        if Path(rel).name not in MACHINE_WRITABLE:
            return False
        ours = run_git(repo, ["show", f":2:{rel}"], check=False)
        theirs = run_git(repo, ["show", f":3:{rel}"], check=False)
        ours_text = ours.stdout if ours.returncode == 0 else ""
        theirs_text = theirs.stdout if theirs.returncode == 0 else ""
        if not ours_text and not theirs_text:
            return False
        events = _events_from_text(ours_text) + _events_from_text(theirs_text)
        seen: set[str] = set()
        unique: list[dict] = []
        for e in events:
            key = str(e.get("eid", ""))
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            unique.append(e)
        base = ours_text or theirs_text
        header = re.search(r"^id:\s*(\S+)", base, re.MULTILINE)
        learning_id = header.group(1) if header else "(orphan)"
        tracking = re.search(r"^tracking_since:\s*(\S+)", base, re.MULTILINE)
        summary = _merge_summary_buckets(
            _summary_from_text(ours_text), _summary_from_text(theirs_text)
        )
        write_usage_file(
            repo / rel,
            learning_id=learning_id,
            events=unique,
            summary=summary,
            tracking_since=tracking.group(1) if tracking else None,
        )
        run_git(repo, ["add", str(repo / rel)], check=False)
    return True


def _header_value(path: Path, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1) if m else None


# ------------------------------------------------------------------ status


def _learning_counts(path: Path) -> dict:
    events = read_events(path)
    summary = read_summary(path)
    counts = {e: 0 for e in EVENTS}
    last_used: str | None = None
    machines: set[str] = set()
    verdict_tasks: set[str] = set()
    opened_tasks: dict[str, str] = {}
    for e in events:
        name = str(e.get("event", ""))
        if name in counts:
            counts[name] += 1
        machines.add(str(e.get("machine", "?")))
        ts = str(e.get("ts", ""))
        task = e.get("task")
        if name == "used" and ts > (last_used or ""):
            last_used = ts
        if name in VERDICTS and task:
            verdict_tasks.add(str(task))
        if name == "opened" and task:
            opened_tasks[str(task)] = ts
    for bucket in summary.values():
        for name in EVENTS:
            counts[name] += int(bucket.get(name, 0) or 0)
        bucket_last = str(bucket.get("last_used") or "")
        if bucket_last and bucket_last > (last_used or ""):
            last_used = bucket_last
        machines.update(str(x) for x in (bucket.get("machines") or []))
    unresolved = sorted(set(opened_tasks) - verdict_tasks)
    # Age unresolved: only count entries newer than UNRESOLVED_DAYS
    cutoff = (datetime.now(timezone.utc).timestamp() - UNRESOLVED_DAYS * 86400)
    fresh_unresolved = [
        t for t in unresolved
        if _ts_to_ts(opened_tasks[t]) > cutoff
    ]
    return {
        "counts": counts,
        "last_used": last_used,
        "machines": len(machines),
        "unresolved": fresh_unresolved,
        "raw_events": len(events),
    }


def _ts_to_ts(value: str) -> float:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _flags(counts: dict, machines: int, unresolved: list) -> list[str]:
    flags: list[str] = []
    if counts["outdated"] >= 1:
        flags.append("OUTDATED")
    verdicts = counts["used"] + counts["not_used"]
    if verdicts >= LOW_FIT_VERDICTS and counts["used"] / verdicts < 0.5:
        flags.append("LOW-FIT")
    if counts["opened"] >= RULE_CANDIDATE_OPENED and machines >= RULE_CANDIDATE_MACHINES:
        flags.append("RULE-CANDIDATE")
    if unresolved:
        flags.append(f"UNRESOLVED({len(unresolved)})")
    return flags


def cmd_status(args: argparse.Namespace) -> int:
    home = Path(args.home) if args.home else core_home()
    rows: list[dict] = []
    files = _all_usage_files(home)
    for path in files:
        learning_id = _header_value(path, "id") or path.parent.name
        counts = _learning_counts(path)
        c = counts["counts"]
        rows.append(
            {
                "id": learning_id,
                "file": str(path),
                "tracked_since": _header_value(path, "tracking_since"),
                "counts": c,
                "last_used": counts["last_used"],
                "machines": counts["machines"],
                "unresolved": counts["unresolved"],
                "flags": _flags(c, counts["machines"], counts["unresolved"]),
            }
        )

    buf = _buffer_events(buffer_path(home))
    orphans = read_events(orphan_path(home))
    rule_candidates = [r["id"] for r in rows if "RULE-CANDIDATE" in r["flags"]]
    outdated = [r["id"] for r in rows if "OUTDATED" in r["flags"]]

    if args.json:
        payload = {
            "learnings": rows,
            "buffer_pending": len(buf),
            "orphans": orphans,
            "rule_candidates": rule_candidates,
            "outdated": outdated,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if not rows and not buf and not orphans:
        say_info("usage: no tracked learnings yet (run: sa learning migrate)")
        return 0

    print(bold(cyan("Learning usage")))
    print()
    cols = [
        "learning".ljust(44),
        "open".rjust(4),
        "used".rjust(4),
        "nused".rjust(5),
        "outdt".rjust(5),
        "reads".rjust(5),
        "mach".rjust(4),
        "last_used".ljust(10),
        "flags",
    ]
    print("  " + plain(" ".join(cols)))
    for r in rows:
        c = r["counts"]
        flag_txt = ", ".join(r["flags"]) if r["flags"] else plain("\u2014")
        last = (r["last_used"] or "\u2014")[:10].ljust(10)
        print(
            "  "
            + r["id"][:44].ljust(44)
            + " %4d %4d" % (c["opened"], c["used"])
            + " %5d %5d %5d" % (c["not_used"], c["outdated"], c["read"])
            + " %4d %s %s" % (r["machines"], last, flag_txt)
        )
    print()
    print(plain("  domain: opened/used/not_used/outdated = knowledge · reads = agent telemetry"))
    print(
        plain(
            "  flags: OUTDATED = stale content · LOW-FIT = used < 50% · "
            "RULE-CANDIDATE = too general, move to team/rules · UNRESOLVED = verdicts missing"
        )
    )
    if rule_candidates:
        print()
        for rid in rule_candidates:
            say_warn(f"{rid}: rule candidate (used by {RULE_CANDIDATE_MACHINES}+ machines) → sa rule new + archive")
    if buf:
        say_warn(f"usage buffer: {len(buf)} event(s) not pushed → sa learning push")
    if orphans:
        say_warn(f"orphan events: {len(orphans)} (learning removed/moved or unmigrated) → {orphan_path(home).name}")
    unmigrated = unmigrated_count(home)
    if unmigrated:
        say_warn(f"{unmigrated} learning(s) still on flat legacy layout → sa learning migrate")
    return 0


# ------------------------------------------------------------------ events


def cmd_events(args: argparse.Namespace) -> int:
    home = Path(args.home) if args.home else core_home()
    target = find_usage_path(home, args.id)
    if target is None:
        say_warn_stderr(f"No approved learning with id: {args.id}")
        return 1
    events = read_events(target)
    buffered = [
        e for e in _buffer_events(buffer_path(home)) if e.get("learning") == args.id
    ]
    for e in events:
        print(json.dumps(e, ensure_ascii=False))
    for e in buffered:
        print(json.dumps(e, ensure_ascii=False) + "  (buffered, not pushed)")
    if not events and not buffered:
        say_info(f"no usage events for {args.id}")
    return 0


# ----------------------------------------------------------------- migrate


def cmd_migrate(args: argparse.Namespace) -> int:
    home = Path(args.home) if args.home else core_home()
    root = lr_root(home)
    index = index_path(home)
    moved = 0
    skipped = 0
    remap: list[tuple[str, str]] = []

    for entry_id, rel in index_entries(home):
        src = root / rel
        if not src.is_file() or src.name == "learning.md":
            continue
        folder = src.parent / src.stem
        if (folder / "learning.md").is_file():
            skipped += 1
            continue
        if not rel.endswith(".md"):
            skipped += 1
            continue
        new_rel = f"{rel[:-3]}/learning.md"
        if args.dry_run:
            say_info(f"[dry-run] {rel} -> {new_rel} + usage.yaml")
            moved += 1
            continue
        folder.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(folder / "learning.md"))
        init_usage_file(folder, entry_id)
        remap.append((rel, new_rel))
        moved += 1

    if remap and index.is_file():
        text = index.read_text(encoding="utf-8")
        for old_rel, new_rel in remap:
            text = text.replace(f"file: {old_rel}", f"file: {new_rel}")
        index.write_text(text, encoding="utf-8")

    if is_git_repo(home) and moved and not args.dry_run and not args.no_git:
        repo = repo_home(home)
        if ensure_gitignore(home):
            run_git(repo, ["add", str(repo / ".gitignore")], check=False)
        try:
            rel_prefix = lr_root(home).relative_to(repo).as_posix()
        except ValueError:
            rel_prefix = "."
        run_git(repo, ["add", "-A", rel_prefix], check=False)
        staged = run_git(repo, ["diff", "--cached", "--quiet"], check=False)
        if staged.returncode != 0:
            run_git(
                repo,
                ["commit", "-m", "chore(learnings): migrate approved learnings to per-learning folders"],
                check=False,
            )
            say_info("committed migration (push when ready)")

    if args.dry_run:
        say_info(f"[dry-run] {moved} file(s) to migrate")
        return 0
    say_success(f"migrate: {moved} learning(s) moved, {skipped} already migrated")
    return 0


# ------------------------------------------------------------------ main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sa learning", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd")

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--home", help="SHARED_AGENTS_HOME (default: env/~)")
        p.add_argument("--quiet", action="store_true")

    p = sub.add_parser("report", help="Buffer a usage event (no git)")
    p.add_argument("--id", required=True, help="Learning id")
    p.add_argument("--event", required=True, choices=EVENTS)
    p.add_argument("--project")
    p.add_argument("--task", help="Task slug (dedupes opened per task)")
    p.add_argument("--note", help="Context (required for outdated)")
    p.add_argument("--agent", help="Agent/tool name (machine identity suffix)")
    p.add_argument("--home")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("push", help="Flush buffer into per-learning usage.yaml + commit/push")
    p.add_argument("--no-git", action="store_true", help="File changes only, no commit/push")
    common(p)
    p.set_defaults(func=cmd_push)

    p = sub.add_parser("status", help="Aggregates + flags (knowledge vs telemetry)")
    p.add_argument("--json", action="store_true")
    common(p)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("events", help="Raw events for one learning")
    p.add_argument("id")
    p.add_argument("--home")
    p.set_defaults(func=cmd_events)

    p = sub.add_parser("migrate", help="One-time: flat approved/*.md -> <id>/learning.md + usage.yaml")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-git", action="store_true")
    common(p)
    p.set_defaults(func=cmd_migrate)

    p = sub.add_parser("compact", help="Fold finished months into summary blocks")
    common(p)
    p.set_defaults(func=cmd_compact)

    return parser


def cmd_compact(args: argparse.Namespace) -> int:
    home = Path(args.home) if args.home else core_home()
    n = 0
    for path in _all_usage_files(home):
        if compact_usage(path, quiet=True):
            n += 1
    say_info(f"compact: {n} file(s) updated")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "cmd", None):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    run_cli_main(main)
