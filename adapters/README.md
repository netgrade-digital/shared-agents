# Adapters

Per-tool wiring is defined in [`manifest.json`](manifest.json). **`sa install`** configures detected tools; **`sa sync`** refreshes skill symlinks, rule symlinks (Cursor), and team-rules blocks in `AGENTS.md` / `CLAUDE.md`.

| Tool | Doc | Rules delivery |
|------|-----|----------------|
| [Cursor](cursor/README.md) | Hooks + `.mdc` symlinks | `~/.cursor/rules/` |
| [Claude Code](claude-code/README.md) | Session hook + `CLAUDE.md` | Marker block |
| [Zed](zed/README.md) | `~/.config/zed/AGENTS.md` | Marker block |
| [Codex CLI](codex/README.md) | `~/.codex/AGENTS.md` | Marker block |
| [OpenCode](opencode/README.md) | `~/.config/opencode/AGENTS.md` | Marker block |
| [Gemini CLI](gemini/README.md) | `~/.gemini/GEMINI.md` | Marker block |
| [Windsurf](windsurf/README.md) | `~/.codeium/windsurf/AGENTS.md` | Marker block |
| [Continue](continue/README.md) | `~/.continue/AGENTS.md` | Marker block |
| [Copilot](copilot/README.md) | `~/.copilot/AGENTS.md` | Marker block |
| [Aider](aider/README.md) | `~/.aider/AGENTS.md` | Marker block |
| [OpenClaw](openclaw/README.md) | Entrypoint wrapper (headless) | Read paths under `$SHARED_AGENTS_HOME` |
| [Kimi Code CLI](kimi/README.md) | `~/.kimi/AGENTS.md` | Marker block (best-effort) |
| [Generic](generic/README.md) | Copy-paste instructions | Manual |

Team content (all tools): `sa skill new|list|rm` · `sa rule new|list|rm` — see root [README.md](../README.md).

Repair symlink issues (e.g. Cursor rule as regular file): **`sa doctor --fix`**
