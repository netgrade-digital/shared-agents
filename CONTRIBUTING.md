# Contributing

Thanks for helping make shared-agents open-source ready.

## CLI

Team shell entry point: **`sa`** (aliases: `shared-agents`, `sharedagents`).  
**`sa`** without arguments = **`sa help`**. Full guide: skill **`sa-cli`** in `skills/sa-cli/SKILL.md`.

```bash
./sa install --dry-run
sa install
sa check
```

Low-level equivalent: `./install.sh` (same options, forwarded by `sa install`).

## Adding support for a new AI CLI

1. **Detect** — add entry to [`adapters/manifest.json`](adapters/manifest.json):
   - `detect`: config directory path (e.g. `~/.mycli`)
   - `detect_bins`: optional CLI binary names on `$PATH`
   - `agents_md` or `sync` hook fields (see existing tools)

2. **Document** — add `adapters/<tool-id>/README.md` (setup via **`sa install`**)

3. **Test**:
   ```bash
   sa install --dry-run
   sa install
   sa check
   # or: ./install.sh --dry-run && ./install.sh && ./install.sh --check
   ```

4. **Pull request** — include sample `sa check` (or `install.sh --check`) output

## Manifest schema

| Field | Purpose |
|-------|---------|
| `detect` | Config dir; tool considered installed if this exists |
| `detect_bins` | Extra detection via binary on PATH |
| `agents_md` | Global instructions file (merged with marker block) |
| `sync` | Hook-based sync (Cursor, Claude Code) |

## Check vs install

- **`sa install`** — only configures tools where `installed == true`
- **`sa check`** — reports all tools: missing / not configured / ok

Installed = config dir exists **or** any `detect_bins` binary found.

Configured = shared-agents marker or hook present in expected paths.

## Canonical paths (mandatory for agents)

All team files live under `$SHARED_AGENTS_HOME` (default `~/.shared-agents`), **not** in the Cursor workspace or customer project unless that path equals `$SHARED_AGENTS_HOME`.

| Action | Path / command |
|--------|-----------------|
| Write learning draft | `sa pending path <slug>` → usually `team/learnings/pending/…` |
| Publish draft | `sa pending push <file>` |
| Read team knowledge | `$SHARED_AGENTS_HOME/team/learnings/approved/` + `index.yaml` |
| Promote to approved | `sa review <file>` (human only) |
| Resolve path | `sa pending path <slug>` or `scripts/learning-path.sh` |

Full spec: [docs/canonical-paths.md](docs/canonical-paths.md). Update `capture-learning`, `sa-cli`, and `rules/shared-agents-knowledge.mdc` when changing this contract.

## Shared MCPs (planned)

MCP server wiring is documented in [docs/shared-mcps.md](docs/shared-mcps.md). When implementing `install-mcps.py`:

- Follow the same patterns as `install-adapters.py` (stdlib, idempotent, `--check`, `--dry-run`)
- Wire through **`sa install`** / `install.sh` (not a separate legacy alias)
- Never commit `mcps.local.yaml` or secrets in the manifest
- Use managed prefix `sa-` for team servers; leave user keys untouched

Reference: [mcps/manifest.example.json](mcps/manifest.example.json)

## Code style

- Installer: Python 3 stdlib only (no pip deps)
- Shell: `bash`, `set -euo pipefail`
- Idempotent: re-running `sa install` must be safe
- CLI: extend `scripts/sa` — keep **`sa help`** in sync with new commands
