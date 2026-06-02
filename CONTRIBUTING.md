# Contributing

Thanks for helping make shared-agents open-source ready.

## Adding support for a new AI CLI

1. **Detect** — add entry to [`adapters/manifest.json`](manifest.json):
   - `detect`: config directory path (e.g. `~/.mycli`)
   - `detect_bins`: optional CLI binary names on `$PATH`
   - `agents_md` or `sync` hook fields (see existing tools)

2. **Document** — add `adapters/<tool-id>/README.md`

3. **Test**:
   ```bash
   ./install.sh --dry-run
   ./install.sh
   ./install.sh --check
   ```

4. **Pull request** — include sample `install.sh --check` output

## Manifest schema

| Field | Purpose |
|-------|---------|
| `detect` | Config dir; tool considered installed if this exists |
| `detect_bins` | Extra detection via binary on PATH |
| `agents_md` | Global instructions file (merged with marker block) |
| `sync` | Hook-based sync (Cursor, Claude Code) |

## Check vs install

- **`install`** — only configures tools where `installed == true`
- **`check`** — reports all tools: missing / not configured / ok

Installed = config dir exists **or** any `detect_bins` binary found.

Configured = shared-agents marker or hook present in expected paths.

## Canonical paths (mandatory for agents)

All team files live under `$SHARED_AGENTS_HOME` (default `~/.shared-agents`), **not** in the Cursor workspace or customer project unless that path equals `$SHARED_AGENTS_HOME`.

| Action | Path |
|--------|------|
| Write learning draft | `$SHARED_AGENTS_HOME/learnings/pending/YYYY-MM-DD-slug.md` |
| Read team knowledge | `$SHARED_AGENTS_HOME/learnings/approved/` + `index.yaml` |
| Resolve path | `scripts/learning-path.sh <slug>` |

Full spec: [docs/canonical-paths.md](docs/canonical-paths.md). Update `capture-learning` and `rules/shared-agents-knowledge.mdc` when changing this contract.

## Shared MCPs (planned)

MCP server wiring is documented in [docs/shared-mcps.md](docs/shared-mcps.md). When implementing `install-mcps.py`:

- Follow the same patterns as `install-adapters.py` (stdlib, idempotent, `--check`, `--dry-run`)
- Never commit `mcps.local.yaml` or secrets in the manifest
- Use managed prefix `sa-` for team servers; leave user keys untouched

Reference: [mcps/manifest.example.json](mcps/manifest.example.json)

## Code style

- Installer: Python 3 stdlib only (no pip deps)
- Shell: `bash`, `set -euo pipefail`
- Idempotent: re-running install must be safe
