# Bug Log — Aegis AI

**Last Updated**: 2026-04-24  
**Total Bugs Logged**: 10  
**Status**: All resolved ✅

---

## BUG-001: Port 8000 Held by Tool Runner Proxy

**Severity**: 🔴 High (blocks local dev)  
**Date Found**: 2026-04-17  
**Date Fixed**: 2026-04-17  
**Status**: ✅ Resolved

### Symptom
```
OSError: [Errno 48] Address already in use (port 8000)
```
When attempting to start uvicorn for FastAPI development server.

### Root Cause
Claude Code tool runner proxy from previous session held port 8000. PIDs 9356 and 12608 appeared in `netstat`, but standard OS tools (`taskkill`, `lsof`) could not kill them — they are not real OS processes but internal tool runner agents.

### Investigation
```bash
# Confirmed port was held
netstat -ano | findstr :8000
# Output: PID 9356, 12608 (both tried, both failed with normal kill)

# Attempted fixes (all failed):
taskkill /F /PID 9356          # Process not found
taskkill /PID 9356 /F /T       # Could not find process
lsof -i :8000                  # Command not found on Windows
```

### Solution
User killed PIDs from their own terminal (outside Claude Code) — this worked because the terminal had different process context than the tool runner proxy.

### Prevention
- Restart Claude Code between sessions if long-running background tasks (uvicorn, streamlit) were active
- Use `pkill -f uvicorn` or equivalent before exiting session

### Workaround for Next Time
Instead of relying on pid kill, use:
```bash
# On Windows (PowerShell):
Get-Process -Name python | Where-Object { $_.ProcessName -like "*8000*" } | Stop-Process -Force

# Better: Use a fixed stop script
# scripts/stop_server.sh
```

---

## BUG-002: pycache Stale Bytecode After main.py Update

**Severity**: 🟠 Medium (confusing, not obvious)  
**Date Found**: 2026-04-17  
**Date Fixed**: 2026-04-17  
**Status**: ✅ Resolved

### Symptom
After updating `ingestion/main.py` to register new routers, `/companies` endpoint returned 404. Other endpoints (existing `/predict/*`) still worked.

### Root Cause
Python cached old `.pyc` bytecode in `ingestion/__pycache__/`. When uvicorn reloaded (on hot-reload), it loaded the stale compiled bytecode instead of the updated source file.

### Investigation
```python
# In uvicorn debug session:
from ingestion.main import app

# Inspected app.routes — `/companies` was missing
# But `ingestion/main.py` source file clearly had:
#   from ingestion.routers import companies
#   app.include_router(companies.router, ...)
```

### Solution
```bash
# Clear all pycache directories
find "c:/Rupalprojects/aegis-ai/ingestion" -name "*.pyc" -delete
find "c:/Rupalprojects/aegis-ai/ingestion" -name "__pycache__" -type d -exec rm -rf {} +

# Restart uvicorn
# Verified routes were loaded
python -c "from ingestion.main import app; print([r.path for r in app.routes if 'companies' in r.path])"
# Output: ['/companies', '/companies/{company_id}/employees'] ✅
```

### Prevention
- Before restarting uvicorn after code changes: `find . -name "__pycache__" -type d -delete`
- Consider disabling bytecode caching for dev: `PYTHONDONTWRITEBYTECODE=1`

---

## BUG-003: ModuleNotFoundError — `from dashboard.auth import ...`

**Severity**: 🔴 High (blocks dashboard startup)  
**Date Found**: 2026-04-17  
**Date Fixed**: 2026-04-17  
**Status**: ✅ Resolved

### Symptom
```
ModuleNotFoundError: No module named 'dashboard'
```
When running `streamlit run dashboard/app.py`.

### Root Cause
Streamlit adds **only the script's directory** (`dashboard/`) to `sys.path`, not the project root. So:
- Script: `dashboard/app.py`
- Script dir: `dashboard/`
- sys.path: `[..., "dashboard/", ...]` ← no project root!
- Import: `from dashboard.auth` tries to import from `dashboard/dashboard/` (doesn't exist)

### Solution
At the top of `dashboard/app.py`, manually insert project root into sys.path:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now sys.path = [project_root, dashboard/, ...]
# So `from dashboard.auth` works ✅
```

### Prevention
- Always add this snippet when Streamlit imports from parent directories
- Consider running Streamlit from project root: `streamlit run dashboard/app.py` (instead of `cd dashboard && streamlit run app.py`)

---

## BUG-004: Metric Cards Showing Blank Values (Dark Theme CSS)

**Severity**: 🟠 Medium (UI broken, values not visible)  
**Date Found**: 2026-04-17 (user screenshot)  
**Date Fixed**: 2026-04-17  
**Status**: ✅ Resolved

### Symptom
Streamlit metric cards displayed labels (e.g., "Total companies") but no values (e.g., "42").

**Screenshot**: User showed 4 metrics with labels only, values invisible.

### Root Cause
Dark theme CSS override was hiding all child elements of `.stMetric`:

```css
/* BROKEN: */
.stMetric label {
    color: #5F5E5A;  /* Dark gray text */
}

/* Problem: .stMetric contains nested elements:
   <div class="stMetric">
     <div class="stMetric label">
       <span>Label</span>
       <span>VALUE</span>  ← This is also a child of .stMetric!
     </div>
   </div>
   
   So targeting .stMetric label hides EVERYTHING under it.
*/
```

### Solution
Instead of targeting `.stMetric label`, use the safe Streamlit data-testid selector:

```css
/* FIXED: */
[data-testid="stMetric"] {
    background-color: #f5f5f7;
    border: 1px solid #e0e0e5;
    border-radius: 10px;
    padding: 16px 20px;
}

/* This targets only the container card, not sub-elements.
   Streamlit's internal value rendering is untouched.
*/
```

Also created `.streamlit/config.toml` to force light theme globally:

```toml
[theme]
base = "light"
primaryColor = "#0071e3"
backgroundColor = "#ffffff"
textColor = "#1d1d1f"
```

### Prevention
- Avoid targeting `.st*` classes directly (fragile, changes between Streamlit versions)
- Use `[data-testid="..."]` selectors instead (more stable)
- Test CSS changes with light + dark themes
- Use Chrome DevTools to inspect actual DOM structure before writing CSS

---

## BUG-005: UnicodeEncodeError in Bash Test Output

**Severity**: 🟡 Low (cosmetic, doesn't affect logic)  
**Date Found**: 2026-04-17 (during test output verification)  
**Date Fixed**: 2026-04-17  
**Status**: ✅ Resolved

### Symptom
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 0: character maps to <undefined>
```
When running Python `-c` script in Windows Bash that outputs the arrow character `→`.

### Root Cause
Windows PowerShell uses CP1252 encoding by default (not UTF-8). The `→` character (U+2192) is not in the CP1252 character set, causing encode failure.

### Solution
Replace `→` with `->` (ASCII-compatible):

```python
# BEFORE (fails on Windows):
output = f"Phase 4 → ✅ Complete"

# AFTER (works everywhere):
output = f"Phase 4 -> Complete"
```

Also, to fix properly for future Unicode output:
```bash
# Force UTF-8 in PowerShell:
$env:PYTHONIOENCODING = 'utf-8'
python -c "print('→ works now')"
```

### Prevention
- Test output scripts on Windows (not just Linux/Mac)
- Use ASCII when output encoding is uncertain
- Or: Set `PYTHONIOENCODING=utf-8` environment variable

---

## BUG-006: Dashboard → API Connection Refused Inside Docker

**Severity**: 🔴 High (dashboard completely broken in Docker)  
**Date Found**: 2026-04-18  
**Date Fixed**: 2026-04-18  
**Status**: ✅ Resolved

### Symptom
```
httpx.ConnectError: [Errno 111] Connection refused
```
Occurred immediately after login when the underwriter view tried to load companies. Full traceback pointed to `api_client.py → _get("/companies") → httpx.Client.get("http://localhost:8000/companies")`.

### Root Cause
`dashboard/api_client.py` hardcoded `API_BASE = "http://localhost:8000"`. Inside the dashboard container, `localhost` resolves to the container itself — not the API container. Docker networking requires using the **container name** as hostname (`api`), which Docker's internal DNS resolves to the correct container IP.

```
# What the code did:
dashboard container → http://localhost:8000  ← WRONG: this is dashboard itself

# What it should do:
dashboard container → http://api:8000  ← Docker DNS resolves to api container
```

The issue was masked during local development (where all services share the host network and `localhost:8000` works).

### Solution
Made `API_BASE` read from an environment variable with a localhost fallback:

```python
# Before:
API_BASE = "http://localhost:8000"

# After:
import os
API_BASE = os.environ.get("AEGIS_API_URL", "http://localhost:8000")
```

`docker-compose.yml` already had `AEGIS_API_URL: http://api:8000` in the dashboard service — just needed the code to read it.

### Prevention
- Never hardcode service hostnames in multi-container applications
- Always read base URLs from environment variables
- The docker-compose env var was already in place from the start — the code just wasn't using it

---

## BUG-007: Metric Card Text Invisible in Dark Mode (Second Occurrence)

**Severity**: 🟠 Medium (UI values not visible)  
**Date Found**: 2026-04-18 (user screenshot after Docker deployment)  
**Date Fixed**: 2026-04-18  
**Status**: ✅ Resolved

### Symptom
After Docker deployment, metric card values appeared invisible or very faint against the background. The dashboard was rendering with a light/mixed theme causing contrast failures.

### Root Cause
Two compounding issues:
1. `.streamlit/config.toml` set `base = "light"` but CSS overrides used near-white `#f5f5f7` backgrounds — creating very low contrast with Streamlit's default light text
2. Metric value elements weren't explicitly targeted, so Streamlit could render them in colours that blended with the card background depending on detected theme

### Solution
Full dark mode overhaul:

**`.streamlit/config.toml`**:
```toml
base                     = "dark"
primaryColor             = "#0a84ff"
backgroundColor          = "#0d0d0f"
secondaryBackgroundColor = "#1c1c1e"
textColor                = "#f5f5f7"
```

**`dashboard/app.py` CSS** — explicit targeting of all metric sub-elements:
```css
[data-testid="stMetricValue"] {
    color: #f5f5f7 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #aeaeb2 !important;
}
```

**Chart colors** in both `underwriter_view.py` and `hr_view.py`:
```python
PLOT_BG  = "#1c1c1e"   # dark card
GRID_CLR = "#3a3a3c"   # subtle grid
FONT_CLR = "#f5f5f7"   # near-white text
ACCENT   = "#0a84ff"   # iOS blue
```

### Prevention
- Target `[data-testid="stMetricValue"]` explicitly rather than relying on theme inheritance
- Use `!important` on colour overrides to guarantee they apply regardless of Streamlit version
- Test in both light and dark modes before shipping

---

## BUG-008: `/auth/token` Returns 404 — Stale Docker Image

**Severity**: 🔴 High (auth system completely broken)  
**Date Found**: 2026-04-22  
**Date Fixed**: 2026-04-22  
**Status**: ✅ Resolved

### Symptom
`POST /auth/token` returned 404. Security test suite passed only 17/25 tests. All auth-dependent tests cascaded to fail.

### Root Cause
The running `aegis-api` container was built from a cached Docker image that predated the `ingestion/auth/` and `ingestion/routers/auth_router.py` modules. Even though these files existed in the repo, Docker had not been rebuilt since they were added — so the container's `ingestion/` copy was missing them entirely.

Confirmed via:
```bash
docker exec aegis-api python3 -c "from ingestion.routers.auth_router import router"
# ModuleNotFoundError: No module named 'ingestion.routers.auth_router'
```

Secondary issue: `config/users.json` (the bcrypt user store) was also missing from the image — `Dockerfile.api` had no `COPY config/ ./config/` line.

### Solution
1. Added `COPY config/ ./config/` to `Dockerfile.api`
2. Rebuilt the image: `docker compose build api`
3. Restarted: `docker compose up -d api`

### Prevention
- After adding new top-level source directories (`auth/`, `config/`, etc.), always verify they are `COPY`'d in the Dockerfile
- Add a startup check: `docker exec <api> python -c "from ingestion.routers.auth_router import router; print('OK')"`

---

## BUG-009: `DATABASE_URL=localhost` Fails Inside Container

**Severity**: 🔴 High (API cannot start — bootstrap times out)  
**Date Found**: 2026-04-22  
**Date Fixed**: 2026-04-22  
**Status**: ✅ Resolved

### Symptom
After container rebuild, API container crashed at startup:
```
RuntimeError: Database not reachable after 60s
```
`docker ps` showed `aegis-db` healthy, but `aegis-api` failed to connect.

### Root Cause
`.env` had `DATABASE_URL=postgresql://aegis_user:aegis_pass@localhost:5432/aegis_db`.  
Inside the API container, `localhost` resolves to the container itself — not the PostgreSQL container. The correct hostname is `db` (the Docker Compose service name), which Docker's internal DNS resolves to the database container's IP.

This is the same class of bug as BUG-006 (dashboard → API), but for the API → DB connection.

### Solution
Changed `.env`:
```
# Before:
DATABASE_URL=postgresql://aegis_user:aegis_pass@localhost:5432/aegis_db

# After:
DATABASE_URL=postgresql://aegis_user:aegis_pass@db:5432/aegis_db
```

### Prevention
- In multi-container Docker Compose stacks, **always use service names** as hostnames for inter-container connections
- `localhost` only works if services share the host network (e.g., local dev without Docker, or `network_mode: host`)
- Pattern: `postgresql://<user>:<pass>@<service-name>:<internal-port>/<db>`

---

## BUG-010: Plotly Waterfall `marker_color` Array Not a Valid Property

**Severity**: 🔴 High (dashboard crash — HR ROI tab completely unrenderable)  
**Date Found**: 2026-04-24  
**Date Fixed**: 2026-04-24  
**Status**: ✅ Resolved  
**Commit**: `b6afd7c`

### Symptom
```
ValueError: Invalid property specified for object of type
plotly.graph_objs.Waterfall: 'marker'

Bad property path:
marker_color
```
The HR Manager dashboard crashed when loading the Wellness ROI simulator tab. Full traceback pointed to `hr_view.py:216 → go.Waterfall(marker_color=[...])`.

### Root Cause
`go.Waterfall` does not support `marker_color` as a top-level array property (unlike `go.Bar`, which does). The Waterfall trace uses per-category sub-objects instead:
- `increasing` → bars that go up (positive relative measures)
- `decreasing` → bars that go down (negative relative measures)
- `totals` → absolute and total measure bars

The previous code was copied from a Bar chart pattern and never caught during testing because the HR view test path didn't reach the ROI tab.

### Solution
Replaced `marker_color=[...]` array with the correct sub-object API:

```python
# BEFORE (crashes):
go.Waterfall(
    ...
    marker_color=["#374151", "#22C55E", "#9BC800"],
)

# AFTER (correct):
go.Waterfall(
    ...
    decreasing={"marker": {"color": "#22C55E"}},   # savings bar (negative relative)
    totals={"marker": {"color": "#9BC800"}},        # projected premium (total measure)
    increasing={"marker": {"color": "#374151"}},    # current premium (absolute measure)
)
```

Color mapping:
- Current premium (`measure="absolute"`) → routed via `increasing` → `#374151` dark gray
- Wellness savings (`measure="relative"`, negative) → `decreasing` → `#22C55E` green
- Projected premium (`measure="total"`) → `totals` → `#9BC800` NullMask accent

### Prevention
- `go.Waterfall` and `go.Bar` look similar but have different coloring APIs — don't copy Bar chart color patterns to Waterfall
- Per-bar coloring in Waterfall must go through `increasing`/`decreasing`/`totals`, not `marker_color`

---

## Summary Statistics

| Severity | Count | Avg. Fix Time | Impact |
|----------|-------|---------------|--------|
| 🔴 High | 6 | ~25 min | Blocks dev / service |
| 🟠 Medium | 3 | ~20 min | UX broken |
| 🟡 Low | 1 | ~5 min | Cosmetic |
| **Total** | **10** | **~135 min** | **All resolved** |

### Timeline

```
2026-04-17 09:00 — BUG-001: Port 8000 held → User kills PID (30 min)
2026-04-17 09:30 — BUG-002: pycache stale bytecode → Clear cache (10 min)
2026-04-17 09:45 — BUG-003: ModuleNotFoundError → sys.path.insert fix (15 min)
2026-04-17 10:05 — BUG-004: Blank metrics (CSS) → [data-testid] + theme (20 min)
2026-04-17 10:25 — BUG-005: Unicode in Bash → Replace → with -> (5 min)
2026-04-18 14:00 — BUG-006: Docker localhost vs container DNS → AEGIS_API_URL env var (10 min)
2026-04-18 14:15 — BUG-007: Dark mode metric text invisible → explicit stMetricValue CSS + full dark theme (20 min)
2026-04-22 01:00 — BUG-008: /auth/token 404, stale Docker image → add COPY config/, rebuild (20 min)
2026-04-22 01:20 — BUG-009: DATABASE_URL localhost fails in container → change to db:5432 (5 min)
2026-04-24 — BUG-010: Plotly Waterfall marker_color invalid → decreasing/totals/increasing dicts (5 min)

Total: ~140 min across 3 days, all resolved ✅
```

---

## Lessons Learned

1. **Byte cache matters**: Always clear pycache after code changes in hot-reload scenarios
2. **CSS is fragile**: Streamlit classes change between versions; use data-testid instead
3. **sys.path surprises**: Streamlit/pytest add script dir, not project root—always verify with print
4. **Process killing**: Claude Code tool runner proxies can't be killed by OS tools—user must handle
5. **Unicode encoding**: Test output scripts on Windows, or set PYTHONIOENCODING env var

---

## Open Issues

None at this time. All bugs from Phase 5 development are resolved.

### Monitoring Points

- **Port 8000 recurrence**: If uvicorn fails to start, check `netstat -ano | findstr 8000`
- **CSS regressions**: If metrics go blank again, check `.streamlit/config.toml` theme setting
- **Module imports**: If new modules fail to import, verify `sys.path.insert` is in `dashboard/app.py`

