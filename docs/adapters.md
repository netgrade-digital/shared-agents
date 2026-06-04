# Adapters

Adapters wire Shared Agents into each AI tool: session hooks, skill symlinks, rule symlinks, and merged instruction files.

Configuration is driven by [`adapters/manifest.json`](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/manifest.json).

| Command | Purpose |
|---------|---------|
| **`sa install`** | Configure detected tools (first time or new tool) |
| **`sa sync`** | Refresh symlinks and `AGENTS.md` / `CLAUDE.md` blocks |
| **`sa check`** | Installed vs configured matrix |
| **`sa doctor --fix`** | Repair broken rule symlinks |

**Installed** ≠ **configured**. `sa install` only touches tools detected as installed.

---

## Supported tools

| Tool | Adapter ID | Rules delivery | Details |
|------|------------|----------------|---------|
| Cursor IDE | `cursor` | `~/.cursor/rules/` symlinks | [cursor/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/cursor/README.md) |
| Claude Code | `claude-code` | `~/.claude/CLAUDE.md` marker | [claude-code/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/claude-code/README.md) |
| Zed | `zed` | `~/.config/zed/AGENTS.md` | [zed/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/zed/README.md) |
| OpenAI Codex CLI | `codex` | `~/.codex/AGENTS.md` | [codex/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/codex/README.md) |
| OpenCode | `opencode` | `~/.config/opencode/AGENTS.md` | [opencode/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/opencode/README.md) |
| Gemini CLI | `gemini` | `~/.gemini/GEMINI.md` | [gemini/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/gemini/README.md) |
| Windsurf | `windsurf` | `~/.codeium/windsurf/AGENTS.md` | [windsurf/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/windsurf/README.md) |
| Continue.dev | `continue` | `~/.continue/AGENTS.md` | [continue/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/continue/README.md) |
| GitHub Copilot | `copilot` | Copilot `AGENTS.md` paths | [copilot/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/copilot/README.md) |
| Aider | `aider` | `~/.aider/AGENTS.md` | [aider/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/aider/README.md) |
| OpenClaw / headless | `openclaw` | Reads `$SHARED_AGENTS_HOME` | [openclaw/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/openclaw/README.md) |
| Generic / manual | `generic` | Copy-paste instructions | [generic/README](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/generic/README.md) |

---

## What `sa sync` does per tool

1. **Skill symlinks** — Core + team skills → `~/.agents/skills`, `~/.claude/skills`, etc.
2. **Cursor rule symlinks** — Core + team `.mdc` → `~/.cursor/rules/`
3. **Team-rules blocks** — Injected between markers in each tool’s global agents file

Session hooks (where configured) run **`sa sync`** quietly at session start.

---

## Cursor

- Hook: `sessionStart` → `shared-agents-sync.sh`
- Rules: symlinked `.mdc` files
- If a rule path is a regular file, **`sa doctor --fix`** backs it up and relinks

---

## Claude Code, Zed, Codex, …

- Merged blocks in `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`
- Base block: `<!-- shared-agents:begin -->` (sync + learnings hints)
- Team rules block: `<!-- shared-agents:team-rules:begin/end -->`

Zed has no session hook — agents should run sync as an early step when needed.

---

## Adding a new tool (contributors)

1. Add entry to `adapters/manifest.json` (`detect`, `detect_bins`, `agents_md`, `sync`, …)
2. Add `adapters/<tool-id>/README.md`
3. Run `sa install --dry-run`, `sa install`, `sa check`
4. Open a PR with sample `sa check` output

See [Contributing](/docs/contributing).

---

## Generic fallback

If your CLI is not in the manifest, copy [adapters/generic/instructions.md](https://github.com/netgrade-digital/shared-agents/blob/main/adapters/generic/instructions.md) into your global agent config and set `$SHARED_AGENTS_HOME`.

---

## See also

- [Installation](/docs/installation)
- [Skills and rules](/docs/skills-and-rules)
- [CLI reference](/docs/cli-reference)
