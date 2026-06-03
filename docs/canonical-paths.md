# Canonical Paths (Pflicht für Agenten)

**Single Source of Truth für Dateipfade** in shared-agents. Agenten und Skripte müssen diese Pfade verwenden — nicht den Cursor-Workspace, nicht das Kunden-Projekt.

Env-Variable:

```bash
SHARED_AGENTS_HOME="${SHARED_AGENTS_HOME:-$HOME/.shared-agents}"
```

Default: `~/.shared-agents`

---

## Pflicht-Pfade

| Was | Absoluter Pfad | Wer schreibt |
|-----|----------------|--------------|
| Core-Skills (OSS) | `$SHARED_AGENTS_HOME/skills/` | Upstream (PR ins Core) |
| Team-Skills | `$SHARED_AGENTS_HOME/team/skills/` | Team-Repo (privat) |
| Learnings Index | `$SHARED_AGENTS_HOME/team/learnings/index.yaml` | Mensch / **`sa review`** |
| Learnings **approved** | `$SHARED_AGENTS_HOME/team/learnings/approved/` | **Nur Mensch** (`sa review`) |
| Learnings **pending** | `$SHARED_AGENTS_HOME/team/learnings/pending/` | **Agent** (nach explizitem Ja) |
| Lokale Config | `$SHARED_AGENTS_HOME/config.local.yaml` | Installer / **`sa bootstrap`** (gitignored) |
| Team-Daten (privat) | `$SHARED_AGENTS_HOME/team/` | Eigenes Git-Remote — **nie** ins Core-Remote committen |
| Sync | `$SHARED_AGENTS_HOME/scripts/sync.sh` | Hook / Agent / **`sa sync`** |
| Adapter-Manifest | `$SHARED_AGENTS_HOME/adapters/manifest.json` | Mensch (PR) |
| MCP-Manifest (Entwurf) | `$SHARED_AGENTS_HOME/mcps/manifest.example.json` | Mensch (PR) |
| MCP lokal (gitignored) | `$SHARED_AGENTS_HOME/mcps.local.yaml` | User |

---

## Regel: Learnings — immer `$SHARED_AGENTS_HOME`

Agenten **müssen** Learnings-Entwürfe hier ablegen:

```text
${SHARED_AGENTS_HOME}/team/learnings/pending/YYYY-MM-DD-short-slug.md
```

Auflösung per CLI: `sa pending path <slug>` (nutzt `config.local.yaml` / Solo-Fallback).

**Nicht im Core-Repo:** Learnings liegen nur im privaten Team-Clone unter `team/` — siehe [learnings.md](learnings.md).

### Verboten

- Learnings in den **Cursor-Workspace** oder ins **Core-Repo** committen
- Learnings in den Dev-Checkout `Development/…/shared-agents/` schreiben, **wenn** das nicht `$SHARED_AGENTS_HOME` ist
- Learnings im **Kunden-Projekt** (`.cursor/`, `docs/`, Projekt-Root)
- Relative Pfade wie `learnings/pending/foo.md` ohne aufgelöstes `$SHARED_AGENTS_HOME`
- Direkt nach `learnings/approved/` schreiben

### Pflicht vor dem Schreiben

1. Pfad explizit auflösen: `sa pending path <slug>` oder `"${SHARED_AGENTS_HOME}/team/learnings/pending/…"`
2. Optional prüfen: Zielverzeichnis existiert (sonst anlegen)
3. **Nicht** annehmen, dass Workspace-Root = `$SHARED_AGENTS_HOME`

### Zwei Klone (typisches Setup)

| Pfad | Rolle |
|------|--------|
| `~/.shared-agents/` | **Laufzeit** — Sync, Hooks, Agent schreibt Learnings **hierher** |
| `~/Development/…/shared-agents/` | **Dev-Checkout** — Repo-Entwicklung (README, Skripte, Doku) |

Git-Commit für ein Learning: aus dem Clone, in dem die Datei liegt (meist `~/.shared-agents`), oder nach `git pull` im Dev-Checkout — **Schreibort bleibt immer `$SHARED_AGENTS_HOME`**.

Hilfsskript:

```bash
sa pending path 2026-06-02-my-slug
# oder: "$SHARED_AGENTS_HOME/scripts/learning-path.sh" 2026-06-02-my-slug
# → /home/you/.shared-agents/team/learnings/pending/2026-06-02-my-slug.md
```

Shell-CLI (nach **`sa install`** in `~/.bashrc`): **`sa`** · `shared-agents` · `sharedagents` — **`sa` ohne Argument = `sa help`**.  
Vollständige Bedienung: Skill **`sa-cli`** · Live-Referenz: **`sa help`**

---

## Regel: Lesen (Retrieve)

Vor nicht-trivialen Tasks:

1. **`sa sync`** (oder `"$SHARED_AGENTS_HOME/scripts/sync.sh" pull`)
2. `$SHARED_AGENTS_HOME/team/learnings/index.yaml`
3. Grep in `$SHARED_AGENTS_HOME/team/learnings/approved/`

Nicht nur im Workspace suchen.

---

## Regel: Skills symlinks

Installierte Skills liegen unter `~/.agents/skills/` etc. und zeigen auf `$SHARED_AGENTS_HOME/skills/`. Quelle bearbeiten = Dateien unter `$SHARED_AGENTS_HOME/skills/` (bzw. Dev-Checkout, der nach Pull synchron ist).

---

## Siehe auch

- [learnings.md](learnings.md) — Workflow (Team-Repo)
- [README.md](../README.md) — Übersicht
- [skills/sa-cli/SKILL.md](../skills/sa-cli/SKILL.md) — CLI-Bedienung
- [skills/capture-learning/SKILL.md](../skills/capture-learning/SKILL.md)
- [rules/shared-agents-knowledge.mdc](../rules/shared-agents-knowledge.mdc)
