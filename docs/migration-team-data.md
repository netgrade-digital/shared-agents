# Migration: `learnings/` → `team/`

Wenn ihr **vor** dem Core/Team-Split Learnings unter `~/.shared-agents/learnings/` hattet, liegen sie am falschen Ort. Team-Wissen gehört ins **private Team-Repo** unter `team/`.

## Voraussetzungen

1. `config.local.yaml` mit `team.remote` (oder erneut **`sa bootstrap`**)
2. Leeres oder neues Team-Remote (oder bereit zum Merge)

## Automatisch (empfohlen)

```bash
sa team migrate --dry-run    # Vorschau
sa team migrate              # verschiebt learnings/ → team/learnings/
cd ~/.shared-agents/team && git status
git push                     # falls noch nicht gepusht
```

`sa check` / **`sa team verify`** melden Legacy-`learnings/` und Struktur-Probleme.

## Manuell

```bash
# 1) Team-Repo klonen/init (falls noch nicht)
sa bootstrap   # oder Team-URL in config.local.yaml

# 2) Inhalt verschieben
mv ~/.shared-agents/learnings ~/.shared-agents/team/learnings

# 3) Im Team-Repo committen
cd ~/.shared-agents/team
git add learnings/
git commit -m "chore(team): migrate learnings from core home"
git push
```

## Danach

- **`sa sync`** — Core + Team
- Pfade nur noch über **`sa pending path <slug>`** (zeigt `team/learnings/pending/…`)
- Core-Dev-Checkout (`Development/…/shared-agents`) enthält **keine** Learnings mehr

## Solo-Modus (ohne Team-Remote)

Ohne `team.remote` kann der Code weiter `core/learnings/` nutzen (Fallback). Für Teams mit privatem Wissen: immer **`team.remote`** setzen.
