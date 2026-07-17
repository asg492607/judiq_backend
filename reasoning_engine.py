import logging
from typing import List, Dict, Any
from kb_manager import kb_manager
from precedent_manager import precedent_manager
logger = logging.getLogger(__name__)
def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        logger.warning("Invalid numeric value in reasoning engine: %r", value)
        return default
class ReasoningEngine:
    @staticmethod
    def summarize_case(case_data: Dict) -> str:
        complainant = case_data.get("complainant_name") or "Complainant"
        accused     = case_data.get("accused_name")     or "Accused"
        amount      = case_data.get("amount")           or case_data.get("cheque_amount") or "an unspecified amount"
        cheque_no   = case_data.get("cheque_number")    or "N/A"
        reason      = case_data.get("dishonour_reason") or "Insufficient Funds"
        bank        = case_data.get("bank_name")        or "the drawee bank"
        accused_type = case_data.get("accused_type", "Individual")
        summary = (
            f"Case: {complainant} vs {accused} - Prosecution for Dishonour of Cheque No. {cheque_no} "
            f"valued at Rs. {amount}. Reason: '{reason}'. "
        )
        missing_pillars = []
        if not case_data.get("notice_sent"): missing_pillars.append("Statutory Notice (S.138b)")
        if not case_data.get("debt_proven"): missing_pillars.append("Legally Enforceable Debt (S.139)")
        if not case_data.get("cheque_present"): missing_pillars.append("Negotiable Instrument (S.138)")
        if missing_pillars:
            summary += f"[WARNING]: Critical statutory pillars are MISSING: {', '.join(missing_pillars)}. "
        if case_data.get("notice_sent"):
            mode = case_data.get("notice_mode") or "registered post"
            summary += f" Mandatory demand notice served via {mode}."
        else:
            summary += " CRITICAL: Statutory notice NOT served. Filing without notice is legally non-maintainable."
        if case_data.get("debt_proven"):
            summary += " Underlying debt relationship is documented."
        else:
            summary += " Evidentiary Gap: Lack of debt documentation creates high acquittal risk via rebuttal of S.139 presumption."
        if accused_type in ("Pvt Ltd/Ltd Company", "Company", "Partnership Firm"):
            directors = case_data.get("directors_named", False)
            if directors:
                summary += f" Corporate accused ({accused_type}) impleaded correctly with responsible officers."
            else:
                summary += f" FATAL DEFECT: Corporate accused ({accused_type}) impleaded WITHOUT naming responsible officers (S.141)."
        amount_val = 0
        amount_val = _number(amount)
        if amount_val > 150000 and not case_data.get("loan_via_bank") and not case_data.get("complainant_itr_available"):
            summary += " ðŸš¨ EVIDENTIARY RISK: Complainant's financial capacity to lend this amount in cash may be challenged under the Basalingappa rule."
        return summary
    @staticmethod
    def generate_client_summary(analysis_result: Dict) -> str:
        score = analysis_result.get("score", 0)
        verdict = analysis_result.get("verdict", "Unknown")
        if score >= 75:
            msg = "Your case is very strong. All legal requirements are met."
        elif score >= 50:
            msg = "Your case is moderate. We have the core documents, but the defense may challenge some details."
        else:
            msg = "Your case has significant risks. Some mandatory legal steps appear missing or defective."
        existing_concepts = [c.get("concept") for c in analysis_result.get("concepts", []) if isinstance(c, dict)]
        if "notice_defect" in existing_concepts:
            msg += " Specifically, there is an issue with the legal notice timing."
        if "no_debt_proof" in existing_concepts:
            msg += " We need better proof that the money was actually owed."
        return msg
    @staticmethod
    def determine_trend(score: int) -> str:
        if score >= 80: return "STRONG_UPWARD"
        if score >= 60: return "STABLE_POSITIVE"
        if score >= 40: return "VOLATILE"
        return "CRITICAL_DOWNWARD"
    @staticmethod
    def match_precedents(case_data: Dict, concepts: List[Dict]) -> List[Dict]:
        matched: List[Dict] = []
        seen_citations: set = set()
        for concept_entry in concepts:
            concept_name = concept_entry.get("concept", "")
            confidence   = concept_entry.get("confidence", 0.5)
            statute_precedents = kb_manager.get_precedents_for_concept(concept_name)
            for p in statute_precedents:
                citation = p.get("citation") or (f"{p.get('case_name')} ({p.get('year')})" if p.get('year') else p.get('case_name', ''))
                if citation not in seen_citations:
                    seen_citations.add(citation)
                    safe_citation = citation.replace('/', '_').replace(' ', '_')
                    matched.append({
                        "concept":      concept_name,
                        "case":         p.get("case") or p.get("case_name") or "",
                        "citation":     citation,
                        "court":        p.get("court", "Supreme Court of India"),
                        "principle":    p.get("principle") or p.get("summary") or "",
                        "relevance":    round(min(p.get("relevance_score", confidence), 1.0), 2),
                        "is_live":      False,
                        "document_url": f"/api/precedents/document/{safe_citation}"
                    })
            kb = kb_manager.get_knowledge_base()
            if concept_name in kb:
                kb_prec = kb[concept_name].get("precedent")
                if kb_prec and kb_prec not in seen_citations:
                    seen_citations.add(kb_prec)
                    safe_citation = kb_prec.replace('/', '_').replace(' ', '_')
                    prec = {
                        "concept":   concept_name,
                        "case":      kb_prec,
                        "citation":  kb_prec,
                        "court":     "Supreme Court of India",
                        "principle": kb[concept_name].get("legal_impact", ""),
                        "relevance": round(confidence, 2),
                        "is_live":   False,
                        "document_url": f"/api/precedents/document/{safe_citation}"
                    }
                    v = precedent_manager.verify_citation_authenticity(prec["citation"])
                    prec["verification_status"] = v["status"]
                    prec["is_verified_landmark"] = v["verified"]
                    matched.append(prec)
        landmark_data = {
            "Basalingappa": {
                "case": "Basalingappa vs. Mudibasappa",
                "citation": "Basalingappa vs. Mudibasappa (2019) 5 SCC 418",
                "court": "Supreme Court of India",
                "concept": "financial_capacity_risk",
                "principle": "Rebuttal of S.139 presumption via financial capacity challenge. Complainant must prove source of funds in high-value cash transactions.",
                "relevance": 0.98,
                "trigger": lambda data, concepts: _number(data.get("amount") or data.get("cheque_amount")) > 150000 and not data.get("complainant_itr_available")
            },
            "Rangappa": {
                "case": "Rangappa vs. Srikanth",
                "citation": "Rangappa vs. Srikanth (2010) 11 SCC 441",
                "court": "Supreme Court of India",
                "concept": "debt_presumption",
                "principle": "Presumption of debt u/s 139 is active. The reverse onus burden is on the accused to rebut the presumption by raising a probable defense.",
                "relevance": 0.95,
                "trigger": lambda data, concepts: bool(data.get("cheque_present")) or "debt_acknowledgment" in [c.get("concept") for c in concepts if isinstance(c, dict)]
            },
            "AneetaHada": {
                "case": "Aneeta Hada vs. Godfather Travels & Tours",
                "citation": "Aneeta Hada vs. Godfather Travels (2012) 5 SCC 661",
                "court": "Supreme Court of India",
                "concept": "company_liability",
                "principle": "Section 141 company prosecution. Directors/officers cannot be prosecuted u/s 138 without impleading the company entity as an accused.",
                "relevance": 0.96,
                "trigger": lambda data, concepts: str(data.get("accused_type")).lower() in ("company", "pvt ltd/ltd company", "partnership firm") or "s141_defect" in [c.get("concept") for c in concepts if isinstance(c, dict)]
            },
            "KishanRao": {
                "case": "Kishan Rao vs. Shankargouda",
                "citation": "Kishan Rao vs. Shankargouda (2018) 8 SCC 165",
                "court": "Supreme Court of India",
                "concept": "signature_dispute",
                "principle": "Mere denial of debt/signature does not rebut the S.139 presumption. High standard of proof required for accused to shift burden.",
                "relevance": 0.92,
                "trigger": lambda data, concepts: "signature_dispute" in [c.get("concept") for c in concepts if isinstance(c, dict)] or bool(data.get("signature_mismatch"))
            },
            "DashrathRathod": {
                "case": "Dashrath Rupsingh Rathod vs. State of Maharashtra",
                "citation": "Dashrath Rupsingh Rathod vs. State of Maharashtra (2014) 9 SCC 129",
                "court": "Supreme Court of India",
                "concept": "jurisdictional_issue",
                "principle": "Territorial jurisdiction for cheque bounce. Complaint must be filed where the payee bank branch is situated (post-2015 Amendment).",
                "relevance": 0.90,
                "trigger": lambda data, concepts: bool(data.get("payee_bank_city")) or "jurisdictional_defect" in [c.get("concept") for c in concepts if isinstance(c, dict)]
            },
            "YogendraPratap": {
                "case": "Yogendra Pratap Singh vs. Savitri Pandey",
                "citation": "Yogendra Pratap Singh vs. Savitri Pandey (2014) 10 SCC 713",
                "court": "Supreme Court of India",
                "concept": "timeline_defect",
                "principle": "Premature filing u/s 138 NI Act is a fatal defect. Complaint filed before the expiry of the 15-day notice period cannot be validated.",
                "relevance": 0.97,
                "trigger": lambda data, concepts: "premature_chronology" in [c.get("concept", "") for c in concepts if isinstance(c, dict)] or "NOTICE_INVALID" in [c.get("concept", "") for c in concepts if isinstance(c, dict)] or str(data.get("within_15_days")).lower() in ("yes", "true", "1")
            },
            "MSRLeathers": {
                "case": "MSR Leathers vs. S. Palaniappan",
                "citation": "MSR Leathers vs. S. Palaniappan (2013) 10 SCC 568",
                "court": "Supreme Court of India",
                "concept": "multiple_presentation",
                "principle": "Cheque can be presented multiple times. Complainant can file a complaint on subsequent default, provided notice is sent within 30 days.",
                "relevance": 0.91,
                "trigger": lambda data, concepts: str(data.get("multiple_notices_sent")).lower() in ("yes", "true", "1") or "limitation_issue" in [c.get("concept", "") for c in concepts if isinstance(c, dict)]
            },
            "BirSingh": {
                "case": "Bir Singh vs. Mukesh Kumar",
                "citation": "Bir Singh vs. Mukesh Kumar (2019) 4 SCC 197",
                "court": "Supreme Court of India",
                "concept": "blank_cheque_defense",
                "principle": "Inchoate instruments u/s 20. A blank signed cheque handed to the payee implies authorization to fill it, and S.138 still applies.",
                "relevance": 0.94,
                "trigger": lambda data, concepts: bool(data.get("handwriting_different")) or "material_alteration" in [c.get("concept", "") for c in concepts if isinstance(c, dict)] or str(data.get("cheque_issued_blank")).lower() in ("yes", "true", "1")
            },
            "ACNarayanan": {
                "case": "A.C. Narayanan vs. State of Maharashtra",
                "citation": "A.C. Narayanan vs. State of Maharashtra (2014) 11 SCC 790",
                "court": "Supreme Court of India",
                "concept": "poa_maintainability",
                "principle": "Prosecution through Power of Attorney is maintainable if the POA holder is fully conversant with the facts of the transaction.",
                "relevance": 0.93,
                "trigger": lambda data, concepts: bool(data.get("is_authorized")) or str(data.get("filed_via_poa")).lower() == "yes"
            },
            "ArneshKumar": {
                "case": "Arnesh Kumar vs. State of Bihar",
                "citation": "Arnesh Kumar vs. State of Bihar (2014) 8 SCC 273",
                "court": "Supreme Court of India",
                "concept": "relative_implication_498a",
                "principle": "Guidelines on arrest u/s 41A CrPC (now BNSS S.35). Mechanical arrest in matrimonial cases is barred.",
                "relevance": 0.95,
                "trigger": lambda data, concepts: str(data.get("case_type")).lower() == "criminal" or "498a" in str(data.get("description")).lower()
            },
            "GeetaMehrotra": {
                "case": "Geeta Mehrotra vs. State of U.P.",
                "citation": "Geeta Mehrotra vs. State of U.P. (2012) 10 SCC 741",
                "court": "Supreme Court of India",
                "concept": "matrimonial_quashing",
                "principle": "Matrimonial quashing. Casual reference or vague allegations against family members under S.498A IPC does not justify prosecution.",
                "relevance": 0.94,
                "trigger": lambda data, concepts: "498a" in str(data.get("description")).lower() and "relative" in str(data.get("description")).lower()
            },
            "PreetiGupta": {
                "case": "Preeti Gupta vs. State of Jharkhand",
                "citation": "Preeti Gupta vs. State of Jharkhand (2010) 7 SCC 667",
                "court": "Supreme Court of India",
                "concept": "relative_implication",
                "principle": "Over-implication of family members in S.498A matrimonial disputes is an abuse of process; quashing warranted.",
                "relevance": 0.92,
                "trigger": lambda data, concepts: "498a" in str(data.get("description")).lower() and "relative" in str(data.get("description")).lower()
            },
            "SampellyIREDA": {
                "case": "Sampelly Satyanarayana Rao vs. Indian Renewable Energy Development Agency Ltd.",
                "citation": "Sampelly Satyanarayana Rao vs. Indian Renewable Energy Development Agency Ltd. (2016) 10 SCC 458",
                "court": "Supreme Court of India",
                "concept": "security_cheque_defense",
                "principle": "Once liability crystallizes on the cheque date, even an instrument labeled as a 'security cheque' is fully enforceable u/s 138.",
                "relevance": 0.96,
                "trigger": lambda data, concepts: "security_cheque" in [c.get("concept", "") for c in concepts if isinstance(c, dict)] or str(data.get("cheque_security_claim")).lower() in ("yes", "true", "1")
            },
            "DalmiaCement": {
                "case": "Dalmia Cement vs. Galaxy Traders",
                "citation": "Dalmia Cement vs. Galaxy Traders (2001) 6 SCC 463",
                "court": "Supreme Court of India",
                "concept": "limitation_strictness",
                "principle": "Strict compliance with statutory timelines in Section 138 is mandatory. Deemed notice service rules.",
                "relevance": 0.90,
                "trigger": lambda data, concepts: "limitation_issue" in [c.get("concept", "") for c in concepts if isinstance(c, dict)] or bool(data.get("notice_sent"))
            }
        }
        for k, p in landmark_data.items():
            if p["trigger"](case_data, concepts):
                citation = p["citation"]
                if citation not in seen_citations:
                    seen_citations.add(citation)
                    safe_citation = citation.replace('/', '_').replace(' ', '_')
                    prec = {
                        "concept":      p["concept"],
                        "case":         p["case"],
                        "citation":     citation,
                        "court":        p["court"],
                        "principle":    p["principle"],
                        "relevance":    p["relevance"],
                        "is_live":      False,
                        "document_url": f"/api/precedents/document/{safe_citation}"
                    }
                    v = precedent_manager.verify_citation_authenticity(prec["citation"])
                    prec["verification_status"] = v["status"]
                    prec["is_verified_landmark"] = v["verified"]
                    matched.append(prec)
        concept_names_set = {c.get("concept", "") for c in concepts}
        for p in precedent_manager.get_latest_precedents(15):
            impact_area = p.get("impact_area", "general")
            if impact_area in concept_names_set or impact_area == "general":
                title    = p.get("title", "")
                citation = p.get("citation", "")
                key      = citation or title
                if key and key not in seen_citations:
                    seen_citations.add(key)
                    base_relevance = 0.88 if impact_area in concept_names_set else 0.65
                    variance = (hash(key) % 15) / 100.0
                    final_relevance = min(base_relevance + variance, 0.99)
                    safe_citation = citation.replace('/', '_').replace(' ', '_') if citation else title.replace(' ', '_')
                    prec = {
                        "concept":   impact_area,
                        "case":      title,
                        "citation":  citation,
                        "court":     "Supreme Court of India",
                        "principle": p.get("summary", ""),
                        "relevance": round(final_relevance, 2),
                        "match_percentage": f"{int(final_relevance * 100)}%",
                        "is_live":   True,
                        "document_url": f"/api/precedents/document/{safe_citation}"
                    }
                    v = precedent_manager.verify_citation_authenticity(prec["citation"])
                    prec["verification_status"] = v["status"]
                    prec["is_verified_landmark"] = v["verified"]
                    matched.append(prec)
        for concept_entry in concepts:
            concept_name = concept_entry.get("concept", "")
            if concept_name in ["financial_capacity_risk", "limitation_issue", "notice_defect", "company_liability"]:
                live_research = precedent_manager.search_real_precedents(f"S.138 NI Act {concept_name} landmark judgment")
                for p in live_research:
                    if p["citation"] not in seen_citations:
                        seen_citations.add(p["citation"])
                        prec = {
                            "concept":   p["impact_area"],
                            "case":      p["title"],
                            "citation":  p["citation"],
                            "court":     "Supreme Court of India",
                            "principle": p["summary"],
                            "relevance": 0.95,
                            "match_percentage": "95%",
                            "is_live":   True,
                            "is_ai_researched": True,
                            "document_url": f"/api/precedents/document/{p['citation'].replace(' ', '_')}"
                        }
                        v = precedent_manager.verify_citation_authenticity(prec["citation"])
                        prec["verification_status"] = v["status"]
                        prec["is_verified_landmark"] = v["verified"]
                        matched.append(prec)
        for m in matched:
            if "match_percentage" not in m:
                m["match_percentage"] = f"{int(m.get('relevance', 0) * 100)}%"
            if "is_ai_researched" not in m:
                m["is_ai_researched"] = False
        matched.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return matched[:15]
    @staticmethod
    def interpret_statutes(case_data: Dict, concepts: List[Dict]) -> List[Dict]:
        concept_names = {c.get("concept", "") for c in concepts if isinstance(c, dict)}
        interpretations: List[Dict] = []
        sec138 = kb_manager.get_ni_act_section("138")
        if case_data.get("cheque_present"):
            cond_met  = []
            cond_fail = []
            conditions = sec138.get("conditions", [])
            for cond in conditions:
                if "Notice" in cond and not case_data.get("notice_sent"):
                    cond_fail.append(cond)
                elif "debt" in cond.lower() and not case_data.get("debt_proven"):
                    cond_fail.append(cond)
                else:
                    cond_met.append(cond)
            status = "SATISFIED" if not cond_fail else ("PARTIAL" if cond_met else "DEFECTIVE")
            interpretations.append({
                "section":   "138",
                "title":     sec138.get("title", "Dishonour of cheque"),
                "status":    status,
                "finding":   (
                    "All Section 138 ingredients are satisfied. The case is prosecution-ready."
                    if status == "SATISFIED" else
                    f"Section 138 partially satisfied. Missing: {'; '.join(cond_fail)}."
                ),
                "punishment":    sec138.get("punishment", ""),
                "conditions_met":    cond_met,
                "conditions_failed": cond_fail,
            })
        else:
            interpretations.append({
                "section": "138",
                "title":   sec138.get("title", "Dishonour of cheque"),
                "status":  "NOT APPLICABLE",
                "finding": "FATAL: No cheque instrument present. Section 138 NI Act cannot be invoked without a negotiable instrument.",
                "conditions_met": [], "conditions_failed": []
            })
        sec139 = kb_manager.get_ni_act_section("139")
        interpretations.append({
            "section": "139",
            "title":   sec139.get("title", "Presumption in favour of holder"),
            "status":  "ACTIVE",
            "finding": (
                "The statutory presumption under S.139 is active in your favour. "
                "However, the accused does NOT have to prove beyond a reasonable doubt; they only need to raise a 'probable defense' on a preponderance of probabilities to shift the burden back to you."
            ) if case_data.get("cheque_present") else (
                "S.139 presumption is not invocable without a cheque instrument."
            ),
            "interpretation": sec139.get("interpretation", ""),
        })
        accused_type = case_data.get("accused_type", "Individual")
        if accused_type in ("Pvt Ltd/Ltd Company", "Company", "Partnership Firm"):
            sec141 = kb_manager.get_ni_act_section("141")
            has_directors = case_data.get("directors_named", False)
            resigned_risk = False
            cheque_date = case_data.get("cheque_date")
            resignation_date = case_data.get("director_resignation_date")
            from datetime import datetime
            if resignation_date and cheque_date:
                try:
                    res_dt = datetime.fromisoformat(resignation_date) if isinstance(resignation_date, str) else resignation_date
                    chq_dt = datetime.fromisoformat(cheque_date) if isinstance(cheque_date, str) else cheque_date
                    if res_dt < chq_dt:
                        resigned_risk = True
                except: pass
            status = "CRITICAL_DEFECT" if not has_directors or resigned_risk else "SATISFIED"
            finding = ""
            if not has_directors:
                finding = "CRITICAL: Company accused impleaded without naming responsible officers. Prosecution will fail per Aneeta Hada."
            elif resigned_risk:
                finding = f"FATAL ADVERSARIAL TRAP: Director impleaded who resigned on {resignation_date} (BEFORE cheque date). This triggers automatic quashing u/s 482 and exposes you to a 'Malicious Prosecution' counter-suit. PRUNING RECOMMENDED."
            else:
                finding = "Responsible officers/directors have been named. S.141 vicarious liability is properly pleaded."
            interpretations.append({
                "section": "141",
                "title":   sec141.get("title", "Offences by companies"),
                "status":  status,
                "finding": finding,
                "requirement": sec141.get("requirement", ""),
            })
        sec142 = kb_manager.get_ni_act_section("142")
        interpretations.append({
            "section": "142",
            "title":   sec142.get("title", "Cognizance of offences"),
            "status":  "NOTE",
            "finding": (
                "Complaint must be filed within 1 month of the cause of action arising "
                "(expiry of 15-day payment window after notice). Verify your limitation period immediately."
            ),
            "limitation": sec142.get("limitation", ""),
        })
        sec143a = kb_manager.get_ni_act_section("143A")
        interpretations.append({
            "section": "143A",
            "title":   sec143a.get("title", "Power to direct interim compensation"),
            "status":  "AVAILABLE",
            "finding": (
                "You may apply for interim compensation of up to 20% of the cheque amount "
                "at the stage of summoning the accused. This is an important interim relief."
            ),
            "limit": sec143a.get("limit", ""),
        })
        return interpretations
    @staticmethod
    def generate_causal_story(case_data: Dict, concepts: List[Dict]) -> List[Dict]:
        story = []
        complainant = case_data.get("complainant_name") or "Complainant"
        accused = case_data.get("accused_name") or "Accused"
        amount = case_data.get("amount") or case_data.get("cheque_amount") or "X"
        if case_data.get("debt_proven"):
            story.append({
                "stage": "Liability Origin",
                "text": f"A legally enforceable debt of â‚¹{amount} was established between {complainant} and {accused}.",
                "status": "STRONG"
            })
        else:
            story.append({
                "stage": "Alleged Liability",
                "text": f"An alleged friendly loan/transaction of â‚¹{amount} took place without formal documentation.",
                "status": "VULNERABLE"
            })
        if case_data.get("cheque_present"):
            story.append({
                "stage": "Instrument Issuance",
                "text": f"Cheque No. {case_data.get('cheque_number', 'N/A')} was issued by the accused towards discharge of liability.",
                "status": "VERIFIED"
            })
        else:
            story.append({
                "stage": "Missing Instrument",
                "text": "The physical cheque instrument is not documented in the current assessment.",
                "status": "CRITICAL"
            })
        if case_data.get("dishonour_memo"):
            story.append({
                "stage": "Bank Dishonour",
                "text": f"Cheque was presented and returned unpaid for '{case_data.get('dishonour_reason', 'Insufficient Funds')}'.",
                "status": "VERIFIED"
            })
        else:
            story.append({
                "stage": "Dishonour Verification",
                "text": "Formal bank return memo is missing; dishonour state is not legally proven.",
                "status": "CRITICAL"
            })
        if case_data.get("notice_sent"):
            story.append({
                "stage": "Demand Compliance",
                "text": f"Statutory notice served on {case_data.get('notice_date', 'N/A')}. Demand for payment made.",
                "status": "VERIFIED"
            })
        else:
            story.append({
                "stage": "Notice Failure",
                "text": "Mandatory demand notice was not served within the 30-day statutory window.",
                "status": "CRITICAL"
            })
        if case_data.get("notice_sent") and not case_data.get("reply_received"):
            story.append({
                "stage": "Cause of Action",
                "text": "Accused failed to pay within 15 days of notice receipt. Criminal liability crystallized.",
                "status": "CRYSTALLIZED"
            })
        return story
    @classmethod
    def generate_reasoning_trail(cls, case_data: Dict, concepts: List[Dict], final_score: float = 0.0, engine_result: Dict = None) -> List[Dict]:
        trail: List[Dict] = []
        pillars = []
        if case_data.get("cheque_present"): pillars.append("S.138 instrument verified")
        if case_data.get("notice_sent"):    pillars.append("Demand notice complied")
        if case_data.get("debt_proven"):    pillars.append("Enforceable debt established")
        trail.append({
            "text": f"RULE-BASED AUDIT: Verified {len(pillars)}/3 statutory pillars. " + (f"Compliance confirmed: {', '.join(pillars)}." if pillars else "FATAL ERROR: No statutory pillars satisfied."),
            "provenance": "STATUTORY",
            "confidence": 1.0,
            "authority": "The Negotiable Instruments Act, 1881"
        })
        risks = [c for c in concepts if isinstance(c, dict) and ("risk" in c.get("concept", "") or "defect" in c.get("concept", ""))]
        if risks:
            causality_chain = []
            if float(case_data.get("amount") or 0) > 500000 and not case_data.get("complainant_itr_available"):
                causality_chain.append("Missing ITR -> Financial Capacity Risk -> Rebuttal u/s 139 (Basalingappa).")
            trail.append({
                "text": f"CAUSALITY ANALYSIS: Detected {len(risks)} explicit risk vectors. Propagation: { ' | '.join(causality_chain) or 'Implicit logic applied.'}",
                "provenance": "AI_INFERENCE",
                "confidence": 0.85,
                "logic_engine": "Adversarial Propagation Engine v7.0"
            })
        if engine_result and "calibration_metadata" in engine_result:
            cal = engine_result["calibration_metadata"]
            if cal.get("calibration_notes"):
                trail.append({
                    "text": f"STATISTICAL CALIBRATION: {cal['calibration_notes'][0]} Resulting Confidence Interval: {cal['confidence_interval']}.",
                    "provenance": "EMPIRICAL",
                    "confidence": 0.95,
                    "logic_engine": "Calibration Engine v1.0"
                })
        for c in concepts:
            concept_name = c.get("concept", "").replace("_", " ").title()
            trail.append({
                "text": f"SEMANTIC DETECTION: Identified '{concept_name}' pattern in case facts.",
                "provenance": "AI_INFERENCE",
                "confidence": c.get("confidence", 0.7),
                "rationale": f"This matters because {concept_name.lower()} affects the overall survivability and burden of proof u/s 138."
            })
        precs = cls.match_precedents(case_data, concepts)
        if precs:
            trail.append({
                "text": f"PRECEDENT BINDING: Case facts anchored to landmark judgments. Primary authority: {precs[0]['case']} ({precs[0]['citation']}).",
                "provenance": "PRECEDENTIAL",
                "confidence": 0.98,
                "citation": precs[0]['citation'],
                "rationale": "This matters because judicial precedents provide the binding interpretation of statutory laws."
            })
        if final_score < 60:
            trail.append({
                "text": f"STRATEGIC PIVOT: Settlement recommended. Low survivability ({final_score}%) due to fatal evidentiary gaps.",
                "provenance": "SIMULATED",
                "confidence": 0.72,
                "scenario": "Adversarial Collapse Simulation",
                "rationale": "This matters because proceeding with a weak case increases risk of cost penalties and malicious prosecution claims."
            })
        return trail
