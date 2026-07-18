import os
import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ── Colour palette (JudiQ brand) ───────────────────────────────────────────
_C_NAVY       = '#1a2744'   # headings, title
_C_BLUE       = '#2563eb'   # subheadings, accents
_C_LIGHT_BLUE = '#eff6ff'   # alternate row / back colour
_C_GREEN      = '#16a34a'   # high score
_C_AMBER      = '#d97706'   # medium score
_C_RED        = '#dc2626'   # low score / fatal
_C_GREY_TEXT  = '#374151'   # draft body
_C_MID_GREY   = '#6b7280'   # cover meta
_C_TABLE_HDR  = '#1e3a5f'   # table header bg
_C_DARK_TEXT  = '#111827'   # cover title


class PDFGenerator:

    # ──────────────────────────────────────────────────────────────────────
    # generate_report  – full analysis report
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_report(analysis_result: Dict[str, Any]) -> bytes:
        """
        Generate comprehensive PDF report with all analysis details.
        Ensures proper PDF format with correct MIME type.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                             Spacer, Table, TableStyle,
                                             PageBreak, KeepTogether,
                                             Preformatted)
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
                title="JUDIQ Legal Analysis Report",
                author="JUDIQ AI Legal Intelligence"
            )
            elements = []
            styles = getSampleStyleSheet()

            # ── styles ────────────────────────────────────────────────────
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor(_C_NAVY),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            heading_style = ParagraphStyle(
                'ReportHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.white,
                spaceAfter=12,
                spaceBefore=16,
                fontName='Helvetica-Bold',
                backColor=colors.HexColor(_C_NAVY),
                borderPadding=8
            )
            subheading_style = ParagraphStyle(
                'ReportSubHeading',
                parent=styles['Heading3'],
                fontSize=13,
                textColor=colors.HexColor(_C_BLUE),
                spaceAfter=8,
                spaceBefore=10,
                fontName='Helvetica-Bold'
            )
            body_style = ParagraphStyle(
                'ReportBody',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT,
                wordWrap='CJK'
            )

            # ── title ─────────────────────────────────────────────────────
            elements.append(Paragraph("JUDIQ AI - Legal Case Intelligence Report", title_style))
            elements.append(Spacer(1, 0.2 * inch))

            # ── summary table ─────────────────────────────────────────────
            score = analysis_result.get('score', 0)
            verdict = analysis_result.get('verdict', 'Unknown')
            risk_level = analysis_result.get('risk_level', 'Unknown')
            if score >= 70:
                score_color = colors.HexColor(_C_GREEN)
            elif score >= 40:
                score_color = colors.HexColor(_C_AMBER)
            else:
                score_color = colors.HexColor(_C_RED)

            summary_data = [
                ['Case Score:', f"{score}/100"],
                ['Verdict:', verdict],
                ['Risk Level:', risk_level],
                ['Generated:', datetime.now().strftime('%d %B %Y, %H:%M:%S')]
            ]
            summary_table = Table(summary_data, colWidths=[2 * inch, 4.5 * inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(_C_TABLE_HDR)),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('BACKGROUND', (1, 0), (1, 0), score_color),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(_C_MID_GREY)),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('PADDING', (0, 0), (-1, -1), 12),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.3 * inch))

            # ── decision ──────────────────────────────────────────────────
            decision = analysis_result.get('decision', {})
            if decision:
                decision_block = [Paragraph("Recommended Action", heading_style), Spacer(1, 0.1 * inch)]
                decision_label = decision.get('decision_label', 'Review Case')
                decision_detail = decision.get('detail', '')
                decision_block.append(Paragraph(f"<b>{decision_label}</b>", subheading_style))
                if decision_detail:
                    decision_block.append(Paragraph(decision_detail, body_style))
                decision_block.append(Spacer(1, 0.15 * inch))
                next_steps = decision.get('next_steps', [])
                if next_steps:
                    decision_block.append(Paragraph("<b>Next Steps:</b>", subheading_style))
                    for i, step in enumerate(next_steps, 1):
                        decision_block.append(Paragraph(f"{i}. {step}", body_style))
                        decision_block.append(Spacer(1, 0.05 * inch))
                decision_block.append(Spacer(1, 0.2 * inch))
                elements.append(KeepTogether(decision_block))

            # ── strengths ─────────────────────────────────────────────────
            strengths = analysis_result.get('strengths', [])
            if strengths:
                elements.append(Paragraph("Case Strengths", heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                for strength in strengths:
                    elements.append(Paragraph(f"✓ {strength if isinstance(strength, str) else str(strength)}", body_style))
                    elements.append(Spacer(1, 0.05 * inch))
                elements.append(Spacer(1, 0.2 * inch))

            # ── weaknesses ────────────────────────────────────────────────
            weaknesses = analysis_result.get('weaknesses', [])
            if weaknesses:
                elements.append(Paragraph("Identified Weaknesses", heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                for weakness in weaknesses:
                    if isinstance(weakness, dict):
                        risk = weakness.get('risk') or weakness.get('title') or weakness.get('text') or 'Unknown Risk'
                        severity = weakness.get('severity') or 'Unknown'
                        detail = weakness.get('detail') or weakness.get('description') or ''
                        sev_upper = str(severity).upper()
                        if sev_upper == 'FATAL':
                            color_hex = _C_RED
                        elif sev_upper == 'CRITICAL':
                            color_hex = '#ea580c'
                        elif sev_upper == 'HIGH':
                            color_hex = _C_AMBER
                        else:
                            color_hex = _C_BLUE
                        weakness_text = (
                            f"<b>{risk}</b> "
                            f"[<font color='{color_hex}'><b>{severity}</b></font>]: {detail}"
                        )
                    else:
                        weakness_text = str(weakness)
                    elements.append(Paragraph(f"⚠ {weakness_text}", body_style))
                    elements.append(Spacer(1, 0.05 * inch))
                elements.append(Spacer(1, 0.2 * inch))

            # ── timeline ──────────────────────────────────────────────────
            timeline = analysis_result.get('timeline', [])
            if timeline:
                elements.append(Paragraph("Case Timeline", heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                for event in timeline:
                    elements.append(Paragraph(f"• {event if isinstance(event, str) else str(event)}", body_style))
                    elements.append(Spacer(1, 0.05 * inch))
                elements.append(Spacer(1, 0.2 * inch))

            # ── legal reasoning ───────────────────────────────────────────
            legal_analysis = analysis_result.get('legal_analysis', '')
            reasoning_lines = []
            if isinstance(legal_analysis, dict):
                reasoning_lines = legal_analysis.get('reasoning', [])
            elif isinstance(legal_analysis, str) and legal_analysis.strip():
                reasoning_lines = [l.strip() for l in legal_analysis.split('\n') if l.strip()]
            elif isinstance(legal_analysis, list):
                reasoning_lines = legal_analysis
            if reasoning_lines:
                re_elements = [Paragraph("Legal Reasoning", heading_style), Spacer(1, 0.1 * inch)]
                for reason in reasoning_lines:
                    re_elements.append(Paragraph(f"\u2192 {reason if isinstance(reason, str) else str(reason)}", body_style))
                    re_elements.append(Spacer(1, 0.05 * inch))
                re_elements.append(Spacer(1, 0.2 * inch))
                elements.append(KeepTogether(re_elements))

            # ── defence strategy ──────────────────────────────────────────
            defences = analysis_result.get('defence_strategy', [])
            if defences:
                elements.append(Paragraph("Predicted Defence Strategies", heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                defence_data = [['Argument', 'Probability', 'Strength']]
                for defence in defences[:5]:
                    if not isinstance(defence, dict):
                        continue
                    defence_data.append([
                        Paragraph(defence.get('argument', 'N/A'), body_style),
                        f"{defence.get('success_probability', 0)}%",
                        Paragraph(defence.get('strength', 'N/A'), body_style)
                    ])
                defence_table = Table(defence_data, colWidths=[3.5 * inch, 1.2 * inch, 1.3 * inch])
                defence_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_C_TABLE_HDR)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(_C_LIGHT_BLUE)]),
                ]))
                elements.append(defence_table)
                elements.append(Spacer(1, 0.2 * inch))

            # ── semantic / concepts ───────────────────────────────────────
            semantic = analysis_result.get('semantic_analysis', {})
            concepts = semantic.get('concepts_detected', [])
            if concepts:
                concept_elements = [Paragraph("Legal Concepts Detected", heading_style), Spacer(1, 0.1 * inch)]
                concept_data = [['Concept', 'Confidence', 'Impact']]
                for concept in concepts[:8]:
                    if not isinstance(concept, dict):
                        continue
                    impact_raw = concept.get('legal_impact', 'N/A') or 'N/A'
                    concept_data.append([
                        Paragraph(concept.get('concept', 'N/A').replace('_', ' ').title(), body_style),
                        f"{int(concept.get('confidence', 0) * 100)}%",
                        Paragraph((impact_raw[:50] + '...') if len(impact_raw) > 50 else impact_raw, body_style)
                    ])
                concept_table = Table(concept_data, colWidths=[2 * inch, 1 * inch, 3 * inch])
                concept_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_C_TABLE_HDR)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(_C_LIGHT_BLUE)]),
                ]))
                concept_elements.append(concept_table)
                concept_elements.append(Spacer(1, 0.2 * inch))
                elements.append(KeepTogether(concept_elements))

            # ── statutory interpretation ──────────────────────────────────
            statutes = analysis_result.get('statutory_interpretation', [])
            if statutes:
                elements.append(Paragraph("Statutory Interpretation (NI Act)", heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                for s in statutes:
                    elements.append(Paragraph(f"<b>Section {s.get('section', '')}: {s.get('title', '')}</b>", subheading_style))
                    elements.append(Paragraph(f"Finding: {s.get('finding', '')}", body_style))
                    elements.append(Paragraph(f"Status: {s.get('status', '')}", body_style))
                    elements.append(Spacer(1, 0.08 * inch))
                elements.append(Spacer(1, 0.2 * inch))

            # ── precedents ────────────────────────────────────────────────
            precedents = analysis_result.get('precedents', [])
            if precedents:
                elements.append(Paragraph("Landmark Precedents", heading_style))
                elements.append(Spacer(1, 0.1 * inch))
                for p in precedents[:10]:
                    case_name = p.get('case') or p.get('case_name') or 'Landmark Case'
                    citation = p.get('citation') or (f"{p.get('case_name')} ({p.get('year')})" if p.get('year') else '')
                    principle = p.get('principle') or p.get('summary') or ''
                    elements.append(Paragraph(f"<b>{case_name}</b>", subheading_style))
                    elements.append(Paragraph(f"<i>Citation: {citation}</i>", body_style))
                    elements.append(Paragraph(f"Principle: {principle}", body_style))
                    elements.append(Spacer(1, 0.1 * inch))
                elements.append(Spacer(1, 0.2 * inch))

            # ── draft ─────────────────────────────────────────────────────
            draft_text = analysis_result.get('draft') or analysis_result.get('draft_raw') or ''
            if draft_text:
                import re
                draft_clean = re.sub(r'^\[(?:Rule-Based|AI Enhanced)\]\s*[\r\n]*', '', draft_text)
                elements.append(PageBreak())
                elements.append(Paragraph("Drafted Legal Document", heading_style))
                elements.append(Spacer(1, 0.15 * inch))
                draft_style = ParagraphStyle(
                    'DraftText',
                    parent=styles['Normal'],
                    fontName='Courier',
                    fontSize=8.5,
                    leading=11.5,
                    textColor=colors.HexColor(_C_GREY_TEXT)
                )
                elements.append(Preformatted(draft_clean, draft_style))
                elements.append(Spacer(1, 0.2 * inch))

            # ── footer ────────────────────────────────────────────────────
            elements.append(Spacer(1, 0.3 * inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            elements.append(Paragraph("\u2500" * 80, footer_style))
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph(
                "This report was generated by JUDIQ AI Legal Intelligence Platform<br/>"
                "For informational purposes only. Consult a qualified legal professional for legal advice.<br/>"
                f"Report Version: v20.2 | Engine: {analysis_result.get('engine_version', 'v20.0')}",
                footer_style
            ))

            doc.build(elements)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            logger.info(f"PDF generated successfully: {len(pdf_bytes)} bytes")
            return pdf_bytes

        except ImportError as e:
            logger.error(f"ReportLab not installed: {e}")
            raise RuntimeError(f"PDF generation requires ReportLab: {e}")
        except Exception as e:
            logger.error(f"PDF generation error: {e}", exc_info=True)
            raise RuntimeError(f"PDF generation error: {e}")

    # ──────────────────────────────────────────────────────────────────────
    # generate_draft_pdf  – formatted legal draft with cover page
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_draft_pdf(title: str, content: str, metadata: dict = None) -> bytes:
        """
        Generate a professional legal draft PDF from raw text with a dynamic Cover Page.
        """
        if metadata is None:
            metadata = {}
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (SimpleDocTemplate, Paragraph,
                                             Spacer, PageBreak, Table,
                                             TableStyle, KeepTogether,
                                             Preformatted)
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
            from reportlab.platypus.flowables import Flowable
            import re
            import hashlib

            class Bookmark(Flowable):
                def __init__(self, bm_title, level=0):
                    Flowable.__init__(self)
                    self.title = bm_title
                    self.level = level
                    self.width = 0
                    self.height = 0

                def draw(self):
                    key = self.title.replace(" ", "_")
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(self.title, key, self.level, False)

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer, pagesize=letter,
                rightMargin=1 * inch, leftMargin=1.5 * inch,
                topMargin=1 * inch, bottomMargin=1 * inch,
                title=title, author="JUDIQ Legal Drafts"
            )
            elements = []
            styles = getSampleStyleSheet()

            # ── cover styles ──────────────────────────────────────────────
            cover_supertitle_style = ParagraphStyle(
                'CoverSuper', parent=styles['Normal'],
                fontSize=28, textColor=colors.HexColor(_C_NAVY),
                alignment=TA_CENTER, fontName='Helvetica-Bold',
                spaceAfter=40, spaceBefore=100
            )
            cover_title_style = ParagraphStyle(
                'CoverTitle', parent=styles['Heading1'],
                fontSize=18, textColor=colors.HexColor(_C_DARK_TEXT),
                alignment=TA_CENTER, fontName='Helvetica',
                spaceAfter=60
            )
            cover_meta_style = ParagraphStyle(
                'CoverMeta', parent=styles['Normal'],
                fontSize=14, textColor=colors.HexColor(_C_MID_GREY),
                alignment=TA_CENTER, fontName='Courier',
                spaceAfter=15
            )

            # ── draft body styles ─────────────────────────────────────────
            title_style = ParagraphStyle(
                'DraftTitle', parent=styles['Heading1'],
                fontSize=14, textColor=colors.black,
                alignment=TA_CENTER, fontName='Helvetica-Bold',
                spaceAfter=20
            )
            body_style = ParagraphStyle(
                'DraftBody', parent=styles['Normal'],
                fontSize=12, leading=18,
                alignment=TA_JUSTIFY, fontName='Courier'
            )
            center_bold_style = ParagraphStyle(
                'CenterBold', parent=styles['Normal'],
                fontSize=12, leading=18,
                alignment=TA_CENTER, fontName='Courier-Bold',
                spaceAfter=10, spaceBefore=10
            )
            right_style = ParagraphStyle(
                'RightAlign', parent=styles['Normal'],
                fontSize=12, leading=18,
                alignment=TA_RIGHT, fontName='Courier-Bold',
                spaceBefore=20
            )
            hanging_style = ParagraphStyle(
                'HangingIndent', parent=styles['Normal'],
                fontSize=12, leading=18,
                alignment=TA_JUSTIFY, fontName='Courier',
                leftIndent=20, firstLineIndent=-20
            )

            # ── watermark / header-footer callback ────────────────────────
            def watermark_canvas(canvas, doc):
                canvas.saveState()
                if doc.page > 1:
                    canvas.setFont('Helvetica-Bold', 8)
                    canvas.setFillColorRGB(0.4, 0.4, 0.4)
                    case_ref = metadata.get('caseId', 'Unknown Case')
                    canvas.drawString(1.5 * inch, 10.6 * inch, f"Case Ref: {case_ref}")
                    canvas.drawRightString(7.5 * inch, 10.6 * inch, "CONFIDENTIAL - JUDIQ AI DOSSIER")
                    canvas.setStrokeColorRGB(0.8, 0.8, 0.8)
                    canvas.setLineWidth(0.5)
                    canvas.line(1.5 * inch, 10.55 * inch, 7.5 * inch, 10.55 * inch)
                    canvas.setFont('Helvetica', 9)
                    canvas.setFillColorRGB(0.5, 0.5, 0.5)
                    canvas.drawRightString(7.5 * inch, 0.5 * inch, f"Page {doc.page - 1} | Generated by JudiQ AI")
                    canvas.setStrokeColorRGB(0.2, 0.2, 0.2)
                    canvas.setLineWidth(1)
                    canvas.line(1.3 * inch, 0.5 * inch, 1.3 * inch, 10.5 * inch)
                    canvas.line(1.35 * inch, 0.5 * inch, 1.35 * inch, 10.5 * inch)
                    canvas.setFont('Helvetica', 12)
                    canvas.setFillColorRGB(0.5, 0.5, 0.5)
                    y_position = 10 * inch
                    line_spacing = 0.339 * inch
                    for i in range(1, 29):
                        canvas.drawCentredString(0.8 * inch, y_position, str(i))
                        y_position -= line_spacing
                canvas.restoreState()

            # ── cover page ────────────────────────────────────────────────
            elements.append(Bookmark("The Strategy Brief", 0))
            elements.append(Paragraph("JUDIQ LEGAL DRAFTS", cover_supertitle_style))
            elements.append(Paragraph(title.upper(), cover_title_style))

            case_id    = metadata.get('caseId', 'Unknown Case')
            gen_date   = datetime.now().strftime("%B %d, %Y - %H:%M:%S")
            court_name = metadata.get('courtName', 'Competent Court')
            score      = metadata.get('score', 'N/A')
            risk_level = metadata.get('riskLevel', 'Unknown')
            client_role = metadata.get('clientRole', 'Client')

            elements.append(Paragraph(f"<b>Court:</b> {court_name}", cover_meta_style))
            elements.append(Paragraph(f"<b>Case Reference:</b> {case_id}", cover_meta_style))
            elements.append(Paragraph(f"<b>Generated On:</b> {gen_date}", cover_meta_style))
            elements.append(Spacer(1, 0.5 * inch))

            # risk badge
            risk_upper = str(risk_level).upper()
            if "HIGH" in risk_upper:
                bg_color     = colors.HexColor('#fee2e2')
                border_color = colors.HexColor(_C_RED)
                text_color   = colors.HexColor(_C_RED)
            elif "MOD" in risk_upper:
                bg_color     = colors.HexColor('#fef3c7')
                border_color = colors.HexColor(_C_AMBER)
                text_color   = colors.HexColor(_C_AMBER)
            else:
                bg_color     = colors.HexColor('#dcfce7')
                border_color = colors.HexColor(_C_GREEN)
                text_color   = colors.HexColor(_C_GREEN)

            analytics_style = ParagraphStyle(
                'AnalyticsStyle', parent=styles['Normal'],
                fontSize=12, textColor=text_color,
                alignment=TA_CENTER, fontName='Helvetica-Bold',
                borderPadding=10, backColor=bg_color,
                borderColor=border_color, borderWidth=1,
                spaceAfter=20
            )
            elements.append(Paragraph(
                f"<b>AI PREDICTION METRICS</b><br/>"
                f"Score: {score}/100 | Risk Level: {risk_level}",
                analytics_style
            ))
            elements.append(Spacer(1, 0.3 * inch))

            # brief section styles
            brief_heading_style = ParagraphStyle(
                'BriefHeading', parent=styles['Normal'],
                fontSize=12, textColor=colors.HexColor(_C_NAVY),
                fontName='Helvetica-Bold', spaceAfter=10, spaceBefore=15
            )
            brief_bullet_style = ParagraphStyle(
                'BriefBullet', parent=styles['Normal'],
                fontSize=10, leading=14, textColor=colors.HexColor(_C_GREY_TEXT),
                fontName='Helvetica', leftIndent=15, spaceAfter=6
            )

            defences_brief  = metadata.get('defences', [])
            precedents_brief = metadata.get('precedents', [])
            if defences_brief:
                elements.append(Paragraph("Key Strategic Arguments", brief_heading_style))
                for d in defences_brief:
                    elements.append(Paragraph(f"• {d}", brief_bullet_style))
            if precedents_brief:
                elements.append(Paragraph("Landmark Precedents Cited", brief_heading_style))
                for p in precedents_brief:
                    elements.append(Paragraph(f"• {p}", brief_bullet_style))

            elements.append(Spacer(1, 1.5 * inch))
            doc_hash = hashlib.sha256(f"{case_id}{gen_date}{score}".encode()).hexdigest()[:24]
            hash_style = ParagraphStyle(
                'HashStyle', parent=styles['Normal'],
                fontSize=8, textColor=colors.grey,
                alignment=TA_CENTER, fontName='Courier'
            )
            elements.append(Paragraph(f"Digital Verification Hash<br/>SHA-256: {doc_hash.upper()}", hash_style))
            elements.append(Spacer(1, 0.4 * inch))
            elements.append(Paragraph("DRAFT PREVIEW", cover_meta_style))
            elements.append(PageBreak())

            # ── dossier section (optional) ─────────────────────────────────
            analysis_result = metadata.get('analysis_result', {})
            if analysis_result:
                heading_style_d = ParagraphStyle(
                    'DossierHeading', parent=styles['Heading2'],
                    fontSize=14, textColor=colors.HexColor(_C_NAVY),
                    fontName='Helvetica-Bold', spaceAfter=15, spaceBefore=20
                )
                subheading_style_d = ParagraphStyle(
                    'DossierSubheading', parent=styles['Normal'],
                    fontSize=11, textColor=colors.HexColor(_C_BLUE),
                    fontName='Helvetica-Bold', spaceAfter=8
                )
                timeline = analysis_result.get('timeline', [])
                if timeline:
                    elements.append(Bookmark("Factual Timeline", 0))
                    elements.append(Paragraph("Extracted Factual Timeline", heading_style_d))
                    for event in timeline:
                        event_text = event.get('event', '') if isinstance(event, dict) else str(event)
                        elements.append(Paragraph(f"• {event_text}", body_style))
                        elements.append(Spacer(1, 0.05 * inch))
                    elements.append(Spacer(1, 0.2 * inch))

                legal_analysis = analysis_result.get('legal_analysis', '')
                reasoning_lines = []
                if isinstance(legal_analysis, dict):
                    reasoning_lines = legal_analysis.get('reasoning', [])
                elif isinstance(legal_analysis, str) and legal_analysis.strip():
                    reasoning_lines = [l.strip() for l in legal_analysis.split('\n') if l.strip()]
                elif isinstance(legal_analysis, list):
                    reasoning_lines = legal_analysis
                if reasoning_lines:
                    re_els = [Bookmark("Legal Reasoning", 0), Paragraph("Legal Reasoning", heading_style_d), Spacer(1, 0.1 * inch)]
                    for reason in reasoning_lines:
                        re_els.append(Paragraph(f"\u2192 {reason if isinstance(reason, str) else str(reason)}", body_style))
                        re_els.append(Spacer(1, 0.05 * inch))
                    re_els.append(Spacer(1, 0.2 * inch))
                    elements.append(KeepTogether(re_els))

                defences_full = analysis_result.get('defence_strategy', [])
                if defences_full:
                    elements.append(Bookmark("Predicted Defence Strategies", 0))
                    elements.append(Paragraph("Predicted Defence Strategies", heading_style_d))
                    elements.append(Spacer(1, 0.1 * inch))
                    defence_data = [['Argument', 'Probability', 'Strength']]
                    for defence in defences_full[:5]:
                        if not isinstance(defence, dict):
                            continue
                        defence_data.append([
                            Paragraph(defence.get('argument', 'N/A'), body_style),
                            f"{defence.get('success_probability', 0)}%",
                            Paragraph(defence.get('strength', 'N/A'), body_style)
                        ])
                    if len(defence_data) > 1:
                        defence_table = Table(defence_data, colWidths=[3.5 * inch, 1.2 * inch, 1.3 * inch])
                        defence_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_C_TABLE_HDR)),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('PADDING', (0, 0), (-1, -1), 8),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(_C_LIGHT_BLUE)]),
                        ]))
                        elements.append(defence_table)
                        elements.append(Spacer(1, 0.2 * inch))

                semantic = analysis_result.get('semantic_analysis', {})
                concepts = semantic.get('concepts_detected', [])
                if concepts:
                    concept_elements = [Bookmark("Semantic Analysis", 0), Paragraph("Legal Concepts Detected", heading_style_d), Spacer(1, 0.1 * inch)]
                    concept_data = [['Concept', 'Confidence', 'Impact']]
                    for concept in concepts[:8]:
                        if not isinstance(concept, dict):
                            continue
                        impact_raw = concept.get('legal_impact', 'N/A') or 'N/A'
                        concept_data.append([
                            Paragraph(concept.get('concept', 'N/A').replace('_', ' ').title(), body_style),
                            f"{int(concept.get('confidence', 0) * 100)}%",
                            Paragraph((impact_raw[:50] + '...') if len(impact_raw) > 50 else impact_raw, body_style)
                        ])
                    if len(concept_data) > 1:
                        concept_table = Table(concept_data, colWidths=[2 * inch, 1 * inch, 3 * inch])
                        concept_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(_C_TABLE_HDR)),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 10),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('PADDING', (0, 0), (-1, -1), 8),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(_C_LIGHT_BLUE)]),
                        ]))
                        concept_elements.append(concept_table)
                        concept_elements.append(Spacer(1, 0.2 * inch))
                        elements.append(KeepTogether(concept_elements))

                statutes = analysis_result.get('statutory_interpretation', [])
                if statutes:
                    elements.append(Bookmark("Statutory Interpretation", 0))
                    elements.append(Paragraph("Statutory Interpretation", heading_style_d))
                    elements.append(Spacer(1, 0.1 * inch))
                    for s in statutes:
                        elements.append(Paragraph(f"<b>Section {s.get('section', '')}: {s.get('title', '')}</b>", subheading_style_d))
                        elements.append(Paragraph(f"Finding: {s.get('finding', '')}", body_style))
                        elements.append(Paragraph(f"Status: {s.get('status', '')}", body_style))
                        elements.append(Spacer(1, 0.08 * inch))
                    elements.append(Spacer(1, 0.2 * inch))

                elements.append(PageBreak())

            # ── draft body ────────────────────────────────────────────────
            elements.append(Bookmark("Draft Pleading", 0))
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 0.2 * inch))

            for p in content.split('\n'):
                if p.strip() == "":
                    elements.append(Spacer(1, 12))
                    continue
                safe_p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                upper_p = safe_p.upper().strip()
                if (upper_p.startswith("IN THE COURT OF") or
                        upper_p in {"VERSUS", "BETWEEN", "AND"}):
                    elements.append(Paragraph(safe_p, center_bold_style))
                elif any(kw in upper_p for kw in ("DEPONENT", "ADVOCATE", "SIGNATURE")):
                    elements.append(Paragraph(safe_p, right_style))
                elif re.match(r'^\d+\.', safe_p.strip()):
                    elements.append(Paragraph(safe_p, hanging_style))
                else:
                    elements.append(Paragraph(safe_p, body_style))
                    elements.append(Spacer(1, 6))

            elements.append(Spacer(1, 1 * inch))
            elements.append(Paragraph("___________________________", right_style))
            elements.append(Paragraph(f"ADVOCATE FOR {client_role.upper()}", right_style))
            elements.append(Spacer(1, 0.5 * inch))
            elements.append(Paragraph("___________________________", right_style))
            elements.append(Paragraph(f"{client_role.upper()}", right_style))

            doc.build(elements, onFirstPage=watermark_canvas, onLaterPages=watermark_canvas)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes

        except Exception as e:
            logger.error(f"Draft PDF generation error: {e}", exc_info=True)
            raise RuntimeError(f"Draft PDF generation error: {e}")
