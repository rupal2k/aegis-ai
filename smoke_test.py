"""
Aegis AI smoke test — runs against one or both environments.
Usage:
    python smoke_test.py prod        # production only
    python smoke_test.py local       # localhost only
    python smoke_test.py both        # both (default)
"""
import httpx, sys, time

ENVS = {
    "prod":  "https://aegis-ai-wss8.onrender.com",
    "local": "http://localhost:8000",
}
PASS = "demo123"
USERS = [
    ("underwriter@safenet.com", "underwriter"),
    ("hr@technova.com",         "hr_admin"),
    ("hr@bharatsteel.com",      "hr_admin"),
]

# ── helpers ─────────────────────────────────────────────────────────────────

class Results:
    def __init__(self, label):
        self.label   = label
        self.passed  = 0
        self.failed  = 0
        self.details = []

    def ok(self, msg, detail=""):
        self.passed += 1
        suffix = f"  ({detail})" if detail else ""
        print(f"    [PASS] {msg}{suffix}")

    def fail(self, msg, detail=""):
        self.failed += 1
        self.details.append(f"{msg}: {detail}")
        suffix = f"  ({detail})" if detail else ""
        print(f"    [FAIL] {msg}{suffix}")

    def check(self, msg, ok, detail=""):
        (self.ok if ok else self.fail)(msg, detail)

    def summary(self):
        total = self.passed + self.failed
        status = "ALL PASS" if self.failed == 0 else f"{self.failed} FAILED"
        print(f"\n  {self.label}: {self.passed}/{total} pass  [{status}]")
        for d in self.details:
            print(f"    !! {d}")


def get_token(base, email, timeout=45):
    try:
        r = httpx.post(f"{base}/auth/token",
                       data={"username": email, "password": PASS},
                       timeout=timeout)
        if r.status_code == 200:
            return r.json().get("access_token")
    except Exception as e:
        pass
    return None


def auth_header(token):
    return {"Authorization": f"Bearer {token}"} if token else {}


# ── per-environment test suite ───────────────────────────────────────────────

def run_suite(label, base):
    r = Results(label)
    print(f"\n{'='*55}")
    print(f"  {label}  ({base})")
    print(f"{'='*55}")

    # 1. Health
    print("\n  [1] Health")
    try:
        h = httpx.get(f"{base}/health", timeout=30)
        r.check("GET /health", h.status_code == 200, h.json().get("status"))
    except Exception as e:
        r.fail("GET /health", str(e)[:60])

    try:
        hdb = httpx.get(f"{base}/health/db", timeout=30)
        r.check("GET /health/db", hdb.status_code == 200,
                hdb.json().get("database", "?"))
    except Exception as e:
        r.fail("GET /health/db", str(e)[:60])

    # 2. Auth
    print("\n  [2] Authentication")
    tokens = {}
    for email, role in USERS:
        t = get_token(base, email)
        tokens[role] = tokens.get(role) or t
        tokens[email] = t
        r.check(f"Login {email}", t is not None)

    uw_token = tokens.get("underwriter@safenet.com")
    hr_token = tokens.get("hr@technova.com")

    # 3. Companies
    print("\n  [3] Companies")
    companies, comp_ids = [], []
    if uw_token:
        try:
            resp = httpx.get(f"{base}/companies",
                             headers=auth_header(uw_token), timeout=20)
            r.check("GET /companies (underwriter)", resp.status_code == 200)
            if resp.status_code == 200:
                companies = resp.json()
                comp_ids  = [c.get("company_id") for c in companies]
                r.check("Companies present", len(companies) > 0,
                        f"{len(companies)} companies")
                r.check("COMP_001 in list", "COMP_001" in comp_ids)
                r.check("COMP_002 in list", "COMP_002" in comp_ids)
        except Exception as e:
            r.fail("GET /companies", str(e)[:60])

    # 4. RBAC — hr_admin sees only own company
    print("\n  [4] RBAC")
    if hr_token:
        try:
            resp = httpx.get(f"{base}/companies",
                             headers=auth_header(hr_token), timeout=20)
            r.check("hr_admin GET /companies", resp.status_code == 200)
            if resp.status_code == 200:
                hr_cos = resp.json()
                r.check("hr_admin sees only COMP_001",
                        len(hr_cos) == 1 and hr_cos[0].get("company_id") == "COMP_001",
                        f"got {[c.get('company_id') for c in hr_cos]}")
        except Exception as e:
            r.fail("RBAC check", str(e)[:60])

    # 5. Company prediction
    print("\n  [5] Company prediction")
    if uw_token and comp_ids:
        cid = comp_ids[0]
        try:
            t0   = time.time()
            resp = httpx.get(f"{base}/predict/company/{cid}",
                             headers=auth_header(uw_token), timeout=60)
            elapsed = time.time() - t0
            r.check(f"GET /predict/company/{cid}", resp.status_code == 200,
                    f"{elapsed:.1f}s")
            if resp.status_code == 200:
                p = resp.json()
                hrs = p.get("mean_hrs")
                r.check("mean_hrs valid",  hrs is not None and 0 <= hrs <= 100,
                        f"HRS={hrs}")
                r.check("risk_band set",   "risk_band" in p, p.get("risk_band"))
                drivers = p.get("top_risk_drivers", [])
                r.check("SHAP drivers",    len(drivers) > 0, f"{len(drivers)} drivers")
                r.check("Band pcts sum ~100",
                        abs(sum(p.get(k, 0) for k in
                            ["low_risk_pct","moderate_risk_pct",
                             "high_risk_pct","critical_risk_pct"]) - 100) < 1,
                        f"L={p.get('low_risk_pct')}% M={p.get('moderate_risk_pct')}% "
                        f"H={p.get('high_risk_pct')}% C={p.get('critical_risk_pct')}%")
        except Exception as e:
            r.fail(f"GET /predict/company/{cid}", str(e)[:60])

    # 6. Employee endpoint
    print("\n  [6] Employee prediction")
    if uw_token:
        payload = {
            "age": 38, "gender": "M", "bmi": 24.5,
            "smoker": False, "diabetic": False, "hypertension": False,
            "avg_daily_steps": 8000, "avg_resting_hr": 68,
            "avg_active_mins": 45, "avg_sleep_hours": 7.5, "avg_spo2": 98.0,
        }
        try:
            resp = httpx.post(f"{base}/predict/employee", json=payload,
                              headers=auth_header(uw_token), timeout=20)
            r.check("POST /predict/employee", resp.status_code == 200)
            if resp.status_code == 200:
                ep = resp.json()
                hrs_e = ep.get("health_risk_score")
                r.check("health_risk_score valid",
                        hrs_e is not None and 0 <= hrs_e <= 100, f"HRS={hrs_e}")
                r.check("top_drivers present",
                        len(ep.get("top_drivers", [])) > 0,
                        f"{len(ep.get('top_drivers', []))} drivers")
        except Exception as e:
            r.fail("POST /predict/employee", str(e)[:60])

    # 7. Employees list
    print("\n  [7] Employee roster")
    if uw_token and comp_ids:
        cid = comp_ids[0]
        try:
            resp = httpx.get(f"{base}/companies/{cid}/employees",
                             headers=auth_header(uw_token), timeout=20)
            r.check(f"GET /companies/{cid}/employees", resp.status_code == 200)
            if resp.status_code == 200:
                emps = resp.json()
                r.check("Employees present", len(emps) > 0, f"{len(emps)} employees")
        except Exception as e:
            r.fail("GET employees", str(e)[:60])

    # 8. Premium
    print("\n  [8] Premium & wellness ROI")
    if uw_token:
        try:
            resp = httpx.post(f"{base}/predict/premium",
                              json={"base_premium": 1_000_000, "hrs": 65},
                              headers=auth_header(uw_token), timeout=20)
            r.check("POST /predict/premium", resp.status_code == 200)
            if resp.status_code == 200:
                prem = resp.json()
                adj  = prem.get("adjusted_premium", 0)
                r.check("adjusted_premium > base (loading zone)",
                        adj > 1_000_000, f"{adj:,.0f}")
                r.check("zone = loading",
                        prem.get("zone") == "loading", prem.get("zone"))
        except Exception as e:
            r.fail("POST /predict/premium", str(e)[:60])

        try:
            resp = httpx.post(
                f"{base}/predict/wellness-roi",
                json={"base_premium": 1_000_000,
                      "current_hrs": 70,
                      "projected_hrs_after_program": 45},
                headers=auth_header(uw_token), timeout=20)
            r.check("POST /predict/wellness-roi", resp.status_code == 200)
            if resp.status_code == 200:
                roi = resp.json()
                sav = roi.get("annual_savings", 0)
                r.check("annual_savings > 0 (HRS improved)",
                        sav > 0, f"{sav:,.0f}")
                r.check("projected_zone better than current",
                        roi.get("projected_zone") in ("discount","standard"),
                        f"current={roi.get('current_zone')} -> projected={roi.get('projected_zone')}")
        except Exception as e:
            r.fail("POST /predict/wellness-roi", str(e)[:60])

    # 9. Auth rejection
    print("\n  [9] Security")
    try:
        resp = httpx.get(f"{base}/companies", timeout=10)
        r.check("No-auth rejected (401)", resp.status_code == 401,
                f"got {resp.status_code}")
    except Exception as e:
        r.fail("No-auth test", str(e)[:60])

    try:
        resp = httpx.get(f"{base}/companies",
                         headers={"Authorization": "Bearer bad.token.here"},
                         timeout=10)
        r.check("Bad token rejected (401)", resp.status_code == 401,
                f"got {resp.status_code}")
    except Exception as e:
        r.fail("Bad token test", str(e)[:60])

    r.summary()
    return r


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "both"
    targets = list(ENVS.items()) if mode == "both" else [(mode, ENVS[mode])]

    all_results = []
    for label, base in targets:
        all_results.append(run_suite(label.upper(), base))

    print(f"\n{'='*55}")
    print("  FINAL SUMMARY")
    print(f"{'='*55}")
    total_pass = sum(r.passed for r in all_results)
    total_fail = sum(r.failed for r in all_results)
    for r in all_results:
        status = "OK" if r.failed == 0 else f"{r.failed} FAIL"
        print(f"  {r.label:<8} {r.passed:>2}/{r.passed+r.failed} pass  [{status}]")
    print(f"\n  Overall: {total_pass}/{total_pass+total_fail} pass")
    sys.exit(0 if total_fail == 0 else 1)
