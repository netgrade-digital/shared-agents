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

**CLI:** `sa` · `sa help` · `shared-agents` · `sharedagents` — ohne Argument = Hilfe-Übersicht  
Vollständige Bedienung: Skill **`sa-cli`** in `$SHARED_AGENTS_HOME/skills/` (ergänzt `sa help`)

| Befehl | Beschreibung |
|--------|--------------|
| `sa` | Hilfe-Übersicht (Default) |
| `sa help` | Wie `sa` — alle Befehle |
| `sa review` | Review / approve |
| `sa review list` | Pending-Liste |
| `sa pending push` | Pending ans Team pushen |
| `sa sync` | Pull |
| `sa unapprove` | Aus approved entfernen |

Definiert in `scripts/shell-aliases.sh`, eingebunden via `scripts/configure-shell-rc.sh` (bei `sa install`).

Shell-CLI nach Install: **`sa`** ohne Argument = Hilfe · **`sa help`** = gleich

## Frontmatter: `versions`

Bei Framework-/Runtime-Wissen immer die **verifizierte Version** angeben:

```yaml
versions: [shopware:6.6.10, php:8.3.14]
versions: [laravel:11.31.0]
versions: []   # nur wenn kein Stack (z. B. reines Team-Workflow-Wissen)
```

**Format:** mindestens `MAJOR.MINOR.PATCH` (drei Zahlen), keine Wildcards (`6.6.x`). Vierter Teil nur wenn vom Produkt geliefert; `.0` am Ende weglassen (`6.6.10.0` → `6.6.10`).

Agents und Reviewer: Version aus Projektdateien (`composer.lock`, `package-lock.json`, Shopware-CLI) — die **exakte** Version, gegen die die Erkenntnis geprüft wurde.

**Unapprove:** `sa unapprove` — Wizard: **[1] Löschen** oder **[2] Nach pending/** (`--to-pending` / `--delete` nur für Scripts mit `-y`).

**Uninstall:** `sa uninstall` (Bestätigung: **y/N**) — `--keep-repo` behält den Git-Checkout.
