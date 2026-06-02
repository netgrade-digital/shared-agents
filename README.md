# Shared Agents

Team-weites **Skills- und Learnings-Repo** für KI-Assistenten. Tool-neutral (Markdown + Git), automatischer Sync, manifest-basierte Adapter für gängige IDEs und CLIs.

> **Ein Repo · Ein Pfad · Ein Format**  
> Remote: [bitbucket.org/netgrade/shared-agents](https://bitbucket.org/netgrade/shared-agents/src/main/)  
> Standardpfad: `~/.shared-agents` · Env: `$SHARED_AGENTS_HOME`

---

## Inhalt

- [Konzept](#konzept)
- [Quick Start](#quick-start)
- [Install & Check](#install--check)
- [Unterstützte Tools](#unterstützte-tools)
- [Automatischer Sync](#automatischer-sync)
- [Täglicher Ablauf](#täglicher-ablauf)
- [Repo-Struktur](#repo-struktur)
- [Learnings](#learnings)
- [Canonical Paths](#canonical-paths)
- [Skills](#skills)
- [Shared MCPs (geplant)](#shared-mcps-geplant)
- [Headless / CI](#headless--ci)
- [Neues Tool hinzufügen](#neues-tool-hinzufügen)
- [Troubleshooting](#troubleshooting)
- [Open Source](#open-source)

---

## Konzept

| Was | Rolle | Analogie |
|-----|-------|----------|
| **Skills** | Stabile Workflows („So machen wir X") | Firmen-Handbuch |
| **Learnings** | Wiederverwendbares Wissen („Y bricht wegen Z") | Team-Tagebuch |

```
                    ┌─────────────────────────┐
                    │  Bitbucket (Remote)     │
                    │  netgrade/shared-agents │
                    └───────────┬─────────────┘
                                │ git pull / push (PR)
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
   ~/.shared-agents       ~/.shared-agents       ~/.shared-agents
   + Cursor               + Zed                  + OpenClaw
   + Claude Code          + Codex                + …
```

- **Ein Repo** = Single Source of Truth für Skills + Learnings
- **Lokal** = `$SHARED_AGENTS_HOME` auf jedem Rechner / Container
- **Adapter** = dünne Schicht pro IDE/CLI (Hooks, AGENTS.md, Symlinks)
- **Sync** = automatisch — kein manuelles `git pull` im Alltag

---

## Quick Start

```bash
# 1. Klonen
git clone git@bitbucket.org:netgrade/shared-agents.git ~/.shared-agents
# oder HTTPS:
# git clone https://bitbucket.org/netgrade/shared-agents.git ~/.shared-agents

# 2. Setup — Wizard: Agenten auswählen, Adapter setzen, Check am Ende
~/.shared-agents/scripts/install.sh

# 3. Shell
export SHARED_AGENTS_HOME="$HOME/.shared-agents"
```

**Dev-Install** (lokaler Ordner, ohne Git-Remote):

```bash
cd /path/to/shared-agents
./scripts/install.sh --source "$(pwd)" --home "$HOME/.shared-agents"
```

**Neues KI-Tool installiert?** → `install.sh` erneut ausführen.

---

## Install & Check

Der Installer ist **manifest-driven** ([`adapters/manifest.json`](adapters/manifest.json)), idempotent und ohne Netzwerk-Calls.

### Setup-Wizard (empfohlen)

In einem Terminal startet `install.sh` automatisch den **interaktiven Wizard** (OpenClaw-Style):

```bash
~/.shared-agents/scripts/install.sh
# oder explizit:
~/.shared-agents/scripts/install.sh --wizard
```

Ablauf:

1. **Install-Pfad** — `SHARED_AGENTS_HOME` bestätigen (Default: `~/.shared-agents`)
2. **Agenten wählen** — Checkbox-Liste aller Tools aus dem Manifest
   - Nummer → an/aus
   - `all` / `detected` / `none`
   - Enter → weiter (Default: alle erkannten Tools)
3. **Shell** — `SHARED_AGENTS_HOME` in `~/.bashrc` exportieren?
4. **Summary + Bestätigung** — dann Setup + Check

Nicht-interaktiv (CI, Scripts):

```bash
install.sh --non-interactive              # alle erkannten Tools
install.sh --non-interactive --tools cursor,claude-code
install.sh --dry-run --wizard             # Wizard-Vorschau
```

### Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `install.sh` | Repo aktualisieren + **Wizard** (TTY) oder alle erkannten Tools |
| `install.sh --wizard` | Interaktiver Setup-Wizard |
| `install.sh --non-interactive` | Alle erkannten Tools ohne Prompts |
| `install.sh --tools cursor,claude-code` | Nur bestimmte Adapter |
| `install.sh --check` | Status: welche Tools installiert / konfiguriert? |
| `install.sh --check --json` | Wie oben, JSON (CI / Scripts) |
| `install.sh --dry-run` | Vorschau — keine Dateien schreiben |
| `install.sh --help` | Alle Optionen |

Optionen:

```bash
--source DIR     # Quell-Repo (Default: Parent von scripts/)
--home DIR       # Zielpfad (Default: ~/.shared-agents)
--shell-rc FILE  # Shell-RC für SHARED_AGENTS_HOME (Default: ~/.bashrc)
```

Low-level (von `install.sh` aufgerufen):

```bash
python3 scripts/install-adapters.py install ~/.shared-agents
python3 scripts/install-adapters.py check  ~/.shared-agents --json
```

### Erkennung (installed)

Ein Tool gilt als **installiert**, wenn mindestens eines zutrifft:

1. **Config-Ordner** existiert (`detect` in Manifest, z.B. `~/.cursor`)
2. **CLI-Binary** auf `$PATH` (`detect_bins`, z.B. `cursor`, `claude`, `aider`)

### Konfiguration (configured)

Ein Tool ist **konfiguriert**, wenn shared-agents aktiv ist:

- **Hook-Tools** (Cursor, Claude Code): Hook in `hooks.json` / `settings.json` + Rule/Script
- **AGENTS.md-Tools** (Zed, Codex, …): Marker-Block `<!-- shared-agents:begin -->` in globaler Config
- **Skills**: Symlinks in `~/.agents/skills/` etc. zeigen auf `$SHARED_AGENTS_HOME/skills/`

### Check-Ausgabe

```text
shared-agents check v0.1.0
SHARED_AGENTS_HOME=/home/you/.shared-agents
Repo: OK — ok

TOOL           INSTALLED  CONFIGURED   STATUS
cursor         yes        yes          ok
windsurf       no         no           missing_tool
zed            yes        no           not_configured
```

| STATUS | Bedeutung |
|--------|-----------|
| `ok` | Tool da + shared-agents eingerichtet |
| `missing_tool` | CLI/Config nicht gefunden |
| `not_configured` | Tool da, aber `install.sh` fehlt / veraltet |
| `available` | Fallback (generic instructions) |

### CI-Beispiel

```bash
#!/bin/bash
export SHARED_AGENTS_HOME="$HOME/.shared-agents"
"$SHARED_AGENTS_HOME/scripts/install.sh" --check --json | jq '.tools[] | select(.status != "ok" and .status != "missing_tool")'
```

---

## Unterstützte Tools

Vollständige Registry: [`adapters/manifest.json`](adapters/manifest.json)

| Tool | Sync | Was `install.sh` setzt | Docs |
|------|------|------------------------|------|
| Cursor | Hook | Rule + `sessionStart` hook | [cursor](adapters/cursor/README.md) |
| Claude Code | Hook | `SessionStart` hook | [claude-code](adapters/claude-code/README.md) |
| Zed | Agent¹ | `~/.config/zed/AGENTS.md` | [zed](adapters/zed/README.md) |
| Codex CLI | Agent¹ | `~/.codex/AGENTS.md` | [codex](adapters/codex/README.md) |
| OpenCode | Agent¹ | `~/.config/opencode/AGENTS.md` | [opencode](adapters/opencode/README.md) |
| Gemini CLI | Agent¹ | `~/.gemini/GEMINI.md` | [gemini](adapters/gemini/README.md) |
| Windsurf | Agent¹ | `~/.codeium/windsurf/AGENTS.md` | [windsurf](adapters/windsurf/README.md) |
| Continue.dev | Agent¹ | `~/.continue/AGENTS.md` | [continue](adapters/continue/README.md) |
| GitHub Copilot | Agent¹ | `~/.config/github-copilot/AGENTS.md` | [copilot](adapters/copilot/README.md) |
| Aider | Agent¹ | `~/.aider/AGENTS.md` | [aider](adapters/aider/README.md) |
| OpenClaw / headless | Entrypoint² | `agent-entrypoint.sh` | [openclaw](adapters/openclaw/README.md) |
| Beliebiges CLI | Agent¹ | [generic/instructions.md](adapters/generic/instructions.md) | [generic](adapters/generic/README.md) |

¹ **Agent-Sync** — globaler Instruction-Block: Agent führt `sync.sh pull` als ersten Shell-Befehl aus (ohne User-Rückfrage).

² **Entrypoint** — Wrapper startet immer mit Sync:

```bash
"$SHARED_AGENTS_HOME/scripts/agent-entrypoint.sh" <dein-agent-befehl>
```

---

## Automatischer Sync

Drei überlappende Sicherheitsnetze — absichtlich redundant:

```
Session / Thread start
        │
        ▼
┌───────────────────┐
│ 1. IDE/CLI Hook   │  Cursor, Claude Code → git pull (Hintergrund)
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 2. Instructions   │  AGENTS.md / Rule → sync als 1. Agent-Aktion
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ 3. Skill          │  shared-agents-knowledge → sync vor Learnings
└─────────┬─────────┘
          ▼
    Agent arbeitet
```

| Script | Aufgerufen von | Verhalten |
|--------|----------------|-----------|
| `sync.sh pull` | Hooks, Agent | `git pull --ff-only` |
| `session-sync.sh` | Cursor/Claude Hook | fail-open (blockiert IDE nie) |
| `agent-entrypoint.sh` | Headless/CI | sync → exec |

**Im Alltag kein manuelles Syncen.**

---

## Täglicher Ablauf

| Phase | Wer | Aktion |
|-------|-----|--------|
| Session Start | Hook / Agent | Neueste Learnings pullen |
| Vor Tasks | Agent | `learnings/approved/` + `index.yaml` durchsuchen |
| Nach großen Tasks | Agent → **du** | Frage: „Learning anlegen?" → bei **Ja**: `pending/` |
| Review | **Mensch** | PR → `approved/` + `index.yaml` → alle auto-sync |

---

## Repo-Struktur

```
shared-agents/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── skills/
│   ├── shared-agents-knowledge/   # Sync, Retrieve, Workflow
│   └── capture-learning/          # Learning-Vorschläge
├── learnings/
│   ├── README.md                  # pending vs approved + Schreibort
│   ├── approved/                  # Freigegeben
│   ├── pending/                   # KI-Entwürfe → PR
│   └── index.yaml                 # Suchindex
├── rules/
│   └── shared-agents-knowledge.mdc
├── scripts/
│   ├── install.sh                 # Entrypoint: install | check | dry-run
│   ├── install-adapters.py        # Detect, install, verify (stdlib only)
│   ├── learning-path.sh           # Canonical pending path ausgeben
│   ├── shell-aliases.sh           # sa-review, sa-sync, … (sourced from bashrc)
│   ├── configure-shell-rc.sh      # Idempotent bashrc block
│   ├── promote-learning.sh        # Kurzform: sofort promoten (-y)
│   ├── review-learning.sh         # Interaktiv: review + promote + index
│   ├── review-learning.py
│   ├── sync.sh
│   ├── session-sync.sh
│   └── agent-entrypoint.sh
├── docs/
│   ├── team-ki-setup.md           # Rollout / Abteilung
│   ├── shared-mcps.md             # MCP-Design (Entwurf)
│   └── canonical-paths.md         # Pflicht-Pfade für Agenten
├── mcps/
│   ├── manifest.example.json      # MCP-Manifest-Referenz
│   └── mcps.local.yaml.example    # Lokale Werte (nicht committen)
├── adapters/
│   ├── manifest.json              # Tool-Registry (detect, detect_bins, paths)
│   ├── cursor/ … generic/          # Pro-Tool Docs + Hook-Scripts
│   └── generic/instructions.md    # Auto-generiert bei install
└── skills-lock.json
```

---

## Learnings

### Datei-Format

```markdown
---
id: project-2026-05-short-slug
project: my-project
domain: [vue, laravel]
tags: [dropdown, sidebar]
confidence: high          # high | medium | experimental
source: task              # task | pr | incident | manual
created: 2026-05-28
author: name
---

## Kontext
Was ist passiert?

## Erkenntnis
Wiederverwendbare Erkenntnis.

## Anwendung
Konkrete Regel für nächstes Mal.

## Links
- path/to/file oder PR
```

### Workflow: pending → approved

Learnings haben **zwei Stufen**. Das ist der wichtigste Punkt:

```text
┌─────────────────────────────────────────────────────────────────┐
│ 1. AGENT (nach großem Task + dein „Ja")                        │
│    schreibt Entwurf →  learnings/pending/2026-05-28-foo.md      │
│    Status: Entwurf — andere sehen es noch NICHT als Wissen      │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. MENSCH (Review)                                              │
│    • Inhalt prüfen (keine Secrets, stimmt es?)                  │
│    • review-learning.sh …  (verschiebt + index.yaml automatisch) │
│    • git commit + PR → merge                                   │
└───────────────────────────────┬─────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. TEAM (automatisch)                                           │
│    sync pull → Learning liegt in learnings/approved/            │
│    Agent *soll* es bei passenden Tasks finden und nutzen        │
└─────────────────────────────────────────────────────────────────┘
```

| Ordner | Wer schreibt | Wer liest | Bedeutung |
|--------|--------------|-----------|-----------|
| **`pending/`** | Agent (nur nach deinem **Ja**) | Niemand als Wissensbasis | Vorschlag / Entwurf |
| **`approved/`** | Mensch (via PR) | Alle Agents | Offizielles Team-Wissen |

**Merksatz:** Agent erstellt **Vorschläge**. Erst **`approved/`** macht daraus Team-Wahrheit.

### Nach großen Tasks: immer fragen

Der Agent **muss** nach nicht-trivialen Tasks fragen:

> „Soll ich ein Team-Learning in shared-agents anlegen?"

| Deine Antwort | Was passiert |
|---------------|--------------|
| **Ja** | Agent schreibt Datei in `pending/` |
| **Nein** | Nichts |

In **Cursor** zusätzlich: `stop`-Hook erinnert den Agenten am Session-Ende.  
In **Zed/ andere CLIs**: steht in globaler `AGENTS.md` (via `install.sh`).

Der Agent schreibt **nie direkt** nach `approved/`.

**Pflicht-Pfad für Agenten:** Learnings-Entwürfe immer unter `$SHARED_AGENTS_HOME/learnings/pending/` — nicht im Cursor-Workspace oder Kunden-Projekt (siehe [Canonical Paths](#canonical-paths)).

```bash
"$SHARED_AGENTS_HOME/scripts/learning-path.sh" 2026-06-02-my-slug
# → …/learnings/pending/2026-06-02-my-slug.md
```

### Review (Mensch, ~30 Sek)

```bash
# Interaktiv: pending anzeigen, bestätigen, verschieben + index.yaml
sa-review

# Bestimmte Datei (Slug reicht — Pfad wird unter $SHARED_AGENTS_HOME aufgelöst)
sa-review 2026-05-28-sidebar-radix.md

# Nur anzeigen
sa-review-list
sa-review-dry 2026-05-28-sidebar-radix.md

# Domain überschreiben (Default: erstes Feld aus frontmatter domain)
sa-review 2026-05-28-sidebar-radix.md --domain vue
```

Aliase werden bei `install.sh` in `~/.bashrc` eingetragen (`scripts/shell-aliases.sh`). Nach Install: `source ~/.bashrc` oder neues Terminal.

Low-level (ohne Alias):

```bash
~/.shared-agents/scripts/review-learning.sh --list
```

Das Command:

1. zeigt den Entwurf
2. fragt `Approve and promote? [y/N]`
3. verschiebt nach `learnings/approved/by-domain/<domain>/`
4. trägt `learnings/index.yaml` automatisch ein (aus Frontmatter)
5. **committet und pusht** `learnings/` automatisch (`--no-git` zum Überspringen)

Danach ist das Learning im Remote — Team sync pull.

`promote-learning.sh` bleibt als Kurzform (`-y`, ohne Preview) — bevorzugt: `review-learning.sh`.

### Format

Team-Skills in `skills/`. `install.sh` symlinkt nach:

| Pfad | Tools |
|------|-------|
| `~/.agents/skills/` | Cursor, Zed, skills MCP |
| `~/.claude/skills/` | Claude Code |
| `~/.codex/skills/` | Codex CLI |
| `~/.config/opencode/skills/` | OpenCode |
| `~/.gemini/skills/` | Gemini CLI |

Skills liegen im Repo unter `skills/` — `install.sh` symlinkt sie nach `~/.agents/skills/` usw.  
([skills.sh](https://skills.sh) ist GitHub-zentriert; für Bitbucket reicht Clone + `install.sh`.)

---

## Shared MCPs (geplant)

Team-weite **MCP-Server** (Cursor `mcp.json`, später weitere IDEs) im gleichen Stil wie Adapter: **Manifest + lokale Overrides + Installer** — nicht als kopiertes JSON mit SSH/Docker-Details im Git.

| Dokument | Inhalt |
|----------|--------|
| [docs/shared-mcps.md](docs/shared-mcps.md) | Design, Ebenen, Merge-Strategie, Migration, Sicherheit |
| [mcps/README.md](mcps/README.md) | Kurzreferenz + Status |
| [mcps/manifest.example.json](mcps/manifest.example.json) | Schema-Referenz (Browser Tools, SF-Spider-Generator) |
| [mcps/mcps.local.yaml.example](mcps/mcps.local.yaml.example) | Vorlage für `~/.shared-agents/mcps.local.yaml` (gitignored) |

**Status:** Entwurf — `install-mcps.py` noch nicht implementiert. Team-Server sollen Prefix `sa-` nutzen; private MCP-Einträge bleiben beim Re-Install erhalten.

---

## Canonical Paths

**Pflicht für Agenten:** Dateien an feste Pfade unter `$SHARED_AGENTS_HOME` — nicht an den geöffneten Workspace.

| Dokument | Inhalt |
|----------|--------|
| [docs/canonical-paths.md](docs/canonical-paths.md) | Learnings, Skills, Sync — absolut vs. Workspace |
| [learnings/README.md](learnings/README.md) | Kurzregel pending/approved |
| `scripts/learning-path.sh` | Gibt Pfad für pending-Learning aus |

Learnings schreiben: `"${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/learnings/pending/…"` — Details in [docs/canonical-paths.md](docs/canonical-paths.md).

---

## Headless / CI

```bash
export SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"

# Agent immer über Entrypoint starten
"$SHARED_AGENTS_HOME/scripts/agent-entrypoint.sh" node run-agent.js

# Oder in Docker
ENV SHARED_AGENTS_HOME=/data/shared-agents
ENTRYPOINT ["/data/shared-agents/scripts/agent-entrypoint.sh"]
```

Details: [`adapters/openclaw/README.md`](adapters/openclaw/README.md)

---

## Neues Tool hinzufügen

1. Eintrag in [`adapters/manifest.json`](adapters/manifest.json):
   - `detect`, `detect_bins`, `agents_md` und/oder `sync`
2. `adapters/<tool-id>/README.md` anlegen
3. Testen:

```bash
./scripts/install.sh --dry-run
./scripts/install.sh
./scripts/install.sh --check
```

Siehe [CONTRIBUTING.md](CONTRIBUTING.md).

Unbekanntes CLI ohne Manifest: [`adapters/generic/instructions.md`](adapters/generic/instructions.md) in globale `AGENTS.md` / `CLAUDE.md` kopieren.

---

## Scope: global vs. projekt

| Scope | Ort | Inhalt |
|-------|-----|--------|
| Team-weit | `~/.shared-agents` | Skills, Learnings, Adapter |
| Projekt | `.shared-agents/` Submodule | Optional, gleicher Inhalt |
| Projekt-Regeln | Repo-`AGENTS.md`, `.cursor/rules/` | Nur dieses Projekt |

Team-Wissen global halten. Projekt-Regeln ergänzen, ersetzen nicht.

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Tool in Check = `missing_tool` | CLI installieren oder einmal starten (Config-Ordner), dann `install.sh` |
| Tool = `not_configured` | `install.sh` ausführen |
| Sync blockiert (Zed etc.) | `agent.tool_permissions.default: "allow"` oder einmal freigeben |
| Veraltete Learnings | `install.sh --check` → Hook/AGENTS.md prüfen; `sync.sh pull` testen |
| Learning fehlt beim Team | PR in `approved/`? `index.yaml` aktualisiert? |
| `install.sh --check --json` | Für exakte Pfade / Status pro Tool |

---

## Environment

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `SHARED_AGENTS_HOME` | `~/.shared-agents` | Lokaler Repo-Pfad |
| `CODEX_HOME` | — | Optional: Codex liest auch `$CODEX_HOME/AGENTS.md` |
| `SHELL_RC` | `~/.bashrc` | Nur bei `install.sh` für Env-Eintrag |

---

## Open Source

- **Lizenz:** [MIT](LICENSE)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Design:** Manifest-driven, Python-Stdlib-only Installer, idempotent, keine Netzwerk-Calls
- **Version:** Installer `v0.1.0` (siehe `install.sh` / `install-adapters.py --version`)

Repo: `https://bitbucket.org/netgrade/shared-agents` (Branch `main`).
