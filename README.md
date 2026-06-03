<p align="center">
  <!-- Replace with your banner (recommended: 1200×400, docs/assets/shared-agents-banner.png) -->
  <img src="docs/assets/shared-agents-banner.png" alt="Shared Agents"/>
</p>

---

<p align="center">
  <strong>Team skills and learnings for AI assistants</strong> — one install, Git-synced, IDE-agnostic.
</p>

<p align="center">
  <a href="https://github.com/netgrade-digital/shared-agents/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/netgrade-digital/shared-agents/ci.yml?branch=main&label=BUILD&style=flat-square" alt="Build" /></a>
  <a href="https://github.com/netgrade-digital/shared-agents/releases"><img src="https://img.shields.io/badge/RELEASE-v0.3.2-blue?style=flat-square" alt="Release" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/LICENSE-MIT-2196f3?style=flat-square" alt="License" /></a>
  <a href="https://github.com/netgrade-digital/shared-agents/stargazers"><img src="https://img.shields.io/github/stars/netgrade-digital/shared-agents?label=STARS&style=flat-square" alt="GitHub stars" /></a>
</p>

<p align="center">
  If this project helps your team, consider giving it a <a href="https://github.com/netgrade-digital/shared-agents/stargazers">⭐ on GitHub</a>.
</p>

---

## Why this exists

Teams use many AI tools (Cursor, Claude Code, Zed, Codex, …). Each session starts cold: no shared workflows, no institutional memory, and knowledge trapped in chats or private notes.

**Shared Agents** gives you one place to:

- **Skills** — how we work (repeatable workflows for agents)
- **Learnings** — what we already figured out (bugs, stack quirks, decisions)

Everyone syncs the same content. Agents load it automatically at session start. Sensitive team data stays in a **private** repo, not public.

---

## What it is

| Piece | Role |
|-------|------|
| **Core** (this repo) | Open-source CLI (`sa`), adapters, shared skills, installer |
| **Team** (your private Git remote) | Learnings + optional team-only skills under `team/` |
| **Local install** | `~/.shared-agents` (or `$SHARED_AGENTS_HOME`) on each machine |

```
  GitHub (Core)              Your private remote (Team)
        │                              │
        └────────── sa sync ───────────┘
                        │
                        ▼
              ~/.shared-agents  ──►  Cursor · Claude Code · Zed · …
```

- **Tool-neutral** — Markdown + Git, no vendor lock-in
- **Manifest-driven adapters** — hooks and global instructions per IDE/CLI
- **Human-in-the-loop learnings** — agents propose drafts; a person approves via `sa review`

---

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/netgrade-digital/shared-agents/refs/heads/main/scripts/bootstrap.sh | bash
```

The bootstrap wizard installs Core, optionally wires your team repo, and configures detected tools. Then open a new shell and run `sa`.

Non-interactive (CI/scripts): `SA_BOOTSTRAP_NON_INTERACTIVE=1 curl -fsSL … | bash`

---

## Everyday use

| Task | Command |
|------|---------|
| Pull latest Core + team data | `sa sync` |
| Overview / all commands | `sa` or `sa help` |
| Adapter health | `sa check` |
| Review a learning draft | `sa review` |

Sync also runs automatically via IDE hooks and agent instructions after install.

---

## Repository layout

```
shared-agents/
├── skills/              # Core skills (synced to ~/.agents/skills, etc.)
├── adapters/            # Per-tool wiring (manifest.json + docs)
├── scripts/             # sa CLI, sync, bootstrap, learning tools
├── docs/                # Detailed guides
├── rules/               # Cursor rule template
└── team/                # Private team data (gitignored here — separate remote)
```

Install path defaults to `~/.shared-agents`. Team learnings live at `team/learnings/` inside that directory.

---

## Documentation

| Topic | Guide |
|-------|--------|
| Learnings workflow | [docs/learnings.md](docs/learnings.md) |
| Paths agents must use | [docs/canonical-paths.md](docs/canonical-paths.md) |
| Migrating legacy `learnings/` | [docs/migration-team-data.md](docs/migration-team-data.md) |
| Supported tools | [adapters/manifest.json](adapters/manifest.json) |
| CLI reference (full) | Skill `sa-cli` in [skills/sa-cli/SKILL.md](skills/sa-cli/SKILL.md) |

---

## Contributing

Contributions to **Core** (adapters, CLI, docs, shared skills) are welcome. Team learnings belong in your **private team repo**, not in pull requests here.

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

[MIT](LICENSE) — maintained by [netgrade-digital](https://github.com/netgrade-digital).

---

## Star History

<a href="https://www.star-history.com/?repos=netgrade-digital%2Fshared-agents&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=netgrade-digital/shared-agents&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=netgrade-digital/shared-agents&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=netgrade-digital/shared-agents&type=date&legend=top-left" />
 </picture>
</a>
