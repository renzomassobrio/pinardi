from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

def create_pdf(dataframe, title="Reporte", total_cost=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("PROYECTO PINARDI", styles["Title"]))
    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1, 12))
    
    # Date
    date_str = datetime.now().strftime("%d-%m-%Y")
    elements.append(Paragraph(f"Fecha: {date_str}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    if not dataframe.empty:
        # Prepare table data
        data = [list(dataframe.columns)] + dataframe.values.tolist()
        table = Table(data, hAlign='CENTER', repeatRows=1)

        # Table style
        style = TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4F81BD")),  # header blue
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 12),
            ("BOTTOMPADDING", (0,0), (-1,0), 10),
            ("BACKGROUND", (0,1), (-1,-1), colors.whitesmoke),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey]),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black)
        ])
        table.setStyle(style)
        elements.append(table)
        elements.append(Spacer(1, 12))

        # Total cost
        if total_cost is not None:
            elements.append(Paragraph(f"<b>Costo total: ${total_cost:,.2f}</b>", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

