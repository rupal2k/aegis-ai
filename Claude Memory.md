# Claude Memory â€” Aegis AI

What Claude Code remembers about this project across sessions.  
**Auto-memory files**: `C:\Users\Rupal\.claude\projects\c--Rupalprojects-aegis-ai\memory\`  
**Rules, code patterns, constants**: [[../memory]]  
**Vault root**: `C:\Rupalprojects\Obsidian Vault\Aegis AI`  
**Vault on GitHub**: `https://github.com/rupal2k/aegis-ai` â†’ branch `vault`  
**Last synced**: 2026-04-29

---

## User Profile

Rupal â€” building Aegis AI as a capstone project (AI-powered B2B group insurance underwriting). All 6 phases complete; now in post-capstone additions.

**Working style**:
- Direct and concise â€” no trailing summaries, no restating completed work
- Maintains this Obsidian vault alongside the codebase
- Prefers clean vault: no redundant nodes, merge into existing files rather than creating new ones
- Provides explicit step-by-step specs for major phases; expects deviations flagged immediately

---

## Current Project State

| Item | Value |
|------|-------|
| Status | All 6 phases âœ… + Upload Dataset tab + Security Hardening + Security Testing & Remediation (post-capstone) |
| Tests | 75 passed, 5 skipped (latest full pytest) |
| Dashboard tabs | 7 (4 underwriter + 3 HR manager) |
| Bugs resolved | 7 (all fixed â€” see [[Bug Log]]) |
| Docker services | 5 (db, mlflow, api, dashboard, nginx) |
| Auth | JWT bearer tokens â€” `/auth/token` endpoint, bcrypt in `config/users.json` |
| RBAC | `underwriter` = all companies; `hr_admin` = own company only |
| TLS | nginx reverse proxy on ports 80/443 (self-signed dev cert) |
| Docs | OpenAPI disabled in production (`ENV != development`) |
| Rate limiting | `slowapi` 5 req/min on `/auth/token` |
| Security headers | `X-Frame-Options`, `CSP`, `HSTS`, `X-Content-Type-Options`, `Referrer-Policy` |
| Container user | Non-root `appuser` (UID 1000) in API container |
| Known open issue | MEDIUM: `ingest.py` missing `require_company_access` â€” hr_admin can POST to other company's ingest endpoints |

---

## Session-Learned Feedback

**HF training data selection**: Company-profile datasets are not valid inputs for the underwriting model. Structured underwriting tables, insurance-charge tables, and clinical-note corpora can be adapted; generic business profile data should be rejected explicitly.

**Latest retrain**: Combined local 5,237-row dataset with 225 rows from `bubuuunel/healthylife-insurance-charge-log`. MLflow run `b10e7565acbd451e92556509b52dfa6d`; full verification `75 passed, 5 skipped`.

**Vault structure**: Do not create separate daily notes for phase work â€” merge into `Phase Progress.md`. Confirmed when user asked to merge two phase6 daily notes and delete the separate files.

**Docker + new files**: When new dashboard files are added, rebuild with `docker-compose build dashboard` â€” the running container won't pick up host file changes until the image is rebuilt.

**Vault updates**: Always update vault after feature work without asking for confirmation â€” it is always expected.

---

## Vault-as-Brain Rule

**All conversation aspects must be recorded in the vault.** The vault is the persistent brain for all sessions â€” not just code decisions. After any session that produces new information (feature designs, config changes, preferences, rationale), record it in the appropriate vault file before closing.

Recording targets:
- Feature work â†’ `Phase Progress.md`
- Config changes (graph, settings) â†’ this file (`Claude Memory.md`)
- New code pitfalls â†’ `Bug Log.md` + `memory.md` Part 3
- Architecture decisions â†’ `Architecture Decisions.md`
- New LLM rules â†’ `behaviour.md` + `memory.md` (relevant Part)

---

## Graph View Color Scheme

Set in `C:\Rupalprojects\Obsidian Vault\Aegis AI\.obsidian\graph.json` â†’ `colorGroups`. **Do not overwrite when editing graph.json.**  
âš ï¸ Obsidian may revert this file while the app is open â€” close the Graph View pane before editing, then reopen it to apply.

| Tier | Color | Hex | Nodes |
|------|-------|-----|-------|
| 1 â€“ Core navigation | Red | `#FF5252` | Aegis AI Hub, INDEX |
| 2 â€“ LLM/AI guides | Amber | `#FFB300` | memory, behaviour, Claude Memory |
| 3 â€“ Progress tracking | Green | `#4CAF50` | Phase Progress, Bug Log |
| 4 â€“ Architecture docs | Blue | `#2196F3` | Architecture Decisions, Decisions & Rationale |
| 5 â€“ Deep dives | Purple | `#9C27B0` | all 5 deep-dive notes |
| 6 â€“ Deployment plan | Teal | `#00BCD4` | Free Deployment Plan |
| 7 â€“ Daily notes | Gray | `#9E9E9E` | Daily notes |

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

Add entries here only for things not already in [[../memory]]: user working-style preferences, session corrections, vault config, and project state changes. Do not copy code rules, pitfalls, or constants â€” link to the relevant Part of memory.md instead.

