#!/usr/bin/env python3
"""
Generate publication-grade UI cards / mockups for Aegis AI README:
1. docs/images/underwriter-workbench.png (Underwriter Portfolio, Risk Triage & SHAP Waterfall)
2. docs/images/hr-wellness-portal.png (Corporate HR Dashboard, Department Comparison & ROI)
3. docs/images/actuarial-pricing-model.png (HRS Calibration Curve, Discount/Standard/Loading Zones)
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

def make_underwriter_workbench():
    W, H = 1200, 750
    img = Image.new("RGBA", (W, H), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    CYAN = (56, 189, 248, 255)
    GREEN = (52, 211, 153, 255)
    AMBER = (245, 158, 11, 255)
    ROSE = (244, 63, 94, 255)
    CARD_BG = (22, 27, 34, 255)
    CARD_BORDER = (48, 54, 61, 255)
    TEXT_WHITE = (240, 246, 252, 255)
    TEXT_MUTED = (139, 148, 158, 255)

    # Top app bar
    draw.rounded_rectangle([25, 20, W - 25, 75], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((45, 34), "🛡️ AEGIS AI — UNDERWRITER WORKBENCH", font=get_font(18, bold=True), fill=TEXT_WHITE)
    draw.text((580, 37), "Book View: 20 Companies • 5,000 Lives • Active Model: XGBoost v1", font=get_font(12), fill=TEXT_MUTED)
    
    # User pill
    draw.rounded_rectangle([W - 220, 30, W - 45, 65], radius=6, fill=(56//5, 189//5, 248//5, 255), outline=CYAN, width=1)
    draw.text((W - 205, 39), "👤 Demo Underwriter", font=get_font(12, bold=True), fill=CYAN)

    # Panel 1: Portfolio Triage & Summary KPIs
    kpi_w = 265
    kpi_h = 105
    kpis = [
        ("PORTFOLIO HRS", "48.2 / 100", "Standard Risk Band", GREEN),
        ("EXPECTED LOSS RATIO", "74.8%", "Target: ≤ 80.0%", CYAN),
        ("ACTIVE POLICIES", "20 Groups", "5,000 Covered Employees", AMBER),
        ("PRICING IMPACT", "+4.2% Net", "8 Discount / 6 Loaded", ROSE),
    ]
    for i, (title, val, sub, col) in enumerate(kpis):
        kx = 25 + i * (kpi_w + 20)
        draw.rounded_rectangle([kx, 95, kx + kpi_w, 95 + kpi_h], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
        draw.rounded_rectangle([kx + 10, 95, kx + kpi_w - 10, 98], radius=2, fill=col)
        draw.text((kx + 15, 108), title, font=get_font(11, bold=True), fill=TEXT_MUTED)
        draw.text((kx + 15, 128), val, font=get_font(22, bold=True), fill=TEXT_WHITE)
        draw.text((kx + 15, 168), sub, font=get_font(11), fill=col)

    # Panel 2: Company Explorer & Risk Triage (Left 560px)
    px, py, pw, ph = 25, 220, 560, 500
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((px + 20, py + 16), "EMPLOYER GROUP RISK TRIAGE", font=get_font(15, bold=True), fill=TEXT_WHITE)
    draw.text((px + 20, py + 40), "Select company to inspect underwriting profile and employee cohort", font=get_font(11), fill=TEXT_MUTED)
    draw.line([(px + 15, py + 62), (px + pw - 15, py + 62)], fill=CARD_BORDER, width=1)

    # Table Header
    draw.text((px + 20, py + 72), "COMPANY NAME", font=get_font(11, bold=True), fill=TEXT_MUTED)
    draw.text((px + 220, py + 72), "INDUSTRY", font=get_font(11, bold=True), fill=TEXT_MUTED)
    draw.text((px + 340, py + 72), "HRS", font=get_font(11, bold=True), fill=TEXT_MUTED)
    draw.text((px + 420, py + 72), "ZONE / ACTION", font=get_font(11, bold=True), fill=TEXT_MUTED)

    companies = [
        ("Apex Cloud Technologies", "IT Services", "34.1", "DISCOUNT (-11%)", GREEN),
        ("Titan Logistics India", "Logistics", "72.4", "LOADING (+18%)", ROSE),
        ("Bharat Engineering Ltd", "Manufacturing", "44.6", "STANDARD (0%)", CYAN),
        ("Kaveri Healthcare Labs", "Healthcare", "38.2", "DISCOUNT (-7%)", GREEN),
        ("Horizon Media Network", "Media", "68.9", "LOADING (+14%)", ROSE),
        ("Deccan Financial Corp", "Finance", "42.0", "STANDARD (0%)", CYAN),
        ("Surya Textiles Corp", "Textiles", "76.5", "LOADING (+22%)", ROSE),
    ]
    cy = py + 98
    for c_name, ind, score, zone, z_col in companies:
        draw.line([(px + 15, cy - 6), (px + pw - 15, cy - 6)], fill=(30, 36, 46), width=1)
        draw.text((px + 20, cy), c_name, font=get_font(12, bold=True), fill=TEXT_WHITE)
        draw.text((px + 220, cy), ind, font=get_font(11), fill=TEXT_MUTED)
        draw.text((px + 340, cy), score, font=get_font(12, bold=True), fill=z_col)
        draw.text((px + 420, cy), zone, font=get_font(11, bold=True), fill=z_col)
        cy += 48

    # Panel 3: Individual Employee SHAP Waterfall & Risk Drivers (Right 560px)
    sx, sy, sw, sh = 615, 220, 560, 500
    draw.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((sx + 20, sy + 16), "INDIVIDUAL SHAP WATERFALL ATTR.", font=get_font(15, bold=True), fill=TEXT_WHITE)
    draw.text((sx + 20, sy + 40), "Employee: #7a3f8e • Base Loss: 0.72 • Predicted HRS: 72.4 (Loading)", font=get_font(11), fill=TEXT_MUTED)
    draw.line([(sx + 15, sy + 62), (sx + sw - 15, sy + 62)], fill=CARD_BORDER, width=1)

    shap_items = [
        ("Daily Steps < 4,200 (Sedentary)", "+14.8 pts", 220, ROSE, True),
        ("Elevated Resting HR (84 bpm)", "+9.2 pts", 140, ROSE, True),
        ("Smoker Status (Active)", "+8.5 pts", 130, ROSE, True),
        ("Past Hospital Stay (1 event)", "+6.1 pts", 95, ROSE, True),
        ("Normal Blood SpO2 (98.2%)", "-4.5 pts", 70, GREEN, False),
        ("High Sleep Hours (7.8 hrs)", "-3.2 pts", 50, GREEN, False),
    ]
    shy = sy + 80
    for label, val, bar_w, col, is_pos in shap_items:
        draw.text((sx + 20, shy), label, font=get_font(12, bold=True), fill=TEXT_WHITE)
        draw.text((sx + 350, shy), val, font=get_font(12, bold=True), fill=col)
        # Bar
        bx = sx + 20
        by = shy + 22
        draw.rounded_rectangle([bx, by, bx + bar_w, by + 10], radius=3, fill=col)
        shy += 46

    # Bottom Underwriting Recommendation Box
    rec_y = sy + 370
    draw.rounded_rectangle([sx + 15, rec_y, sx + sw - 15, rec_y + 110], radius=6, fill=(13, 17, 23, 255), outline=CARD_BORDER, width=1)
    draw.text((sx + 25, rec_y + 12), "UNDERWRITER DECISION MEMO", font=get_font(11, bold=True), fill=AMBER)
    draw.text((sx + 25, rec_y + 32), "Workforce exhibits high sedentary lifestyle indicators and elevated resting vitals.", font=get_font(11), fill=TEXT_WHITE)
    draw.text((sx + 25, rec_y + 50), "Recommendation: Apply +18% risk loading, or offer structured wellness clawback.", font=get_font(11), fill=TEXT_WHITE)
    draw.text((sx + 25, rec_y + 75), "Generated automatically via ReportLab • PDF Ready for Broker Export", font=get_font(10), fill=TEXT_MUTED)

    out = "docs/images/underwriter-workbench.png"
    img.save(out, "PNG", optimize=True)
    print(f"Saved {out}")

def make_hr_portal():
    W, H = 1200, 750
    img = Image.new("RGBA", (W, H), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    CYAN = (56, 189, 248, 255)
    GREEN = (52, 211, 153, 255)
    AMBER = (245, 158, 11, 255)
    PURPLE = (168, 85, 247, 255)
    CARD_BG = (22, 27, 34, 255)
    CARD_BORDER = (48, 54, 61, 255)
    TEXT_WHITE = (240, 246, 252, 255)
    TEXT_MUTED = (139, 148, 158, 255)

    # Top app bar
    draw.rounded_rectangle([25, 20, W - 25, 75], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((45, 34), "🏢 AEGIS AI — CORPORATE HR WELLNESS PORTAL", font=get_font(18, bold=True), fill=TEXT_WHITE)
    draw.text((640, 37), "Tenant: Apex Cloud Technologies • 450 Active Employees", font=get_font(12), fill=TEXT_MUTED)
    
    # User pill
    draw.rounded_rectangle([W - 200, 30, W - 45, 65], radius=6, fill=(45//5, 212//5, 191//5, 255), outline=(45, 212, 191), width=1)
    draw.text((W - 185, 39), "👤 Demo HR Admin", font=get_font(12, bold=True), fill=(45, 212, 191))

    # KPIs
    kpi_w = 265
    kpi_h = 105
    kpis = [
        ("WORKFORCE HRS", "34.1 / 100", "Tier: Preferred Discount Zone", GREEN),
        ("AVG DAILY STEPS", "8,920 steps", "+1,240 vs. industry avg", CYAN),
        ("CURRENT PREMIUM", "₹42,50,000", "Eligible for -11% Discount", AMBER),
        ("PROJECTED SAVINGS", "₹4,67,500/yr", "Via Target Wellness Milestones", PURPLE),
    ]
    for i, (title, val, sub, col) in enumerate(kpis):
        kx = 25 + i * (kpi_w + 20)
        draw.rounded_rectangle([kx, 95, kx + kpi_w, 95 + kpi_h], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
        draw.rounded_rectangle([kx + 10, 95, kx + kpi_w - 10, 98], radius=2, fill=col)
        draw.text((kx + 15, 108), title, font=get_font(11, bold=True), fill=TEXT_MUTED)
        draw.text((kx + 15, 128), val, font=get_font(22, bold=True), fill=TEXT_WHITE)
        draw.text((kx + 15, 168), sub, font=get_font(11), fill=col)

    # Panel 2: Department Health Comparison (Left)
    px, py, pw, ph = 25, 220, 560, 500
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((px + 20, py + 16), "DEPARTMENT HEALTH BREAKDOWN", font=get_font(15, bold=True), fill=TEXT_WHITE)
    draw.text((px + 20, py + 40), "Cohort comparison across core corporate operational units", font=get_font(11), fill=TEXT_MUTED)
    draw.line([(px + 15, py + 62), (px + pw - 15, py + 62)], fill=CARD_BORDER, width=1)

    depts = [
        ("Engineering & QA", "160 Lives", "29.4", "Low Risk", GREEN, 320),
        ("Product & Design", "45 Lives", "31.2", "Low Risk", GREEN, 300),
        ("Human Resources", "20 Lives", "33.8", "Low Risk", GREEN, 280),
        ("Sales & Field Mktg", "110 Lives", "39.5", "Moderate", CYAN, 230),
        ("Finance & Admin", "55 Lives", "43.1", "Standard", AMBER, 190),
        ("Customer Support", "60 Lives", "46.2", "Standard", AMBER, 160),
    ]
    dy = py + 80
    for name, lives, score, tag, col, bar_w in depts:
        draw.text((px + 20, dy), name, font=get_font(12, bold=True), fill=TEXT_WHITE)
        draw.text((px + 220, dy), lives, font=get_font(11), fill=TEXT_MUTED)
        draw.text((px + 320, dy), f"HRS {score}", font=get_font(12, bold=True), fill=col)
        draw.text((px + 440, dy), tag, font=get_font(11, bold=True), fill=col)
        # Bar
        draw.rounded_rectangle([px + 20, dy + 22, px + 20 + bar_w, dy + 30], radius=3, fill=col)
        dy += 54

    # Panel 3: Wellness ROI Projection Simulator (Right)
    sx, sy, sw, sh = 615, 220, 560, 500
    draw.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((sx + 20, sy + 16), "WELLNESS PROGRAM ROI SIMULATOR", font=get_font(15, bold=True), fill=TEXT_WHITE)
    draw.text((sx + 20, sy + 40), "Simulate premium savings from targeted employee health improvements", font=get_font(11), fill=TEXT_MUTED)
    draw.line([(sx + 15, sy + 62), (sx + sw - 15, sy + 62)], fill=CARD_BORDER, width=1)

    sims = [
        ("Target Step Increase (+2,000/day)", "HRS -3.8 pts", "Save ₹1,85,000 / yr"),
        ("Sleep Hygiene Campaign (+45 min sleep)", "HRS -2.1 pts", "Save ₹98,000 / yr"),
        ("Smoking Cessation Program (15 quitters)", "HRS -4.5 pts", "Save ₹2,10,000 / yr"),
        ("Cardio & Fitness Challenge (Active mins)", "HRS -2.9 pts", "Save ₹1,40,000 / yr"),
    ]
    smy = sy + 80
    for title, hrs_delta, sav in sims:
        draw.rounded_rectangle([sx + 20, smy, sx + sw - 20, smy + 68], radius=6, fill=(13, 17, 23, 255), outline=CARD_BORDER, width=1)
        draw.text((sx + 35, smy + 12), title, font=get_font(12, bold=True), fill=TEXT_WHITE)
        draw.text((sx + 35, smy + 36), f"Impact: {hrs_delta}", font=get_font(11, bold=True), fill=CYAN)
        draw.text((sx + 320, smy + 36), sav, font=get_font(12, bold=True), fill=GREEN)
        smy += 80

    # Total projected box
    tot_y = sy + 410
    draw.rounded_rectangle([sx + 20, tot_y, sx + sw - 20, tot_y + 70], radius=6, fill=(52//5, 211//5, 153//5, 255), outline=GREEN, width=1)
    draw.text((sx + 35, tot_y + 14), "CUMULATIVE ESTIMATED BENEFIT", font=get_font(11, bold=True), fill=GREEN)
    draw.text((sx + 35, tot_y + 36), "HRS Improvement: 34.1 → 25.8  •  Annual Premium Saving: ₹6,33,000", font=get_font(12, bold=True), fill=TEXT_WHITE)

    out = "docs/images/hr-wellness-portal.png"
    img.save(out, "PNG", optimize=True)
    print(f"Saved {out}")

def make_pricing_model():
    W, H = 1200, 750
    img = Image.new("RGBA", (W, H), (13, 17, 23, 255))
    draw = ImageDraw.Draw(img)

    CYAN = (56, 189, 248, 255)
    GREEN = (52, 211, 153, 255)
    AMBER = (245, 158, 11, 255)
    ROSE = (244, 63, 94, 255)
    CARD_BG = (22, 27, 34, 255)
    CARD_BORDER = (48, 54, 61, 255)
    TEXT_WHITE = (240, 246, 252, 255)
    TEXT_MUTED = (139, 148, 158, 255)

    # Top app bar
    draw.rounded_rectangle([25, 20, W - 25, 75], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((45, 34), "📊 AEGIS AI — ACTUARIAL PRICING & RISK BANDS", font=get_font(18, bold=True), fill=TEXT_WHITE)
    draw.text((610, 37), "Health Risk Score (0-100) Mapping • Market Multipliers • Loss Ratio Calibration", font=get_font(12), fill=TEXT_MUTED)

    # Panel 1: Three Risk Zones (Horizontal Bar)
    zx, zy, zw, zh = 25, 95, W - 50, 240
    draw.rounded_rectangle([zx, zy, zx + zw, zy + zh], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((zx + 20, zy + 16), "ACTUARIAL PRICING BANDS & LOSS RATIO CALIBRATION", font=get_font(15, bold=True), fill=TEXT_WHITE)
    draw.text((zx + 20, zy + 40), "Translating individual biometric risk into insurer underwriting rate adjustments", font=get_font(11), fill=TEXT_MUTED)
    draw.line([(zx + 15, zy + 62), (zx + zw - 15, zy + 62)], fill=CARD_BORDER, width=1)

    # 3 Zone Cards
    zone_w = (zw - 60) // 3
    zones = [
        ("DISCOUNT ZONE", "HRS: 0 — 40", "Up to -15% Premium Discount", "Low predicted claims loss. Offers preferred rates to retain healthy corporate books.", GREEN),
        ("STANDARD ZONE", "HRS: 41 — 60", "0% Baseline Adjustment", "Average market loss ratio (70-80%). Policies priced strictly at book rates.", CYAN),
        ("LOADING ZONE", "HRS: 61 — 100", "Up to +30% Risk Surcharge", "Elevated loss expectation. Surcharges applied to preserve underwriting margin.", ROSE),
    ]
    for i, (z_title, hrs_rng, adj, desc, col) in enumerate(zones):
        bx = zx + 20 + i * (zone_w + 10)
        by = zy + 78
        draw.rounded_rectangle([bx, by, bx + zone_w, by + 140], radius=6, fill=(13, 17, 23, 255), outline=col, width=1)
        draw.text((bx + 15, by + 12), z_title, font=get_font(12, bold=True), fill=col)
        draw.text((bx + 15, by + 34), hrs_rng, font=get_font(16, bold=True), fill=TEXT_WHITE)
        draw.text((bx + 15, by + 60), adj, font=get_font(12, bold=True), fill=col)
        # Small description wrapping
        draw.text((bx + 15, by + 86), desc[:42], font=get_font(10), fill=TEXT_MUTED)
        draw.text((bx + 15, by + 102), desc[42:], font=get_font(10), fill=TEXT_MUTED)

    # Panel 2: Market Multipliers (Left)
    mx, my, mw, mh = 25, 355, 560, 370
    draw.rounded_rectangle([mx, my, mx + mw, my + mh], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((mx + 20, my + 16), "INDUSTRY & REGIONAL RISK MULTIPLIERS", font=get_font(15, bold=True), fill=TEXT_WHITE)
    draw.text((mx + 20, my + 40), "Derived from 200 Indian corporate group health insurance quotes", font=get_font(11), fill=TEXT_MUTED)
    draw.line([(mx + 15, my + 62), (mx + mw - 15, my + 62)], fill=CARD_BORDER, width=1)

    mults = [
        ("Telecom & Media", "1.135x / 1.133x", "+13.5% (High sedentary stress)", ROSE),
        ("Logistics & Transport", "1.101x", "+10.1% (Field risk / irregular sleep)", ROSE),
        ("Retail & Services", "1.045x", "+4.5% (Average shift variability)", AMBER),
        ("Pharma & Healthcare", "0.997x / 1.034x", "±1.5% (Baseline medical awareness)", CYAN),
        ("IT & Tech Services", "0.995x", "Book Rate (High wellness adoption)", CYAN),
        ("Construction & Heavy", "0.876x", "-12.4% (Lower sedentary claims in India)", GREEN),
    ]
    myy = my + 76
    for ind, mult, expl, col in mults:
        draw.text((mx + 20, myy), ind, font=get_font(12, bold=True), fill=TEXT_WHITE)
        draw.text((mx + 210, myy), mult, font=get_font(12, bold=True), fill=col)
        draw.text((mx + 330, myy), expl, font=get_font(10), fill=TEXT_MUTED)
        myy += 44

    # Panel 3: Premium Formula & Calculation Engine (Right)
    rx, ry, rw, rh = 615, 355, 560, 370
    draw.rounded_rectangle([rx, ry, rx + rw, ry + rh], radius=8, fill=CARD_BG, outline=CARD_BORDER, width=1)
    draw.text((rx + 20, ry + 16), "MATHEMATICAL PRICING SPECIFICATION", font=get_font(15, bold=True), fill=TEXT_WHITE)
    draw.text((rx + 20, ry + 40), "Loss ratio regression calibrated via percentile normalization", font=get_font(11), fill=TEXT_MUTED)
    draw.line([(rx + 15, ry + 62), (rx + rw - 15, ry + 62)], fill=CARD_BORDER, width=1)

    formulas = [
        ("Base Rate Multiplier", "Eff_Base = Base_Premium × Industry_Mult × Region_Mult × Sum_Band"),
        ("Discount Calculation", "Discount% = (40 - HRS) / 40 × 15%   (for HRS ≤ 40)"),
        ("Standard Calculation", "Adjustment% = 0%   (for 40 < HRS ≤ 60)"),
        ("Loading Calculation", "Loading% = (HRS - 60) / 40 × 30%   (for HRS > 60)"),
        ("Final Premium Quote", "Adjusted_Premium = Eff_Base × (1 ± Adjustment%)"),
    ]
    fy = ry + 80
    for name, form in formulas:
        draw.rounded_rectangle([rx + 20, fy, rx + rw - 20, fy + 48], radius=5, fill=(13, 17, 23, 255), outline=CARD_BORDER, width=1)
        draw.text((rx + 30, fy + 8), name, font=get_font(11, bold=True), fill=CYAN)
        draw.text((rx + 30, fy + 26), form, font=get_font(11), fill=TEXT_WHITE)
        fy += 56

    out = "docs/images/actuarial-pricing-model.png"
    img.save(out, "PNG", optimize=True)
    print(f"Saved {out}")

if __name__ == "__main__":
    make_underwriter_workbench()
    make_hr_portal()
    make_pricing_model()
