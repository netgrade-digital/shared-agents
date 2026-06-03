"""Terminal UI for shared-agents CLI (colors, logo). Respects NO_COLOR and TTY."""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Callable

_PATH_RE = re.compile(r"(/[^\s]+|~[^\s]+)")

# figlet "Shared Agents" — font: standard (readable Latin letters)
LOGO_LINES: tuple[str, ...] = (
    "  ____  _                        _      _                    _       ",
    " / ___|| |__   __ _ _ __ ___  __| |    / \\   __ _  ___ _ __ | |_ ___ ",
    " \\___ \\| '_ \\ / _` | '__/ _ \\/ _` |   / _ \\ / _` |/ _ \\ '_ \\| __/ __|",
    "  ___) | | | | (_| | | |  __/ (_| |  / ___ \\ (_| |  __/ | | | |_\\__ \\",
    " |____/|_| |_|\\__,_|_|  \\___|\\__,_| /_/   \\_\\__, |\\___|_| |_|\\__|___/",
    "                                            |___/                     ",
)

TAGLINE = "team skills · rules · learnings · sync"


def _stream_colors_enabled(stream) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return stream.isatty()


def colors_enabled() -> bool:
    return _stream_colors_enabled(sys.stdout)


def stderr_colors_enabled() -> bool:
    return _stream_colors_enabled(sys.stderr)


def is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _c(code: str, text: str, *, stream=None) -> str:
    enabled = (
        stderr_colors_enabled()
        if stream is sys.stderr
        else colors_enabled()
        if stream is None
        else _stream_colors_enabled(stream)
    )
    if not enabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    return _c("1", text)


def plain(text: str) -> str:
    """Terminal default foreground — readable on dark themes (no dim grey)."""
    return text


def muted(text: str) -> str:
    """Only for decorative hints; prefer plain() for descriptions."""
    return _c("90", text)


def green(text: str) -> str:
    return _c("1;32", text)


def yellow(text: str) -> str:
    return _c("93", text)


def warn(text: str) -> str:
    return yellow(text)


def cyan(text: str) -> str:
    return _c("96", text)


def magenta(text: str) -> str:
    return _c("95", text)


def red(text: str) -> str:
    return _c("91", text)


# Aliases used by install-adapters / status
dim = muted


def logo_colored() -> list[str]:
    if not colors_enabled():
        return list(LOGO_LINES) + [f"  ◈  {TAGLINE}"]
    lines: list[str] = []
    gradient = ("36", "96", "34", "94", "35", "95")
    for i, line in enumerate(LOGO_LINES):
        lines.append(_c(gradient[i % len(gradient)], line))
    lines.append(f"  ◈  {TAGLINE}")
    return lines


def print_logo(*, file=None) -> None:
    out = sys.stdout if file is None else file
    for line in logo_colored():
        print(line, file=out)


def print_banner(*, subtitle: str | None = None, file=None) -> None:
    out = sys.stdout if file is None else file
    print(file=out)
    print_logo(file=out)
    if subtitle:
        print(muted(f"  {subtitle}"), file=out)
    print(file=out)


def _cmd(cmd: str, desc: str) -> None:
    print(f"  {green(cmd)}{plain(desc)}")


def _example(cmd: str, desc: str = "") -> None:
    if desc:
        print(f"  {green(cmd)}{plain(desc)}")
    else:
        print(f"  {green(cmd)}")


def print_help(*, version: str, home: str) -> None:
    print()
    print_logo()
    print(f"  {bold('shared-agents CLI')}  {green(f'(sa v{version})')}")
    print()
    print(f"  Home: {cyan('$SHARED_AGENTS_HOME')} {plain(f'({home})')}")
    print()
    print(
        f"  Invoke: {bold('sa')} | {bold('shared-agents')} | "
        f"{bold('sharedagents')} {plain('<command> [args…]')}"
    )
    print(f"  Usage:  {bold('sa <command> [args…]')}")
    print()

    print(f"  {cyan('Setup')}")
    _cmd("bootstrap", "             Full setup (Core + team repo + adapters)")
    _cmd("install", " [opts]       Setup wizard (TTY: TUI ↑↓ Space · Cursor: text)")
    _cmd("install --non-interactive", "   No wizard — all detected tools")
    _cmd("check", "                Adapter install vs configured")
    _cmd("uninstall", " [opts]     Uninstall (confirm: y/N)")
    _cmd("sync", "                 Pull Core + team; link skills + rules")
    _cmd("team verify", "           Validate team repo (git, index, folders)")
    _cmd("team migrate", "          Move legacy learnings/ → team/learnings/")
    _cmd("status", "               Open items (review, skills, adapters)")
    print()

    print(f"  {cyan('Team content')}")
    _cmd("skill new", " [opts]       Wizard: team/skills/<name>/SKILL.md")
    _cmd("skill rm", " [name]       Remove team skill (picker if omitted)")
    _cmd("skill list", "             List team skills")
    _cmd("rule new", " [opts]       Wizard: team/rules/<slug>.mdc")
    _cmd("rule rm", " [slug]       Remove team rule (picker if omitted)")
    _cmd("rule list", "             List team rules")
    print()

    print(f"  {magenta('Learnings')}")
    _cmd("review", " [file]        Review pending → approved (+ commit/push)")
    _cmd("review list", "          List pending")
    _cmd("review dry", " [file]    Dry-run review")
    _cmd("pending push", " [file]    Commit + push pending (team review)")
    _cmd("pending path", " [slug]    Show canonical pending path")
    _cmd("unapprove", " [id|file]  Remove from approved (wizard: delete/pending)")
    _cmd("unapprove list", "       List approved")
    print()

    print(f"  {yellow('Info')}")
    _cmd("help", "                 This help")
    _cmd("version", "              Show version")
    print()

    print(f"  {bold('Examples')}")
    _example("sa bootstrap", "                      First-time setup (curl | bash)")
    _example("sa install", "                        Re-run adapters / wizard")
    _example("sa install --non-interactive", "        Quick, no prompts")
    _example("sa install --check", "                  Adapter status")
    _example("sa sync")
    _example("sa status")
    _example("sa team verify")
    _example("sa skill new")
    _example("sa skill rm my-skill")
    _example("sa rule new")
    _example("sa rule list")
    _example("sa review list")
    _example("sa pending push 2026-06-02-my-slug.md")
    _example("sa review 2026-06-02-my-slug.md")
    print()

    print(f"  {bold('Common flags')}{plain(' (install / review / unapprove / pending)')}")
    _cmd("--wizard", "             Interactive setup wizard (install)")
    _cmd("--non-interactive", "    All detected tools (install)")
    _cmd("--dry-run", "            Preview only")
    _cmd("-y, --yes", "            Skip prompts")
    _cmd("--no-git", "             No commit/push")
    _cmd("--domain DOMAIN", "      Target domain folder (review)")
    print()

    print(
        f"  No ~/.shared-agents yet? "
        f"{bold('sa bootstrap')} {plain('(Core + private team repo)')}"
    )
    print(
        f"  From repo root: {bold('./install.sh')} · {bold('./sa install')} · {bold('sa help')}"
    )
    print(f"  Docs: {cyan('$SHARED_AGENTS_HOME/README.md#command-reference')}")
    print()


def _cmd_after(name: str, desc: str) -> None:
    print(f"  {green(f'{name:<22}')}{plain(desc)}")


def print_install_footer(*, home: str, shell_rc: str) -> None:
    print()
    print(green(bold("Install OK.")))
    print()
    print(plain("CLI:  ") + green("sa help") + plain("   (also: shared-agents help · sharedagents help)"))
    print()
    print(bold("Reload your shell:"))
    print(f"  {cyan(f'source {shell_rc}')}")
    print()
    print(bold("Next commands:"))
    _cmd_after("sa sync", "Pull Core + team; refresh skill/rule links")
    _cmd_after("sa skill new", "Wizard: team skill")
    _cmd_after("sa rule new", "Wizard: team rule")
    _cmd_after("sa review", "Review / approve learnings")
    _cmd_after("sa pending push", "Push pending for team review")
    _cmd_after("sa team verify", "Validate team repo layout")
    _cmd_after("sa check", "Adapter status")
    _cmd_after("sa uninstall", "Uninstall (y/N)")
    print()
    print(plain("Docs:     ") + cyan(f"{home}/README.md"))
    print(plain("Check:    ") + green("sa check"))
    print(plain("Wizard:   ") + green("sa install"))
    print(plain("Quick:    ") + green("sa install --non-interactive"))
    print(plain("Remove:   ") + green("sa uninstall"))
    print()


def print_version(
    *,
    version: str,
    home: str,
    install_sh: str | None = None,
    install_hint: str | None = None,
) -> None:
    print()
    print_logo()
    print()
    print(f"{bold('shared-agents sa')} {green(f'v{version}')}")
    print(f"{plain('SHARED_AGENTS_HOME=')}{cyan(home)}")
    if install_sh:
        print(f"{plain('install.sh=')}{cyan(install_sh)}")
    elif install_hint:
        print(plain(install_hint))


def print_error(*lines: str) -> None:
    for line in lines:
        text = red(line) if stderr_colors_enabled() else line
        print(text, file=sys.stderr)


# --- Shared CLI output (review, sync, uninstall, …) ---


def heading(text: str) -> str:
    return bold(cyan(text))


def say(msg: str = "") -> None:
    print(msg)


def say_stderr(msg: str) -> None:
    text = red(msg) if stderr_colors_enabled() else msg
    print(text, file=sys.stderr)


def say_warn_stderr(msg: str) -> None:
    text = warn(f"Warning: {msg}") if stderr_colors_enabled() else f"Warning: {msg}"
    print(text, file=sys.stderr)


def say_success(msg: str) -> None:
    print(green(msg) if colors_enabled() else msg)


def say_warn(msg: str) -> None:
    print(warn(msg) if colors_enabled() else msg)


def say_info(msg: str) -> None:
    print(plain(msg))


def divider(width: int = 72) -> None:
    print(plain("-" * width))


def label_line(label: str, value: str) -> None:
    print(f"{plain(label)}{cyan(value)}")


def bullet_ok(msg: str) -> None:
    print(f"  {green('✓')} {plain(msg)}")


def bullet_warn(msg: str) -> None:
    print(f"  {yellow('!')} {plain(msg)}")


def highlight_paths(text: str) -> str:
    if not colors_enabled():
        return text
    parts: list[str] = []
    last = 0
    for match in _PATH_RE.finditer(text):
        parts.append(plain(text[last : match.start()]))
        parts.append(cyan(match.group(1)))
        last = match.end()
    parts.append(plain(text[last:]))
    return "".join(parts)


def print_dry_run_line(msg: str, *, symbol: str = "○") -> None:
    sym = yellow(symbol)
    if msg.startswith("[dry-run]"):
        rest = msg[len("[dry-run]") :].lstrip()
        print(f"  {sym} {yellow('[dry-run]')} {highlight_paths(rest)}")
    else:
        print(f"  {sym} {highlight_paths(msg)}")


def bullet_skip(msg: str) -> None:
    print_dry_run_line(msg)


def bullet_fail(msg: str) -> None:
    print(f"  {red('✗')} {plain(msg)}")


def arrow_line(msg: str) -> None:
    print(f"  {green('→')} {plain(msg)}")


def menu_option(key: str, label: str) -> None:
    print(f"  {cyan(key)} {plain(label)}")


def list_section(title: str) -> None:
    print(heading(title))


def list_pick_item(num: int, name: str) -> None:
    print(f"  {cyan(f'{num})')} {yellow(name)}")


def list_tsv_row(filename: str, **meta: str) -> None:
    parts = [yellow(filename)]
    for key, value in meta.items():
        parts.append(f"{plain(key + '=')}{cyan(value)}")
    print("\t".join(parts))


def preview_header(title: str, **fields: str) -> None:
    print()
    print(heading(title))
    for label, value in fields.items():
        label_line(f"{label}: ", value)


def preview_body(text: str) -> None:
    divider()
    print(text.rstrip())
    divider()


EXIT_CANCELLED = 130


class UserCancelled(Exception):
    """User cancelled an interactive flow (Ctrl+C or wizard abort)."""


def say_cancelled() -> None:
    say_warn("Cancelled.")


def prompt_line(prompt: str) -> str:
    """Read one line; Ctrl+C raises UserCancelled (no traceback)."""
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print()
        raise UserCancelled from None


def prompt_yes_no(prompt: str, *, default: bool = False) -> bool:
    """y/N (or Y/n) prompt; Ctrl+C raises UserCancelled."""
    hint = "Y/n" if default else "y/N"
    while True:
        try:
            answer = input(f"{prompt} [{hint}]: ").strip().lower()
        except KeyboardInterrupt:
            print()
            raise UserCancelled from None
        if not answer:
            return default
        if answer in {"y", "yes", "j", "ja"}:
            return True
        if answer in {"n", "no", "nein"}:
            return False
        say_warn("Please answer y or n.")


def run_cli_main(main: Callable[[], int]) -> None:
    """Wrap script __main__ for clean Ctrl+C / UserCancelled exit."""
    try:
        raise SystemExit(main())
    except UserCancelled:
        say_cancelled()
        raise SystemExit(EXIT_CANCELLED) from None
    except KeyboardInterrupt:
        print()
        say_cancelled()
        raise SystemExit(EXIT_CANCELLED) from None


def git_skip_no_git() -> None:
    say_warn("Skipped git commit/push (--no-git).")


def git_skip_not_repo(*, extra: str | None = None) -> None:
    say_warn("Not a git repo — skipped commit/push.")
    if extra:
        say_info(extra)


def git_dry_run(commands: list[str]) -> None:
    print()
    say_warn("[dry-run] Would run:")
    for cmd in commands:
        arrow_line(cmd)


def git_note(msg: str) -> None:
    say_info(msg)


def git_nothing_staged(msg: str) -> None:
    say_warn(msg)


def git_committed(commit_msg: str) -> None:
    say_success(f"Committed: {commit_msg}")


def git_pushed(msg: str = "Pushed to remote.") -> None:
    say_success(msg)


def git_push_failed(err: str, *, hints: list[str] | None = None) -> None:
    say_stderr(f"Commit OK, but push failed: {err}")
    for hint in hints or []:
        say_stderr(hint)


def print_sync_ok() -> None:
    say_success("✓ Core + team data synced.")
    say_success("✓ Skills + rules linked for detected tools.")


def print_uninstall_intro(*, home: str, shell_rc: str, keep_repo: bool) -> None:
    print()
    print(heading("shared-agents uninstall"))
    label_line("  HOME:      ", home)
    label_line("  Shell rc:  ", shell_rc)
    if keep_repo:
        print(f"  {plain('Data:      keep core + team/ + config.local.yaml')}")
        print(f"  {plain('Remove:    adapters + skill symlinks only')}")
    else:
        print(f"  {plain('Data:      ')}{warn('DELETE')} {cyan(home)}")
        print(f"  {plain('           ')}{plain('(core, team/ learnings, config.local.yaml)')}")
    print()


def print_uninstall_step(title: str) -> None:
    print(bold(title))


def print_uninstall_footer(*, dry_run: bool) -> None:
    print()
    if dry_run:
        say_warn("Dry run complete — no changes made.")
    else:
        say_success("Uninstall complete.")
        say_info("Neues Terminal öffnen (oder: exec $SHELL) — sa / shared-agents sind dann weg.")
        print(f"{plain('Re-install: ')}{green('sa bootstrap')}")
    print()


def print_styled(kind: str, text: str) -> None:
    styles = {
        "heading": heading,
        "success": green,
        "warn": warn,
        "error": red,
        "plain": plain,
        "cyan": cyan,
        "bold": bold,
        "green": green,
        "yellow": yellow,
        "magenta": magenta,
    }
    fn = styles.get(kind, plain)
    print(fn(text))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    version = os.environ.get("SA_VERSION", "0.0.0")
    home = os.environ.get("SHARED_AGENTS_HOME", os.path.expanduser("~/.shared-agents"))

    if arg in {"--logo", "logo"}:
        print_logo()
    elif arg in {"--help", "help"}:
        print_help(version=version, home=home)
    elif arg in {"--version", "version"}:
        print_version(
            version=version,
            home=home,
            install_sh=os.environ.get("SA_INSTALL_SH") or None,
            install_hint=os.environ.get("SA_INSTALL_HINT") or None,
        )
    elif arg == "--error":
        print_error(*sys.argv[2:])
    elif arg == "--install-footer":
        print_install_footer(
            home=home,
            shell_rc=os.environ.get("SHELL_RC", os.path.expanduser("~/.bashrc")),
        )
    elif arg == "--sync-ok":
        print_sync_ok()
    elif arg == "--uninstall-intro":
        keep = os.environ.get("SA_KEEP_REPO", "0") == "1"
        print_uninstall_intro(
            home=home,
            shell_rc=os.environ.get("SHELL_RC", os.path.expanduser("~/.bashrc")),
            keep_repo=keep,
        )
    elif arg == "--uninstall-step" and len(sys.argv) >= 3:
        print_uninstall_step(" ".join(sys.argv[2:]))
    elif arg == "--uninstall-footer":
        print_uninstall_footer(dry_run=os.environ.get("SA_DRY_RUN", "0") == "1")
    elif arg == "--dry-run-line" and len(sys.argv) >= 3:
        print_dry_run_line(" ".join(sys.argv[2:]))
    elif arg == "--out" and len(sys.argv) >= 4:
        print_styled(sys.argv[2], " ".join(sys.argv[3:]))
    elif arg == "--line" and len(sys.argv) >= 4:
        label_line(sys.argv[2], " ".join(sys.argv[3:]))
    else:
        print(
            "Usage: sa_ui.py --logo | --help | --version | --install-footer | "
            "--sync-ok | --out KIND TEXT | --line LABEL VALUE | --error MSG…",
            file=sys.stderr,
        )
        raise SystemExit(2)
