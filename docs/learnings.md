# Learnings (Team-Daten — nicht im Core-Repo)

Learnings leben im **privaten Team-Repo** unter `$SHARED_AGENTS_HOME/team/` (nach `sa bootstrap`), nicht im öffentlichen Core.

## Pfade

```text
${SHARED_AGENTS_HOME}/team/learnings/pending/YYYY-MM-DD-short-slug.md
${SHARED_AGENTS_HOME}/team/learnings/approved/…
${SHARED_AGENTS_HOME}/team/learnings/index.yaml
```

Pfad anzeigen:

```bash
sa pending path 2026-06-02-my-slug
```

| Ordner | Wer schreibt | Agent nutzt als Wissen |
|--------|--------------|-------------------------|
| `pending/` | Agent (nach deinem Ja) | Nein |
| `approved/` | Mensch via `sa review` | Ja |

## Workflow

```bash
sa pending push <datei>    # Entwurf ans Team
sa review list
sa review <datei>          # → approved + push (nur team/)
sa sync                    # Core + Team pullen
```

Details: [canonical-paths.md](canonical-paths.md) · Skills `capture-learning`, `shared-agents-knowledge`

**Prüfen:** `sa team verify` · **Migration** von altem `learnings/`: [migration-team-data.md](migration-team-data.md) · `sa team migrate`
