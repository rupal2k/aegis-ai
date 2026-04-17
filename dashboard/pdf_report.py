"""Generate PDF underwriting reports."""
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
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    rate, sym = _RATES.get(currency, _RATES["INR"])

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Heading1"],
        fontSize=20, textColor=colors.HexColor("#0C447C"), spaceAfter=12
    )
    h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                        fontSize=14, textColor=colors.HexColor("#185FA5"),
                        spaceBefore=12, spaceAfter=6)

    story = []

    story.append(Paragraph("Aegis AI — Underwriting Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}  |  Currency: {currency}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Company Profile", h2))
    profile = [
        ["Company",        company_data.get("company_name", "—")],
        ["Company ID",     company_data.get("company_id", "—")],
        ["Employees",      str(company_data.get("employee_count", 0))],
        ["Report Date",    datetime.now().strftime("%Y-%m-%d")],
    ]
    t = Table(profile, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#E6F1FB")),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#B5D4F4")),
        ("PADDING",    (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Health Risk Assessment", h2))
    hrs = company_data.get("mean_hrs", 0)
    band = company_data.get("risk_band", "—")
    risk = [
        ["Mean Health Risk Score",   f"{hrs:.1f} / 100"],
        ["Risk Band",                band],
        ["Predicted Loss Ratio",     f"{company_data.get('mean_loss_ratio', 0):.3f}"],
        ["Low Risk Employees",       f"{company_data.get('low_risk_pct', 0):.1f}%"],
        ["Moderate Risk Employees",  f"{company_data.get('moderate_risk_pct', 0):.1f}%"],
        ["High Risk Employees",      f"{company_data.get('high_risk_pct', 0):.1f}%"],
        ["Critical Risk Employees",  f"{company_data.get('critical_risk_pct', 0):.1f}%"],
    ]
    t = Table(risk, colWidths=[7*cm, 8*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#E1F5EE")),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#9FE1CB")),
        ("PADDING",    (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Premium Recommendation", h2))
    prem = [
        ["Base Premium",         _fmt(premium_data.get("base_premium", 0), rate, sym)],
        ["Adjusted Premium",     _fmt(premium_data.get("adjusted_premium", 0), rate, sym)],
        ["Adjustment",           f"{premium_data.get('adjustment_pct', 0):+.2f}%"],
        ["Pricing Zone",         premium_data.get("zone", "—").title()],
    ]
    t = Table(prem, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#FAEEDA")),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#FAC775")),
        ("PADDING",    (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f"<b>Recommendation:</b> {premium_data.get('recommendation', '')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    drivers = company_data.get("top_risk_drivers", [])
    if drivers:
        story.append(Paragraph("Top Risk Drivers", h2))
        rows = [["Feature", "Importance"]]
        for d in drivers[:5]:
            rows.append([d.get("feature", "—"), f"{d.get('importance', 0):.3f}"])
        t = Table(rows, colWidths=[10*cm, 5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EEEDFE")),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#CECBF6")),
            ("PADDING",    (0,0), (-1,-1), 6),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ]))
        story.append(t)

    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "<i>Generated by Aegis AI — Dynamic Underwriting Platform</i>",
        styles["Italic"]
    ))

    doc.build(story)
    return buf.getvalue()
