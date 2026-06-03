#!/usr/bin/env python3
"""Interactive TUI for shared-agents install wizard (stdlib curses)."""

from __future__ import annotations

import curses
import os
import sys
from dataclasses import dataclass
from enum import Enum


class ShellRcState(str, Enum):
    CONFIGURED = "configured"
    NEEDS_CLI = "needs_cli"
    ASK = "ask"


@dataclass
class WizardChoices:
    home: str
    team_remote: str | None
    selected_tools: set[str]
    add_shell: bool
    run_setup: bool


@dataclass
class ToolRow:
    tool_id: str
    name: str
    status: str
    installed: bool


from sa_ui import UserCancelled

WizardCancelled = UserCancelled


def _getch(stdscr: curses.window) -> int:
    try:
        return stdscr.getch()
    except KeyboardInterrupt:
        raise UserCancelled from None


class WizardTuiFailed(Exception):
    pass


def tui_available() -> bool:
    if os.environ.get("SA_WIZARD_PLAIN", "").strip().lower() in {"1", "true", "yes"}:
        return False
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    term = os.environ.get("TERM", "")
    if not term or term == "dumb":
        return False
    if not sys.platform.startswith(("linux", "darwin", "freebsd", "openbsd")):
        return False
    # Curses in IDE terminals often hangs or renders blank — use text wizard.
    term_program = os.environ.get("TERM_PROGRAM", "")
    if term_program in {"Cursor", "vscode", "Code"}:
        return False
    if os.environ.get("VSCODE_INJECTION") or os.environ.get("CURSOR_TRACE_ID"):
        return False
    if not _curses_probe():
        return False
    return True


def _curses_probe() -> bool:
    try:
        curses.setupterm()
    except curses.error:
        return False
    return True


def _init_colors() -> None:
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(5, 8, -1)  # dim


def _attr(stdscr: curses.window, pair: int, *, bold: bool = False) -> int:
    bits = curses.color_pair(pair)
    if bold:
        bits |= curses.A_BOLD
    return bits


def _safe_addstr(win: curses.window, y: int, x: int, text: str, attr: int = 0) -> None:
    height, width = win.getmaxyx()
    if y < 0 or y >= height or x >= width:
        return
    win.addstr(y, x, text[: max(0, width - x - 1)], attr)


def _draw_frame(stdscr: curses.window, title: str, step: str, footer: str) -> tuple[int, int]:
    height, width = stdscr.getmaxyx()
    inner_w = max(20, width - 4)
    _safe_addstr(stdscr, 1, 2, "+" + "-" * inner_w + "+", _attr(stdscr, 1))
    _safe_addstr(stdscr, 2, 2, "|", _attr(stdscr, 1))
    _safe_addstr(stdscr, 2, 3, f" {title}"[: inner_w - 1].ljust(inner_w - 1), _attr(stdscr, 1, bold=True))
    _safe_addstr(stdscr, 2, 2 + inner_w, "|", _attr(stdscr, 1))
    _safe_addstr(stdscr, 3, 2, "|", _attr(stdscr, 1))
    _safe_addstr(stdscr, 3, 3, f" {step}"[: inner_w - 1].ljust(inner_w - 1), _attr(stdscr, 5))
    _safe_addstr(stdscr, 3, 2 + inner_w, "|", _attr(stdscr, 1))
    _safe_addstr(stdscr, 4, 2, "+" + "-" * inner_w + "+", _attr(stdscr, 1))
    _safe_addstr(stdscr, height - 2, 2, footer[: width - 4], _attr(stdscr, 5))
    return 5, inner_w


def _confirm_cancel(stdscr: curses.window, y: int) -> None:
    _safe_addstr(stdscr, y, 4, "Setup abbrechen?  [y/N]  (Enter = nein)", _attr(stdscr, 3, bold=True))
    stdscr.refresh()
    while True:
        key = _getch(stdscr)
        if key in (ord("y"), ord("Y")):
            raise WizardCancelled
        if key in (ord("n"), ord("N"), 10, 13, curses.KEY_ENTER, 27):
            return


def _wait_enter(
    stdscr: curses.window,
    y: int,
    message: str = ">>> Enter oder Space = weiter · Esc = abbrechen <<<",
) -> None:
    _safe_addstr(stdscr, y, 4, message, _attr(stdscr, 2, bold=True))
    stdscr.refresh()
    while True:
        key = _getch(stdscr)
        if key in (10, 13, curses.KEY_ENTER, ord(" "), ord("j"), ord("J"), ord("y"), ord("Y")):
            return
        if key in (27, ord("q"), ord("Q")):
            _confirm_cancel(stdscr, y + 1)
            return


def _screen_welcome(stdscr: curses.window, *, bootstrap: bool = False) -> None:
    stdscr.clear()
    title = "shared-agents Bootstrap" if bootstrap else "shared-agents Setup Wizard"
    _draw_frame(
        stdscr,
        title,
        "Welcome",
        "Enter/Space = weiter · Esc = abbrechen",
    )
    _safe_addstr(stdscr, 6, 4, "Team skills + learnings for your AI tools", _attr(stdscr, 2))
    if bootstrap:
        _safe_addstr(stdscr, 8, 4, "Core (open tools) + your private team-data repo.", 0)
        _safe_addstr(stdscr, 9, 4, "One wizard — adapters, sa CLI, learnings scaffold.", 0)
    else:
        _safe_addstr(stdscr, 8, 4, "This wizard configures adapters, shell CLI (sa),", 0)
        _safe_addstr(stdscr, 9, 4, "and symlinks team skills to your machine.", 0)
    _wait_enter(stdscr, 12)
    stdscr.refresh()


def _screen_path(stdscr: curses.window, default_home: str) -> str:
    buf = list(default_home)
    cursor = len(buf)

    while True:
        stdscr.clear()
        _draw_frame(
            stdscr,
            "Install location",
            "Step 1/5 — SHARED_AGENTS_HOME",
            "Type path · Enter confirm · Esc cancel",
        )
        _safe_addstr(stdscr, 6, 4, "Where should shared-agents live on this machine?", 0)
        _safe_addstr(stdscr, 8, 4, "Path:", _attr(stdscr, 1, bold=True))
        line = "".join(buf)
        _safe_addstr(stdscr, 8, 10, line + " ", 0)
        height, width = stdscr.getmaxyx()
        cx = min(10 + cursor, width - 2)
        if 8 < height:
            stdscr.move(8, cx)

        key = _getch(stdscr)
        if key in (10, 13, curses.KEY_ENTER):
            value = "".join(buf).strip()
            return value or default_home
        if key in (27, ord("q")):
            raise WizardCancelled
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if cursor > 0:
                buf.pop(cursor - 1)
                cursor -= 1
            continue
        if key == curses.KEY_HOME:
            cursor = 0
            continue
        if key == curses.KEY_END:
            cursor = len(buf)
            continue
        if key == curses.KEY_LEFT and cursor > 0:
            cursor -= 1
            continue
        if key == curses.KEY_RIGHT and cursor < len(buf):
            cursor += 1
            continue
        if key == curses.KEY_DC:
            if cursor < len(buf):
                buf.pop(cursor)
            continue
        if 32 <= key <= 126 and chr(key).isprintable():
            buf.insert(cursor, chr(key))
            cursor += 1


def _screen_team_remote(stdscr: curses.window) -> str | None:
    use_team = _screen_yes_no(
        stdscr,
        title="Team data (private)",
        step="Step 2/5 — Learnings + team skills",
        question=(
            "Separate git repo for team learnings/skills?\n"
            "(Core stays public — team/ is local only)"
        ),
        default=True,
    )
    if not use_team:
        return None

    buf: list[str] = []
    cursor = 0
    while True:
        stdscr.clear()
        _draw_frame(
            stdscr,
            "Team data remote",
            "Step 2/5 — git remote URL",
            "Type URL · Enter confirm · Esc cancel",
        )
        _safe_addstr(stdscr, 6, 4, "Empty private repo URL (SSH or HTTPS):", 0)
        _safe_addstr(stdscr, 8, 4, "URL:", _attr(stdscr, 1, bold=True))
        line = "".join(buf)
        _safe_addstr(stdscr, 8, 10, line + " ", 0)
        height, width = stdscr.getmaxyx()
        cx = min(10 + cursor, width - 2)
        if 8 < height:
            stdscr.move(8, cx)

        key = _getch(stdscr)
        if key in (10, 13, curses.KEY_ENTER):
            value = "".join(buf).strip()
            if value:
                return value
            _safe_addstr(stdscr, 10, 4, "URL required (or go back and choose Solo).", _attr(stdscr, 3, bold=True))
            stdscr.refresh()
            _getch(stdscr)
            continue
        if key in (27, ord("q")):
            raise WizardCancelled
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if cursor > 0:
                buf.pop(cursor - 1)
                cursor -= 1
            continue
        if 32 <= key <= 126 and chr(key).isprintable():
            buf.insert(cursor, chr(key))
            cursor += 1


def _screen_tools(stdscr: curses.window, rows: list[ToolRow], selected: set[str]) -> set[str]:
    if not rows:
        stdscr.clear()
        _draw_frame(
            stdscr,
            "Select AI tools",
            "Step 3/5 — No installable tools in manifest",
            "Enter continue · Esc cancel",
        )
        _wait_enter(stdscr, 8)
        return set()

    cursor = 0
    scroll = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        _draw_frame(
            stdscr,
            "Select AI tools",
            "Step 3/5 — Space toggle · a all · d detected · Enter continue",
            "↑↓ move · Space toggle · a/d/n shortcuts · Enter continue · Esc cancel",
        )

        list_top = 6
        list_height = max(3, height - 10)
        if cursor < scroll:
            scroll = cursor
        if cursor >= scroll + list_height:
            scroll = cursor - list_height + 1

        for vis, idx in enumerate(range(scroll, min(len(rows), scroll + list_height))):
            row = rows[idx]
            y = list_top + vis
            mark = "x" if row.tool_id in selected else " "
            active = idx == cursor
            prefix = ">" if active else " "
            name = f"{prefix} [{mark}] {row.name}"
            status = row.status
            attr = curses.color_pair(4) if active else 0
            _safe_addstr(stdscr, y, 4, name.ljust(28)[:28], attr)
            status_attr = _attr(stdscr, 2 if "configured" in status else 3 if "needs" in status else 5)
            _safe_addstr(stdscr, y, 34, status[: width - 36], status_attr)

        key = _getch(stdscr)
        if key in (10, 13, curses.KEY_ENTER):
            return selected
        if key in (27, ord("q")):
            raise WizardCancelled
        if key in (curses.KEY_UP, ord("k")):
            cursor = (cursor - 1) % len(rows)
            continue
        if key in (curses.KEY_DOWN, ord("j")):
            cursor = (cursor + 1) % len(rows)
            continue
        if key == ord(" "):
            tid = rows[cursor].tool_id
            if tid in selected:
                selected.remove(tid)
            else:
                selected.add(tid)
            continue
        if key in (ord("a"), ord("A")):
            selected = {row.tool_id for row in rows}
            continue
        if key in (ord("d"), ord("D")):
            selected = {row.tool_id for row in rows if row.installed}
            continue
        if key in (ord("n"), ord("N")):
            selected = set()
            continue


def _screen_yes_no(
    stdscr: curses.window,
    *,
    title: str,
    step: str,
    question: str,
    default: bool,
) -> bool:
    idx = 0 if default else 1
    options = ("Yes", "No")

    while True:
        stdscr.clear()
        _draw_frame(
            stdscr,
            title,
            step,
            "←→ or ↑↓ choose · Enter confirm · y/n · Esc cancel",
        )
        for i, line in enumerate(question.split("\n")):
            _safe_addstr(stdscr, 6 + i, 4, line, 0)
        option_y = 6 + len(question.split("\n")) + 2
        for i, label in enumerate(options):
            y = option_y + i
            marker = ">" if i == idx else " "
            attr = curses.color_pair(4) if i == idx else 0
            _safe_addstr(stdscr, y, 6, f"{marker} {label}", attr)

        key = _getch(stdscr)
        if key in (curses.KEY_LEFT, curses.KEY_UP):
            idx = (idx - 1) % 2
        elif key in (curses.KEY_RIGHT, curses.KEY_DOWN):
            idx = (idx + 1) % 2
        elif key in (ord("y"), ord("Y"), ord("j"), ord("J")):
            return True
        elif key in (ord("n"), ord("N")):
            return False
        elif key in (10, 13, curses.KEY_ENTER):
            return idx == 0
        elif key in (27, ord("q")):
            raise WizardCancelled


def _screen_shell(
    stdscr: curses.window,
    shell_rc: str,
    shell_state: ShellRcState,
) -> bool:
    if shell_state == ShellRcState.CONFIGURED:
        stdscr.clear()
        _draw_frame(
            stdscr,
            "Shell environment",
            "Step 4/5 — Already configured",
            "Enter continue · Esc cancel",
        )
        _safe_addstr(stdscr, 6, 4, f"{shell_rc}", _attr(stdscr, 2))
        _safe_addstr(stdscr, 7, 4, "SHARED_AGENTS_HOME + sa CLI already present.", 0)
        _wait_enter(stdscr, 10)
        return False

    question = f"Add SHARED_AGENTS_HOME + sa CLI to\n{shell_rc}?"
    if shell_state == ShellRcState.NEEDS_CLI:
        question = (
            f"{shell_rc} has SHARED_AGENTS_HOME but no CLI yet.\n"
            "Add sa / shared-agents commands?"
        )

    return _screen_yes_no(
        stdscr,
        title="Shell environment",
        step="Step 4/5 — Shell CLI",
        question=question,
        default=True,
    )


def _screen_summary(
    stdscr: curses.window,
    *,
    home: str,
    team_remote: str | None,
    rows: list[ToolRow],
    selected: set[str],
    add_shell: bool,
    shell_rc: str,
    shell_state: ShellRcState,
) -> bool:
    run_idx = 0  # 0 = Run setup, 1 = Cancel

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        _draw_frame(
            stdscr,
            "Summary",
            "Step 5/5 — Confirm setup",
            "↑↓ choose · Enter confirm · Esc cancel",
        )
        y = 6
        _safe_addstr(stdscr, y, 4, f"Install path: {home}", 0)
        y += 1
        if team_remote:
            team_line = f"Team data:    {team_remote}"
        else:
            team_line = "Team data:    solo (core learnings only)"
        _safe_addstr(stdscr, y, 4, team_line[: width - 6], 0)
        y += 1
        _safe_addstr(stdscr, y, 4, "Skills:       link core + team skills", 0)
        y += 1
        if shell_state == ShellRcState.CONFIGURED:
            shell_line = f"Shell:        keep existing ({shell_rc})"
        elif add_shell:
            shell_line = f"Shell:        configure {shell_rc}"
        else:
            shell_line = "Shell:        skip"
        _safe_addstr(stdscr, y, 4, shell_line[: width - 6], 0)
        y += 2
        _safe_addstr(stdscr, y, 4, "Configure tools:", _attr(stdscr, 1, bold=True))
        y += 1
        if selected:
            for row in rows:
                if row.tool_id not in selected:
                    continue
                _safe_addstr(stdscr, y, 6, f"• {row.name} ({row.status})", 0)
                y += 1
                if y >= height - 6:
                    break
        else:
            _safe_addstr(stdscr, y, 6, "(none — skills only)", _attr(stdscr, 5))
            y += 1

        options = ("Run setup now", "Cancel")
        base = max(y + 1, height - 8)
        for i, label in enumerate(options):
            yy = base + i
            marker = ">" if i == run_idx else " "
            attr = curses.color_pair(4) if i == run_idx else 0
            _safe_addstr(stdscr, yy, 4, f"{marker} {label}", attr)

        key = _getch(stdscr)
        if key in (curses.KEY_UP, ord("k")):
            run_idx = (run_idx - 1) % 2
        elif key in (curses.KEY_DOWN, ord("j")):
            run_idx = (run_idx + 1) % 2
        elif key in (10, 13, curses.KEY_ENTER):
            return run_idx == 0
        elif key in (27, ord("q")):
            raise WizardCancelled


def _wizard_main(
    stdscr: curses.window,
    *,
    default_home: str,
    rows: list[ToolRow],
    shell_rc: str,
    shell_state: ShellRcState,
    bootstrap: bool = False,
    ask_team: bool = True,
) -> WizardChoices:
    curses.curs_set(1)
    stdscr.keypad(True)
    _init_colors()

    _screen_welcome(stdscr, bootstrap=bootstrap)
    home = _screen_path(stdscr, default_home)

    team_remote: str | None = None
    if ask_team:
        team_remote = _screen_team_remote(stdscr)

    selected = {row.tool_id for row in rows if row.installed}
    selected = _screen_tools(stdscr, rows, selected)

    add_shell = _screen_shell(stdscr, shell_rc, shell_state)
    run_setup = _screen_summary(
        stdscr,
        home=home,
        team_remote=team_remote,
        rows=rows,
        selected=selected,
        add_shell=add_shell,
        shell_rc=shell_rc,
        shell_state=shell_state,
    )

    curses.curs_set(0)
    return WizardChoices(
        home=home,
        team_remote=team_remote,
        selected_tools=selected,
        add_shell=add_shell,
        run_setup=run_setup,
    )


def run_wizard_tui(
    *,
    default_home: str,
    rows: list[ToolRow],
    shell_rc: str,
    shell_state: ShellRcState,
    bootstrap: bool = False,
    ask_team: bool = True,
) -> WizardChoices | None:
    try:
        return curses.wrapper(
            _wizard_main,
            default_home=default_home,
            rows=rows,
            shell_rc=shell_rc,
            shell_state=shell_state,
            bootstrap=bootstrap,
            ask_team=ask_team,
        )
    except UserCancelled:
        try:
            curses.endwin()
        except Exception:
            pass
        return None
    except curses.error as exc:
        raise WizardTuiFailed("terminal too small or curses unavailable") from exc


def detect_shell_rc_state(shell_rc_path: str) -> ShellRcState:
    path = os.path.expanduser(shell_rc_path)
    if not os.path.isfile(path):
        return ShellRcState.ASK
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return ShellRcState.ASK
    has_home = "SHARED_AGENTS_HOME=" in text
    has_cli = "shell-aliases.sh" in text
    if has_home and has_cli:
        return ShellRcState.CONFIGURED
    if has_home:
        return ShellRcState.NEEDS_CLI
    return ShellRcState.ASK
