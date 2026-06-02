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
