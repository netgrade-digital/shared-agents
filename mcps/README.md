# MCPs (geplant)

Team-weite MCP-Server-Konfiguration für Cursor und später weitere IDEs.

**Status:** Entwurf — Manifest und Beispiele liegen hier; **`install-mcps.py` fehlt noch**.  
**Vollständige Spezifikation:** [docs/shared-mcps.md](../docs/shared-mcps.md)

---

## Kurzüberblick

| Datei | Zweck |
|-------|--------|
| [`manifest.example.json`](manifest.example.json) | Schema-Referenz — Server, Templates, Generator |
| [`mcps.local.yaml.example`](mcps.local.yaml.example) | Vorlage für **lokale** Werte (SSH, Counts) — **nicht committen** |

Nach Implementierung:

```bash
cp "$SHARED_AGENTS_HOME/mcps/mcps.local.yaml.example" \
   "$SHARED_AGENTS_HOME/mcps.local.yaml"
# Werte anpassen, dann:
"$SHARED_AGENTS_HOME/scripts/install.sh"
```

Team-verwaltete Server erscheinen in `~/.cursor/mcp.json` mit Prefix `sa-`. Eigene Einträge ohne dieses Prefix bleiben beim Re-Install erhalten.

---

## Warum nicht `mcp.json` ins Git?

Hosts, SSH und Container-Namen sind maschinenspezifisch. Secrets gehören nicht ins Remote. Stattdessen: **Manifest im Repo + lokale YAML + Installer-Merge** — gleiche Idee wie `adapters/manifest.json` für IDE-Hooks.

Details: [docs/shared-mcps.md](../docs/shared-mcps.md).
