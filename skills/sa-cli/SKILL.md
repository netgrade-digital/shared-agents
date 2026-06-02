---
name: sa-cli
description: >-
  Complete guide to the shared-agents shell CLI (sa). Use when the user asks
  how to run sa, sa help, install, sync, review, pending, unapprove, check,
  uninstall, status, or any shared-agents terminal command. Also use when explaining
  setup, wizard, or troubleshooting the CLI after sa install.
---

# shared-agents CLI (`sa`)

**Canonical live help:** run **`sa`** or **`sa help`** — always prefer that over memorizing flags.

```bash
sa                  # Hilfe-Übersicht (Default ohne Argument)
sa help             # gleich
shared-agents …     # Alias
sharedagents …      # Alias
```

Without shell aliases (agents, CI, fresh shell):

```bash
"${SHARED_AGENTS_HOME:-$HOME/.shared-agents}/scripts/sa" help
```

Repo root (Dev-Checkout): **`./sa`** · **`./sa install`**

Env: **`SHARED_AGENTS_HOME`** (default `~/.shared-agents`) · Version: **`sa version`**

---

## Erst-Setup (typischer Ablauf)

```bash
git clone git@bitbucket.org:netgrade/shared-agents.git ~/.shared-agents
cd ~/.shared-agents
./sa install              # Wizard (TTY) — oder: sa install nach bashrc
source ~/.bashrc          # sa | shared-agents | sharedagents aktiv
sa check                  # Adapter-Status
```

**Bootstrap ohne Clone:** aus Dev-Checkout `./sa install` — Wizard **vor** Clone; Abbruch legt **kein** `~/.shared-agents` an.

**Neues KI-Tool installiert?** → `sa install` erneut.

---

## Befehle (Übersicht)

| Bereich | Befehl | Kurz |
|---------|--------|------|
| Info | `sa` · `sa help` | Alle Befehle |
| Info | `sa version` | CLI-Version + HOME |
| Setup | `sa install` | Wizard (Standard im Terminal) |
| Setup | `sa install --non-interactive` | Alle erkannten Tools, ohne Prompts |
| Setup | `sa install --wizard` | Wizard explizit |
| Setup | `sa check` | Tool installiert vs. konfiguriert |
| Setup | `sa sync` | `git pull` Learnings (ff-only) |
| Setup | `sa status` | Offene Punkte: Review, Skills, Adapter |
| Setup | `sa uninstall` | Deinstallieren (y/N) |
| Learnings | `sa review` | Interaktiv: pending → approved |
| Learnings | `sa review list` | Pending-Liste |
| Learnings | `sa review dry [file]` | Dry-run |
| Learnings | `sa pending push [file]` | pending commit + push |
| Learnings | `sa pending path [slug]` | Canonical pending-Pfad |
| Learnings | `sa unapprove [id\|file]` | Aus approved entfernen |
| Learnings | `sa unapprove list` | Approved-Liste |

Alias: **`sa install`** = **`sa setup`**

---

## Status / Erinnerungen — `sa status`

Zeigt, was leicht vergessen wird:

| Prüfung | Bedeutung | Aktion |
|---------|-----------|--------|
| Pending-Learnings | Dateien in `learnings/pending/` | `sa review list` · `sa review` |
| Noch nicht gepusht | Lokale pending-Änderungen | `sa pending push` |
| Skill-Symlinks | Neuer Skill im Repo, nicht verlinkt | `sa install` |
| Adapter | Tool da, nicht konfiguriert | `sa install` |

```bash
sa status              # Vollständige Liste (oder „alles erledigt ✓“)
sa status --brief      # Eine Zeile
sa status --quiet      # Nur ausgeben wenn Handlung nötig (exit 1)
sa status --json       # CI / Scripts
```

**Automatisch nach Pull:** `sa sync` (nicht `--quiet`) ruft `sa status --quiet` auf — Kurzhinweis direkt im Terminal.

Cursor/Claude Session-Hook syncen still (`--quiet`); dort erinnert die **Rule** den Agenten, **`sa status --brief`** zu prüfen und dich kurz zu informieren.

---

## Setup — `sa install`

Ruft `install.sh` auf (manifest-driven, idempotent).

### Wizard (empfohlen, TTY)

```bash
sa install
```

| Schritt | Steuerung |
|---------|-----------|
| Install-Pfad | Pfad tippen · Enter |
| Agenten | `↑↓` · **Space** an/aus · `a` alle · `d` erkannte · Enter |
| Shell-CLI | `←→` / `↑↓` Ja/Nein · Enter |
| Summary | `↑↓` Run/Cancel · Enter (Default: Cancel) |

- **Cursor / VS Code Terminal:** oft Text-Wizard (`SA_WIZARD_PLAIN=1` automatisch)
- **foot / alacritty:** TUI mit Pfeiltasten

### Schnell / CI

```bash
sa install --non-interactive
sa install --non-interactive --tools cursor,claude-code
sa install --dry-run
sa install --dry-run --wizard
```

### Install-Optionen (an `install.sh` durchgereicht)

| Flag | Bedeutung |
|------|-----------|
| `--home DIR` | Zielpfad (Default: `~/.shared-agents`) |
| `--source DIR` | Quell-Repo (Dev-Checkout) |
| `--shell-rc FILE` | bashrc für `SHARED_AGENTS_HOME` + `sa` (Default: `~/.bashrc`) |
| `--tools IDS` | Nur bestimmte Adapter (kommagetrennt) |
| `--check` | Status statt Install (`sa check`) |
| `--check --json` | JSON für CI |
| `--dry-run` | Vorschau, keine Writes |

Low-level: `./install.sh` im Repo-Root — gleiche Optionen.

---

## Status — `sa check`

```bash
sa check
sa check --json          # CI / Scripts
sa install --check       # gleich
```

| STATUS | Bedeutung |
|--------|-----------|
| `ok` | Tool da + shared-agents eingerichtet |
| `missing_tool` | CLI/Config nicht gefunden |
| `not_configured` | Tool da, Adapter fehlt/veraltet → `sa install` |
| `available` | generic fallback |

---

## Sync — `sa sync`

```bash
sa sync
# = "$SHARED_AGENTS_HOME/scripts/sync.sh" pull
```

- ff-only pull von Bitbucket
- Agenten: am Session-Start (Hook + Rule); manuell nur bei Offline/Debug

---

## Learnings-Workflow

```text
Agent schreibt pending/  →  sa pending push  →  sa review  →  approved/
```

### Pending veröffentlichen — `sa pending push`

```bash
sa pending push 2026-06-02-my-slug.md
sa pending push              # unstaged pending/*.md
# Flags: --all --dry-run --no-git
```

### Review — `sa review`

```bash
sa review list
sa review dry 2026-06-02-my-slug.md
sa review                    # interaktiv: Datei wählen
sa review 2026-06-02-my-slug.md
```

| Flag | Bedeutung |
|------|-----------|
| `--domain DOMAIN` | Ziel-Ordner unter `approved/by-domain/` |
| `--dry-run` | Nur anzeigen |
| `--no-git` | Kein commit/push |
| `-y` / `--yes` | Ohne Bestätigung |

Verschiebt nach `learnings/approved/`, trägt `index.yaml` ein, commit + push (nur `learnings/`).

### Pfad auflösen — `sa pending path`

```bash
sa pending path 2026-06-02-my-slug
# → …/learnings/pending/2026-06-02-my-slug.md
```

### Unapprove — `sa unapprove`

```bash
sa unapprove list
sa unapprove fantasy-2026-06-dragon-cache
# Wizard: [1] Löschen  [2] Nach pending/  [q] Abbrechen
```

| Flag | Bedeutung |
|------|-----------|
| `--to-pending` | Nach pending/ (non-interactive) |
| `--delete` | Datei löschen (non-interactive) |
| `--dry-run` · `--no-git` · `-y` | wie bei review |

Alias: **`sa unapprove`** = **`sa rm`** (Learning entfernen, nicht Repo löschen)

---

## Deinstall — `sa uninstall`

```bash
sa uninstall                 # Bestätigung: y/N
sa uninstall -y              # ohne Nachfrage
sa uninstall --keep-repo     # nur Adapter, Repo behalten
sa uninstall --dry-run
```

Danach: **`source ~/.bashrc`** oder neues Terminal.

---

## Häufige Probleme

| Problem | Lösung |
|---------|--------|
| `sa: command not found` | `source ~/.bashrc` oder `"$SHARED_AGENTS_HOME/scripts/sa" help` |
| shared-agents not installed | `sa install` oder `./sa install` |
| Tool `not_configured` | `sa install` |
| Veraltete Learnings | `sa sync` · Hook/`sa check` prüfen |
| Wizard abgebrochen, halbes Setup | `rm -rf ~/.shared-agents` · `./sa install` neu |

---

## Agent-Anweisung

Wenn der User CLI-Hilfe braucht:

1. **`sa help`** ausführen (voller, aktueller Text aus `scripts/sa`).
2. Dieses Skill für Kontext und Workflows — **keine** parallele Command-Liste erfinden.
3. Pfade: **`$SHARED_AGENTS_HOME`** — siehe Skill `shared-agents-knowledge` und `capture-learning`.

Weitere Doku: **`$SHARED_AGENTS_HOME/README.md`** · **`docs/canonical-paths.md`**
