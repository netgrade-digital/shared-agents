---
id: shared-agents-2026-06-shared-mcps-manifest
project: shared-agents
domain: [infra, ai-tooling, seo]
tags: [mcp, cursor, manifest, installer, screaming-frog, team-setup]
confidence: high
source: task
created: 2026-06-02
author: quentin
---

## Kontext

MCP-Server (z. B. Browser Tools, Screaming Frog über SSH/Docker) liegen pro Person in `~/.cursor/mcp.json`. Copy-Paste führt zu dutzenden nahezu identischen Einträgen; Hosts und Container-Namen sind maschinenspezifisch und gehören nicht ins Team-Git.

## Erkenntnis

Shared MCPs folgen dem gleichen Muster wie IDE-Adapter: **Manifest im Repo + gitignored lokale YAML + idempotenter Installer** — nicht die fertige `mcp.json`. Team-Server nutzen Prefix `sa-`; private MCP-Einträge ohne dieses Prefix bleiben beim Re-Install unangetastet. Betriebswissen (Parallel-Crawls, Speicher, NDA) landet in **Learnings**, nicht in Args-Listen im Manifest.

## Anwendung

1. Schema und Design: `docs/shared-mcps.md`, Beispiel-Manifest: `mcps/manifest.example.json`
2. Lokale Werte: `mcps/mcps.local.yaml.example` → `~/.shared-agents/mcps.local.yaml` (nie committen)
3. Wiederholte Server (z. B. N Spider): **Generator** mit `spider_count` in lokaler YAML — nicht N× JSON im Git
4. Optional/Infra-MCPs: `detect` vor Install; ohne SSH/VPN → nicht eintragen, Check = `not_available`
5. Implementierung offen: `scripts/install-mcps.py` + Hook in `install.sh --check` (Checkliste in `docs/shared-mcps.md` §13)
6. Projekt-spezifische MCPs: optional `.cursor/mcp.json` im Kundenrepo — ohne Secrets, ohne Team-Hosts duplizieren
7. Learnings schreiben: immer `$SHARED_AGENTS_HOME/learnings/pending/` (siehe `docs/canonical-paths.md`)

## Links

- docs/shared-mcps.md
- docs/canonical-paths.md
- mcps/manifest.example.json
- mcps/mcps.local.yaml.example
