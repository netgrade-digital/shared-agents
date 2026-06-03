# Shared MCPs — Design & Rollout (Entwurf)

**Status:** Entwurf / geplant — Installer (`install-mcps.py`) noch nicht implementiert.  
**Ziel:** Team-weite MCP-Server-Konfiguration im gleichen Stil wie Skills und Learnings: Manifest + lokale Overrides + Learnings — **nicht** als kopiertes `mcp.json` mit SSH/Docker-Details im Git.

**Siehe auch:** [README.md](../README.md) · [learnings.md](learnings.md) · [mcps/README.md](../mcps/README.md)

---

## 1. Problem

MCP-Konfiguration liegt heute typischerweise pro Person in `~/.cursor/mcp.json` (oder äquivalent in anderen IDEs). Das führt zu:

| Problem | Beispiel |
|---------|----------|
| Copy-Paste-Explosion | 15× derselbe Screaming-Frog-Block, nur Container-Name ändert sich |
| Maschinenabhängigkeit | `ssh alte-infra`, Docker-Namen, feste Pfade — nicht 1:1 übertragbar |
| Secrets-Risiko | API-Keys oder Tokens landen im Team-Repo |
| Kein „configured?“ | Unklar, wer welchen MCP wirklich nutzen kann |
| Tool-Fragmentierung | Cursor, Claude Code, Zed — unterschiedliche Config-Pfade |

**Skills/Learnings funktionieren**, weil sie textuell und maschinenunabhängig sind. MCP-Config ist **Runtime-Wiring** — gehört in Installer + lokale Datei, nicht als Roh-JSON ins Remote.

---

## 2. Drei Ebenen (analog zu Team / Projekt / Session)

```
┌─────────────────────────────────────────────────────────────┐
│ EBENE 1 — Team ($SHARED_AGENTS_HOME/mcps/)                  │
│ Manifest: Was es gibt, Version, Template, Detect, Generator │
│ Installer schreibt markierte Einträge in IDE-Config         │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ EBENE 1b — User lokal (~/.shared-agents/mcps.local.yaml)    │
│ SSH-Host, Spider-Count, Pfade — gitignored, nie im Remote     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ EBENE 2 — Projekt (optional .cursor/mcp.json im Kundenrepo) │
│ Nur projekt-spezifische Server                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ EBENE 3 — Session                                           │
│ Agent wählt z. B. spider3 für parallelen Crawl — kein Persist │
└─────────────────────────────────────────────────────────────┘
```

| Ebene | Ort | Wer pflegt | Inhalt |
|-------|-----|------------|--------|
| Team | `mcps/manifest.json` | PR / Maintainer | Server-Definitionen, Templates, Versionen |
| User lokal | `mcps.local.yaml` | Jede Person | Hosts, Counts, SSH-Alias — **gitignored** |
| Projekt | `projekt/.cursor/mcp.json` | Projekt-Team | Kundenspezifische MCPs ohne Secrets |
| Session | IDE-Chat | — | Welcher Spider, welcher crawl_id |

**Regel:** Team-Manifest enthält **keine** Secrets, keine festen SSH-Hosts, keine Kundennamen.

---

## 3. Artefakte im Repo

```
shared-agents/
├── docs/
│   └── shared-mcps.md              ← dieses Dokument
├── mcps/
│   ├── README.md                     ← Kurzreferenz + Status
│   ├── manifest.example.json         ← Schema-Referenz (Beispiel)
│   └── mcps.local.yaml.example       ← Vorlage für lokale Werte
├── scripts/
│   └── install-mcps.py               ← geplant (noch nicht da)
└── team/learnings/approved/by-domain/…    ← Betriebswissen (wann/wie MCPs nutzen)
```

| Artefakt | Rolle |
|----------|--------|
| **Manifest** | Deklarativ: Server-ID, Template, Generator, Detect, `tier` |
| **mcps.local.yaml** | Maschinenspezifische Variablen — **nie committen** |
| **Installer** | Idempotent merge in IDE-Config; `--check` wie `install-adapters.py` |
| **Learning** | Parallelität, Speicher, Fallstricke — **keine** Args-Listen |

---

## 4. Manifest-Schema (Entwurf)

Referenz: [`mcps/manifest.example.json`](../mcps/manifest.example.json)

### Top-Level

| Feld | Zweck |
|------|--------|
| `version` | Manifest-Version |
| `shared.marker_*` | Optional für dokumentierte Blöcke |
| `shared.local_config` | Pfad zur gitignored lokalen Datei |
| `shared.managed_prefix` | Prefix für vom Team verwaltete Server-Keys (Default: `sa-`) |
| `hosts` | Pro IDE: Config-Pfad und Format |
| `servers[]` | MCP-Server-Definitionen |

### Server-Eintrag

| Feld | Zweck |
|------|--------|
| `id` | Stabile ID (z. B. `browser-tools-mcp`) |
| `name` | Menschenlesbar für `--check` |
| `tier` | `team` \| `optional` \| `infra` — wer bekommt es standardmäßig |
| `domain` | Tags für Doku / Learnings (`seo`, `frontend`, …) |
| `detect` | Pre-Install-Check (Binary, SSH, …) |
| `template` | Statischer MCP-Block mit `{{variablen}}` |
| `generator` | Wiederholte Blöcke (z. B. N Spider-Instanzen) |
| `requires_local` | Pflichtfelder in `mcps.local.yaml` |
| `vars` | Defaults + optional `from_local` |

### Generator (`type: repeat`)

Ersetzt Copy-Paste wie `screaming-frog-spider1` … `spider15`:

```json
"generator": {
  "type": "repeat",
  "id_pattern": "sa-screaming-frog-spider{{n}}",
  "count_var": "spider_count",
  "template": { "command": "ssh", "args": ["…", "seo-spider-{{n}}", "…"] }
}
```

Lokal: `spider_count: 6` → Installer erzeugt 6 Einträge. Wer 15 Container hat, setzt 15 — **ohne** 15× JSON im Git.

---

## 5. Lokale Config

Vorlage: [`mcps/mcps.local.yaml.example`](../mcps/mcps.local.yaml.example)

```yaml
# ~/.shared-agents/mcps.local.yaml — NIE ins Git committen
ssh_host: alte-infra
docker_user: abc
spider_count: 6
```

Optional Profile (VPN vs. Laptop ohne Infra):

```yaml
profile: default   # oder: laptop

profiles:
  default:
    ssh_host: alte-infra
    spider_count: 15
  laptop:
    ssh_host: null   # SF-MCP wird nicht installiert
```

**Onboarding (geplant):**

```bash
cp "$SHARED_AGENTS_HOME/mcps/mcps.local.yaml.example" \
   "$SHARED_AGENTS_HOME/mcps.local.yaml"
# editieren
sa install              # Adapter + MCPs (wenn implementiert)
# Low-level: "$SHARED_AGENTS_HOME/install.sh"
```

`mcps.local.yaml` gehört in `.gitignore` des Repos (Root oder Hinweis in README).

---

## 6. Installer-Verhalten (geplant)

Philosophie wie [`scripts/install-adapters.py`](../scripts/install-adapters.py): Python-Stdlib, idempotent, kein Netzwerk.

### Merge-Strategie (Cursor)

Cursor-`mcp.json` hat keine Kommentar-Marker. Deshalb **Namespacing**:

1. Alle Team-Server nutzen Prefix `sa-` (konfigurierbar in Manifest).
2. Installer liest `~/.cursor/mcp.json`.
3. Entfernt nur Keys mit `sa-`-Prefix, die im Manifest verwaltet werden.
4. Fügt neu generierte Einträge ein.
5. **Alle anderen Keys bleiben unberührt** (private Experimente des Users).

### Befehle (geplant)

| Befehl | Beschreibung |
|--------|--------------|
| `sa install` | Adapter + MCPs (wenn Manifest + local ok) |
| `sa install --mcps-only` | Nur MCP-Block neu schreiben (geplant) |
| `sa check` | Zeigt pro MCP: `ok` / `missing_local` / `detect_fail` (geplant) |
| `sa install --dry-run` | Diff der `mcp.json` ohne Schreiben (geplant) |

Low-level: `./install.sh` — gleiche Flags, wenn an Installer angebunden.

### Check-Ausgabe (Beispiel)

```text
MCP                         HOST    CONFIGURED   STATUS
browser-tools-mcp           cursor  yes          ok
screaming-frog-spider       cursor  partial      detect_fail (ssh alte-infra)
my-private-server           cursor  n/a          user_managed
```

`detect_fail` bei optionalem Server = kein Fehler für Leute ohne VPN/Infra.

### Detect-Beispiele

| Typ | Prüfung |
|-----|---------|
| `command` | Binary auf `$PATH` (`npx`, `node`, …) |
| `ssh_exec` | `ssh -o BatchMode=yes HOST docker ps …` |
| `file` | Pfad existiert |

Schlägt Detect fehl → Server wird **nicht** eingetragen (optional) oder Check = `not_available`.

---

## 7. Learnings vs. Manifest

| Inhalt | Wo |
|--------|-----|
| `command`, `args`, Version-Pin | Manifest |
| SSH-Host, Spider-Count | `mcps.local.yaml` |
| Wann parallele Crawls, Speicher-Limits, `delete_crawl` | Learning in `approved/` |
| Agent-Workflow („max 1 crawl pro Spider“) | Skill oder Learning |

**Gutes Learning** (Beispiel-Themen):

- Max. parallele Crawls = `spider_count`
- Vor großen Crawls: `storage_summary` auf Infra-Host
- Kein SF-Crawl bei Kunden mit NDA ohne Freigabe

**Schlechtes Learning:** 20 Zeilen `args`-Array — das ist Generator/Manifest.

---

## 8. Projekt-Ebene (Kundenrepo)

Für kundenspezifische MCPs:

```
projekt/
  .cursor/mcp.json          # nur dieser Kunde
  .cursor/mcp.json.example  # ohne Secrets, env-Platzhalter
```

| Prefix | Bedeutung |
|--------|-----------|
| `sa-*` | Von shared-agents verwaltet — nicht im Projekt duplizieren |
| `projekt-*` oder ohne Prefix | Projekt-spezifisch, im Kundenrepo |

Team-Manifest: **keine** Kunden-SSH-Hosts. Höchstens generische Templates + Learning „Setup auf Anfrage beim Lead“.

---

## 9. Sicherheit & Governance

1. **Keine Secrets** in Manifest oder Learnings — nur `env_from_local: ["API_KEY"]` als Dokumentation, Werte in `mcps.local.yaml` oder OS-Keychain.
2. **Manifest-Änderungen = PR** — nicht vom Agent nach `approved/` schreiben (wie Learnings-Workflow, aber Maintainer-Review).
3. **Repo-Zugriff = Infra-Gate** — wer SF-SSH hat, kann crawlen; MCP-Install ersetzt keine Berechtigungsmatrix.
4. **Version-Pins** — z. B. `@agentdeskai/browser-tools-mcp@1.2.1` im Manifest, kein blindes `@latest`.
5. **Datenschutz** — keine Secrets/NDA-Inhalte in Learnings oder Manifest-Args.

---

## 10. Beispiel: Screaming Frog Spider-Pool

**Ausgangslage:** Remote-Docker auf Infra-Host, N Container `seo-spider-1` … `seo-spider-N`, MCP pro Container für parallele Crawls.

| Ansatz | Pro | Contra |
|--------|-----|--------|
| N× MCP-Einträge (heute) | Echter Parallelismus, einfaches Agent-Modell | Wartung, viele Prozesse beim IDE-Start |
| Generator + `spider_count` | DRY, skaliert lokal | Count muss zu Infra passen |
| 1 MCP + Queue im Server | Ein Prozess | MCP müsste Queue implementieren |
| Serialisierung durch Agent | Minimal | Langsam |

**Empfehlung:** Generator im Manifest, Team-Default z. B. `spider_count: 6`, Learning dokumentiert Limits und Speicher.

**Agent-Hinweis (Skill/Learning):** `screaming-frog-spider3` = **Instanz 3**, nicht „dritter Versuch“. Max. ein aktiver `crawl_site` pro Spider.

---

## 11. Migration (wenn Installer da ist)

| Phase | Inhalt |
|-------|--------|
| **1 — Doku** | Dieses Dokument + `manifest.example.json` + `mcps.local.yaml.example` |
| **2 — Installer** | `install-mcps.py`, Integration in **`sa check`** / `install.sh --check` |
| **3 — Lokal** | Alte Keys `screaming-frog-spider*` entfernen oder via `aliases` im Manifest mappen → `sa-*` |
| **4 — Team** | Onboarding-Checkliste erweitern; Pilot 2 Personen |

**Alias-Map (Übergang):**

```json
"aliases": {
  "screaming-frog-spider1": "sa-screaming-frog-spider1"
}
```

Installer entfernt alte Aliases beim nächsten Lauf.

---

## 12. Was bewusst nicht im Scope ist

- Zentraler Cloud-MCP-Host (widerspricht lokal + Bitbucket)
- Auto-Update ohne PR (`npx -y` ohne Pin)
- Ersatz für SSH-Keys (`~/.ssh/config` bleibt beim User)
- Einheitliches MCP-Format über alle IDEs in v1 — Cursor zuerst, Claude/Zed folgen im Manifest unter `hosts`

---

## 13. Nächste Schritte (Implementierung)

- [ ] `scripts/install-mcps.py` (stdlib, merge, detect, generator)
- [ ] Hook in `install.sh` / **`sa install`** (`--mcps-only`, `sa check` JSON-Feld `mcps`)
- [ ] `.gitignore`-Eintrag für `mcps.local.yaml` am Repo-Root
- [ ] Learning-Vorlage im Team-Repo: `team/learnings/approved/by-domain/seo/screaming-frog-mcp-pool.md` (nach erstem Betrieb)
- [ ] Optional: Skill `shared-agents-mcp` für Agent-Workflow vor SEO-Tasks

---

## Anhang: Befehle (Soll-Zustand)

```bash
# Lokale Config anlegen
cp "$SHARED_AGENTS_HOME/mcps/mcps.local.yaml.example" \
   "$SHARED_AGENTS_HOME/mcps.local.yaml"

# Install / Check (wenn implementiert)
sa install
sa check
sa install --mcps-only --dry-run
# Low-level: "$SHARED_AGENTS_HOME/install.sh" …
```
