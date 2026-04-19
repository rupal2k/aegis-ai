# Claude Memory — Aegis AI

What Claude Code remembers about this project across sessions.  
**Auto-memory files**: `C:\Users\Rupal\.claude\projects\c--Rupalprojects-aegis-ai\memory\`  
**Rules, code patterns, constants**: [[../memory]]  
**Last synced**: 2026-04-18

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
| Status | All 6 phases ✅ + Upload Dataset tab (post-capstone) |
| Tests | 63/63 passing (~74s, 6 files) |
| Dashboard tabs | 7 (4 underwriter + 3 HR manager) |
| Bugs resolved | 7 (all fixed — see [[Bug Log]]) |
| Docker services | 4 (db, mlflow, api, dashboard) |

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

Set in `.obsidian/graph.json` → `colorGroups`. **Do not overwrite when editing graph.json.**

| Tier | Color | Hex | Nodes |
|------|-------|-----|-------|
| 1 – Core navigation | Red | `#FF5252` | Aegis AI Hub, INDEX |
| 2 – LLM/AI guides | Amber | `#FFB300` | memory, behaviour, Claude Memory |
| 3 – Progress tracking | Green | `#4CAF50` | Phase Progress, Bug Log |
| 4 – Architecture docs | Blue | `#2196F3` | Architecture Decisions, Decisions & Rationale |
| 5 – Deep dives | Purple | `#9C27B0` | all 5 deep-dive notes |
| 6 – Deployment plan | Teal | `#00BCD4` | Free Deployment Plan |
| 7 – Daily notes | Gray | `#9E9E9E` | Daily Notes folder |

Query format: `file:"Name" OR file:"Name"` with rgb as decimal integer `(r<<16)|(g<<8)|b`.

---

## How to Update This File

Add entries here only for things not already in [[../memory]]: user working-style preferences, session corrections, vault config, and project state changes. Do not copy code rules, pitfalls, or constants — link to the relevant Part of memory.md instead.
