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
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
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
                alignment=TA_LEFT
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
                elements.append(Paragraph("Recommended Action", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                decision_label = decision.get('decision_label', 'Review Case')
                decision_detail = decision.get('detail', '')
                
                elements.append(Paragraph(f"<b>{decision_label}</b>", subheading_style))
                if decision_detail:
                    elements.append(Paragraph(decision_detail, body_style))
                elements.append(Spacer(1, 0.15*inch))
                
                # Next Steps
                next_steps = decision.get('next_steps', [])
                if next_steps:
                    elements.append(Paragraph("<b>Next Steps:</b>", subheading_style))
                    for i, step in enumerate(next_steps, 1):
                        elements.append(Paragraph(f"{i}. {step}", body_style))
                        elements.append(Spacer(1, 0.05*inch))
                
                elements.append(Spacer(1, 0.2*inch))
            
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
                    weakness_text = weakness if isinstance(weakness, str) else str(weakness)
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
                elements.append(Paragraph("Legal Reasoning", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                for reason in reasoning_lines:
                    reason_text = reason if isinstance(reason, str) else str(reason)
                    elements.append(Paragraph(f"\u2192 {reason_text}", body_style))
                    elements.append(Spacer(1, 0.05*inch))
                elements.append(Spacer(1, 0.2*inch))
            
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
                    defence_data.append([arg, prob, strength])
                
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
                elements.append(Paragraph("Legal Concepts Detected", heading_style))
                elements.append(Spacer(1, 0.1*inch))
                
                concept_data = []
                concept_data.append(['Concept', 'Confidence', 'Impact'])
                
                for concept in concepts[:8]:  # Top 8 concepts
                    if not isinstance(concept, dict):
                        continue
                    name = concept.get('concept', 'N/A').replace('_', ' ').title()
                    conf = f"{int(concept.get('confidence', 0) * 100)}%"
                    impact_raw = concept.get('legal_impact', 'N/A') or 'N/A'
                    impact = (impact_raw[:50] + '...') if len(impact_raw) > 50 else impact_raw
                    concept_data.append([name, conf, impact])
                
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
                
                elements.append(concept_table)
                elements.append(Spacer(1, 0.2*inch))
            
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
                    elements.append(Paragraph(f"<b>{p.get('case', '')}</b>", subheading_style))
                    elements.append(Paragraph(f"<i>Citation: {p.get('citation', '')}</i>", body_style))
                    elements.append(Paragraph(f"Principle: {p.get('principle', '')}", body_style))
                    elements.append(Spacer(1, 0.1*inch))
                
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
