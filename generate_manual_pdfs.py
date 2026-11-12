#!/usr/bin/env python3
"""
Generates executive-quality PDF manuals for SkyOps XP12 from MANUAL_IT.md and MANUAL_EN.md.
"""
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        # Suppress running header on cover (page 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0284C7"))
            self.drawString(18 * mm, 285 * mm, "SKYOPS XP12")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            doc_title = getattr(self, "doc_title", "Manuale Operativo")
            self.drawString(42 * mm, 285 * mm, f"|   {doc_title}")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.6)
            self.line(18 * mm, 282 * mm, 192 * mm, 282 * mm)

        # Running Footer on all pages
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.6)
        self.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(18 * mm, 10 * mm, "SkyOps XP12 — Zero Plugins Required (Native UDP 49000)")
        is_it = getattr(self, "lang", "it") == "it"
        page_text = f"Pagina {self._pageNumber} di {page_count}" if is_it else f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(192 * mm, 10 * mm, page_text)
        self.restoreState()

def clean_markdown_inline(text):
    """Converts inline markdown like **bold**, *italic*, `code` to ReportLab tags."""
    # Replace math KaTeX formulas with clean readable unicode
    text = text.replace(r"\sqrt{\text{MTOW} / 50} \times (\text{distanza} / 100) \times \text{tariffa}", "√[MTOW / 50] × [Distanza / 100] × Tariffa Base")
    text = text.replace(r"\sqrt{\text{MTOW} / 50} \times (\text{distance} / 100) \times \text{unit rate}", "√[MTOW / 50] × [Distance / 100] × Unit Rate")
    text = text.replace(r"$\sqrt{\text{MTOW} / 50} \times (\text{distanza} / 100) \times \text{tariffa}$", "<b>√[MTOW / 50] × [Distanza / 100] × Tariffa Base</b>")
    text = text.replace(r"$\sqrt{\text{MTOW} / 50} \times (\text{distance} / 100) \times \text{unit rate}$", "<b>√[MTOW / 50] × [Distance / 100] × Unit Rate</b>")

    # 1. Extract and protect backtick code spans
    code_spans = []
    def save_code(m):
        code_spans.append(m.group(1))
        return f"___CODE_{len(code_spans)-1}___"
    
    text = re.sub(r"`([^`]+)`", save_code, text)

    # 2. XML escape & < >
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 3. Bold **text**
    text = re.sub(r"\*\*([^\*]+?)\*\*", r"<b>\1</b>", text)

    # 4. Italic *text* (only when surrounded by word/space, not bare asterisks like K*)
    text = re.sub(r"(?<!\w)\*([^\*\s][^\*]*?[^\*\s]|\w)\*(?!\w)", r"<i>\1</i>", text)

    # 5. Restore code spans cleanly
    for idx, c in enumerate(code_spans):
        clean_c = c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace(f"___CODE_{idx}___", f'<font face="Courier" color="#0369A1"><b>{clean_c}</b></font>')

    return text

def build_pdf_from_markdown(md_path, pdf_path, lang="it"):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#BAE6FD"),
        alignment=0
    )

    badge_style = ParagraphStyle(
        "CoverBadge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#38BDF8"),
        alignment=0
    )

    h1_style = ParagraphStyle(
        "CustomH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "CustomH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#0369A1"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        "CustomH3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=2,
        spaceAfter=3
    )

    bullet_style = ParagraphStyle(
        "CustomBullet",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=12,
        firstLineIndent=-8,
        spaceBefore=1.5,
        spaceAfter=1.5
    )

    code_style = ParagraphStyle(
        "CustomCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0F172A")
    )

    callout_style = ParagraphStyle(
        "CustomCallout",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#0F172A")
    )

    story = []

    # 1. Header Banner
    banner_title = "SKYOPS XP12"
    banner_sub = (
        "Piattaforma Operativa, Gestione Flotta &amp; Economia Reale per X-Plane 12"
        if lang == "it"
        else "Operations, Persistent Fleet &amp; Authentic Airline Economy for X-Plane 12"
    )
    banner_badge = (
        "MANUALE OPERATIVO &amp; GUIDA UTENTE  •  VERSIONE 1.0.0  •  ZERO PLUGIN RICHIESTI (UDP 49000)"
        if lang == "it"
        else "OPERATIONS MANUAL &amp; USER GUIDE  •  VERSION 1.0.0  •  ZERO PLUGINS REQUIRED (UDP 49000)"
    )

    banner_data = [
        [
            Paragraph(banner_badge, badge_style),
        ],
        [
            Spacer(1, 1 * mm),
        ],
        [
            Paragraph(f"<b>{banner_title}</b>", title_style),
        ],
        [
            Paragraph(banner_sub, subtitle_style),
        ]
    ]
    banner_table = Table(banner_data, colWidths=[174 * mm])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0B132B")),
        ("PADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, -1), (-1, -1), 3, colors.HexColor("#0284C7")),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 8 * mm))

    # Parse markdown lines
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()

        # Code block handler
        if line.startswith("```"):
            if in_code_block:
                # End code block
                in_code_block = False
                code_text = "<br/>".join(clean_markdown_inline(c) for c in code_lines)
                code_p = Paragraph(code_text, code_style)
                code_table = Table([[code_p]], colWidths=[174 * mm])
                code_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ]))
                story.append(code_table)
                story.append(Spacer(1, 3 * mm))
                code_lines = []
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(raw_line)
            i += 1
            continue

        # Skip main markdown top title (already in banner) and table of contents
        if line.startswith("# ✈️") or line.startswith("## Indice") or line.startswith("## Table of"):
            i += 1
            # Skip subsequent TOC lines
            while i < len(lines) and (lines[i].strip().startswith("1.") or lines[i].strip().startswith("- [") or lines[i].strip() == "---" or lines[i].strip() == ""):
                i += 1
            continue

        # Horizontal Rule
        if line == "---":
            story.append(Spacer(1, 2 * mm))
            story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#E2E8F0"), spaceAfter=5, spaceBefore=3))
            i += 1
            continue

        # Headings
        if line.startswith("## "):
            h_text = clean_markdown_inline(line[3:])
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(h_text, h1_style))
            story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#0284C7"), spaceAfter=4, spaceBefore=0))
            i += 1
            continue

        if line.startswith("### "):
            h_text = clean_markdown_inline(line[4:])
            story.append(Paragraph(h_text, h2_style))
            i += 1
            continue

        if line.startswith("#### "):
            h_text = clean_markdown_inline(line[5:])
            story.append(Paragraph(h_text, h3_style))
            i += 1
            continue

        # Empty line
        if not line:
            i += 1
            continue

        # Bullet list items
        if line.startswith("* ") or line.startswith("- "):
            bullet_text = clean_markdown_inline(line[2:])
            p_text = f"•&nbsp;&nbsp;{bullet_text}"
            story.append(Paragraph(p_text, bullet_style))
            i += 1
            continue

        # Numbered list items
        m_num = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m_num:
            num_idx, num_rest = m_num.groups()
            p_text = f"<b>{num_idx}.</b>&nbsp;&nbsp;{clean_markdown_inline(num_rest)}"
            story.append(Paragraph(p_text, bullet_style))
            i += 1
            continue

        # Q&A / Callout boxes
        if line.startswith("D:") or line.startswith("Q:") or line.startswith("R:") or line.startswith("A:"):
            is_q = line.startswith("D:") or line.startswith("Q:")
            call_text = clean_markdown_inline(line)
            call_p = Paragraph(call_text, callout_style)
            bg_col = colors.HexColor("#F0F9FF") if is_q else colors.HexColor("#F8FAFC")
            line_col = colors.HexColor("#0284C7") if is_q else colors.HexColor("#10B981")
            call_table = Table([[call_p]], colWidths=[174 * mm])
            call_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), bg_col),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("LINELEFT", (0, 0), (-1, -1), 3, line_col),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(call_table)
            story.append(Spacer(1, 2 * mm))
            i += 1
            continue

        # Standard paragraph
        p_text = clean_markdown_inline(line)
        story.append(Paragraph(p_text, body_style))
        i += 1

    # Build document
    def on_first_page(canvas_obj, doc_obj):
        canvas_obj.lang = lang
        canvas_obj.doc_title = "Manuale Utente" if lang == "it" else "User Manual"

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated: {pdf_path} (size: {os.path.getsize(pdf_path) / 1024:.1f} KB)")

if __name__ == "__main__":
    base = "/home/simmer77/X-Plane/XplaneSDK/SDK/SkyOps-XP"
    build_pdf_from_markdown(
        os.path.join(base, "MANUAL_IT.md"),
        os.path.join(base, "SkyOps_XP12_Manuale_Utente_IT.pdf"),
        lang="it"
    )
    build_pdf_from_markdown(
        os.path.join(base, "MANUAL_EN.md"),
        os.path.join(base, "SkyOps_XP12_User_Manual_EN.pdf"),
        lang="en"
    )
