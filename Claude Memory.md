# Claude Memory — Aegis AI

What Claude Code remembers about this project across sessions.  
**Auto-memory files**: `C:\Users\Rupal\.claude\projects\c--Rupalprojects-aegis-ai\memory\`  
**Rules, code patterns, constants**: [[../memory]]  
**Vault root**: `C:\Rupalprojects\Obsidian Vault\Aegis AI`  
**Vault on GitHub**: `https://github.com/rupal2k/aegis-ai` → branch `vault`  
**Last synced**: 2026-04-21

---

## User Profile

Rupal — building Aegis AI as a capstone project (AI-powered B2B group insurance underwriting). All 6 phases complete; now in post-capstone additions.

**Working style**:
- Direct and concise — no trailing summaries, no restating completed work
- Maintains this Obsidian vault alongside the codebase
- Prefers clean vault: no redundant nodes, merge into existing files rather than creating new ones
- Provides explicit step-by-step specs for major phases; expects deviations flagged immediately

---

## Current Project State

| Item | Value |
|------|-------|
| Status | All 6 phases ✅ + Upload Dataset tab + Security Hardening (post-capstone) |
| Tests | 63+ passing (+ new RBAC tests) |
| Dashboard tabs | 7 (4 underwriter + 3 HR manager) |
| Bugs resolved | 7 (all fixed — see [[Bug Log]]) |
| Docker services | 5 (db, mlflow, api, dashboard, nginx) |
| Auth | JWT bearer tokens — `/auth/token` endpoint, bcrypt in `config/users.json` |
| RBAC | `underwriter` = all companies; `hr_admin` = own company only |
| TLS | nginx reverse proxy on ports 80/443 (self-signed dev cert) |
| Docs | OpenAPI disabled in production (`ENV != development`) |

---

## Session-Learned Feedback

**Vault structure**: Do not create separate daily notes for phase work — merge into `Phase Progress.md`. Confirmed when user asked to merge two phase6 daily notes and delete the separate files.

**Docker + new files**: When new dashboard files are added, rebuild with `docker-compose build dashboard` — the running container won't pick up host file changes until the image is rebuilt.

**Vault updates**: Always update vault after feature work without asking for confirmation — it is always expected.

---

## Vault-as-Brain Rule

**All conversation aspects must be recorded in the vault.** The vault is the persistent brain for all sessions — not just code decisions. After any session that produces new information (feature designs, config changes, preferences, rationale), record it in the appropriate vault file before closing.

Recording targets:
- Feature work → `Phase Progress.md`
- Config changes (graph, settings) → this file (`Claude Memory.md`)
- New code pitfalls → `Bug Log.md` + `memory.md` Part 3
- Architecture decisions → `Architecture Decisions.md`
- New LLM rules → `behaviour.md` + `memory.md` (relevant Part)

---

## Graph View Color Scheme

Set in `C:\Rupalprojects\Obsidian Vault\Aegis AI\.obsidian\graph.json` → `colorGroups`. **Do not overwrite when editing graph.json.**  
⚠️ Obsidian may revert this file while the app is open — close the Graph View pane before editing, then reopen it to apply.

| Tier | Color | Hex | Nodes |
|------|-------|-----|-------|
| 1 – Core navigation | Red | `#FF5252` | Aegis AI Hub, INDEX |
| 2 – LLM/AI guides | Amber | `#FFB300` | memory, behaviour, Claude Memory |
| 3 – Progress tracking | Green | `#4CAF50` | Phase Progress, Bug Log |
| 4 – Architecture docs | Blue | `#2196F3` | Architecture Decisions, Decisions & Rationale |
| 5 – Deep dives | Purple | `#9C27B0` | all 5 deep-dive notes |
| 6 – Deployment plan | Teal | `#00BCD4` | Free Deployment Plan |
| 7 – Daily notes | Gray | `#9E9E9E` | Daily notes |

Query format: `file:"Name" OR file:"Name"` with rgb as decimal integer `(r<<16)|(g<<8)|b`.

---

## Vault on GitHub

The vault is tracked on a separate `vault` branch of the main repo.

| Item | Value |
|------|-------|
| Repo | `https://github.com/rupal2k/aegis-ai` |
| Branch | `vault` |
| Excluded | `workspace.json` (too noisy) |
| Included | All `.md` files + `.obsidian/graph.json` (preserves colors) |

**To push vault updates:**
```bash
cd "C:/Rupalprojects/Obsidian Vault/Aegis AI"
git add .
git commit -m "vault: <description>"
git push origin vault
```

---

## How to Update This File

Add entries here only for things not already in [[../memory]]: user working-style preferences, session corrections, vault config, and project state changes. Do not copy code rules, pitfalls, or constants — link to the relevant Part of memory.md instead.
