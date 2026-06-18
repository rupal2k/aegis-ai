"""Compare data between production and localhost environments."""
import httpx, json
from tabulate import tabulate

ENVS = {
    "PROD":  "https://aegis-ai-wss8.onrender.com",
    "LOCAL": "http://localhost:8000",
}
PASS = "demo123"

def get_token(base):
    r = httpx.post(f"{base}/auth/token",
                   data={"username": "underwriter@safenet.com", "password": PASS},
                   timeout=45)
    return r.json()["access_token"]

def api(base, token, path, **params):
    r = httpx.get(f"{base}{path}", headers={"Authorization": f"Bearer {token}"},
                  params=params, timeout=60)
    return r.json()

print("Authenticating...")
tokens = {k: get_token(v) for k, v in ENVS.items()}
print("Done.\n")

# ── 1. Companies ─────────────────────────────────────────────────────────────
print("=" * 60)
print("1. COMPANIES")
print("=" * 60)

companies = {k: api(v, tokens[k], "/companies") for k, v in ENVS.items()}
prod_ids  = {c["company_id"] for c in companies["PROD"]}
local_ids = {c["company_id"] for c in companies["LOCAL"]}

print(f"  PROD  : {len(companies['PROD'])} companies")
print(f"  LOCAL : {len(companies['LOCAL'])} companies")

only_prod  = prod_ids - local_ids
only_local = local_ids - prod_ids
if only_prod:  print(f"  Only in PROD : {only_prod}")
if only_local: print(f"  Only in LOCAL: {only_local}")
if not only_prod and not only_local:
    print("  Company IDs match exactly ✓")

# ── 2. Employees per company ──────────────────────────────────────────────────
print(f"\n{'=' * 60}")
print("2. EMPLOYEE COUNTS PER COMPANY")
print("=" * 60)

prod_emp  = {}
local_emp = {}

all_ids = sorted(prod_ids | local_ids)
for cid in all_ids:
    if cid in prod_ids:
        emps = api(ENVS["PROD"],  tokens["PROD"],  f"/companies/{cid}/employees")
        prod_emp[cid] = len(emps)
    if cid in local_ids:
        emps = api(ENVS["LOCAL"], tokens["LOCAL"], f"/companies/{cid}/employees")
        local_emp[cid] = len(emps)

rows = []
diffs = []
for cid in all_ids:
    p = prod_emp.get(cid, "N/A")
    l = local_emp.get(cid, "N/A")
    diff = "✓" if p == l else f"DIFF ({p} vs {l})"
    if p != l: diffs.append(cid)
    rows.append([cid, p, l, diff])

print(tabulate(rows, headers=["Company", "PROD employees", "LOCAL employees", "Match"]))
if not diffs:
    print("\n  All employee counts match ✓")
else:
    print(f"\n  Mismatches: {diffs}")

# ── 3. HRS scores per company ─────────────────────────────────────────────────
print(f"\n{'=' * 60}")
print("3. HRS SCORES PER COMPANY  (model predictions)")
print("=" * 60)

prod_hrs  = {}
local_hrs = {}

print("  Fetching predictions (this takes ~30s)...")
for cid in all_ids[:5]:   # first 5 for speed
    if cid in prod_ids:
        p = api(ENVS["PROD"],  tokens["PROD"],  f"/predict/company/{cid}")
        prod_hrs[cid]  = (p.get("mean_hrs"), p.get("risk_band"))
    if cid in local_ids:
        p = api(ENVS["LOCAL"], tokens["LOCAL"], f"/predict/company/{cid}")
        local_hrs[cid] = (p.get("mean_hrs"), p.get("risk_band"))

hrs_rows = []
for cid in sorted(prod_hrs):
    ph, pb = prod_hrs.get(cid, ("N/A", "N/A"))
    lh, lb = local_hrs.get(cid, ("N/A", "N/A"))
    hrs_diff = abs(ph - lh) if isinstance(ph, float) and isinstance(lh, float) else "N/A"
    band_match = "✓" if pb == lb else f"DIFF ({pb} / {lb})"
    hrs_rows.append([cid, f"{ph:.1f}" if isinstance(ph, float) else ph, pb,
                          f"{lh:.1f}" if isinstance(lh, float) else lh, lb,
                          f"{hrs_diff:.1f}" if isinstance(hrs_diff, float) else hrs_diff,
                          band_match])

print(tabulate(hrs_rows,
    headers=["Company", "PROD HRS", "PROD Band", "LOCAL HRS", "LOCAL Band", "Δ HRS", "Band Match"]))

# ── 4. DB row counts (local only via psycopg2) ────────────────────────────────
print(f"\n{'=' * 60}")
print("4. DATABASE ROW COUNTS")
print("=" * 60)
try:
    import psycopg2, os
    db_url = "postgresql://aegis_user:aegis_pass@localhost:5432/aegis_db"
    conn = psycopg2.connect(db_url)
    cur  = conn.cursor()
    tables = ["companies", "employees", "telemetry", "clinical_events", "training_snapshots"]
    local_counts = {}
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        local_counts[t] = cur.fetchone()[0]
    conn.close()

    # Prod counts via API (approximate from companies * avg employees)
    prod_total_emp = sum(prod_emp.values())
    local_total_emp = sum(local_emp.values())

    db_rows = [
        ["companies",         len(companies["PROD"]), local_counts["companies"]],
        ["employees (total)", prod_total_emp,          local_counts["employees"]],
        ["training_snapshots","N/A (no direct DB)",   local_counts["training_snapshots"]],
        ["telemetry",         "N/A (no direct DB)",   local_counts["telemetry"]],
        ["clinical_events",   "N/A (no direct DB)",   local_counts["clinical_events"]],
    ]
    print(tabulate(db_rows, headers=["Table", "PROD", "LOCAL"]))
except Exception as e:
    print(f"  Could not connect to local DB directly: {e}")

# ── 5. Key differences summary ────────────────────────────────────────────────
print(f"\n{'=' * 60}")
print("5. SUMMARY OF DIFFERENCES")
print("=" * 60)

diffs_found = []
if only_prod or only_local:
    diffs_found.append(f"Company set mismatch: +prod={only_prod}, +local={only_local}")
if diffs:
    diffs_found.append(f"Employee count mismatches: {diffs}")

# HRS model differences (expected — different model artifacts)
hrs_gaps = [(cid, prod_hrs[cid][0], local_hrs[cid][0])
            for cid in prod_hrs if cid in local_hrs
            and isinstance(prod_hrs[cid][0], float)
            and isinstance(local_hrs[cid][0], float)]
avg_gap = sum(abs(p-l) for _, p, l in hrs_gaps) / len(hrs_gaps) if hrs_gaps else 0

diffs_found.append(f"Model artifacts: PROD uses Render-baked model, LOCAL uses Docker-baked model")
diffs_found.append(f"Avg HRS delta across {len(hrs_gaps)} companies sampled: {avg_gap:.1f} points")
diffs_found.append(f"Lab columns: LOCAL training_snapshots all default 0 (migrated, not reseeded)")
diffs_found.append(f"config/users.json: PROD uses AEGIS_USERS_JSON env var, LOCAL uses docker cp copy")

for i, d in enumerate(diffs_found, 1):
    print(f"  {i}. {d}")
