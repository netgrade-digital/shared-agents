# Shared MCPs — design & rollout

**Status:** Draft / planned — installer (`install-mcps.py`) not implemented yet.  
**Goal:** Team-wide MCP server configuration in the same spirit as skills and learnings: manifest + local overrides + learnings — **not** a copied `mcp.json` with SSH/Docker details in Git.

**See also:** [Repository README](https://github.com/netgrade-digital/shared-agents/blob/main/README.md) · [Learnings](/docs/learnings) · [mcps/README](https://github.com/netgrade-digital/shared-agents/blob/main/mcps/README.md)

---

## 1. Problem

MCP configuration usually lives per person in `~/.cursor/mcp.json` (or the equivalent in other IDEs). That leads to:

| Problem | Example |
|---------|---------|
| Copy-paste explosion | Same Screaming Frog block 15×, only the container name changes |
| Machine-specific config | `ssh old-infra`, Docker names, fixed paths — not portable |
| Secret leakage risk | API keys or tokens in the team repo |
| No “configured?” signal | Unclear who can actually use which MCP |
| Tool fragmentation | Cursor, Claude Code, Zed — different config paths |

**Skills and learnings work** because they are text and machine-independent. MCP config is **runtime wiring** — it belongs in an installer + local file, not raw JSON in the remote.

---

## 2. Three layers (like team / project / session)

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1 — Team ($SHARED_AGENTS_HOME/mcps/)                  │
│ Manifest: what exists, version, template, detect, generator │
│ Installer writes marked entries into IDE config             │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ LAYER 1b — User local (~/.shared-agents/mcps.local.yaml)    │
│ SSH host, spider count, paths — gitignored, never in remote   │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ LAYER 2 — Project (optional .cursor/mcp.json in client repo)│
│ Project-specific servers only                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ LAYER 3 — Session                                           │
│ Agent picks e.g. spider3 for parallel crawl — no persist      │
└─────────────────────────────────────────────────────────────┘
```

| Layer | Location | Maintainer | Content |
|-------|----------|------------|---------|
| Team | `mcps/manifest.json` | PR / maintainer | Server defs, templates, versions |
| User local | `mcps.local.yaml` | Each person | Hosts, counts, SSH alias — **gitignored** |
| Project | `project/.cursor/mcp.json` | Project team | Client MCPs without secrets |
| Session | IDE chat | — | Which spider, which `crawl_id` |

**Rule:** The team manifest contains **no** secrets, fixed SSH hosts, or client names.

---

## 3. Repository artifacts

```
shared-agents/
├── docs/shared-mcps.md           ← this document
├── mcps/
│   ├── README.md
│   ├── manifest.example.json
│   └── mcps.local.yaml.example
├── scripts/install-mcps.py       ← planned
└── team/learnings/approved/…     ← operational knowledge (when/how to use MCPs)
```

| Artifact | Role |
|----------|------|
| **Manifest** | Declarative: server ID, template, generator, detect, `tier` |
| **mcps.local.yaml** | Machine-specific values — **never commit** |
| **Installer** | Idempotent merge into IDE config; `--check` like adapters |
| **Learning** | Parallelism, disk, pitfalls — **not** long arg lists |

---

## 4. Manifest schema (draft)

Reference: [`mcps/manifest.example.json`](https://github.com/netgrade-digital/shared-agents/blob/main/mcps/manifest.example.json)

### Top level

| Field | Purpose |
|-------|---------|
| `version` | Manifest version |
| `shared.marker_*` | Optional documented blocks |
| `shared.local_config` | Path to gitignored local file |
| `shared.managed_prefix` | Prefix for team-managed server keys (default: `sa-`) |
| `hosts` | Per IDE: config path and format |
| `servers[]` | MCP server definitions |

### Server entry

| Field | Purpose |
|-------|---------|
| `id` | Stable ID (e.g. `browser-tools-mcp`) |
| `name` | Human label for `--check` |
| `tier` | `team` \| `optional` \| `infra` |
| `domain` | Tags for docs / learnings (`seo`, `frontend`, …) |
| `detect` | Pre-install check (binary, SSH, …) |
| `template` | Static MCP block with `{{variables}}` |
| `generator` | Repeated blocks (e.g. N spider instances) |
| `requires_local` | Required fields in `mcps.local.yaml` |
| `vars` | Defaults + optional `from_local` |

### Generator (`type: repeat`)

Replaces copy-paste like `screaming-frog-spider1` … `spider15`:

```json
"generator": {
  "type": "repeat",
  "id_pattern": "sa-screaming-frog-spider{{n}}",
  "count_var": "spider_count",
  "template": { "command": "ssh", "args": ["…", "seo-spider-{{n}}", "…"] }
}
```

Local: `spider_count: 6` → installer creates 6 entries. Someone with 15 containers sets 15 — **without** 15× JSON in Git.

---

## 5. Local config

Template: [`mcps/mcps.local.yaml.example`](https://github.com/netgrade-digital/shared-agents/blob/main/mcps/mcps.local.yaml.example)

```yaml
# ~/.shared-agents/mcps.local.yaml — NEVER commit
ssh_host: infra-host
docker_user: abc
spider_count: 6
```

Optional profiles (VPN vs laptop without infra):

```yaml
profile: default

profiles:
  default:
    ssh_host: infra-host
    spider_count: 15
  laptop:
    ssh_host: null   # SF MCP not installed
```

**Onboarding (planned):**

```bash
cp "$SHARED_AGENTS_HOME/mcps/mcps.local.yaml.example" \
   "$SHARED_AGENTS_HOME/mcps.local.yaml"
# edit
sa install
```

Keep `mcps.local.yaml` in `.gitignore`.

---

## 6. Installer behavior (planned)

Same philosophy as `install-adapters.py`: Python stdlib, idempotent, no network.

### Merge strategy (Cursor)

Cursor `mcp.json` has no comment markers. Use **namespacing**:

1. All team servers use prefix `sa-` (configurable in manifest).
2. Read `~/.cursor/mcp.json`.
3. Remove only managed keys with the `sa-` prefix.
4. Insert newly generated entries.
5. **Leave all other keys untouched** (private experiments).

### Commands (planned)

| Command | Description |
|---------|-------------|
| `sa install` | Adapters + MCPs (when manifest + local ok) |
| `sa install --mcps-only` | Rewrite MCP block only |
| `sa check` | Per MCP: `ok` / `missing_local` / `detect_fail` |
| `sa install --dry-run` | Diff `mcp.json` without writing |

### Check output (example)

```text
MCP                         HOST    CONFIGURED   STATUS
browser-tools-mcp           cursor  yes          ok
screaming-frog-spider       cursor  partial      detect_fail (ssh infra-host)
my-private-server           cursor  n/a          user_managed
```

`detect_fail` on an optional server is not an error for people without VPN/infra.

---

## 7. Learnings vs manifest

| Content | Where |
|---------|-------|
| `command`, `args`, version pin | Manifest |
| SSH host, spider count | `mcps.local.yaml` |
| When to run parallel crawls, disk limits, `delete_crawl` | Learning in `approved/` |
| Agent workflow (“max 1 crawl per spider”) | Skill or learning |

**Good learning topics:** max parallel crawls = `spider_count`, run `storage_summary` before large crawls, NDA clients need approval.

**Bad learning:** 20-line `args` array — that belongs in generator/manifest.

---

## 8. Project layer (client repos)

```
project/
  .cursor/mcp.json
  .cursor/mcp.json.example   # no secrets, env placeholders
```

| Prefix | Meaning |
|--------|---------|
| `sa-*` | Managed by Shared Agents — do not duplicate in project |
| `project-*` or unprefixed | Client-specific, in client repo |

Team manifest: **no** client SSH hosts. Use generic templates + a learning “ask lead for setup”.

---

## 9. Security & governance

1. **No secrets** in manifest or learnings — document `env_from_local: ["API_KEY"]`, values in `mcps.local.yaml` or OS keychain.
2. **Manifest changes = PR** — not agent-written to `approved/`.
3. **Repo access ≠ infra access** — MCP install does not replace permission boundaries.
4. **Version pins** — e.g. `@agentdeskai/browser-tools-mcp@1.2.1`, not blind `@latest`.
5. **Privacy** — no secrets or NDA content in learnings or manifest args.

---

## 10. Example: Screaming Frog spider pool

**Setup:** Remote Docker on infra host, N containers `seo-spider-1` … `seo-spider-N`, one MCP per container for parallel crawls.

| Approach | Pros | Cons |
|----------|------|------|
| N× MCP entries (today) | True parallelism, simple agent model | Maintenance, many IDE processes at start |
| Generator + `spider_count` | DRY, scales locally | Count must match infra |
| 1 MCP + queue in server | One process | Server must implement queue |
| Agent serializes | Minimal config | Slow |

**Recommendation:** Generator in manifest, team default e.g. `spider_count: 6`, learning documents limits and disk.

**Agent note:** `screaming-frog-spider3` = **instance 3**, not “third attempt”. At most one active `crawl_site` per spider.

---

## 11. Migration (when installer exists)

| Phase | Content |
|-------|---------|
| **1 — Docs** | This doc + `manifest.example.json` + `mcps.local.yaml.example` |
| **2 — Installer** | `install-mcps.py`, integrate into **`sa check`** |
| **3 — Local** | Remove old `screaming-frog-spider*` keys or map via manifest `aliases` → `sa-*` |
| **4 — Team** | Extend onboarding checklist; pilot with 2 people |

**Alias map (transition):**

```json
"aliases": {
  "screaming-frog-spider1": "sa-screaming-frog-spider1"
}
```

Installer removes old aliases on the next run.

---

## 12. Out of scope (for now)

- Central cloud MCP host (conflicts with local + private Git)
- Auto-update without PR (`npx -y` without pin)
- Replacing SSH keys (`~/.ssh/config` stays with the user)
- One MCP format for all IDEs in v1 — Cursor first, others follow under `hosts`

---

## 13. Next implementation steps

- [ ] `scripts/install-mcps.py` (stdlib, merge, detect, generator)
- [ ] Hook in `install.sh` / **`sa install`** (`--mcps-only`, `sa check` JSON field `mcps`)
- [ ] `.gitignore` entry for `mcps.local.yaml`
- [ ] Team learning template after first production use
- [ ] Optional skill `shared-agents-mcp` for agents before SEO tasks

---

## Appendix: commands (target state)

```bash
cp "$SHARED_AGENTS_HOME/mcps/mcps.local.yaml.example" \
   "$SHARED_AGENTS_HOME/mcps.local.yaml"

sa install
sa check
sa install --mcps-only --dry-run
```
