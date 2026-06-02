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
   ./scripts/install.sh --dry-run
   ./scripts/install.sh
   ./scripts/install.sh --check
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

## Code style

- Installer: Python 3 stdlib only (no pip deps)
- Shell: `bash`, `set -euo pipefail`
- Idempotent: re-running install must be safe
