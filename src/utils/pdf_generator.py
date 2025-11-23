from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import HRFlowable
from datetime import datetime
from io import BytesIO
from typing import List


def generate_pdf_report(queries: List[dict], title: str = "Query Report") -> bytes:
    """
    Generate a PDF report from saved queries.

    Args:
        queries: List of query dictionaries
        title: Report title

    Returns:
        PDF content as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=8,
        fontName='Courier',
        backColor=colors.Color(0.95, 0.95, 0.95),
        leftIndent=10,
        rightIndent=10,
        spaceBefore=6,
        spaceAfter=6
    )

    # Build document
    elements = []

    # Title
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ParagraphStyle('Date', parent=styles['Normal'], alignment=1)
    ))
    elements.append(Spacer(1, 30))

    # Summary table
    summary_data = [
        ['Total Queries', str(len(queries))],
        ['Report Date', datetime.now().strftime('%Y-%m-%d')],
    ]
    summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))

    # Queries
    for i, query in enumerate(queries, 1):
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elements.append(Spacer(1, 10))

        # Query header
        elements.append(Paragraph(f"Query {i}", heading_style))

        # Timestamp
        timestamp = query.get('timestamp', '')
        if hasattr(timestamp, 'strftime'):
            timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        elements.append(Paragraph(f"<b>Time:</b> {timestamp}", normal_style))

        # Question
        question = query.get('user_question', 'N/A')
        elements.append(Paragraph(f"<b>Question:</b> {question}", normal_style))

        # Execution time
        exec_time = query.get('execution_time', 0)
        if exec_time:
            elements.append(Paragraph(f"<b>Execution Time:</b> {exec_time:.2f}s", normal_style))

        # SQL Query
        sql = query.get('sql_query', '')
        if sql:
            elements.append(Paragraph("<b>SQL Query:</b>", normal_style))
            # Escape special characters
            sql_escaped = sql.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(f"<pre>{sql_escaped}</pre>", code_style))

        # Result
        result = query.get('result_text', '')
        if result:
            elements.append(Paragraph("<b>Result:</b>", normal_style))
            result_escaped = str(result)[:500].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(result_escaped, normal_style))

        # Notes
        notes = query.get('notes', '')
        if notes:
            elements.append(Paragraph(f"<b>Notes:</b> {notes}", normal_style))

        # Feedback
        feedback = query.get('feedback', 'none')
        if feedback != 'none':
            emoji = '👍' if feedback == 'like' else '👎'
            elements.append(Paragraph(f"<b>Feedback:</b> {emoji} {feedback}", normal_style))

        elements.append(Spacer(1, 20))

        # Page break after every 3 queries
        if i % 3 == 0 and i < len(queries):
            elements.append(PageBreak())

    # Build PDF
    doc.build(elements)

    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
