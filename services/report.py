from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
import re

# Professional Color Palette
PRIMARY_BLUE = colors.HexColor("#1565C0")  # Dark Blue for headings
LIGHT_BLUE = colors.HexColor("#E3F2FD")    # Very light blue for backgrounds
BORDER_GRAY = colors.HexColor("#B0BEC5")   # Soft gray for borders

def generate_report(data):
    os.makedirs("reports", exist_ok=True)

     #get date safely
    date = data.get('client_info', {}).get('date', 'report')

    #sanitize filename (IMPORTANT)
    safe_date = re.sub(r'[^a-zA-Z0-9_-]', '_', str(date))


    filename = f"Report_{safe_date}.pdf"
    filepath = os.path.join("reports", filename)
    
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=0.5*inch, rightMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    
    # --- Custom Professional Styles ---
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Title'], 
        textColor=colors.whitesmoke, fontSize=18, spaceAfter=10, alignment=1
    )
    section_header_style = ParagraphStyle(
        'SectionHeader', parent=styles['Heading3'], 
        textColor=PRIMARY_BLUE, fontSize=11, spaceBefore=10, spaceAfter=5, fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'BodyStyle', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.black
    )
    
    story = []

    # ---------------- PROFESSIONAL HEADER BAR ----------------
    header_data = [[Paragraph("CLINICAL SOAP NOTE", title_style)]]
    header_table = Table(header_data, colWidths=[7.5*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), PRIMARY_BLUE),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # ---------------- CLIENT INFO BOX ----------------
    info = data.get('client_info', {})
    client_data = [
        [Paragraph(f"<b>CLIENT:</b> {info.get('name_last') or '___'}, {info.get('name_first') or '___'}", body_style),
         Paragraph(f"<b>DATE:</b> {info.get('date') or '___'}", body_style),
         Paragraph(f"<b>D.O.B:</b> {info.get('date_of_birth') or '___'}", body_style)]
    ]
    client_table = Table(client_data, colWidths=[3.5*inch, 2*inch, 2*inch])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 10))

    # ---------------- SECTIONS (S, O, A, P) ----------------
    sections = [
        ("SUBJECTIVE Assessment", data.get('subjective', {})),
        ("OBJECTIVE Findings", data.get('objective', {})),
        ("ASSESSMENT & Progress", data.get('assessment', {})),
        ("TREATMENT PLAN", data.get('plan', {}))
    ]

    for title, content in sections:
        story.append(Paragraph(title.upper(), section_header_style))
        story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY_BLUE, spaceAfter=5))
        
        # Format internal content based on the section
        if title.startswith("OBJECTIVE"):
            vitals = content.get('vitals', {})
            text_content = [
                f"<b>BP & PR:</b> Before: {content.get('bp_pr_before') or 'N/A'} | After: {content.get('bp_pr_after') or 'N/A'}",
                f"<b>Visual Findings:</b> {content.get('observations') or 'Normal'}",
                f"<b>Vitals/Tests:</b> Temp: {vitals.get('temperature') or 'Normal'}, Texture: {vitals.get('texture') or 'N/A'}, Tone: {vitals.get('tone_ht') or 'N/A'}"
            ]
        elif title.startswith("TREATMENT"):
            text_content = [
                f"<b>Modality:</b> {content.get('modality') or 'Deep Tissue'} ({content.get('duration_minutes', 60)} min)",
                f"<b>Clinical Focus:</b> {content.get('focus_on') or 'General Area'}",
                f"<b>Home Care:</b> {content.get('home_care_recommendations') or 'None'}"
            ]
        else:
            # Flatten other dictionaries into readable bullet points
            text_content = [f"<b>{k.replace('_', ' ').title()}:</b> {v}" for k, v in content.items() if v]

        for line in text_content:
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 3))
        
        story.append(Spacer(1, 10))

    # ---------------- SIGNATURE AREA ----------------
    story.append(Spacer(1, 20))
    sig_data = [
        [Paragraph(f"<b>Practitioner:</b> {data.get('student_name') or '________________'}", body_style), 
         Paragraph(f"<b>Supervisor:</b> {data.get('supervisor_name') or '________________'}", body_style)],
        [Paragraph("Signature: __________________________", body_style), 
         Paragraph("Signature: __________________________", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[3.75*inch, 3.75*inch])
    sig_table.setStyle(TableStyle([
        ('TOPPADDING', (0, 1), (-1, 1), 15),
    ]))
    story.append(sig_table)

    doc.build(story)
    return filepath