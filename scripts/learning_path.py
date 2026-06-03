#!/usr/bin/env python3
"""Print canonical pending learning path(s)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sa_config import core_home, pending_dir
from sa_ui import run_cli_main, say_warn_stderr


def main() -> int:
    home = core_home()
    pending = pending_dir(home)
    if len(sys.argv) < 2:
        print(pending)
        return 0

    slug = sys.argv[1]
    if "/" in slug or "\\" in slug:
        say_warn_stderr("learning-path: slug must be a filename only (no directories)")
        return 1
    if not slug.endswith(".md"):
        slug = f"{slug}.md"
    print(pending / slug)
    return 0


if __name__ == "__main__":
    run_cli_main(main)
