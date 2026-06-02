---
id: shared-agents-2026-06-test-sa-review-workflow
project: shared-agents
domain: [infra, ai-tooling]
tags: [test, sa-review, git, workflow]
confidence: experimental
source: manual
created: 2026-06-02
author: quentin
---

## Kontext

Smoke-Test für den Learning-Workflow: pending anlegen → `sa-review` → auto commit/push nach Bitbucket.

## Erkenntnis

Learnings gehören nach `$SHARED_AGENTS_HOME/learnings/pending/`, nicht in den Cursor-Dev-Checkout. Review über `sa-review`; nach Approve committet `review-learning.py` nur `learnings/` und pusht — `origin` muss Bitbucket sein (`scripts/ensure-git-remote.sh`).

## Anwendung

1. Pending-Datei unter `~/.shared-agents/learnings/pending/`
2. `sa-review-list` → `sa-review <datei>` → bestätigen
3. Bei Push-Fehler: `bash ~/.shared-agents/scripts/ensure-git-remote.sh && git push`
4. Test-Learning nach Review wieder löschen oder als `experimental` belassen

## Links

- docs/canonical-paths.md
- scripts/review-learning.py
- scripts/ensure-git-remote.sh
