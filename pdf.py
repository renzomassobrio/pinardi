import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

def generate_pdf(df_cuts_flat, parts):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    # Style for wrapped table content
    cell_style = ParagraphStyle(
        "table_cell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        wordWrap="CJK"
    )

    story = []

    PAGE_WIDTH, _ = A4
    usable_width = PAGE_WIDTH - doc.leftMargin - doc.rightMargin

    # Title
    story.append(Paragraph("Lista de Cortes", styles["Title"]))
    story.append(Spacer(1, 12))

    # Tables grouped by "Código"
    for codigo, group in df_cuts_flat.groupby("Código"):
        story.append(Paragraph(
            f"<b>{codigo} - {parts[codigo]['descripcion']}</b>",
            styles["Heading2"]
        ))
        story.append(Spacer(1, 6))

        group_no_code = group.drop(columns="Código")

        # Header and rows as wrapped Paragraphs
        header = [Paragraph(str(col), cell_style) for col in group_no_code.columns]
        rows = [
            [Paragraph(str(cell), cell_style) for cell in row]
            for row in group_no_code.values
        ]

        table_data = [header] + rows

        # Fit table to page width
        num_cols = len(group_no_code.columns)
        col_widths = [usable_width / num_cols] * num_cols

        table = Table(table_data, colWidths=col_widths)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP")
        ]))

        story.append(table)
        story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer

