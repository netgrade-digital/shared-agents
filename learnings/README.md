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

| Ordner | Wer schreibt | Agent nutzt als Wissen |
|--------|--------------|-------------------------|
| `pending/` | Agent (nach Ja) | **Nein** |
| `approved/` | Mensch (PR) | **Ja** |

Review: `scripts/review-learning.sh learnings/pending/<file>.md` (aus `$SHARED_AGENTS_HOME` ausführen).

**Shell-Aliase** (via `install.sh` → `~/.bashrc`):

| Alias | Aktion |
|-------|--------|
| `sa-review` | Interaktiv reviewen / Datei oder Slug übergeben |
| `sa-review-list` | Pending-Liste |
| `sa-review-dry` | Dry-run |
| `sa-unapprove` | Learning aus `approved/` entfernen |
| `sa-unapprove-list` | Approved-Liste |
| `sa-learning-path` | Canonical pending-Pfad ausgeben |
| `sa-sync` | `sync.sh pull` |
| `sa-check` | `install.sh --check` |
| `sa-uninstall` | shared-agents restlos deinstallieren |

Definiert in `scripts/shell-aliases.sh`, eingebunden via `scripts/configure-shell-rc.sh`.

**Unapprove:** `sa-unapprove fantasy-2026-06-dragon-cache-invalidation` — optional `--to-pending` verschiebt zurück nach pending.

**Uninstall:** `sa-uninstall` (Bestätigung: **y/N**) — `--keep-repo` behält den Git-Checkout.
