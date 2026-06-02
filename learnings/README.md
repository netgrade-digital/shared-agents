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
"$SHARED_AGENTS_HOME/scripts/learning-path.sh" 2026-06-02-my-slug
```

| Ordner | Wer schreibt | Git | Agent nutzt als Wissen |
|--------|--------------|-----|-------------------------|
| `pending/` | Agent (nach Ja) | **Auto** `sa-pending-push` | **Nein** |
| `approved/` | Mensch via `sa-review` | Auto bei Review | **Ja** |

Review (lokal oder im Team nach `sa-sync`):

```bash
sa-pending-push 2026-06-02-my-slug.md   # nach Anlegen durch Agent
sa-review-list
sa-review 2026-06-02-my-slug.md
```

**Shell-Aliase** (via `install.sh` → `~/.bashrc`):

| Alias | Aktion |
|-------|--------|
| `sa-review` | Interaktiv reviewen / Datei oder Slug übergeben |
| `sa-review-list` | Pending-Liste |
| `sa-pending-push` | Pending commit + push (Team-Review) |
| `sa-review-dry` | Dry-run |
| `sa-unapprove` | Learning aus `approved/` entfernen |
| `sa-unapprove-list` | Approved-Liste |
| `sa-learning-path` | Canonical pending-Pfad ausgeben |
| `sa-sync` | `sync.sh pull` |
| `sa-check` | `install.sh --check` |
| `sa-uninstall` | shared-agents restlos deinstallieren |

Definiert in `scripts/shell-aliases.sh`, eingebunden via `scripts/configure-shell-rc.sh`.

**Unapprove:** `sa-unapprove` — Wizard: **[1] Löschen** oder **[2] Nach pending/** (`--to-pending` / `--delete` nur für Scripts mit `-y`).

**Uninstall:** `sa-uninstall` (Bestätigung: **y/N**) — `--keep-repo` behält den Git-Checkout.
