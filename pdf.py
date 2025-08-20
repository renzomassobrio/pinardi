import pandas as pd
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


# --- PDF generation ---
def create_pdf(dataframe, title="Generated Report"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("PROYECTO PINARDI", styles["Title"]))
    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 12))
    date_str = datetime.now().strftime("%d-%m-%Y")
    elements.append(Paragraph(f"Fecha: {date_str}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    if not dataframe.empty:
        data = [list(dataframe.columns)] + dataframe.values.tolist()
        table = Table(data)
        style = TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.grey),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("BACKGROUND", (0,1), (-1,-1), colors.beige),
            ("GRID", (0,0), (-1,-1), 1, colors.black)
        ])
        table.setStyle(style)
        elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
