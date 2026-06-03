# Contributing to Shared Agents

Thank you for helping improve the **Core** open-source project. This document covers what belongs here, how to develop locally, and how to submit changes.

---

## Core vs team data

| Contribute here (Core PR) | Do **not** commit to Core |
|---------------------------|---------------------------|
| `scripts/`, `sa` CLI | `team/learnings/` |
| `adapters/`, `adapters/manifest.json` | `config.local.yaml` |
| `skills/` (shared, OSS-safe) | Secrets, customer URLs, internal runbooks |
| `docs/`, `rules/` | Private team skills with sensitive content |

**Learnings** and optional **team-only skills** live in a **separate private Git repository**, mounted at `$SHARED_AGENTS_HOME/team/`. Configure it during `sa bootstrap` or in `config.local.yaml` (`team.remote`).

---

## Development setup

Clone and install into your home directory (or use an existing bootstrap):

```bash
git clone git@github.com:netgrade-digital/shared-agents.git
cd shared-agents
./sa install --home "$HOME/.shared-agents"
source ~/.bashrc
```

Work on the clone, then test changes:

```bash
sa install --dry-run
sa install
sa check
```

Run scripts directly when debugging: `python3 scripts/install-adapters.py check ~/.shared-agents`

---

## Pull requests

1. **Branch** from `main` with a focused change (one feature or fix per PR).
2. **Test** with `sa install` and `sa check` on at least one supported tool you have installed.
3. **Describe** what changed and why; include `sa check` output if you touched adapters.
4. **No secrets** — no tokens, private URLs, or team learnings in Core.
5. **CLI changes** — update `scripts/sa` and keep `sa help` accurate; extend [skills/sa-cli/SKILL.md](skills/sa-cli/SKILL.md) when behavior is non-obvious.

We use fast-forward merges on `main`. Keep PRs small and reviewable.

---

## Adding support for a new AI tool

1. Add an entry to [`adapters/manifest.json`](adapters/manifest.json):
   - `detect` — config directory (e.g. `~/.cursor`)
   - `detect_bins` — optional CLI names on `$PATH`
   - `agents_md` and/or `sync` — see existing tools

2. Add `adapters/<tool-id>/README.md` with setup notes.

3. Verify:

   ```bash
   sa install --dry-run
   sa install
   sa check
   ```

4. Open a PR with sample `sa check` output.

### Manifest fields

| Field | Purpose |
|-------|---------|
| `detect` | Config dir exists → tool considered **installed** |
| `detect_bins` | Binary on `$PATH` → also counts as installed |
| `agents_md` | Global instructions file (marker block merged on install) |
| `sync` | Hook-based sync (e.g. Cursor, Claude Code) |

**Installed** ≠ **configured**. `sa install` only configures tools that are detected as installed. `sa check` reports the full matrix.

For tools without a manifest entry, users can copy [adapters/generic/instructions.md](adapters/generic/instructions.md) into their global agent config.

---

## Adding or changing Core skills

- Place skills under `skills/<name>/SKILL.md`.
- Keep content **safe for a public repo** (no credentials, no client-specific paths).
- After adding a skill, run `sa install` so symlinks under `~/.agents/skills/` (and tool-specific paths) are updated.
- If the skill changes agent workflow (paths, sync, learnings), update [rules/shared-agents-knowledge.mdc](rules/shared-agents-knowledge.mdc) and [skills/shared-agents-knowledge/SKILL.md](skills/shared-agents-knowledge/SKILL.md) when relevant.

---

## Learnings (team repo, not Core)

Agents draft learnings in `team/learnings/pending/` after explicit user approval. Humans promote them with `sa review` into `team/learnings/approved/`.

Contributors documenting this flow should edit [docs/learnings.md](docs/learnings.md) and [docs/canonical-paths.md](docs/canonical-paths.md), not put learning files in Core PRs.

---

## Shared MCPs (planned)

MCP wiring is specced in [docs/shared-mcps.md](docs/shared-mcps.md). When implemented:

- Mirror `install-adapters.py` patterns (stdlib only, idempotent, `--check`, `--dry-run`)
- Integrate via `sa install` / `install.sh`
- Never commit `mcps.local.yaml` or secrets
- Use managed prefix `sa-` for team servers

Reference: [mcps/manifest.example.json](mcps/manifest.example.json)

---

## Code guidelines

| Area | Rule |
|------|------|
| Installer Python | **stdlib only** — no pip dependencies |
| Shell | `bash`, `set -euo pipefail` where applicable |
| Idempotency | Re-running `sa install` must be safe |
| Ctrl+C | Interactive scripts use `UserCancelled` / `run_cli_main` from `sa_ui.py` |
| Paths | Team files under `$SHARED_AGENTS_HOME` — see [docs/canonical-paths.md](docs/canonical-paths.md) |

---

## Questions

Open a [GitHub issue](https://github.com/netgrade-digital/shared-agents/issues) for bugs or design questions. For day-to-day CLI usage, run `sa help` or read the `sa-cli` skill.
