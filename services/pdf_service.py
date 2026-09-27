from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_pdf_report(report_path, inspection_record, user_record):
    try:
        doc = SimpleDocTemplate(report_path, pagesize=letter, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, alignment=1, spaceAfter=18)
        heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, spaceBefore=12, spaceAfter=6)
        body_style = ParagraphStyle("BodyStyle", parent=styles["BodyText"], fontSize=10, leading=14)

        story = []
        story.append(Paragraph("AI PRODUCT QUALITY INSPECTION REPORT", title_style))
        story.append(Spacer(1, 0.2 * inch))

        data = [
            ["Inspection ID", str(inspection_record["id"])],
            ["Date", inspection_record["timestamp"]],
            ["Customer", user_record["full_name"]],
            ["Product", inspection_record["product_name"]],
            ["Category", inspection_record["category"]],
            ["Result", inspection_record["result"]],
            ["Confidence", f"{float(inspection_record['confidence'] or 0) * 100:.0f}%"],
            ["Severity", inspection_record["severity"]],
        ]

        table = Table(data, colWidths=[2.2 * inch, 3.8 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Detected Defects", heading_style))
        defects = inspection_record.get("defects") or "No visible defects detected."
        if isinstance(defects, list):
            defect_text = "<br/>".join([
                f"• {item.get('type', 'Defect')}: {item.get('description', '')} ({item.get('severity', 'Unknown')})"
                for item in defects
            ]) if defects else "No visible defects detected."
        else:
            defect_text = str(defects)
        story.append(Paragraph(defect_text, body_style))

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("AI Summary", heading_style))
        story.append(Paragraph(str(inspection_record.get("summary", "")), body_style))

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Recommendation", heading_style))
        story.append(Paragraph(str(inspection_record.get("recommendation", "")), body_style))

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("This report is generated from AI-assisted visual inspection and should not replace required professional quality-control procedures.", body_style))

        doc.build(story)
        return True
    except Exception:
        return False
