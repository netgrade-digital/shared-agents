#!/usr/bin/env python3
"""Bootstrap: clone core, setup team data, run install wizard (sa_ui design)."""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))


def _load_install_adapters():
    path = _SCRIPT_DIR / "install-adapters.py"
    spec = importlib.util.spec_from_file_location("install_adapters", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ia = _load_install_adapters()

from sa_config import config_path, write_config  # noqa: E402
from sa_ui import bold, cyan, green, plain, print_banner, print_install_footer, say_warn_stderr  # noqa: E402
from team_data import setup_team  # noqa: E402

DEFAULT_CORE_REMOTE = os.environ.get(
    "SHARED_AGENTS_CORE_REMOTE",
    os.environ.get(
        "SHARED_AGENTS_GIT_REMOTE",
        "git@bitbucket.org:netgrade/shared-agents.git",
    ),
)


def ensure_core_clone(
    home: Path,
    core_remote: str,
    *,
    dry_run: bool = False,
) -> Path:
    home = _ia.expand(str(home))
    if dry_run:
        print(f"[dry-run] would ensure core at {home} from {core_remote}")
        return home

    home.parent.mkdir(parents=True, exist_ok=True)
    if (home / ".git").is_dir():
        subprocess.run(
            ["git", "-C", str(home), "pull", "--ff-only", "--no-rebase"],
            check=False,
        )
        return home

    if home.exists() and any(home.iterdir()):
        say_warn_stderr(f"{home} exists but is not a git repo — aborting.")
        raise SystemExit(1)

    clone = subprocess.run(
        ["git", "clone", core_remote, str(home)],
        capture_output=True,
        text=True,
    )
    if clone.returncode != 0:
        err = (clone.stderr or clone.stdout or "clone failed").strip()
        say_warn_stderr(err)
        raise SystemExit(1)
    return home


def apply_bootstrap(
    repo_source: Path,
    choices: _ia.SavedWizardChoices,
    *,
    core_remote: str,
    dry_run: bool = False,
    shell_rc: Path | None = None,
) -> int:
    home = _ia.expand(choices.home)
    os.environ["SHARED_AGENTS_HOME"] = str(home)

    ensure_core_clone(home, core_remote, dry_run=dry_run)

    repo_home = home if (home / "adapters" / "manifest.json").is_file() else repo_source

    if not dry_run:
        write_config(
            home,
            team_remote_url=choices.team_remote,
            core_remote=core_remote,
        )
        if choices.team_remote:
            print()
            print(bold("Team data"))
            try:
                msg = setup_team(home, choices.team_remote, dry_run=False)
                print(f"  {green('✓')} {plain(msg)}")
            except RuntimeError as exc:
                say_warn_stderr(str(exc))
                return 1
        else:
            setup_team(home, None, dry_run=False)
            print(f"  {green('✓')} {plain('Solo mode — learnings under core/')}")

        if choices.team_remote:
            from team_data import print_verify_report, verify_team

            print()
            print_verify_report(verify_team(home))

    return _ia.apply_wizard_choices(
        repo_home,
        choices,
        dry_run=dry_run,
        shell_rc=shell_rc,
        skip_team_setup=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="shared-agents bootstrap wizard")
    parser.add_argument(
        "--source",
        type=Path,
        default=_SCRIPT_DIR.parent,
        help="Core repo source (dev checkout or after clone)",
    )
    parser.add_argument("--home", default=os.environ.get("SHARED_AGENTS_HOME", "~/.shared-agents"))
    parser.add_argument("--shell-rc", default=os.environ.get("SHELL_RC", "~/.bashrc"))
    parser.add_argument("--core-remote", default=DEFAULT_CORE_REMOTE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args()

    repo_source = _ia.expand(str(args.source))
    home = os.path.expanduser(os.path.expandvars(args.home))
    shell_rc = _ia.expand(args.shell_rc)

    print_banner(subtitle="Bootstrap — core + team data + adapters")

    if args.non_interactive:
        choices = _ia.SavedWizardChoices(
            home=home,
            team_remote=None,
            selected_tools=[],
            add_shell=True,
        )
    else:
        ask_team = not config_path(_ia.expand(home)).is_file()
        choices = _ia.gather_wizard_choices(
            repo_source,
            home,
            shell_rc=shell_rc,
            ask_team=ask_team,
            bootstrap=True,
        )
        if choices is None:
            print(plain("Abgebrochen — nichts installiert."))
            return 1

    code = apply_bootstrap(
        repo_source,
        choices,
        core_remote=args.core_remote,
        dry_run=args.dry_run,
        shell_rc=shell_rc,
    )
    if code == 0 and not args.dry_run:
        print_install_footer(home=str(_ia.expand(choices.home)), shell_rc=str(shell_rc))
        print(plain("Daily: ") + cyan("sa sync") + plain(" · ") + cyan("sa review"))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
