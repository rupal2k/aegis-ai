#!/usr/bin/env python3
"""
Generate a publication-grade, high-legibility Architecture & Pipeline Diagram
for Aegis AI (1600 x 1050 px).
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def get_font(size, bold=False):
    font_paths = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans{'-Bold' if bold else '-Regular'}.ttf",
    ]
    for path in font_paths:
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_card(draw, x, y, w, h, title, subtitle, items, accent_col, badge=""):
    CARD_BG = (22, 27, 34, 255)
    CARD_BORDER = (48, 54, 61, 255)
    TEXT_WHITE = (240, 246, 252, 255)
    TEXT_MUTED = (139, 148, 158, 255)
    TEXT_DIM = (110, 118, 129, 255)
    
    font_title = get_font(18, bold=True)
    font_sub = get_font(12, bold=False)
    font_key = get_font(13, bold=True)
    font_val = get_font(12, bold=False)
    font_badge = get_font(11, bold=True)

    # Card background & border
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=CARD_BG, outline=CARD_BORDER, width=1)

    # Accent top border tab
    draw.rounded_rectangle([x + 12, y, x + w - 12, y + 4], radius=2, fill=accent_col)

    # Header Title
    draw.text((x + 16, y + 14), title, font=font_title, fill=TEXT_WHITE)
    
    # Optional Badge
    if badge:
        bbox = draw.textbbox((0, 0), badge, font=font_badge)
        bw, bh = bbox[2] - bbox[0] + 14, bbox[3] - bbox[1] + 8
        bx = x + w - bw - 14
        by = y + 14
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=4, fill=(accent_col[0]//5, accent_col[1]//5, accent_col[2]//5, 255), outline=accent_col, width=1)
        draw.text((bx + 7, by + 3), badge, font=font_badge, fill=accent_col)

    # Subtitle
    draw.text((x + 16, y + 40), subtitle, font=font_sub, fill=accent_col)

    # Separator
    draw.line([(x + 14, y + 62), (x + w - 14, y + 62)], fill=CARD_BORDER, width=1)

    # Items
    curr_y = y + 74
    for key, val in items:
        # Bullet indicator
        draw.ellipse([x + 16, curr_y + 4, x + 22, curr_y + 10], fill=accent_col)
        draw.text((x + 28, curr_y), key, font=font_key, fill=TEXT_WHITE)
        curr_y += 18
        draw.text((x + 28, curr_y), val, font=font_val, fill=TEXT_MUTED)
        curr_y += 24

def draw_arrow(draw, start, end, color, width=2, dashed=False, label=""):
    x1, y1 = start
    x2, y2 = end
    
    if dashed:
        dist = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        dash_len = 8
        steps = max(int(dist / dash_len), 1)
        for i in range(0, steps, 2):
            t1 = i / steps
            t2 = min((i + 1) / steps, 1.0)
            sx = x1 + (x2 - x1) * t1
            sy = y1 + (y2 - y1) * t1
            ex = x1 + (x2 - x1) * t2
            ey = y1 + (y2 - y1) * t2
            draw.line([(sx, sy), (ex, ey)], fill=color, width=width)
    else:
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    # Arrow head
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    head_len = 10
    head_angle = math.pi / 6
    
    left_x = x2 - head_len * math.cos(angle - head_angle)
    left_y = y2 - head_len * math.sin(angle - head_angle)
    right_x = x2 - head_len * math.cos(angle + head_angle)
    right_y = y2 - head_len * math.sin(angle + head_angle)
    
    draw.polygon([(x2, y2), (left_x, left_y), (right_x, right_y)], fill=color)

    # Label
    if label:
        font_lbl = get_font(11, bold=True)
        bbox = draw.textbbox((0, 0), label, font=font_lbl)
        lw, lh = bbox[2] - bbox[0] + 10, bbox[3] - bbox[1] + 6
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        draw.rounded_rectangle([mx - lw/2, my - lh/2, mx + lw/2, my + lh/2], radius=3, fill=(13, 17, 23, 230), outline=(48, 54, 61), width=1)
        draw.text((mx - lw/2 + 5, my - lh/2 + 2), label, font=font_lbl, fill=color)

def main():
    W, H = 1600, 1050
    img = Image.new("RGBA", (W, H), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    # Accent color palette
    CYAN = (56, 189, 248, 255)     # Ingestion & APIs
    AMBER = (245, 158, 11, 255)    # PostgreSQL Database
    PURPLE = (168, 85, 247, 255)   # 31-Feature Store
    GREEN = (52, 211, 153, 255)    # XGBoost & ML Engine
    ROSE = (244, 63, 94, 255)      # TreeSHAP Explainability
    INDIGO = (99, 102, 241, 255)   # Actuarial Premium Engine
    TEAL = (45, 212, 191, 255)     # Dual Dashboards

    # Subtle background dot grid
    for gx in range(0, W, 40):
        for gy in range(0, H, 40):
            draw.point((gx, gy), fill=(30, 36, 46, 180))

    # ---------------- HEADER ----------------
    font_badge = get_font(11, bold=True)
    font_main = get_font(28, bold=True)
    font_sub = get_font(14, bold=False)

    draw.rounded_rectangle([45, 20, 320, 44], radius=4, fill=(56//5, 189//5, 248//5, 255), outline=CYAN, width=1)
    draw.text((55, 25), "ENTERPRISE HEALTH UNDERWRITING ENGINE", font=font_badge, fill=CYAN)

    draw.text((45, 52), "AEGIS AI — SYSTEM ARCHITECTURE & DATA PIPELINE", font=font_main, fill=(240, 246, 252))
    draw.text((45, 88), "End-to-End Enterprise Flow: Biometric Ingestion • 31-Feature Matrix • XGBoost • TreeSHAP • Dynamic Premium Engine", font=font_sub, fill=(139, 148, 158))

    draw.line([(45, 114), (W - 45, 114)], fill=(48, 54, 61), width=1)

    # ---------------- COLUMN 1: INGESTION & STORAGE ----------------
    # 1A: Ingestion & Privacy
    c1_x, c1_w = 45, 345
    draw_card(draw, c1_x, 130, c1_w, 395,
              "INGESTION & PRIVACY",
              "Telemetry Normalization & Zero-PII Security",
              [
                  ("Wearables & Devices", "Garmin, Fitbit, Apple Health continuous vitals"),
                  ("HR Roster Intake", "CSV/Excel employee cohort onboarding"),
                  ("Clinical ICD-10 Registry", "Diagnosis codes, hospitalizations & claims"),
                  ("Salted SHA-256 Hashing", "Deterministic pseudonymization, zero raw PII"),
                  ("FastAPI Validation", "Pydantic contract schemas & rate limiting"),
                  ("Role-Scoped Auth", "JWT tokens: Underwriter vs. HR Admin access"),
              ],
              CYAN, badge="FASTAPI / REST")

    # 1B: PostgreSQL Database
    draw_card(draw, c1_x, 550, c1_w, 385,
              "RELATIONAL CORE & DB",
              "Multi-Tenant Persistence & Telemetry Store",
              [
                  ("Timeseries Telemetry", "60,004 monthly biometric records"),
                  ("Clinical Events DB", "19,160 ICD-10 visit & hospitalization logs"),
                  ("9 Lab Domain Registry", "Cardiac, diabetes, kidney, liver, etc."),
                  ("Multi-Tenant Data Model", "Strict company-scoped partitioning"),
                  ("Synthetic Bootstrap", "5,000 employees, 20 companies, 15 industries"),
                  ("MLflow Model Store", "Tracked training runs, metrics & artifacts"),
              ],
              AMBER, badge="POSTGRESQL 15")

    # ---------------- COLUMN 2: 31-FEATURE STORE ----------------
    c2_x, c2_w = 425, 350
    draw_card(draw, c2_x, 130, c2_w, 805,
              "31-FEATURE MATRIX",
              "Multi-Domain Biometric & Clinical Transformations",
              [
                  ("Demographic Baselines", "Age, BMI, self-reported smoker status"),
                  ("Activity & Motion", "Daily steps, step volatility, active minutes"),
                  ("Cardiorespiratory Vitals", "Resting HR, HR 30-day trend, blood SpO2"),
                  ("Sleep Architecture", "Total sleep duration, rest fragmentation"),
                  ("Clinical History", "Past hospitalizations, clinic visit frequency"),
                  ("Chronic Conditions", "Diabetes, hypertension, chronic comorbidity"),
                  ("9 Clinical Lab Flags", "Lipid, HbA1c, eGFR, ALT/AST, Iron, Thyroid..."),
                  ("Derived Activity Score", "Weighted combo of steps & aerobic minutes"),
                  ("Cardiorespiratory Score", "Resting heart rate & SpO2 stability index"),
                  ("Metabolic Risk Index", "Synergistic BMI, glucose & pressure score"),
                  ("Composite Clinical Score", "Multi-comorbidity weighted severity grade"),
              ],
              PURPLE, badge="FEATURE STORE")

    # ---------------- COLUMN 3: ML ENGINE & SHAP ----------------
    c3_x, c3_w = 810, 350
    draw_card(draw, c3_x, 130, c3_w, 395,
              "XGBOOST RISK ENGINE",
              "Loss Ratio Prediction & HRS Calibration",
              [
                  ("Prediction Target", "log(loss_ratio) expected claims ratio"),
                  ("Monotone Constraints", "Enforced actuarial risk directional guards"),
                  ("Optuna TPE Sampler", "50-trial cross-validated MAE tuning"),
                  ("HRS Scale Calibration", "Percentile mapping: 0 to 100 Health Risk"),
                  ("Production Validation", "MAE ~0.40, R² ~0.54, 60-80ms inference"),
                  ("Subgroup Parity Audit", "Gender-stratified fair underwriting checks"),
              ],
              GREEN, badge="XGBOOST")

    draw_card(draw, c3_x, 550, c3_w, 385,
              "TREESHAP ATTRIBUTION",
              "Localized Interpretability & Underwriter Explanations",
              [
                  ("TreeExplainer Engine", "Exact game-theoretic Shapley attribution"),
                  ("Top-5 Risk Drivers", "Ranked individual positive & negative factors"),
                  ("Risk Mitigators", "High steps, active exercise, healthy SpO2"),
                  ("Risk Accelerators", "Smoking, sedentary trends, elevated vitals"),
                  ("Plain-Language Explanations", "Underwriter-ready human decision memos"),
                  ("Portfolio Aggregation", "Company-wide risk factor summaries"),
              ],
              ROSE, badge="SHAP CORE")

    # ---------------- COLUMN 4: PRICING & DASHBOARDS ----------------
    c4_x, c4_w = 1195, 360
    draw_card(draw, c4_x, 130, c4_w, 395,
              "ACTUARIAL PRICING",
              "Dynamic Premium Engine & Market Calibration",
              [
                  ("Discount Band (HRS 0-40)", "Up to 15% preferred rate reduction"),
                  ("Standard Band (HRS 41-60)", "Book rate baseline policy pricing"),
                  ("Loading Band (HRS 61-100)", "Up to 30% risk loading surcharge"),
                  ("20 Industry Multipliers", "Calibrated to Indian corporate benchmarks"),
                  ("6 Regional Cost Factors", "North, South, East, West, Central, NE"),
                  ("Wellness ROI Engine", "Projected premium delta from lifestyle shifts"),
              ],
              INDIGO, badge="PRICING ENGINE")

    draw_card(draw, c4_x, 550, c4_w, 385,
              "DUAL DASHBOARDS",
              "Role-Scoped Streamlit Portals & Reports",
              [
                  ("Underwriter Workbench", "Portfolio triage, cohort risk & SHAP waterfalls"),
                  ("Corporate HR Portal", "Workforce health summaries & wellness ROI"),
                  ("Automated PDF Memos", "ReportLab executive underwriting files"),
                  ("Roster Onboarding Wizard", "CSV/Excel batch employee scoring"),
                  ("Hugging Face Demo", "Live hosted cloud interactive playground"),
                  ("Render OpenAPI Docs", "Swagger endpoints & interactive sandbox"),
              ],
              TEAL, badge="STREAMLIT & UI")

    # ---------------- INTERCONNECT ARROWS ----------------
    # 1. Ingestion -> DB (Down)
    draw_arrow(draw, (c1_x + c1_w // 2, 525), (c1_x + c1_w // 2, 550), CYAN, width=2, label="Persist")

    # 2. Ingestion -> Feature Store (Right)
    draw_arrow(draw, (c1_x + c1_w, 240), (c2_x, 240), CYAN, width=2, label="Raw Telemetry")

    # 3. DB -> Feature Store (Right)
    draw_arrow(draw, (c1_x + c1_w, 700), (c2_x, 700), AMBER, width=2, label="Batch Sync")

    # 4. Feature Store -> XGBoost (Right)
    draw_arrow(draw, (c2_x + c2_w, 270), (c3_x, 270), PURPLE, width=2, label="31 Features")

    # 5. XGBoost -> SHAP (Down)
    draw_arrow(draw, (c3_x + c3_w // 2, 525), (c3_x + c3_w // 2, 550), GREEN, width=2, label="Model Trees")

    # 6. XGBoost -> Pricing Engine (Right)
    draw_arrow(draw, (c3_x + c3_w, 270), (c4_x, 270), GREEN, width=2, label="0-100 HRS")

    # 7. SHAP -> Dual Dashboards (Right)
    draw_arrow(draw, (c3_x + c3_w, 710), (c4_x, 710), ROSE, width=2, label="Drivers")

    # 8. Pricing Engine -> Dashboards (Down)
    draw_arrow(draw, (c4_x + c4_w // 2, 525), (c4_x + c4_w // 2, 550), INDIGO, width=2, label="Adjusted Quotes")

    # ---------------- FOOTER TECHNICAL LEGEND ----------------
    legend_y = H - 85
    draw.rounded_rectangle([45, legend_y, W - 45, legend_y + 55], radius=8, fill=(16, 20, 28, 245), outline=(48, 54, 61), width=1)
    
    font_sec = get_font(12, bold=True)
    draw.text((65, legend_y + 18), "PIPELINE LEGEND:", font=font_sec, fill=(240, 246, 252))
    leg_x = 220
    legends = [
        ("Ingestion & API (Cyan)", CYAN),
        ("Storage & DB (Amber)", AMBER),
        ("31-Feature Matrix (Purple)", PURPLE),
        ("XGBoost Regressor (Green)", GREEN),
        ("TreeSHAP Attribution (Rose)", ROSE),
        ("Actuarial Pricing (Indigo)", INDIGO),
        ("Role-Scoped UI (Teal)", TEAL),
    ]
    for label, col in legends:
        draw.rounded_rectangle([leg_x, legend_y + 20, leg_x + 14, legend_y + 34], radius=3, fill=col)
        draw.text((leg_x + 22, legend_y + 19), label, font=font_badge, fill=(139, 148, 158))
        leg_x += draw.textbbox((0, 0), label, font=font_badge)[2] + 28
        
    out_png = "docs/images/architecture-diagram.png"
    img.save(out_png, "PNG", optimize=True)
    print(f"Saved publication-grade architecture diagram to {out_png}")

if __name__ == "__main__":
    main()
