import os
import logging
from datetime import datetime
from io import BytesIO
from typing import Dict, Any
logger = logging.getLogger(__name__)
class PDFGenerator:
    @staticmethod
    def generate_report(analysis_result: Dict[str, Any]) -> bytes:
        """
        Generate comprehensive PDF report with all analysis details
        Ensures proper PDF format with correct MIME type
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Preformatted
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            
            buffer = BytesIO()
            
            # Create PDF with proper metadata
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=letter,
                rightMargin=0.75*inch, 
                leftMargin=0.75*inch,
                topMargin=0.75*inch, 
                bottomMargin=0.75*inch,
                title="JUDIQ Legal Analysis Report",
                author="JUDIQ AI Legal Intelligence"
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Enhanced custom styles
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a2e'),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=16,
                fontName='Helvetica-Bold',
                backColor=colors.HexColor('#ecf0f1'),
                borderPadding=8
            )
            
            subheading_style = ParagraphStyle(
                'SubHeading',
                parent=styles['Heading3'],
                fontSize=13,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=8,
                spaceBefore=10,
                fontName='Helvetica-Bold'
            )
            
            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT, wordWrap='CJK'
            )
            
            # ===== TITLE =====
            elements.append(Paragraph("JUDIQ AI - Legal Case Intelligence Report", title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # ===== EXECUTIVE SUMMARY =====
            score = analysis_result.get('score', 0)
            verdict = analysis_result.get('verdict', 'Unknown')
            risk_level = analysis_result.get('risk_level', 'Unknown')
            
            # Determine score color
            if score >= 70:
                score_color = colors.HexColor('#27ae60')
            elif score >= 40:
                score_color = colors.HexColor('#f39c12')
            else:
                score_color = colors.HexColor('#e74c3c')
            
            summary_data = [
                ['Case Score:', f"{score}/100"],
                ['Verdict:', verdict],
                ['Risk Level:', risk_level],
                ['Generated:', datetime.now().strftime('%d %B %Y, %H:%M:%S')]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 4.5*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                ('BACKGROUND', (1, 0), (1, 0), score_color),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('PADDING', (0, 0), (-1, -1), 12),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # ===== DECISION & NEXT STEPS =====
            decision = analysis_result.get('decision', {})
            if decision:
                decision_block = [Paragraph("Recommended Action", heading_style), Spacer(1, 0.1*inch)]

                decision_label = decision.get('decision_label', 'Review Case')
                decision_detail = decision.get('detail', '')

                decision_block.append(Paragraph(f"<b>{decision_label}</b>", subheading_style))
                if decision_detail:
                    decision_block.append(Paragraph(decision_detail, body_style))
                decision_block.append(Spacer(1, 0.15*inch))

                next_steps = decision.get('next_steps', [])
                if next_steps:
                    decision_block.append(Paragraph("<b>Next Steps:</b>", subheading_style))
                    for i, step in enumerate(next_steps, 1):
                        decision_block.append(Paragraph(f"{i}. {step}", body_style))
                        decision_block.append(Spacer(1, 0.05*inch))

                decision_block.append(Spacer(1, 0.2*inch))
                elements.append(KeepTogether(decision_block))
            
            # ===== STRENGTHS =====
            strengths = analysis_result.get('strengths', [])
            if strengths:
                elements.append(Paragraph("Case Strengths", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for strength in strengths:
                    strength_text = strength if isinstance(strength, str) else str(strength)
                    elements.append(Paragraph(f"✓ {strength_text}", body_style))
                    elements.append(Spacer(1, 0.05*inch))
                
                elements.append(Spacer(1, 0.2*inch))
            
            # ===== WEAKNESSES =====
            weaknesses = analysis_result.get('weaknesses', [])
            if weaknesses:
                elements.append(Paragraph("Identified Weaknesses", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for weakness in weaknesses:
                    if isinstance(weakness, dict):
                        risk = weakness.get('risk') or weakness.get('title') or weakness.get('text') or 'Unknown Risk'
                        severity = weakness.get('severity') or 'Unknown'
                        detail = weakness.get('detail') or weakness.get('description') or ''
                        color = "#ef4444" if severity == "FATAL" else ("#f59e0b" if severity in ["CRITICAL", "HIGH"] else "#9ca3af")
                        weakness_text = f"<b>{risk}</b> [<font color='{color}'><b>{severity}</b></font>]: {detail}"
                    else:
                        weakness_text = str(weakness)
                    elements.append(Paragraph(f"⚠ {weakness_text}", body_style))
                    elements.append(Spacer(1, 0.05*inch))
                
                elements.append(Spacer(1, 0.2*inch))
            
            # ===== TIMELINE =====
            timeline = analysis_result.get('timeline', [])
            if timeline:
                elements.append(Paragraph("Case Timeline", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for event in timeline:
                    event_text = event if isinstance(event, str) else str(event)
                    elements.append(Paragraph(f"• {event_text}", body_style))
                    elements.append(Spacer(1, 0.05*inch))
                
                elements.append(Spacer(1, 0.2*inch))
            
            # ===== LEGAL ANALYSIS =====
            # legal_analysis may be a str (joined text) or a dict — handle both
            legal_analysis = analysis_result.get('legal_analysis', '')
            reasoning_lines = []
            if isinstance(legal_analysis, dict):
                reasoning_lines = legal_analysis.get('reasoning', [])
            elif isinstance(legal_analysis, str) and legal_analysis.strip():
                # Split the joined string back into individual lines
                reasoning_lines = [l.strip() for l in legal_analysis.split('\n') if l.strip()]
            elif isinstance(legal_analysis, list):
                reasoning_lines = legal_analysis

            if reasoning_lines:
                reasoning_elements = []
                reasoning_elements.append(Paragraph("Legal Reasoning", heading_style))
                reasoning_elements.append(Spacer(1, 0.1*inch))
                for reason in reasoning_lines:
                    reason_text = reason if isinstance(reason, str) else str(reason)
                    reasoning_elements.append(Paragraph(f"\u2192 {reason_text}", body_style))
                    reasoning_elements.append(Spacer(1, 0.05*inch))
                reasoning_elements.append(Spacer(1, 0.2*inch))
                elements.append(KeepTogether(reasoning_elements))
            
            # ===== DEFENCE STRATEGIES =====
            defences = analysis_result.get('defence_strategy', [])
            if defences:
                elements.append(Paragraph("Predicted Defence Strategies", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                defence_data = []
                defence_data.append(['Argument', 'Probability', 'Strength'])
                
                for defence in defences[:5]:  # Top 5 defences
                    if not isinstance(defence, dict):
                        continue
                    arg = defence.get('argument', 'N/A')
                    prob = f"{defence.get('success_probability', 0)}%"
                    strength = defence.get('strength', 'N/A')
                    defence_data.append([Paragraph(arg, body_style), prob, Paragraph(strength, body_style)])
                
                defence_table = Table(defence_data, colWidths=[3.5*inch, 1.2*inch, 1.3*inch])
                defence_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
                ]))
                
                elements.append(defence_table)
                elements.append(Spacer(1, 0.2*inch))
            
            # ===== SEMANTIC CONCEPTS =====
            semantic = analysis_result.get('semantic_analysis', {})
            concepts = semantic.get('concepts_detected', [])
            if concepts:
                concept_elements = []
                concept_elements.append(Paragraph("Legal Concepts Detected", heading_style))
                concept_elements.append(Spacer(1, 0.1*inch))
                
                concept_data = []
                concept_data.append(['Concept', 'Confidence', 'Impact'])
                
                for concept in concepts[:8]:  # Top 8 concepts
                    if not isinstance(concept, dict):
                        continue
                    name = concept.get('concept', 'N/A').replace('_', ' ').title()
                    conf = f"{int(concept.get('confidence', 0) * 100)}%"
                    impact_raw = concept.get('legal_impact', 'N/A') or 'N/A'
                    impact = (impact_raw[:50] + '...') if len(impact_raw) > 50 else impact_raw
                    concept_data.append([Paragraph(name, body_style), conf, Paragraph(impact, body_style)])
                
                concept_table = Table(concept_data, colWidths=[2*inch, 1*inch, 3*inch])
                concept_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
                ]))
                
                concept_elements.append(concept_table)
                concept_elements.append(Spacer(1, 0.2*inch))
                elements.append(KeepTogether(concept_elements))
            
            # ===== STATUTORY INTERPRETATION (NEW) =====
            statutes = analysis_result.get('statutory_interpretation', [])
            if statutes:
                elements.append(Paragraph("Statutory Interpretation (NI Act)", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for s in statutes:
                    elements.append(Paragraph(f"<b>Section {s.get('section', '')}: {s.get('title', '')}</b>", subheading_style))
                    elements.append(Paragraph(f"Finding: {s.get('finding', '')}", body_style))
                    elements.append(Paragraph(f"Status: {s.get('status', '')}", body_style))
                    elements.append(Spacer(1, 0.08*inch))
                
                elements.append(Spacer(1, 0.2*inch))

            # ===== LANDMARK PRECEDENTS (NEW) =====
            precedents = analysis_result.get('precedents', [])
            if precedents:
                elements.append(Paragraph("Landmark Precedents", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for p in precedents[:10]: # Top 10
                    case_name = p.get('case') or p.get('case_name') or 'Landmark Case'
                    citation = p.get('citation') or (f"{p.get('case_name')} ({p.get('year')})" if p.get('year') else '')
                    principle = p.get('principle') or p.get('summary') or ''
                    elements.append(Paragraph(f"<b>{case_name}</b>", subheading_style))
                    elements.append(Paragraph(f"<i>Citation: {citation}</i>", body_style))
                    elements.append(Paragraph(f"Principle: {principle}", body_style))
                    elements.append(Spacer(1, 0.1*inch))
                
                elements.append(Spacer(1, 0.2*inch))

            # ===== DRAFTED DOCUMENT (NEW) =====
            draft_text = analysis_result.get('draft') or analysis_result.get('draft_raw') or ''
            if draft_text:
                import re
                draft_clean = re.sub(r'^\[(?:Rule-Based|AI Enhanced)\]\s*[\r\n]*', '', draft_text)
                
                elements.append(PageBreak())
                elements.append(Paragraph("Drafted Legal Document", heading_style))
                elements.append(Spacer(1, 0.15*inch))
                
                draft_style = ParagraphStyle(
                    'DraftText',
                    parent=styles['Normal'],
                    fontName='Courier',
                    fontSize=8.5,
                    leading=11.5,
                    textColor=colors.HexColor('#1e293b')
                )
                elements.append(Preformatted(draft_clean, draft_style))
                elements.append(Spacer(1, 0.2*inch))

            # ===== FOOTER =====
            elements.append(Spacer(1, 0.3*inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            
            elements.append(Paragraph("─" * 80, footer_style))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(
                "This report was generated by JUDIQ AI Legal Intelligence Platform<br/>"
                "For informational purposes only. Consult a qualified legal professional for legal advice.<br/>"
                f"Report Version: v20.2 | Engine: {analysis_result.get('engine_version', 'v20.0')}",
                footer_style
            ))
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF bytes
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

    @staticmethod
    def generate_draft_pdf(title: str, content: str) -> bytes:
        """
        Generate a professional legal draft PDF from raw text.
        Applies monospaced/legal formatting for court submissions.
        """
                    elements.append(Paragraph(f"• {event_text}", body_style))
                    elements.append(Spacer(1, 0.05*inch))
                
                elements.append(Spacer(1, 0.2*inch))
            
            # ===== LEGAL ANALYSIS =====
            # legal_analysis may be a str (joined text) or a dict — handle both
            legal_analysis = analysis_result.get('legal_analysis', '')
            reasoning_lines = []
            if isinstance(legal_analysis, dict):
                reasoning_lines = legal_analysis.get('reasoning', [])
            elif isinstance(legal_analysis, str) and legal_analysis.strip():
                # Split the joined string back into individual lines
                reasoning_lines = [l.strip() for l in legal_analysis.split('\n') if l.strip()]
            elif isinstance(legal_analysis, list):
                reasoning_lines = legal_analysis

            if reasoning_lines:
                reasoning_elements = []
                reasoning_elements.append(Paragraph("Legal Reasoning", heading_style))
                reasoning_elements.append(Spacer(1, 0.1*inch))
                for reason in reasoning_lines:
                    reason_text = reason if isinstance(reason, str) else str(reason)
                    reasoning_elements.append(Paragraph(f"\u2192 {reason_text}", body_style))
                    reasoning_elements.append(Spacer(1, 0.05*inch))
                reasoning_elements.append(Spacer(1, 0.2*inch))
                elements.append(KeepTogether(reasoning_elements))
            
            # ===== DEFENCE STRATEGIES =====
            defences = analysis_result.get('defence_strategy', [])
            if defences:
                elements.append(Paragraph("Predicted Defence Strategies", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                defence_data = []
                defence_data.append(['Argument', 'Probability', 'Strength'])
                
                for defence in defences[:5]:  # Top 5 defences
                    if not isinstance(defence, dict):
                        continue
                    arg = defence.get('argument', 'N/A')
                    prob = f"{defence.get('success_probability', 0)}%"
                    strength = defence.get('strength', 'N/A')
                    defence_data.append([Paragraph(arg, body_style), prob, Paragraph(strength, body_style)])
                
                defence_table = Table(defence_data, colWidths=[3.5*inch, 1.2*inch, 1.3*inch])
                defence_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
                ]))
                
                elements.append(defence_table)
                elements.append(Spacer(1, 0.2*inch))
            
            # ===== SEMANTIC CONCEPTS =====
            semantic = analysis_result.get('semantic_analysis', {})
            concepts = semantic.get('concepts_detected', [])
            if concepts:
                concept_elements = []
                concept_elements.append(Paragraph("Legal Concepts Detected", heading_style))
                concept_elements.append(Spacer(1, 0.1*inch))
                
                concept_data = []
                concept_data.append(['Concept', 'Confidence', 'Impact'])
                
                for concept in concepts[:8]:  # Top 8 concepts
                    if not isinstance(concept, dict):
                        continue
                    name = concept.get('concept', 'N/A').replace('_', ' ').title()
                    conf = f"{int(concept.get('confidence', 0) * 100)}%"
                    impact_raw = concept.get('legal_impact', 'N/A') or 'N/A'
                    impact = (impact_raw[:50] + '...') if len(impact_raw) > 50 else impact_raw
                    concept_data.append([Paragraph(name, body_style), conf, Paragraph(impact, body_style)])
                
                concept_table = Table(concept_data, colWidths=[2*inch, 1*inch, 3*inch])
                concept_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
                ]))
                
                concept_elements.append(concept_table)
                concept_elements.append(Spacer(1, 0.2*inch))
                elements.append(KeepTogether(concept_elements))
            
            # ===== STATUTORY INTERPRETATION (NEW) =====
            statutes = analysis_result.get('statutory_interpretation', [])
            if statutes:
                elements.append(Paragraph("Statutory Interpretation (NI Act)", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for s in statutes:
                    elements.append(Paragraph(f"<b>Section {s.get('section', '')}: {s.get('title', '')}</b>", subheading_style))
                    elements.append(Paragraph(f"Finding: {s.get('finding', '')}", body_style))
                    elements.append(Paragraph(f"Status: {s.get('status', '')}", body_style))
                    elements.append(Spacer(1, 0.08*inch))
                
                elements.append(Spacer(1, 0.2*inch))

            # ===== LANDMARK PRECEDENTS (NEW) =====
            precedents = analysis_result.get('precedents', [])
            if precedents:
                elements.append(Paragraph("Landmark Precedents", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                for p in precedents[:10]: # Top 10
                    case_name = p.get('case') or p.get('case_name') or 'Landmark Case'
                    citation = p.get('citation') or (f"{p.get('case_name')} ({p.get('year')})" if p.get('year') else '')
                    principle = p.get('principle') or p.get('summary') or ''
                    elements.append(Paragraph(f"<b>{case_name}</b>", subheading_style))
                    elements.append(Paragraph(f"<i>Citation: {citation}</i>", body_style))
                    elements.append(Paragraph(f"Principle: {principle}", body_style))
                    elements.append(Spacer(1, 0.1*inch))
                
                elements.append(Spacer(1, 0.2*inch))

            # ===== DRAFTED DOCUMENT (NEW) =====
            draft_text = analysis_result.get('draft') or analysis_result.get('draft_raw') or ''
            if draft_text:
                import re
                draft_clean = re.sub(r'^\[(?:Rule-Based|AI Enhanced)\]\s*[\r\n]*', '', draft_text)
                
                elements.append(PageBreak())
                elements.append(Paragraph("Drafted Legal Document", heading_style))
                elements.append(Spacer(1, 0.15*inch))
                
                draft_style = ParagraphStyle(
                    'DraftText',
                    parent=styles['Normal'],
                    fontName='Courier',
                    fontSize=8.5,
                    leading=11.5,
                    textColor=colors.HexColor('#1e293b')
                )
                elements.append(Preformatted(draft_clean, draft_style))
                elements.append(Spacer(1, 0.2*inch))

            # ===== FOOTER =====
            elements.append(Spacer(1, 0.3*inch))
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            
            elements.append(Paragraph("─" * 80, footer_style))
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(
                "This report was generated by JUDIQ AI Legal Intelligence Platform<br/>"
                "For informational purposes only. Consult a qualified legal professional for legal advice.<br/>"
                f"Report Version: v20.2 | Engine: {analysis_result.get('engine_version', 'v20.0')}",
                footer_style
            ))
            
            # Build PDF
            doc.build(elements)
            
            # Get PDF bytes
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
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT
            from io import BytesIO
            import re
            from datetime import datetime

            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer, pagesize=letter,
                rightMargin=1*inch, leftMargin=1.5*inch,
                topMargin=1*inch, bottomMargin=1*inch,
                title=title, author="JUDIQ Legal Drafts"
            )

            elements = []
            styles = getSampleStyleSheet()

            # --- Cover Page Styles ---
            cover_supertitle_style = ParagraphStyle(
                'CoverSuper', parent=styles['Normal'],
                fontSize=28, textColor=colors.HexColor('#1a202c'),
                alignment=TA_CENTER, fontName='Helvetica-Bold',
                spaceAfter=40, spaceBefore=100
            )
            cover_title_style = ParagraphStyle(
                'CoverTitle', parent=styles['Heading1'],
                fontSize=18, textColor=colors.HexColor('#2d3748'),
                alignment=TA_CENTER, fontName='Helvetica',
                spaceAfter=60
            )
            cover_meta_style = ParagraphStyle(
                'CoverMeta', parent=styles['Normal'],
                fontSize=14, textColor=colors.HexColor('#4a5568'),
                alignment=TA_CENTER, fontName='Courier',
                spaceAfter=15
            )

            # --- Draft Body Styles ---
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

            # Pleading Paper Canvas
            def watermark_canvas(canvas, doc):
                canvas.saveState()
                # Page number footer (skip on cover page)
                if doc.page > 1:
                    canvas.setFont('Helvetica', 9)
                    canvas.setFillColorRGB(0.5, 0.5, 0.5)
                    canvas.drawRightString(7.5 * inch, 0.5 * inch, f"Page {doc.page - 1} | Generated by JudiQ AI")
                    
                    # Pleading Layout: Vertical Lines
                    canvas.setStrokeColorRGB(0.2, 0.2, 0.2)
                    canvas.setLineWidth(1)
                    # Draw double vertical lines separating numbers from text
                    canvas.line(1.3 * inch, 0.5 * inch, 1.3 * inch, 10.5 * inch)
                    canvas.line(1.35 * inch, 0.5 * inch, 1.35 * inch, 10.5 * inch)
                    
                    # Pleading Layout: Line Numbers 1-28
                    canvas.setFont('Helvetica', 12)
                    canvas.setFillColorRGB(0.5, 0.5, 0.5)
                    # 28 lines typical for 11 inch letter size paper with 1 inch margins and 18 leading
                    # We start drawing from top (10.5 inch down to 1 inch)
                    y_position = 10 * inch
                    line_spacing = 0.339 * inch # Approximate spacing for 28 lines
                    for i in range(1, 29):
                        # Center the number around 0.8 inches from the left edge
                        canvas.drawCentredString(0.8 * inch, y_position, str(i))
                        y_position -= line_spacing
                canvas.restoreState()

            # ===== 1. COVER PAGE =====
            elements.append(Paragraph("JUDIQ LEGAL DRAFTS", cover_supertitle_style))
            elements.append(Paragraph(title.upper(), cover_title_style))
            
            case_id = metadata.get('caseId', 'Unknown Case')
            gen_date = datetime.now().strftime("%B %d, %Y - %H:%M:%S")
            court_name = metadata.get('courtName', 'Competent Court')
            score = metadata.get('score', 'N/A')
            risk_level = metadata.get('riskLevel', 'Unknown')
            client_role = metadata.get('clientRole', 'Client')
            
            elements.append(Paragraph(f"<b>Court:</b> {court_name}", cover_meta_style))
            elements.append(Paragraph(f"<b>Case Reference:</b> {case_id}", cover_meta_style))
            elements.append(Paragraph(f"<b>Generated On:</b> {gen_date}", cover_meta_style))
            elements.append(Spacer(1, 0.5*inch))
            
            # --- Analytics Box ---
            analytics_style = ParagraphStyle(
                'AnalyticsStyle', parent=styles['Normal'],
                fontSize=12, textColor=colors.HexColor('#2c3e50'),
                alignment=TA_CENTER, fontName='Helvetica-Bold',
                borderPadding=10, backColor=colors.HexColor('#f1f5f9'),
                borderColor=colors.HexColor('#cbd5e1'), borderWidth=1,
                spaceAfter=20
            )
            
            elements.append(Paragraph(
                f"<b>AI PREDICTION METRICS</b><br/>"
                f"Score: {score}/100 | Risk Level: {risk_level}", 
                analytics_style
            ))
            
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph("DRAFT PREVIEW", cover_meta_style))
            
            elements.append(PageBreak())

            # ===== 2. DOCUMENT BODY =====
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 0.2*inch))

            # Smart Typography Heuristics
            paragraphs = content.split('\n')
            for p in paragraphs:
                if p.strip() == "":
                    elements.append(Spacer(1, 12))
                    continue

                safe_p = p.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                upper_p = safe_p.upper().strip()

                # Detect Court Headings
                if upper_p.startswith("IN THE COURT OF") or upper_p == "VERSUS" or upper_p == "BETWEEN" or upper_p == "AND":
                    elements.append(Paragraph(safe_p, center_bold_style))
                # Detect Sign-offs
                elif "DEPONENT" in upper_p or "ADVOCATE" in upper_p or "SIGNATURE" in upper_p:
                    elements.append(Paragraph(safe_p, right_style))
                # Detect Numbered Paragraphs
                elif re.match(r'^\d+\.', safe_p.strip()):
                    elements.append(Paragraph(safe_p, hanging_style))
                else:
                    elements.append(Paragraph(safe_p, body_style))
                    elements.append(Spacer(1, 6))

            # ===== 3. AUTOMATED SIGNATURE BLOCK =====
            elements.append(Spacer(1, 1*inch))
            elements.append(Paragraph("___________________________", right_style))
            elements.append(Paragraph(f"ADVOCATE FOR {client_role.upper()}", right_style))
            elements.append(Spacer(1, 0.5*inch))
            elements.append(Paragraph("___________________________", right_style))
            elements.append(Paragraph(f"{client_role.upper()}", right_style))

            doc.build(elements, onFirstPage=watermark_canvas, onLaterPages=watermark_canvas)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return pdf_bytes

        except Exception as e:
            logger.error(f"Draft PDF generation error: {e}", exc_info=True)
            raise RuntimeError(f"Draft PDF generation error: {e}")
