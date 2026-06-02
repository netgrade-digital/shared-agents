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
| Team-Skills (Quelle) | `$SHARED_AGENTS_HOME/skills/` | Mensch (PR) |
| Learnings Index | `$SHARED_AGENTS_HOME/learnings/index.yaml` | Mensch / **`sa review`** |
| Learnings **approved** | `$SHARED_AGENTS_HOME/learnings/approved/` | **Nur Mensch** (`sa review`) |
| Learnings **pending** | `$SHARED_AGENTS_HOME/learnings/pending/` | **Agent** (nach explizitem Ja) |
| Sync | `$SHARED_AGENTS_HOME/scripts/sync.sh` | Hook / Agent / **`sa sync`** |
| Adapter-Manifest | `$SHARED_AGENTS_HOME/adapters/manifest.json` | Mensch (PR) |
| MCP-Manifest (Entwurf) | `$SHARED_AGENTS_HOME/mcps/manifest.example.json` | Mensch (PR) |
| MCP lokal (gitignored) | `$SHARED_AGENTS_HOME/mcps.local.yaml` | User |

---

## Regel: Learnings — immer `$SHARED_AGENTS_HOME`

Agenten **müssen** Learnings-Entwürfe hier ablegen:

```text
${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/learnings/pending/YYYY-MM-DD-short-slug.md
```

### Verboten

- Learnings in den **Cursor-Workspace** schreiben (z. B. `Development/Work/shared-agents/learnings/pending/`), **wenn** das nicht derselbe Pfad wie `$SHARED_AGENTS_HOME` ist
- Learnings im **Kunden-Projekt** (`.cursor/`, `docs/`, Projekt-Root)
- Relative Pfade wie `learnings/pending/foo.md` ohne aufgelöstes `$SHARED_AGENTS_HOME`
- Direkt nach `learnings/approved/` schreiben

### Pflicht vor dem Schreiben

1. Pfad explizit auflösen: `"${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/learnings/pending/…"`
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
# → /home/you/.shared-agents/learnings/pending/2026-06-02-my-slug.md
```

Shell-CLI (nach **`sa install`** in `~/.bashrc`): **`sa`** · `shared-agents` · `sharedagents` — **`sa` ohne Argument = `sa help`**.  
Vollständige Bedienung: Skill **`sa-cli`** · Live-Referenz: **`sa help`**

---

## Regel: Lesen (Retrieve)

Vor nicht-trivialen Tasks:

1. **`sa sync`** (oder `"$SHARED_AGENTS_HOME/scripts/sync.sh" pull`)
2. `$SHARED_AGENTS_HOME/learnings/index.yaml`
3. Grep in `$SHARED_AGENTS_HOME/learnings/approved/`

Nicht nur im Workspace suchen.

---

## Regel: Skills symlinks

Installierte Skills liegen unter `~/.agents/skills/` etc. und zeigen auf `$SHARED_AGENTS_HOME/skills/`. Quelle bearbeiten = Dateien unter `$SHARED_AGENTS_HOME/skills/` (bzw. Dev-Checkout, der nach Pull synchron ist).

---

## Siehe auch

- [README.md](../README.md) — Learnings-Workflow
- [skills/sa-cli/SKILL.md](../skills/sa-cli/SKILL.md) — CLI-Bedienung
- [skills/capture-learning/SKILL.md](../skills/capture-learning/SKILL.md)
- [rules/shared-agents-knowledge.mdc](../rules/shared-agents-knowledge.mdc)
