# Learnings

Team-Wissen in Markdown. Zwei Stufen: **pending** (Entwurf) → **approved** (nach Review).

## Canonical path (Agenten — Pflicht)

Learnings **niemals** relativ zum Cursor-Workspace oder Kunden-Projekt schreiben.

```text
${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/learnings/pending/YYYY-MM-DD-short-slug.md
```

Details: [docs/canonical-paths.md](../docs/canonical-paths.md)

```bash
# Pfad anzeigen
sa pending path 2026-06-02-my-slug
# oder: "$SHARED_AGENTS_HOME/scripts/learning-path.sh" 2026-06-02-my-slug
```

| Ordner | Wer schreibt | Git | Agent nutzt als Wissen |
|--------|--------------|-----|-------------------------|
| `pending/` | Agent (nach Ja) | **Auto** `sa pending push` | **Nein** |
| `approved/` | Mensch via `sa review` | Auto bei Review | **Ja** |

Review (lokal oder im Team nach `sa sync`):

```bash
sa pending push 2026-06-02-my-slug.md   # nach Anlegen durch Agent
sa review list
sa review 2026-06-02-my-slug.md
```

**CLI:** `sa help` · auch `shared-agents` · `sharedagents`

| Befehl | Beschreibung |
|--------|--------------|
| `sa help` | Alle Befehle |
| `sa review` | Review / approve |
| `sa review list` | Pending-Liste |
| `sa pending push` | Pending ans Team pushen |
| `sa sync` | Pull |
| `sa unapprove` | Aus approved entfernen |

Definiert in `scripts/shell-aliases.sh`, eingebunden via `scripts/configure-shell-rc.sh`.

**Unapprove:** `sa unapprove` — Wizard: **[1] Löschen** oder **[2] Nach pending/** (`--to-pending` / `--delete` nur für Scripts mit `-y`).

**Uninstall:** `sa uninstall` (Bestätigung: **y/N**) — `--keep-repo` behält den Git-Checkout.
