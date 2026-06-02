---
id: example-2026-05-shared-knowledge-setup
project: shared-agents
domain: [infra, ai-tooling]
tags: [skills, learnings, sync, git, multi-cli]
confidence: high
source: manual
created: 2026-05-28
author: team
---

## Kontext

Team nutzt viele KI-Tools (Cursor, Zed, Claude Code, Codex, …). Sync und Wissen müssen überall gleich sein, ohne manuelles `git pull`.

## Erkenntnis

Ein Repo unter `~/.shared-agents` + einmal `install.sh`. Das Script liest `adapters/manifest.json` und konfiguriert alle erkannten CLIs (Hooks oder globale AGENTS.md). Headless: `agent-entrypoint.sh`.

## Anwendung

1. `install.sh` einmal pro Rechner
2. Neues CLI installiert → `install.sh` erneut
3. Unbekanntes CLI → `adapters/generic/instructions.md` in globale Config kopieren

## Links

- adapters/manifest.json
- scripts/install-adapters.py
