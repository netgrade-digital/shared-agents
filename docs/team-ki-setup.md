# Team-KI-Setup — Vereinheitlichtes Agenten-Wissen (Netgrade)

**Ziel:** Alle Agenten (Cursor, Claude Code, OpenClaw/Claw, …) nutzen dieselben **Skills**, **Workflows** und **Learnings** — lokal auf dem Rechner, ohne Cloud-Wissensdatenbank.

**Repo:** [bitbucket.org/netgrade/shared-agents](https://bitbucket.org/netgrade/shared-agents/src/main/)

---

## 1. Ausgangslage

| Was wir schon haben | Lücke |
|---------------------|--------|
| Claw/OpenClaw-Agenten speichern Learnings | Nur für diesen Stack |
| Cursor, Zed, Claude Code im Alltag | Jeder mit eigenen Rules, ohne gemeinsames Gedächtnis |
| Gute Einzelerkenntnisse in Chats | Gehen mit der Session verloren |

**Problem:** Wissen fragmentiert sich pro Tool und pro Person.

**Lösung:** Ein zentrales, git-basiertes Team-Repo (`shared-agents`) + dünne Adapter pro IDE/CLI. Kein Vendor-Lock-in, funktioniert offline nach dem Pull.

---

## 2. Kernprinzip: Drei Ebenen

```
┌─────────────────────────────────────────────────────────────┐
│  EBENE 1 — Team (global, ~/.shared-agents)                 │
│  Skills: stabile Workflows („So machen wir X")              │
│  Learnings: wiederverwendbare Erkenntnisse (approved)       │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  EBENE 2 — Projekt (im Kunden-Repo)                         │
│  AGENTS.md, .cursor/rules/, Projekt-Docs                    │
│  Nur dieses Produkt / dieser Kunde                          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│  EBENE 3 — Session (Chat / Agent-Run)                       │
│  Ephemer — wird nicht automatisch team-weit gespeichert     │
└─────────────────────────────────────────────────────────────┘
```

| Ebene | Ort | Wer pflegt | Beispiel |
|-------|-----|------------|----------|
| Team | `~/.shared-agents` | Alle via PR | „Vue-Sidebar: Radix-Dropdown bricht bei Portal-X" |
| Projekt | `projekt/.cursor/rules/` | Team am Projekt | „API immer über `/api/v2`" |
| Session | IDE-Chat | — | Einmalige Debug-Schritte |

**Regel:** Team-Wissen nie in Projekt-Regeln duplizieren. Projekt-Regeln ergänzen, ersetzen nicht.

---

## 3. Skills vs. Learnings vs. Workflows

| Artefakt | Rolle | Lebensdauer | Format |
|----------|-------|-------------|--------|
| **Skill** | Anleitung für den Agenten (Wann? Wie?) | Stabil, versioniert | `skills/*/SKILL.md` |
| **Learning** | Inhaltliches Wissen (Was? Warum?) | Wächst mit dem Team | `learnings/approved/*.md` |
| **Workflow** | Kombination aus Skill + Team-Gewohnheit | In Skills + CONTRIBUTING | z. B. „erst sync, dann suchen, am Ende Learning fragen" |

### Standard-Workflow (jede Session)

1. **Sync** — `sync.sh pull` (automatisch via Hook oder als erste Agent-Aktion)
2. **Retrieve** — vor nicht-trivialen Tasks: `learnings/index.yaml` + grep in `approved/`
3. **Arbeiten** — mit Projekt-Regeln des aktuellen Repos
4. **Capture** — nach großem Task: Agent fragt *„Soll ich ein Team-Learning anlegen?"*
5. **Review** — Mensch promoted `pending/` → `approved/` per PR

### Pflicht-Skills (Team)

| Skill | Zweck |
|-------|--------|
| `shared-agents-knowledge` | Sync, Learnings suchen, Grenzen (keine Secrets) |
| `capture-learning` | Entwurf in `pending/` nur nach explizitem Ja |

Weitere Skills (z. B. `shadcn-vue`, Domänen-Skills) können ins gleiche Repo unter `skills/` — ein Ordner, alle Tools symlinken dorthin.

---

## 4. Technisches Setup (lokal)

### 4.1 Einmal pro Rechner

```bash
git clone git@bitbucket.org:netgrade/shared-agents.git ~/.shared-agents
~/.shared-agents/scripts/install.sh --wizard
# SHARED_AGENTS_HOME in ~/.bashrc (Wizard fragt danach)
```

`install.sh` erkennt installierte Tools (Cursor, Claude, Zed, …) und setzt:

- **Hooks** (Cursor, Claude Code) → `git pull` bei Session-Start
- **Globale Rules / AGENTS.md** → „sync zuerst, Learnings nutzen, Learning fragen"
- **Skill-Symlinks** → `~/.agents/skills/`, `~/.claude/skills/`, …

### 4.2 Check

```bash
~/.shared-agents/scripts/install.sh --check
```

Ziel: alle genutzten Tools auf `ok`.

### 4.3 OpenClaw / Claw / Headless

Bestehende Claw-Pipelines um einen Wrapper erweitern:

```bash
"$SHARED_AGENTS_HOME/scripts/agent-entrypoint.sh" <bisheriger-claw-befehl>
```

→ Sync, dann Agent — gleiche Learnings wie in der IDE.

### 4.4 Täglich (für Menschen)

Meist **nichts** — Hooks + Agent-Instructions pullen automatisch.

Manuell nur bei Offline/Problemen:

```bash
~/.shared-agents/scripts/sync.sh pull
```

---

## 5. Anbindung Claw ↔ shared-agents

```
Bitbucket shared-agents
        │ git pull
        ▼
~/.shared-agents  ─────┬────── Cursor (Hook + Rule)
                       ├────── Claude Code (Hook)
                       ├────── Zed / Codex (AGENTS.md)
                       └────── OpenClaw (agent-entrypoint.sh)
```

**Migration Claw-Learnings:**

1. Bestehende Claw-Learnings inventarisieren (Format, Ort)
2. In `learnings/pending/` als Markdown-Entwürfe anlegen (keine Secrets)
3. Team-Review → `approved/` + `index.yaml` (`project`, `domain`, `tags`)
4. Claw nur noch über `$SHARED_AGENTS_HOME` lesen — kein zweites Learning-Repo

---

## 6. Rollout-Vorschlag (Abteilung)

| Phase | Dauer | Inhalt | Erfolgskriterium |
|-------|-------|--------|------------------|
| **0 — Pilot** | 1 Woche | Quentin + 1–2 Personen: install, 3 echte Learnings | `--check` = ok, 1 Learning im Alltag genutzt |
| **1 — Cursor-Nutzer** | 2 Wochen | Alle mit Cursor: `install.sh`, Regel aktiv | Kein paralleles „eigenes" Learning in Chats ohne PR |
| **2 — Claw** | 2 Wochen | Entrypoint in Claw-Jobs, Migration alter Learnings | Claw und Cursor finden dasselbe `approved/`-Learning |
| **3 — Restliche IDEs** | laufend | Bei Bedarf Zed, Claude Code, … | Manifest erweitern, kein Sonderweg |
| **4 — Governance** | dauerhaft | Review-Routine, Datenschutz-Matrix, Kosten-Tracking | Siehe Abschnitte 7–8 |

**Onboarding-Checkliste (neuer Kollege):**

- [ ] `git clone` + `install.sh --wizard`
- [ ] `install.sh --check` — genutzte Tools `ok`
- [ ] Kurz: pending vs. approved, keine Secrets in Learnings
- [ ] Einmal `review-learning.sh --list` gesehen (Review-Prozess)

---

## 7. KI — Datenschutz (Entscheidungsrahmen)

*Keine Rechtsberatung — Vorschlag für Team-Entscheidung.*

### 7.1 Grundsätze

1. **Keine Kunden-PII, Credentials, Produktions-DB-Dumps** in Learnings oder Skills.
2. **Repo-Zugang = Datenschutz-Gate:** KI nur dort, wo Menschen das Repo ohnehin bearbeiten dürfen.
3. **Learnings sind abstrahiert:** Muster und Fixes, keine Kundennamen, keine echten URLs mit Tokens.
4. **Cloud-Modelle** sehen den Kontext, den die IDE/CLI sendet — Projekt-Regeln können sensitive Pfade sperren.

### 7.2 Matrix (Vorschlag zur Abstimmung)

| Kunden-Typ / Vertrag | KI im Repo? | Lokale DB / Seeds? | Learnings aus dem Projekt? |
|----------------------|-------------|--------------------|----------------------------|
| **Standard / intern OK** | Ja | Ja (lokal) | Ja → `pending`, nach Review `approved` |
| **NDA, keine KI-Klausel** | Nur nach Rücksprache Lead | Nein | Nur generische Learnings ohne Projektbezug |
| **Explizit keine KI / Auftragsverarbeitung offen** | Nein | Nein | Nein — Agenten für dieses Repo deaktivieren |
| **EU-Hosting gefordert** | Ja mit vereinbartem Tool-Stack | Ja lokal | Ja, ohne personenbezogene Daten |

### 7.3 Technische Leitplanken

- `.cursorignore` / `.gitignore` für `.env`, `storage/`, Dumps
- Globale Rule: „Bei Unsicherheit: kein Learning, Lead fragen"
- `capture-learning`-Skill: explizit keine Secrets

**Offene Frage ans Team:** Wer pflegt die Matrix pro Kunde (Wiki, Projekt-README, CRM-Flag)?

---

## 8. KI — Kosten (Entscheidungsrahmen)

*Zahlen müssen vom Business bestätigt werden — Struktur für die Aufteilung.*

### 8.1 Kostenstellen (vorschlag)

| Bucket | Typische Nutzung | Messung |
|--------|------------------|---------|
| **IDE (Cursor, etc.)** | Tägliche Entwicklung | Cursor-Team-Dashboard / Seats |
| **Claw / Headless** | Automationen, Batch-Jobs | API-Usage pro Pipeline |
| **Ad-hoc CLI** | Claude Code, Codex, Aider | Pro Account / API-Key |

### 8.2 Aufteilungsmodelle (zur Diskussion)

**Modell A — Seats + API-Pool**

- Fixe Seats für Cursor (z. B. N Lizenzen)
- Gemeinsamer API-Pool für Claw/CLI; monatliches Cap; Warnung bei 80 %

**Modell B — Projekt-Budgets**

- Jedes Projekt bekommt X €/Monat; Claw-Jobs taggen `project_id`
- IDE-Kosten über Abteilungs-Flatrate

**Modell C — Fair Use**

- Kein hartes Limit pro Person; Monitoring + Ausreißer-Gespräch

### 8.3 Empfehlung für den Start

1. **Business klärt:** Gesamtbudget/Monat für die Abteilung.
2. **Cursor:** Lizenzen = Hauptkosten IDE → dokumentieren wer Seat hat.
3. **Claw:** Teurer bei Volumen → Entrypoint + Logging; große Jobs nur mit Freigabe.
4. **Review monatlich:** 15-Min-Check Usage-Dashboards (Cursor + API).

**Offene Fragen:**

- Gibt es ein fixes Monatslimit vom Business?
- Wer darf neue Claw-Pipelines mit Premium-Modellen anlegen?
- Fallback-Modell bei Limit (kleineres Modell / Pause)?

---

## 9. Weitere KI-Themen (Agenda)

| Thema | Kurz |
|-------|------|
| **Modellwahl** | Wann Opus/GPT-4 vs. kleines Modell — in Skills festhalten? |
| **Code-Review durch KI** | Nur Vorschläge, Mensch merged |
| **Kundenkommunikation** | Keine KI-generierten Mails ohne Review |
| **Lizenz / OSS** | Learnings zu Copyleft, kommerziellen Libs |
| **Security** | Kein `--no-verify`, keine Secrets in Prompts (steht in Skills) |
| **Shared MCPs** | Geplant: Manifest + lokale YAML + Installer — siehe [shared-mcps.md](shared-mcps.md) |

---

## 10. Zusammenfassung für die Runde

**Vorschlag Quentin:**

1. **`shared-agents` als Single Source of Truth** für Team-Skills und Learnings.
2. **Lokal** unter `~/.shared-agents`, Sync automatisch, Bitbucket als Remote.
3. **Claw** über `agent-entrypoint.sh` anbinden — gleiches Wissen wie Cursor.
4. **Workflow:** Agent schlägt vor (`pending/`) → Mensch reviewed → Team nutzt (`approved/`).
5. **Datenschutz & Kosten** als separate Team-Entscheidungen mit Matrix + monatlichem Check — nicht im Repo hardcoden, aber in Wiki/Confluence verlinken.

**Nächster konkreter Schritt:** Pilot (Phase 0) starten, nach einer Woche Retro: Install-Reibung, erste Learnings, Claw-Migration.

---

## Anhang: Befehle

```bash
# Install / Update
~/.shared-agents/scripts/install.sh
sa-sync

# Learnings reviewen (Aliase aus ~/.bashrc nach install.sh)
sa-review-list
sa-review

# Status aller Tools
sa-check
```

Siehe auch [README.md](../README.md), [shared-mcps.md](shared-mcps.md) und [CONTRIBUTING.md](../CONTRIBUTING.md).
