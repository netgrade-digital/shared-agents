---
id: fantasy-2026-06-dragon-cache-invalidation
project: shared-agents
domain: [infra, fantasy]
tags: [fantasy, test, cache, dragons, experimental]
confidence: experimental
source: manual
created: 2026-06-02
author: quentin
---

## Kontext

Im Reich **Bitbucketia** lagern Team-Learnings in `$SHARED_AGENTS_HOME`. Ein Drache namens *Rebase* verwirrte Reisende, die `sa-sync` riefen, wenn ihre Schriftrollen noch unleserlich waren (uncommitted changes).

## Erkenntnis

Drachen besiegt man nicht mit `--force`, sondern mit **`fetch` + `merge --ff-only`**. Pending-Schriften gehören in die Tasche `learnings/pending/`; erst nach Ritual `sa-review` wandern sie in die Halle `approved/` und werden per Taube (git push) zum Königreich gesendet.

## Anwendung

1. Schriftrolle schreiben: `~/.shared-agents/learnings/pending/YYYY-MM-DD-slug.md`
2. `sa-review-list` — prüfen, welche Entwürfe schlummern
3. `sa-review` — Drache füttern, approve, commit, push
4. Bei origin auf lokalem Dev-Schloss: `ensure-git-remote.sh` ruft Bitbucket an
5. Fantasie-Learnings nach Review löschen oder als `experimental` belassen — nicht in Produktions-Runbooks zitieren

## Links

- docs/canonical-paths.md
- scripts/review-learning.py
