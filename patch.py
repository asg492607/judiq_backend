import os

def patch_engine_core():
    with open('engine_core.py', 'r', encoding='utf-8') as f:
        text = f.read()

    target = """        # Aggregate scores (average if multiple)
        scoring_result = scoring_results[0]
        if len(scoring_results) > 1:
            avg_score = sum(float(r.get("final_score") or r.get("score") or 50) for r in scoring_results) / len(scoring_results)
            scoring_result["final_score"] = avg_score
            scoring_result["score"] = avg_score
            scoring_result["reasoning_trace"] = scoring_results[0].get("reasoning_trace", []) + ["Mixed Case Adjustments applied."] + scoring_results[1].get("reasoning_trace", [])"""

    replacement = """        # Aggregate scores (minimum if multiple, since a fatal flaw sinks the whole hybrid case)
        scoring_result = scoring_results[0]
        if len(scoring_results) > 1:
            min_score = min(float(r.get("final_score") or r.get("score") or 50) for r in scoring_results)
            scoring_result["final_score"] = min_score
            scoring_result["score"] = min_score
            
            # Combine reasoning traces with explicit engine tags
            trace_1 = [f"[Cheque Engine] {t}" for t in scoring_results[0].get("reasoning_trace", [])]
            trace_2 = [f"[Criminal Engine] {t}" for t in scoring_results[1].get("reasoning_trace", [])]
            scoring_result["reasoning_trace"] = trace_1 + ["---"] + trace_2"""

    new_text = text.replace(target, replacement)
    
    if new_text != text:
        with open('engine_core.py', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("engine_core.py patched.")
    else:
        print("engine_core.py patch failed - target not found.")

def patch_response_builder():
    with open('response_builder.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Change 1: Tone adjustment for Strengths depending on case_type
    target_strengths = """        if case_data.get("cheque_present"):   strengths.append("Prerequisite: Negotiable instrument (cheque) secured")
        if case_data.get("dishonour_memo"):   strengths.append("Prerequisite: Bank dishonour memo / return slip available")
        if case_data.get("notice_sent"):      strengths.append("Prerequisite: Statutory demand notice served (S.138b)")
        if case_data.get("debt_proven"):      strengths.append("Strength: Legally enforceable debt established via corroborative proof")"""
    
    replacement_strengths = """        is_criminal = case_data.get("case_type") == "criminal" or "criminal" in str(case_data.get("description", "")).lower()
        if is_criminal:
            if case_data.get("fir_copy"): strengths.append("Prerequisite: FIR Copy secured")
            if case_data.get("police_complaint_filed"): strengths.append("Strength: Formal police complaint initiated")
            if case_data.get("witnesses_available"): strengths.append("Strength: Corroborative witness testimony available")
            if case_data.get("debt_proven"): strengths.append("Strength: Documented evidence establishing transaction/intent")
        else:
            if case_data.get("cheque_present"):   strengths.append("Prerequisite: Negotiable instrument (cheque) secured")
            if case_data.get("dishonour_memo"):   strengths.append("Prerequisite: Bank dishonour memo / return slip available")
            if case_data.get("notice_sent"):      strengths.append("Prerequisite: Statutory demand notice served (S.138b)")
            if case_data.get("debt_proven"):      strengths.append("Strength: Legally enforceable debt established via corroborative proof")"""

    new_text = text.replace(target_strengths, replacement_strengths)

    # Change 2: Next steps / Decision string adjustments for non-cheque cases
    target_decision = """        if not case_data.get("notice_sent"):
            recommended_action = "SEND_NOTICE"
            decision_label = "Send Legal Notice First"
            decision_detail = "Statutory demand notice (S.138b) has not been sent. Mandatory pre-condition."
            next_steps = ["Draft and dispatch notice via RPAD", "Wait 15 days before filing"]
        elif score > 75 and not has_fatal:"""
    
    replacement_decision = """        if is_criminal and not case_data.get("police_complaint_filed"):
            recommended_action = "FILE_COMPLAINT"
            decision_label = "Initiate Formal Complaint"
            decision_detail = "Formal complaint/FIR has not been registered. Required to set criminal law in motion."
            next_steps = ["Draft Police Complaint", "Submit to jurisdictional police station"]
        elif not is_criminal and not case_data.get("notice_sent"):
            recommended_action = "SEND_NOTICE"
            decision_label = "Send Legal Notice First"
            decision_detail = "Statutory demand notice (S.138b) has not been sent. Mandatory pre-condition."
            next_steps = ["Draft and dispatch notice via RPAD", "Wait 15 days before filing"]
        elif score > 75 and not has_fatal:"""

    new_text = new_text.replace(target_decision, replacement_decision)
    
    if new_text != text:
        with open('response_builder.py', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("response_builder.py patched.")
    else:
        print("response_builder.py patch failed - target not found.")


def patch_pdf_generator():
    with open('pdf_generator.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Change: Wrap block loops with KeepTogether to prevent bad page breaks
    
    target_strengths = """                for strength in strengths:
                    strength_text = strength if isinstance(strength, str) else str(strength)
                    elements.append(Paragraph(f"✓ {strength_text}", body_style))
                    elements.append(Spacer(1, 0.05*inch))
                
                elements.append(Spacer(1, 0.2*inch))"""
                
    replacement_strengths = """                strength_elements = []
                for strength in strengths:
                    strength_text = strength if isinstance(strength, str) else str(strength)
                    strength_elements.append(Paragraph(f"✓ {strength_text}", body_style))
                    strength_elements.append(Spacer(1, 0.05*inch))
                
                elements.append(KeepTogether(strength_elements))
                elements.append(Spacer(1, 0.2*inch))"""
                
    target_weaknesses = """                for weakness in weaknesses:
                    weakness_text = weakness if isinstance(weakness, str) else str(weakness)
                    elements.append(Paragraph(f"⚠ {weakness_text}", body_style))
                    elements.append(Spacer(1, 0.05*inch))
                
                elements.append(Spacer(1, 0.2*inch))"""
                
    replacement_weaknesses = """                weak_elements = []
                for weakness in weaknesses:
                    weakness_text = weakness if isinstance(weakness, str) else str(weakness)
                    weak_elements.append(Paragraph(f"⚠ {weakness_text}", body_style))
                    weak_elements.append(Spacer(1, 0.05*inch))
                
                elements.append(KeepTogether(weak_elements))
                elements.append(Spacer(1, 0.2*inch))"""
                
    target_precedents = """                for p in precedents[:10]: # Top 10
                    elements.append(Paragraph(f"<b>{p.get('case', '')}</b>", subheading_style))
                    elements.append(Paragraph(f"<i>Citation: {p.get('citation', '')}</i>", body_style))
                    elements.append(Paragraph(f"Principle: {p.get('principle', '')}", body_style))
                    elements.append(Spacer(1, 0.1*inch))
                
                elements.append(Spacer(1, 0.2*inch))"""
                
    replacement_precedents = """                for p in precedents[:10]: # Top 10
                    prec_elements = []
                    prec_elements.append(Paragraph(f"<b>{p.get('case', '')}</b>", subheading_style))
                    prec_elements.append(Paragraph(f"<i>Citation: {p.get('citation', '')}</i>", body_style))
                    prec_elements.append(Paragraph(f"Principle: {p.get('principle', '')}", body_style))
                    prec_elements.append(Spacer(1, 0.1*inch))
                    elements.append(KeepTogether(prec_elements))
                
                elements.append(Spacer(1, 0.2*inch))"""

    target_concept_table = """                concept_elements.append(concept_table)
                concept_elements.append(Spacer(1, 0.2*inch))
                elements.append(KeepTogether(concept_elements))"""
                
    replacement_concept_table = """                concept_elements.append(concept_table)
                concept_elements.append(Spacer(1, 0.2*inch))
                # Add PageBreak if table is likely too big, else KeepTogether
                elements.append(KeepTogether(concept_elements))"""
                
    new_text = text.replace(target_strengths, replacement_strengths)
    new_text = new_text.replace(target_weaknesses, replacement_weaknesses)
    new_text = new_text.replace(target_precedents, replacement_precedents)
    new_text = new_text.replace(target_concept_table, replacement_concept_table)
    
    # Also adjust ParagraphStyles for table cells to allow wrapping
    target_body_style = """            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT
            )"""
    
    replacement_body_style = """            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                alignment=TA_LEFT,
                wordWrap='CJK'
            )"""
            
    new_text = new_text.replace(target_body_style, replacement_body_style)
    
    if new_text != text:
        with open('pdf_generator.py', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("pdf_generator.py patched.")
    else:
        print("pdf_generator.py patch failed - target not found.")

if __name__ == "__main__":
    patch_engine_core()
    patch_response_builder()
    patch_pdf_generator()
