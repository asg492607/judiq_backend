import re

file_path = 'c:\\Users\\Atharva\\OneDrive\\Desktop\\Level_0judiq\\backend\\draft_engine.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace debt pleading in generate_complaint
old_debt_pleading = '''    # ── EVIDENCE PLEADINGS (Advocate Hardening) ──────────────────────────
    if is_aggressive:
        debt_pleading = f"""The Complainant submits that the Accused is bound by an incontrovertible liability of {amount_str}, arising out of {transaction_nature}. 
    This liability is securely established by contemporaneous commercial records. The issuance of the subject cheque by the Accused was an explicit acknowledgment of this debt. Its subsequent dishonour is a clear demonstration of the Accused's mala fide intent to evade lawful obligations, compelling the Complainant to invoke the strict provisions of Section 138 of the NI Act."""
    else:
        debt_pleading = f"The Complainant states that the Accused is indebted to the Complainant for a sum of {amount_str} arising from {transaction_nature}. The said debt is legally enforceable and constitutes a valid liability under law."'''

new_debt_pleading = '''    # ── EVIDENCE PLEADINGS (Advocate Hardening & Dynamic Variation) ──────────────────────────
    import random
    variation = random.choice(["standard", "formal", "emphatic"])
    
    if is_aggressive:
        if variation == "formal":
            debt_pleading = f"""It is unequivocally submitted that the Accused is bound by a crystallised and incontrovertible liability of {amount_str}, which directly emanates from {transaction_nature}. 
    This liability is cemented by contemporaneous records. The tendering of the subject cheque by the Accused operates as an absolute acknowledgment of this debt. The subsequent dishonour of the instrument is a manifestation of the Accused's mala fide design to defraud the Complainant, necessitating the invocation of the penal provisions of Section 138 of the NI Act."""
        else:
            debt_pleading = f"""The Complainant submits that the Accused is bound by an incontrovertible liability of {amount_str}, arising out of {transaction_nature}. 
    This liability is securely established by contemporaneous commercial records. The issuance of the subject cheque by the Accused was an explicit acknowledgment of this debt. Its subsequent dishonour is a clear demonstration of the Accused's mala fide intent to evade lawful obligations, compelling the Complainant to invoke the strict provisions of Section 138 of the NI Act."""
    else:
        if variation == "emphatic":
            debt_pleading = f"The Complainant respectfully avers that the Accused is indebted for the precise sum of {amount_str} strictly on account of {transaction_nature}. This constitutes a legally enforceable debt recognized under the law."
        else:
            debt_pleading = f"The Complainant states that the Accused is indebted to the Complainant for a sum of {amount_str} arising from {transaction_nature}. The said debt is legally enforceable and constitutes a valid liability under law."'''

content = content.replace(old_debt_pleading, new_debt_pleading)

# Replace defence strategy dynamic injection
old_defence_logic = '''    defences_text = "\\n".join([f"   {i+1}. {d}" for i, d in enumerate(defences_identified)]) if defences_identified else "   (To be determined based on full case facts)"
    arguments_text = "\\n\\n".join([f"   {i+1}. {a}" for i, a in enumerate(legal_arguments)]) if legal_arguments else "   (Legal arguments to be elaborated based on specific case documents)"'''

new_defence_logic = '''    # Inject synthesis for complex cases (multiple defences)
    if len(defences_identified) > 1:
        synthesis = "COMPOSITE DEFENCE STRATEGY:\\nThe Accused has a multi-tiered defence. We will primarily challenge the existence of the legally enforceable debt, whilst simultaneously disputing the mechanics of the cheque's execution. This dual-pronged attack forces the Complainant to prove both the financial transaction and the instrument's integrity beyond reasonable doubt."
        defences_identified.insert(0, synthesis)

    defences_text = "\\n".join([f"   {i+1}. {d}" if not str(d).startswith("COMPOSITE") else f"   {d}" for i, d in enumerate(defences_identified)]) if defences_identified else "   (To be determined based on full case facts)"
    arguments_text = "\\n\\n".join([f"   {i+1}. {a}" for i, a in enumerate(legal_arguments)]) if legal_arguments else "   (Legal arguments to be elaborated based on specific case documents)"'''

content = content.replace(old_defence_logic, new_defence_logic)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
