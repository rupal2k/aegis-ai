"""Generate publication-grade PDF underwriting reports for executive and broker review."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.units import cm
from io import BytesIO
from datetime import datetime

# Inline rates to keep pdf_report free of Streamlit imports
_RATES = {
    "INR": (1.0,      "\u20b9"),
    "USD": (0.01198,  "$"),
    "EUR": (0.01105,  "\u20ac"),
    "GBP": (0.00943,  "\u00a3"),
    "AED": (0.04400,  "AED "),
    "SGD": (0.01613,  "S$"),
    "AUD": (0.01852,  "A$"),
    "JPY": (1.8519,   "\u00a5"),
    "CAD": (0.01634,  "C$"),
    "CHF": (0.01076,  "CHF "),
}


def _fmt(inr_value: float, rate: float, sym: str) -> str:
    val = inr_value * rate
    return f"{sym}{val:,.0f}"


def generate_underwriting_report(company_data: dict, premium_data: dict,
                                  currency: str = "INR") -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.8*cm, bottomMargin=1.8*cm)

    rate, sym = _RATES.get(currency, _RATES["INR"])

    styles = getSampleStyleSheet()
    h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, fontName="Helvetica-Bold", textColor=colors.HexColor("#0F172A"),
        spaceBefore=14, spaceAfter=6
    )

    story = []

    # 1. Executive Top Header Banner
    header_data = [
        [
            Paragraph("<b>AEGIS AI</b> &nbsp;·&nbsp; Executive Underwriting Memo",
                      ParagraphStyle("Hdr", fontName="Helvetica-Bold", fontSize=14, textColor=colors.white)),
            Paragraph("CONFIDENTIAL",
                      ParagraphStyle("HdrR", fontName="Helvetica-Bold", fontSize=10, textColor=colors.HexColor("#38BDF8"), alignment=2))
        ]
    ]
    ht = Table(header_data, colWidths=[13*cm, 4.4*cm])
    ht.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#0F172A")),
        ("PADDING",    (0,0), (-1,-1), 9),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(ht)
    story.append(Spacer(1, 6))

    # Meta sub-line
    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%d %B %Y, %H:%M')} &nbsp;|&nbsp; "
        f"<b>Active Currency:</b> {currency} &nbsp;|&nbsp; "
        f"<b>Underwriting Engine:</b> XGBoost Regressor v1 + TreeSHAP",
        ParagraphStyle("SubMeta", fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#64748B"))
    ))
    story.append(Spacer(1, 10))

    # 2. Company Profile
    story.append(Paragraph("1. Employer Group Profile", h2))
    profile = [
        ["Company Name",   company_data.get("company_name", "—")],
        ["Company ID",     company_data.get("company_id", "—")],
        ["Covered Lives",  str(company_data.get("employee_count", 0)) + " Active Employees"],
        ["Report Date",    datetime.now().strftime("%Y-%m-%d")],
    ]
    t_prof = Table(profile, colWidths=[5.5*cm, 11.9*cm])
    t_prof.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F8FAFC")),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING",    (0,0), (-1,-1), 5),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
    ]))
    story.append(t_prof)
    story.append(Spacer(1, 10))

    # 3. Health Risk Assessment
    story.append(Paragraph("2. Biometric Risk Assessment", h2))
    hrs = company_data.get("mean_hrs", 0)
    band = company_data.get("risk_band", "—")
    risk = [
        ["Mean Health Risk Score (HRS)", f"{hrs:.1f} / 100"],
        ["Assigned Risk Tier",           band],
        ["Expected Claims Loss Ratio",   f"{company_data.get('mean_loss_ratio', 0):.3f}"],
        ["Low Risk Cohort (< 30 HRS)",   f"{company_data.get('low_risk_pct', 0):.1f}%"],
        ["Moderate Risk Cohort (30–60)", f"{company_data.get('moderate_risk_pct', 0):.1f}%"],
        ["High Risk Cohort (60–80)",     f"{company_data.get('high_risk_pct', 0):.1f}%"],
        ["Critical Risk Cohort (> 80)",  f"{company_data.get('critical_risk_pct', 0):.1f}%"],
    ]
    t_risk = Table(risk, colWidths=[7.5*cm, 9.9*cm])
    t_risk.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F0FDF4")),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#BBF7D0")),
        ("PADDING",    (0,0), (-1,-1), 5),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
    ]))
    story.append(t_risk)
    story.append(Spacer(1, 10))

    # 4. Premium Recommendation
    story.append(Paragraph("3. Actuarial Premium Recommendation", h2))
    prem = [
        ["Base Book Rate",         _fmt(premium_data.get("base_premium", 0), rate, sym)],
        ["Adjusted Quoted Rate",   _fmt(premium_data.get("adjusted_premium", 0), rate, sym)],
        ["Dynamic Rate Delta",     f"{premium_data.get('adjustment_pct', 0):+.2f}%"],
        ["Actuarial Pricing Zone", premium_data.get("zone", "—").title()],
    ]
    t_prem = Table(prem, colWidths=[5.5*cm, 11.9*cm])
    t_prem.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#FFFBEB")),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#FDE68A")),
        ("PADDING",    (0,0), (-1,-1), 5),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
    ]))
    story.append(t_prem)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        f"<b>Underwriting Action:</b> {premium_data.get('recommendation', '')}",
        ParagraphStyle("RecStyle", fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#1E293B"))
    ))
    story.append(Spacer(1, 10))

    # 5. Top SHAP Risk Drivers
    drivers = company_data.get("top_risk_drivers", [])
    if drivers:
        story.append(Paragraph("4. Key SHAP Risk Attributions", h2))
        rows = [["Rank", "Biometric / Clinical Feature", "Relative Impact"]]
        for idx, d in enumerate(drivers[:5]):
            rows.append([f"#{idx+1}", d.get("feature", "—"), f"{d.get('importance', 0):.3f}"])
        t_drivers = Table(rows, colWidths=[2.5*cm, 9.9*cm, 5.0*cm])
        t_drivers.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F1F5F9")),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ("PADDING",    (0,0), (-1,-1), 5),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 9),
        ]))
        story.append(t_drivers)

    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "<i>Generated automatically via Aegis AI Underwriting & Pricing Platform · Strictly Confidential for Internal Governance</i>",
        ParagraphStyle("Footer", fontName="Helvetica-Oblique", fontSize=8, textColor=colors.HexColor("#94A3B8"), alignment=1)
    ))

    doc.build(story)
    return buf.getvalue()
