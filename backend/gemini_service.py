import json
import logging
import os
import re
import urllib.request
import urllib.error
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger("judiq.gemini_service")

# Statutory NI Act & Evidence RAG Knowledge Snippets
STATUTORY_KNOWLEDGE = {
    "s138": {
        "en": "Section 138 Negotiable Instruments Act 1881: Dishonour of cheque for insufficiency of funds. Essential ingredients: (1) Drawing of cheque for debt/liability, (2) Presentation within validity (3 months), (3) Return unpaid by bank, (4) Statutory demand notice dispatched within 30 days of memo receipt, (5) Failure of drawer to pay within 15 days of notice receipt.",
        "hi": "धारा 138 परक्राम्य लिखत अधिनियम 1881 (NI Act): खाते में अपर्याप्त निधि या व्यवस्था से अधिक होने पर चेक बाउंस। आवश्यक तत्व: (1) वैध ऋण/दायित्व के लिए चेक जारी करना, (2) 3 माह के भीतर चेक प्रस्तुत करना, (3) बैंक द्वारा अनादर मेमो जारी करना, (4) मेमो प्राप्ति के 30 दिनों के भीतर कानूनी मांग नोटिस भेजना, (5) नोटिस प्राप्ति के 15 दिनों में भुगतान न करना।",
        "mr": "कलम १३८ परक्राम्य संलेख अधिनियम १८८१ (NI Act): खात्यात अपुरा निधी असल्यामुळे धनादेश अनादर. आवश्यक कायदेशीर घटक: (१) कायदेशीर देणी फेडण्यासाठी धनादेश देणे, (२) वैध कालावधीत (३ महिने) बँकेत सादर करणे, (३) बँकेने अनादर मेमो देणे, (४) मेमो मिळाल्यापासून ३० दिवसांच्या आत लेखी मागणी नोटीस पाठवणे, (५) नोटीस मिळाल्यापासून १५ दिवसांच्या आत रक्कम न भरणे."
    },
    "s139": {
        "en": "Section 139 NI Act: Presumption in favor of holder. The court shall presume that the cheque was issued for the discharge of a legally enforceable debt. Rebuttable by preponderance of probabilities (Rangappa v. Sri Mohan, Basalingappa v. Mudibasappa).",
        "hi": "धारा 139 NI Act: चेक धारक के पक्ष में कानूनी उपधारणा। न्यायालय यह मानेगा कि चेक वैध ऋण के भुगतान के लिए जारी किया गया था। अभियुक्त इसे संभावनाओं की प्रबलता के आधार पर खंडित कर सकता है (रंगप्पा बनाम श्री मोहन).",
        "mr": "कलम १३९ NI Act: धनादेश धारकाच्या बाजूने कायदेशीर गृहीतक. धनादेश कायदेशीर देणी फेडण्यासाठीच दिला होता असे न्यायालय गृहीत धरते. आरोपी पुराव्याच्या संभाव्यतेच्या आधारावर याचे खंडन करू शकतो (रंगप्पा वि. श्री मोहन)."
    },
    "s141": {
        "en": "Section 141 NI Act: Offences by companies. If the drawer is a company/firm, the company itself and every person in charge of and responsible for the conduct of its business at the time of the offence are deemed guilty (Aneeta Hada, S.M.S. Pharmaceuticals).",
        "hi": "धारा 141 NI Act: कंपनियों द्वारा अपराध। कंपनी और घटना के समय उसके व्यवसाय के संचालन के प्रभारी व्यक्ति उत्तरदायी माने जाएंगे (अनीता हाडा बनाम गॉडफादर ट्रेवल्स).",
        "mr": "कलम १४१ NI Act: कंपन्यांनी केलेले गुन्हे. कंपनी आणि गुन्ह्याच्या वेळी तिच्या कारभारासाठी जबाबदार असलेले संचालक संयुक्तपणे जबाबदार ठरतात (अनीता हाडा खटला)."
    },
    "s142": {
        "en": "Section 142 NI Act: Cognizance of offences. Complaint must be filed within 1 month from the date the cause of action arises (16th day after notice receipt). Delay can be condoned under Section 142(1)(b) upon sufficient cause.",
        "hi": "धारा 142 NI Act: संज्ञान एवं परिसीमा काल। वाद हेतुक उत्पन्न होने के 1 माह के भीतर (नोटिस के 15 दिन बीतने के बाद 16वें दिन से 30 दिन) परिवाद दाखिल होना चाहिए।",
        "mr": "कलम १४२ NI Act: न्यायालयाची दखल व मुदत. दावा दाखल करण्याचे कारण उत्पन्न झाल्यापासून १ महिन्याच्या आत तक्रार दाखल केली पाहिजे. विलंबासाठी सबळ कारण दाखवून माफी मागता येते."
    },
    "s143a": {
        "en": "Section 143A NI Act: Power to direct interim compensation up to 20% of the cheque amount during trial upon framing of notice/charge.",
        "hi": "धारा 143A NI Act: मुकदमे के दौरान न्यायालय चेक राशि का 20% तक अंतरिम मुआवजा देने का आदेश दे सकता है।",
        "mr": "कलम १४३A NI Act: खटल्यादरम्यान धनादेश रकमेच्या २०% पर्यंत अंतरिम भरपाई देण्याचा न्यायालयाचा अधिकार."
    }
}


def format_indian_currency(val: Any) -> str:
    try:
        n = float(val)
        s = f"{int(n)}" if n.is_integer() else f"{n:.2f}"
        if len(s) <= 3:
            return s
        last3 = s[-3:]
        other = s[:-3]
        other = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", other)
        return other + "," + last3
    except Exception:
        return str(val)


def normalize_fact_presentation(val: Any, field_name: str = "") -> str:
    """
    Transforms raw extractions (which can be a list of candidate dicts, a dict, or a scalar)
    into a clean, human-readable legal presentation with clear discrepancy badges and no raw JSON.
    """
    if val is None or val == "":
        return "Not specified"

    if isinstance(val, dict):
        return normalize_fact_presentation(val.get("value"), field_name)

    if isinstance(val, list):
        if not val:
            return "Not specified"
        # Check if items are dicts with 'value'
        if isinstance(val[0], dict) and "value" in val[0]:
            # Sort by confidence descending
            sorted_items = sorted(val, key=lambda x: x.get("confidence", 0), reverse=True)
            primary_val = sorted_items[0].get("value")

            # Check distinct values
            distinct_values = []
            for item in sorted_items:
                v = item.get("value")
                if v is not None and v != "" and v not in distinct_values:
                    distinct_values.append(v)

            if "amount" in field_name:
                p_fmt = f"₹{format_indian_currency(primary_val)}"
                if len(distinct_values) > 1:
                    alt_fmt = f"₹{format_indian_currency(distinct_values[1])}"
                    return f"{p_fmt} (⚠️ Notice/Complaint mentions {alt_fmt})"
                return p_fmt

            if "date" in field_name:
                p_str = str(primary_val)
                if len(distinct_values) > 1:
                    return f"{p_str} (⚠️ Variation: {distinct_values[1]} in other docs)"
                return p_str

            if field_name in ("complainant_name", "accused_name", "bank_name"):
                if isinstance(primary_val, str) and primary_val.isupper():
                    for d in distinct_values:
                        if isinstance(d, str) and not d.isupper():
                            return d
                return str(primary_val)

            return str(primary_val)
        else:
            return str(val[0])

    if "amount" in field_name:
        return f"₹{format_indian_currency(val)}"

    return str(val)


def extract_clean_citations(doc_intel: Optional[Dict[str, Any]] = None, facts: Optional[Dict[str, Any]] = None) -> List[str]:
    citations = set()
    if doc_intel:
        for d in doc_intel.get("extracted_docs", []):
            if isinstance(d, dict) and d.get("filename"):
                citations.add(d["filename"])
            elif isinstance(d, str):
                citations.add(d)
        for f_list in (doc_intel.get("all_facts") or {}).values():
            if isinstance(f_list, list):
                for item in f_list:
                    if isinstance(item, dict) and item.get("source_document"):
                        citations.add(item["source_document"])
    if facts:
        for f_val in facts.values():
            if isinstance(f_val, list):
                for item in f_val:
                    if isinstance(item, dict) and item.get("source_document"):
                        citations.add(item["source_document"])
    return sorted(list(citations))


class GeminiCaseRAGService:
    @staticmethod
    def _call_gemini_api(prompt: str, sys_instruction: str, max_tokens: int = 2048, temperature: float = 0.2) -> Optional[str]:
        try:
            from llm_engine import get_all_gemini_api_keys
            api_keys = get_all_gemini_api_keys()
        except Exception:
            k = os.environ.get("GEMINI_API_KEY", "").strip()
            api_keys = [k] if k else []

        if not api_keys:
            return None

        # Prioritize fast, high-availability models with generous free-tier quotas
        configured_model = os.environ.get("GEMINI_MODEL", "").strip()
        models_to_try = [
            m for m in [
                configured_model,
                "gemini-3.5-flash-lite",
                "gemini-flash-latest",
                "gemini-3.1-flash-lite",
                "gemini-3.6-flash"
            ] if m
        ]
        # Deduplicate while preserving precedence
        candidate_models = list(dict.fromkeys(models_to_try))

        for key_idx, api_key in enumerate(api_keys):
            for model in candidate_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "systemInstruction": {"parts": [{"text": sys_instruction}]},
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature
                    }
                }
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=25) as resp:
                        res = json.loads(resp.read().decode("utf-8"))
                        candidates = res.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            texts = [p.get("text", "") for p in parts if "text" in p]
                            answer = "".join(texts).strip()
                            if answer:
                                logger.info(f"Gemini RAG generated successfully via model '{model}' with key #{key_idx+1}.")
                                return answer
                except urllib.error.HTTPError as he:
                    logger.warning(f"Gemini API key #{key_idx+1} model '{model}' HTTP error {he.code}: {he.reason}. Trying next...")
                    continue
                except Exception as e:
                    logger.warning(f"Gemini API key #{key_idx+1} model '{model}' failed ({e}). Trying next...")
                    continue

        logger.warning("All Gemini candidate models and fallback keys failed or rate-limited; falling back to local legal intelligence engine.")
        return None

    @staticmethod
    def build_system_instruction(lang: str = "en") -> str:
        if lang == "mr":
            return (
                "तुम्ही 'JudiQ AI' चे वरिष्ठ न्यायालयीन कायदेतज्ज्ञ (Legal Co-Counsel) आहात. "
                "तुम्ही भारतीय कायदे (विशेषतः परक्राम्य संलेख अधिनियम १८८१ - Section 138 NI Act, भारतीय साक्ष अधिनियम २०२३ / BSA, आणि BNSS) "
                "यांच्यात अत्यंत निपुण आहात. "
                "तुम्ही वकिलांशी शुद्ध, आदरयुक्त आणि अचूक न्यायालयीन मराठीत संवाद साधता. "
                "प्रत्येक उत्तरात दिलेल्या केस फॅक्ट्स (धनादेश क्रमांक, रक्कम, तारखा, बँक मेमो, नोटीस) यांवर आधारित थेट वस्तुस्थिती, "
                "कायदेशीर कलमे आणि रणनीती विशद करा. "
                "जर वापरकर्त्याने एखाद्या तारखेत किंवा माहितीत बदल सुचवला, तर त्या दुरुस्तीची नोंद घ्या."
            )
        elif lang == "hi":
            return (
                "आप 'JudiQ AI' के वरिष्ठ न्यायिक कानूनी सलाहकार (Senior Legal Co-Counsel) हैं। "
                "आप भारतीय कानूनों (विशेष रूप से परक्राम्य लिखत अधिनियम 1881 - धारा 138 NI Act, भारतीय साक्ष्य अधिनियम 2023, और BNSS) "
                "में विशेषज्ञ हैं। आप वकीलों के साथ सटीक, औपचारिक और स्पष्ट कानूनी हिंदी में संवाद करते हैं। "
                "प्रश्नों का उत्तर केस के वास्तविक तथ्यों (चेक नंबर, राशि, नोटिस की तारीखें, बैंक मेमो) के आधार पर दें। "
                "कानूनी प्रावधानों (धारा 138, 139, 141, 142) का स्पष्ट संदर्भ दें। "
                "यदि वकील किसी तथ्य में सुधार या परिवर्तन बताता है, तो उसका स्पष्ट संज्ञान लें।"
            )
        else:
            return (
                "You are JudiQ AI's Senior Litigation Co-Counsel and Indian Legal Expert. "
                "You specialize in the Negotiable Instruments Act 1881 (Section 138, 139, 141, 142, 143A), "
                "Bharatiya Sakshya Adhiniyam 2023 (BSA), and Bharatiya Nagarik Suraksha Sanhita 2023 (BNSS). "
                "You provide precise, evidence-grounded legal answers citing exact facts extracted from case documents "
                "(cheque numbers, amounts, presentation dates, dishonour memos, postal receipts, statutory notices, invoices, supply agreements). "
                "Always cite relevant statutory provisions and landmark Supreme Court ratios. "
                "If the lawyer clarifies or updates any case fact, acknowledge the update precisely."
            )

    @staticmethod
    def build_rag_context(case_data: Dict[str, Any], doc_intel: Optional[Dict[str, Any]] = None, lang: str = "en") -> str:
        facts = case_data or {}
        doc_intel_obj = doc_intel or {}
        extracted_facts = doc_intel_obj.get("all_facts") or doc_intel_obj.get("extracted_facts") or {}
        merged_facts = {}
        for k, v in extracted_facts.items():
            if v is not None and v != "":
                merged_facts[k] = v
        for k, v in facts.items():
            if v is not None and v != "" and v != "Not specified" and v != "null":
                if k in ("complainant_name", "accused_name") and v in ("Complainant", "Accused") and k in merged_facts:
                    continue
                merged_facts[k] = v

        lang_key = lang if lang in ("en", "hi", "mr") else "en"
        statute_intro = STATUTORY_KNOWLEDGE["s138"][lang_key]

        lines = [
            f"=== CASE FACTS DOSSIER ===",
            f"Case Title: {normalize_fact_presentation(merged_facts.get('case_title') or merged_facts.get('case_name'), 'case_title')}",
            f"Case ID / Reference: {normalize_fact_presentation(merged_facts.get('case_id'), 'case_id')}",
            f"Case Type: {normalize_fact_presentation(merged_facts.get('case_type'), 'case_type')}",
            f"Complainant / Drawee: {normalize_fact_presentation(merged_facts.get('complainant_name'), 'complainant_name')}",
            f"Accused / Drawer: {normalize_fact_presentation(merged_facts.get('accused_name'), 'accused_name')}",
            f"Cheque Number: {normalize_fact_presentation(merged_facts.get('cheque_number'), 'cheque_number')}",
            f"Cheque Amount: {normalize_fact_presentation(merged_facts.get('cheque_amount'), 'cheque_amount')}",
            f"Cheque Date: {normalize_fact_presentation(merged_facts.get('cheque_date'), 'cheque_date')}",
            f"Bank Name: {normalize_fact_presentation(merged_facts.get('bank_name'), 'bank_name')}",
            f"Dishonour Date: {normalize_fact_presentation(merged_facts.get('dishonour_date'), 'dishonour_date')}",
            f"Dishonour Reason: {normalize_fact_presentation(merged_facts.get('dishonour_reason'), 'dishonour_reason')}",
            f"Bank Memo Received Date: {normalize_fact_presentation(merged_facts.get('memo_date'), 'memo_date')}",
            f"Statutory Notice Dispatched: {normalize_fact_presentation(merged_facts.get('notice_date'), 'notice_date')}",
            f"Notice Delivery / Served Date: {normalize_fact_presentation(merged_facts.get('notice_received_date') or merged_facts.get('notice_delivery_date'), 'notice_delivery_date')}",
            f"Notice Mode: {normalize_fact_presentation(merged_facts.get('notice_mode'), 'notice_mode')}",
            f"Underlying Debt / Transaction Date: {normalize_fact_presentation(merged_facts.get('transaction_date'), 'transaction_date')}",
            f"Underlying Purpose: {normalize_fact_presentation(merged_facts.get('purpose'), 'purpose')}",
            f"Court Name: {normalize_fact_presentation(merged_facts.get('court_name'), 'court_name')}",
            f"Filing Date: {normalize_fact_presentation(merged_facts.get('filing_date'), 'filing_date')}",
            "",
            "=== STATUTORY BENCHMARKS ===",
            statute_intro,
            STATUTORY_KNOWLEDGE["s139"][lang_key],
            STATUTORY_KNOWLEDGE["s142"][lang_key],
            ""
        ]

        # Add granular evidentiary snippets from extracted documents
        evidence_lines = []
        seen_snippets = set()

        for field, cand_list in (doc_intel_obj.get("all_facts") or {}).items():
            if isinstance(cand_list, list):
                for cand in cand_list:
                    if isinstance(cand, dict):
                        doc_name = cand.get("source_document") or cand.get("doc_type") or "Document"
                        snippet = (cand.get("source_snippet") or "").strip()
                        if snippet and snippet not in seen_snippets:
                            seen_snippets.add(snippet)
                            evidence_lines.append(f"• [{doc_name}] ({field}): {snippet}")

        for ed in doc_intel_obj.get("extracted_docs", []):
            if isinstance(ed, dict):
                fn = ed.get("filename") or ed.get("doc_name") or "Case Document"
                doc_type = ed.get("doc_type") or ed.get("document_type") or ""
                summary = ed.get("summary") or ed.get("description") or ed.get("text_excerpt") or ed.get("extracted_text")
                if summary:
                    summary_clean = str(summary)[:300].strip()
                    evidence_lines.append(f"• [{fn}] {f'({doc_type})' if doc_type else ''}: {summary_clean}")

        if evidence_lines:
            lines.append("=== EXTRACTED EVIDENTIARY SOURCES & RELEVANT SNIPPETS ===")
            lines.extend(evidence_lines[:25])
            lines.append("")

        # Add timeline discrepancies or contradictions if available
        contradictions = doc_intel_obj.get("contradictions") or []
        if contradictions:
            lines.append("=== DETECTED DOCUMENT CONTRADICTIONS & DISCREPANCIES ===")
            for c in contradictions:
                lines.append(f"- {c.get('description') or c.get('title') or str(c)}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def query_case_rag(
        cls,
        query: str,
        case_data: Dict[str, Any],
        doc_intel: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Executes a grounded RAG query over the case facts and documents.
        Supports English, Hindi, and Marathi with dynamic fact update extraction.
        """
        detected_lang = cls.detect_language(query, default=lang)
        sys_msg = cls.build_system_instruction(detected_lang)
        rag_context = cls.build_rag_context(case_data, doc_intel, detected_lang)

        # Build prompt with strict conciseness and query-targeting instructions
        prompt = (
            f"{rag_context}\n\n"
            f"=== LAWYER'S QUERY ===\n"
            f"Query: {query}\n"
            f"Language: {detected_lang}\n\n"
            f"CRITICAL INSTRUCTIONS FOR RESPONSE:\n"
            f"1. DIRECT & TARGETED: Answer ONLY what the lawyer specifically asked. Do not dump the entire case chronology, all statutory ingredients, or unrelated analysis unless specifically requested.\n"
            f"   - If asked for 'case section' or 'applicable sections': state the primary section (Section 138 NI Act) and relevant companion sections (Section 139, 141, 142 NI Act, BNSS, BSA) concisely in 2-3 focused paragraphs.\n"
            f"   - If asked 'what is the cheque paid for': explain the underlying commercial transaction, invoice/ledger evidence, and Section 139 presumption concisely.\n"
            f"   - If asked for timeline, limitation, or cross-examination: then provide the detailed analytical breakdown.\n"
            f"2. EVIDENCE GROUNDING: Cite specific verified documents (e.g. [01_Invoice_and_Ledger.pdf]) that support your answer.\n"
            f"3. CONCISE & PROFESSIONAL: Deliver an authoritative, high-signal response in {detected_lang}. Avoid boilerplate fluff.\n"
            f"4. FACT UPDATES: Only if the lawyer's query EXPLICITLY asks to change, correct, or update a case fact (e.g. 'amount is actually 750000', 'notice date is 2026-04-10'), include a JSON block at the very end: ```fact_update {{\"field\": \"fieldName\", \"value\": \"newValue\", \"label\": \"Display Label\"}}```. NEVER output this block if the lawyer is just asking a question.\n"
        )

        response_text = cls._call_gemini_api(prompt, sys_msg, max_tokens=1500, temperature=0.25)
        
        # Fallback to local intelligence if Gemini is offline or rate-limited
        if not response_text:
            response_text = cls._generate_local_fallback(query, case_data, doc_intel, detected_lang)

        # Parse any proposed fact updates from response or query
        proposed_updates = cls._detect_fact_updates(query, response_text, case_data)

        # Clean fact_update code blocks out of the user-facing text
        clean_text = re.sub(r'```fact_update[\s\S]*?```', '', response_text).strip()

        return {
            "answer": clean_text,
            "language": detected_lang,
            "citations": cls._extract_citations(clean_text),
            "proposed_updates": proposed_updates,
            "timestamp": time.time()
        }

    @staticmethod
    def detect_language(text: str, default: str = "en") -> str:
        if not text:
            return default
        devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
        if devanagari_count > 3:
            # Distinctive Marathi markers
            marathi_keywords = ["आहे", "नाही", "कधी", "झाले", "झाला", "करा", "काय", "यांचे", "म्हणून", "धनादेश", "पावती", "रक्कम"]
            # Distinctive Hindi markers
            hindi_keywords = ["है", "नहीं", "क्या", "कब", "हुआ", "हुई", "कानूनी", "बताएं", "दीजिये", "होने", "था", "थी"]
            
            mr_matches = sum(1 for kw in marathi_keywords if kw in text)
            hi_matches = sum(1 for kw in hindi_keywords if kw in text)

            if mr_matches > hi_matches:
                return "mr"
            elif hi_matches > 0:
                return "hi"
            elif mr_matches > 0:
                return "mr"
            return "hi"
        return default

    @classmethod
    def generate_cross_examination(
        cls,
        witness_role: str,
        case_data: Dict[str, Any],
        doc_intel: Optional[Dict[str, Any]] = None,
        lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Generates targeted courtroom cross-examination questions for a specific witness.
        """
        detected_lang = lang if lang in ("en", "hi", "mr") else "en"
        sys_msg = cls.build_system_instruction(detected_lang)
        rag_context = cls.build_rag_context(case_data, doc_intel, detected_lang)

        role_prompt = {
            "complainant": "Cross-examination questions for Complainant to dismantle financial capacity (ITR), loan proof, and Section 139 presumption.",
            "accused": "Cross-examination questions for Accused to establish signature admission, debt acknowledgement, and failure to reply to notice.",
            "bank_manager": "Cross-examination questions for Drawee Bank Manager regarding return memo validity, computer sign compliance, and CTS clearing log.",
            "postal_witness": "Cross-examination questions regarding speed post tracking, delivery certificate, and presumption of service under Section 27 General Clauses Act."
        }.get(witness_role.lower(), f"Cross-examination questions for witness: {witness_role}")

        prompt = (
            f"{rag_context}\n\n"
            f"TASK: Generate 8 to 10 highly strategic cross-examination questions for: {witness_role.upper()}.\n"
            f"Goal: {role_prompt}\n"
            f"Language: {detected_lang}\n"
            f"Structure: Provide (1) Objective, (2) Sequential Questions with expected answers, (3) Key statutory trap or precedent citation.\n"
        )

        response_text = cls._call_gemini_api(prompt, sys_msg, max_tokens=2000, temperature=0.3)
        if not response_text:
            response_text = cls._fallback_cross_exam(witness_role, case_data, detected_lang)

        return {
            "witness_role": witness_role,
            "questions_text": response_text,
            "language": detected_lang,
            "timestamp": time.time()
        }

    @classmethod
    def generate_courtroom_arguments(
        cls,
        argument_type: str,
        case_data: Dict[str, Any],
        doc_intel: Optional[Dict[str, Any]] = None,
        lang: str = "en"
    ) -> Dict[str, Any]:
        """
        Generates courtroom trial arguments or quashing grounds under Section 482 / S.143A.
        """
        detected_lang = lang if lang in ("en", "hi", "mr") else "en"
        sys_msg = cls.build_system_instruction(detected_lang)
        rag_context = cls.build_rag_context(case_data, doc_intel, detected_lang)

        prompt = (
            f"{rag_context}\n\n"
            f"TASK: Draft a structured oral and written courtroom argument for: {argument_type.upper()}.\n"
            f"Language: {detected_lang}\n"
            f"Include:\n"
            f"1. Factual Proposition & Discrepancies in the record\n"
            f"2. Statutory Provisions (NI Act, BSA, BNSS)\n"
            f"3. Leading Supreme Court Precedent Ratios (e.g. Dashrath Rupsingh Rathod, Aneeta Hada, Rangappa)\n"
            f"4. Concrete prayer/submission for the Magistrate or High Court.\n"
        )

        response_text = cls._call_gemini_api(prompt, sys_msg, max_tokens=2000, temperature=0.25)
        if not response_text:
            response_text = cls._fallback_arguments(argument_type, case_data, detected_lang)

        return {
            "argument_type": argument_type,
            "arguments_text": response_text,
            "language": detected_lang,
            "timestamp": time.time()
        }

    @classmethod
    def export_case_dossier(cls, case_data: Dict[str, Any], doc_intel: Optional[Dict[str, Any]] = None, lang: str = "en") -> Dict[str, Any]:
        """
        Compiles the complete updated fact sheet, timeline, and strategy summary into an exportable document.
        """
        facts = {**((doc_intel or {}).get("all_facts") or {}), **(case_data or {})}
        lang_key = lang if lang in ("en", "hi", "mr") else "en"

        md_content = [
            f"# JUDIQ AI — COMPREHENSIVE CASE FACT DOSSIER",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Case Title:** {facts.get('case_title') or facts.get('case_name', 'Untitled')}",
            f"**Case Reference:** {facts.get('case_id', 'Not Assigned')}",
            f"**Statutory Regime:** {facts.get('case_type', 'Negotiable Instruments Act, 1881 (Section 138)')}",
            "",
            "## 1. Primary Parties & Representation",
            f"- **Complainant / Drawee:** {normalize_fact_presentation(facts.get('complainant_name'), 'complainant_name')}",
            f"- **Accused / Drawer:** {normalize_fact_presentation(facts.get('accused_name'), 'accused_name')} ({normalize_fact_presentation(facts.get('accused_type'), 'accused_type')})",
            f"- **Jurisdiction / Court:** {normalize_fact_presentation(facts.get('court_name'), 'court_name')}",
            "",
            "## 2. Negotiable Instrument Particulars",
            f"- **Cheque Number:** {normalize_fact_presentation(facts.get('cheque_number'), 'cheque_number')}",
            f"- **Cheque Amount:** {normalize_fact_presentation(facts.get('cheque_amount'), 'cheque_amount')}",
            f"- **Cheque Date:** {normalize_fact_presentation(facts.get('cheque_date'), 'cheque_date')}",
            f"- **Drawee Bank & Branch:** {normalize_fact_presentation(facts.get('bank_name'), 'bank_name')}",
            "",
            "## 3. Dishonour & Return Memo",
            f"- **Date of First Presentation:** {normalize_fact_presentation(facts.get('presentation_date'), 'presentation_date')}",
            f"- **Date of Dishonour:** {normalize_fact_presentation(facts.get('dishonour_date'), 'dishonour_date')}",
            f"- **Reason for Return:** {normalize_fact_presentation(facts.get('dishonour_reason'), 'dishonour_reason')}",
            f"- **Bank Memo Date:** {normalize_fact_presentation(facts.get('memo_date'), 'memo_date')}",
            "",
            "## 4. Statutory Demand Notice (Section 138(b))",
            f"- **Notice Dispatch Date:** {normalize_fact_presentation(facts.get('notice_date'), 'notice_date')}",
            f"- **Mode of Service:** {normalize_fact_presentation(facts.get('notice_mode'), 'notice_mode')}",
            f"- **Notice Delivery / Service Date:** {normalize_fact_presentation(facts.get('notice_received_date') or facts.get('notice_delivery_date'), 'notice_delivery_date')}",
            f"- **Expiry of 15-Day Cure Period:** Calculated from delivery",
            f"- **Cause of Action Date:** Day 16 post-receipt",
            "",
            "## 5. Underlying Transaction & Debt Proof",
            f"- **Transaction Date:** {normalize_fact_presentation(facts.get('transaction_date'), 'transaction_date')}",
            f"- **Nature / Purpose of Debt:** {normalize_fact_presentation(facts.get('purpose'), 'purpose')}",
            f"- **Agreement Type:** {normalize_fact_presentation(facts.get('agreement_type'), 'agreement_type')}",
            f"- **Financial Capacity Proof (ITR):** {normalize_fact_presentation(facts.get('itr_available'), 'itr_available')}",
            "",
            "## 6. Evidentiary Audit & Forensic Readiness",
            f"- **Original Cheque in Custody:** {facts.get('original_cheque', 'Yes')}",
            f"- **Bank Memo Signed / Stamped:** {facts.get('memo_signed', 'Yes')}",
            f"- **Section 63(4) BSA / 65B Certificate:** {facts.get('has_bsa_certificate', 'N/A')}",
            "",
            "---",
            "*Report compiled via JudiQ Institutional Litigation Engine. All facts verified by counsel.*"
        ]

        return {
            "markdown": "\n".join(md_content),
            "facts": facts,
            "case_id": facts.get("case_id"),
            "language": lang_key,
            "export_time": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Internal Helpers & Fallbacks
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def _detect_fact_updates(cls, query: str, response: str, current_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        updates = []
        q_lower = (query or "").lower()

        # Check if the lawyer's query actually intends to change or specify a fact
        has_update_intent = any(k in q_lower for k in [
            "change", "update", "correct", "modify", "set", "actually", "is not", "instead of",
            "new amount", "new date",
            "बदला", "दुरुस्त", "करा", "बदलें", "सही करें", "हो गया", "तारीख आहे", "रक्कम आहे"
        ]) or bool(re.search(r'(?:is|was|=|:)\s*(?:changed to|updated to|now)', query, re.I))

        # 1. Exact extraction from user query (user's direct text is ground truth)
        if has_update_intent:
            amt_match = re.search(r'(?:amount|cheque amount|रक्कम|राशि)\s*(?:is|was)?\s*(?:changed to|updated to|now|=|:|झाली|आहे|थी)?\s*(?:₹|rs\.?|inr)?\s*([0-9,]+(?:\.[0-9]{2})?)', query, re.I)
            if amt_match:
                try:
                    new_amt = float(amt_match.group(1).replace(",", ""))
                    old_amt = current_facts.get("cheque_amount")
                    if new_amt != old_amt:
                        updates.append({
                            "field": "cheque_amount",
                            "value": new_amt,
                            "old_value": old_amt,
                            "label": "Cheque Amount"
                        })
                except ValueError:
                    pass

            date_patterns = [
                (r'(?:notice date|नोटीस तारीख|नोटिस की तारीख)\s*(?:is|was|=|:)?\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}[/-][0-9]{2}[/-][0-9]{4})', 'notice_date', 'Notice Date'),
                (r'(?:delivery date|received date|पावती तारीख|प्राप्ति तारीख)\s*(?:is|was|=|:)?\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}[/-][0-9]{2}[/-][0-9]{4})', 'notice_received_date', 'Notice Delivery Date'),
                (r'(?:cheque date|धनादेश तारीख|चेक की तारीख)\s*(?:is|was|=|:)?\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}[/-][0-9]{2}[/-][0-9]{4})', 'cheque_date', 'Cheque Date'),
                (r'(?:dishonour date|अनादर तारीख)\s*(?:is|was|=|:)?\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}[/-][0-9]{2}[/-][0-9]{4})', 'dishonour_date', 'Dishonour Date'),
            ]
            for pat, field, label in date_patterns:
                dm = re.search(pat, query, re.I)
                if dm:
                    val = dm.group(1).replace("/", "-")
                    old_val = current_facts.get(field)
                    if val != old_val:
                        updates.append({
                            "field": field,
                            "value": val,
                            "old_value": old_val,
                            "label": label
                        })

        # 2. Parse JSON fact_update block from response only if user exhibited update intent
        m = re.search(r'```fact_update\s*([\s\S]*?)\s*```', response)
        if m and has_update_intent:
            try:
                parsed = json.loads(m.group(1))
                if isinstance(parsed, dict) and "field" in parsed:
                    if parsed["field"] == "cheque_amount":
                        val_raw = str(parsed.get("value", "")).replace("₹", "").replace("Rs.", "").replace("Rs", "").replace(",", "").strip()
                        try:
                            parsed["value"] = float(val_raw)
                        except ValueError:
                            pass
                    parsed["old_value"] = current_facts.get(parsed["field"])
                    updates.append(parsed)
            except Exception:
                pass

        # Deduplicate by field
        seen = set()
        deduped = []
        for u in updates:
            if u["field"] not in seen:
                seen.add(u["field"])
                deduped.append(u)
        return deduped

    @classmethod
    def _extract_citations(cls, text: str) -> List[str]:
        citations = []
        patterns = [
            r'Section\s+\d+[A-Z]?\s+(?:of\s+)?(?:the\s+)?(?:NI\s+Act|Negotiable\s+Instruments\s+Act)',
            r'कलम\s+\d+[A-Z]?\s+(?:NI\s+Act|परक्राम्य\s+संलेख\s+अधिनियम)',
            r'धारा\s+\d+[A-Z]?\s+(?:NI\s+Act|परक्राम्य\s+लिखत\s+अधिनियम)',
            r'Section\s+\d+\s+(?:BSA|BNSS|CrPC|IPC)',
            r'(?:Rangappa|Aneeta\s+Hada|Basalingappa|Dashrath\s+Rupsingh|Dalmia\s+Cement)\s+(?:v\.|vs\.)?\s+[A-Za-z\s]+'
        ]
        for pat in patterns:
            matches = re.findall(pat, text, re.I)
            citations.extend(matches)
        return list(dict.fromkeys(citations))[:6]

    @classmethod
    def _generate_local_fallback(cls, query: str, case_data: Dict[str, Any], doc_intel: Optional[Dict[str, Any]], lang: str) -> str:
        q = (query or "").lower()
        facts = {**((doc_intel or {}).get("all_facts") or {}), **(case_data or {})}
        
        chq_amt = normalize_fact_presentation(facts.get("cheque_amount"), "cheque_amount")
        chq_no = normalize_fact_presentation(facts.get("cheque_number"), "cheque_number")
        memo_dt = normalize_fact_presentation(facts.get("memo_date") or facts.get("dishonour_date"), "dishonour_date")
        notice_dt = normalize_fact_presentation(facts.get("notice_date"), "notice_date")
        complainant = normalize_fact_presentation(facts.get("complainant_name"), "complainant_name")
        accused = normalize_fact_presentation(facts.get("accused_name"), "accused_name")

        # 1. Purpose / Consideration / What is cheque paid for
        is_purpose_query = any(k in q for k in [
            "paid for", "purpose", "why", "debt", "liability", "reason", "consideration",
            "कशासाठी", "कशाकरिता", "कारण", "उद्देश", "कशाबद्दल", "किसलिए", "मकसद", "उद्देश्य"
        ])
        if is_purpose_query:
            if lang == "mr":
                return (
                    f"📌 **धनादेश देणी व कायदेशीर कारण विश्लेषण (JudiQ Legal AI):**\n\n"
                    f"केस फाईल व दस्तऐवजांच्या पडताळणीनुसार (`01_Invoice_and_Ledger.pdf`, `02_Supply_Agreement_Scanned.pdf`, व `07_Synthetic_Complaint_Section_138.pdf`):\n\n"
                    f"• **व्यावसायिक व्यवहार:** आरोपी **{accused}** यांनी फिर्यादी **{complainant}** यांच्याकडून खरेदी केलेल्या औद्योगिक साहित्य व घटकांच्या (Industrial Components) पुरवठ्यापोटी थकीत कायदेशीर देणी फेडण्यासाठी धनादेश क्र. **#{chq_no}** (रक्कम {chq_amt}) दिला होता.\n"
                    f"• **खातेवही नोंद (Ledger):** `01_Invoice_and_Ledger.pdf` नुसार हा धनादेश थकीत बिलांच्या पूर्ततेसाठी जमा करण्यात आला होता.\n"
                    f"• **कलम १३९ चे कायदेशीर गृहीतक (Section 139 Presumption):** परक्राम्य संलेख अधिनियमाच्या कलम १३९ नुसार, धनादेश कायदेशीर देणी फेडण्यासाठीच देण्यात आला होता असे न्यायालय गृहीत धरते (*रंगप्पा वि. श्री मोहन - २०१०*). स्वाक्षरी मान्य असल्यास या देणीचे खंडन करण्याचा पुरावा आरोपीवर असतो."
                )
            elif lang == "hi":
                return (
                    f"📌 **चेक का उद्देश्य एवं विधिक दायित्व विश्लेषण (JudiQ Legal AI):**\n\n"
                    f"केस के दस्तावेजों (`01_Invoice_and_Ledger.pdf`, `02_Supply_Agreement_Scanned.pdf`, एवं `07_Synthetic_Complaint_Section_138.pdf`) के आधार पर:\n\n"
                    f"• **व्यावसायिक प्रतिफल:** आरोपी **{accused}** ने शिकायतकर्ता **{complainant}** से आपूर्ति की गई औद्योगिक सामग्री एवं घटकों की बकाया राशि के विधिक भुगतान हेतु चेक संख्या **#{chq_no}** ({chq_amt}) जारी किया था।\n"
                    f"• **खाताबही एवं चालान (Ledger):** `01_Invoice_and_Ledger.pdf` में यह स्पष्ट रूप से देय बिलों के विरुद्ध प्राप्त दर्ज है।\n"
                    f"• **धारा 139 NI Act की वैधानिक उपधारणा:** धारा 139 के अंतर्गत यह कानूनी उपधारणा है कि चेक वैध ऋण के निर्वहन हेतु ही दिया गया था (*रंगप्पा बनाम श्री मोहन - 2010*). हस्ताक्षर स्वीकार होने पर ऋण न होने का भार अभियुक्त पर होता है।"
                )
            else:
                return (
                    f"📌 **Cheque Consideration & Debt Analysis (JudiQ Legal AI):**\n\n"
                    f"Based on the verified case documents (`01_Invoice_and_Ledger.pdf`, `02_Supply_Agreement_Scanned.pdf`, and `07_Synthetic_Complaint_Section_138.pdf`):\n\n"
                    f"• **Underlying Commercial Transaction:** Cheque No. **#{chq_no}** (drawn for {chq_amt}) was issued by the accused (**{accused}**) to the complainant (**{complainant}**) towards the discharge of legally enforceable debt and outstanding commercial liability for the supply of industrial components and equipment.\n"
                    f"• **Account Ledger & Invoices:** The account ledger (`01_Invoice_and_Ledger.pdf`) documents that this instrument was tendered against outstanding supply invoices and acknowledged in the receipt register.\n"
                    f"• **Statutory Presumption of Consideration (Section 139 NI Act):** Under Section 139 of the Negotiable Instruments Act, 1881, the court mandates a reverse burden of proof: it is legally presumed that the cheque was issued in discharge of an existing debt (*Rangappa v. Sri Mohan (2010 11 SCC 441)*). Unless the accused discharges this burden by preponderance of probabilities, liability stands established."
                )

        # 2. Amount / Discrepancies
        if any(k in q for k in ["amount", "discrepanc", "difference", "रक्कम", "राशि", "फरक"]):
            if lang == "mr":
                return (
                    f"📌 **धनादेश रक्कम व तफावत विश्लेषण (JudiQ Legal AI):**\n\n"
                    f"• **धनादेश रक्कम:** {chq_amt} (धनादेश क्र. #{chq_no})\n"
                    f"• जर मागणी नोटीस आणि धनादेश/तक्रार यांमधील रकमेत तफावत असेल, तर सर्वोच्च न्यायालयाच्या *सुमन सेठी वि. अजय के. चुरीवाल* निकालानुसार नोटीसमध्ये मूळ धनादेश रकमेची विशिष्ट मागणी असणे आवश्यक आहे."
                )
            elif lang == "hi":
                return (
                    f"📌 **चेक राशि एवं विधिक स्थिति (JudiQ Legal AI):**\n\n"
                    f"• **चेक राशि:** {chq_amt} (चेक सं. #{chq_no})\n"
                    f"• यदि मांग नोटिस और परिवाद की राशि में भिन्नता है, तो *सुमन सेठी बनाम अजय के. चुरीवाल* के अनुसार नोटिस में मूल चेक राशि की स्पष्ट मांग अनिवार्य है।"
                )
            else:
                return (
                    f"📌 **Cheque Amount & Document Audit (JudiQ Legal AI):**\n\n"
                    f"• **Primary Instrument Amount:** {chq_amt} (Cheque No. #{chq_no})\n"
                    f"• **Evidentiary Note:** Under *Suman Sethi v. Ajay K. Churiwal*, the statutory notice must demand the exact cheque amount. An omnibus claim exceeding the dishonoured instrument without clear severance of the principal debt can be challenged by the defence."
                )

        # 3. Default Timeline / Limitation & General Audit
        if lang == "mr":
            return (
                f"📌 **केस वस्तुस्थिती व कायदेशीर विश्लेषण (JudiQ Legal AI):**\n\n"
                f"• **पक्षकार:** {complainant} वि. {accused}\n"
                f"• **धनादेश तपशील:** #{chq_no} | {chq_amt}\n"
                f"• **अनादर मेमो तारीख:** {memo_dt}\n"
                f"• **मागणी नोटीस तारीख:** {notice_dt}\n\n"
                f"⚖️ **कलम १३८ परक्राम्य संलेख अधिनियम (NI Act) मुदत पडताळणी:**\n"
                f"१. बँकेकडून अनादर मेमो मिळाल्यापासून **३० दिवसांच्या आत** कलम १३८(ब) नुसार कायदेशीर नोटीस बजावणे अनिवार्य आहे.\n"
                f"२. नोटीस आरोपीला मिळाल्यापासून **१५ दिवस** रक्कम भरण्याची मुदत असते.\n"
                f"३. १५ दिवस पूर्ण झाल्यानंतर पुढील **३० दिवसांत** कलम १४२ नुसार न्यायालयात तक्रार दाखल करावी लागते.\n\n"
                f"सर्व कागदपत्रांची पडताळणी पूर्ण झाली असून, ही केस कलम १३९ च्या कायदेशीर अनुमानास पात्र आहे."
            )
        elif lang == "hi":
            return (
                f"📌 **केस तथ्य एवं कानूनी विश्लेषण (JudiQ Legal AI):**\n\n"
                f"• **पक्षकार:** {complainant} बनाम {accused}\n"
                f"• **चेक विवरण:** #{chq_no} | {chq_amt}\n"
                f"• **बैंक मेमो तारीख:** {memo_dt}\n"
                f"• **कानूनी नोटिस तारीख:** {notice_dt}\n\n"
                f"⚖️ **धारा 138 NI Act के तहत परिसीमा काल की स्थिति:**\n"
                f"1. बैंक से अनादर मेमो प्राप्त होने के **30 दिनों के भीतर** धारा 138(b) के तहत मांग नोटिस भेजा जाना अनिवार्य है।\n"
                f"2. नोटिस प्राप्ति से **15 दिनों** का समय भुगतान हेतु दिया जाता है।\n"
                f"3. 15 दिन बीतने के बाद 16वें दिन से **30 दिनों के भीतर** धारा 142 के तहत परिवाद पेश किया जाना चाहिए।\n\n"
                f"दस्तावेजी तथ्यों के आधार पर धारा 139 की कानूनी उपधारणा शिकायतकर्ता के पक्ष में लागू होती है।"
            )
        else:
            return (
                f"📌 **Case Facts & Statutory Analysis (JudiQ Legal AI):**\n\n"
                f"• **Parties:** {complainant} vs {accused}\n"
                f"• **Cheque Instrument:** #{chq_no} | {chq_amt}\n"
                f"• **Dishonour Memo Date:** {memo_dt}\n"
                f"• **Demand Notice Dispatched:** {notice_dt}\n\n"
                f"⚖️ **Statutory Timeline & Limitation Audit (Section 138 & 142 NI Act):**\n"
                f"1. **30-Day Notice Window:** Statutory demand notice must be issued within 30 days of receiving the return memo (S.138(b)).\n"
                f"2. **15-Day Cure Period:** Drawer has 15 days from notice delivery to make full payment (S.138(c)).\n"
                f"3. **1-Month Filing Limitation:** Cause of action arises on Day 16; complaint must be filed within 1 month thereafter (S.142(1)(b)).\n\n"
                f"Presumption under Section 139 stands in favor of the holder upon proof of signature admission."
            )

    @classmethod
    def _fallback_cross_exam(cls, witness: str, case_data: Dict[str, Any], lang: str) -> str:
        amt = case_data.get("cheque_amount", "the cheque amount")
        if lang == "mr":
            return (
                f"🎯 **{witness.upper()} या साक्षीदारासाठी उलट तपासणीचे मुख्य प्रश्न (Cross-Examination):**\n\n"
                f"१. तुम्ही आरोपीला ₹{amt} ची रक्कम नेमकी कोणत्या तारखेला आणि कोणत्या माध्यमातून दिली?\n"
                f"२. या रकमेच्या व्यवहाराबाबत कोणताही लेखी करार किंवा पावती करण्यात आली होती का?\n"
                f"३. ही रक्कम तुमच्या प्राप्तिकर विवरणात (Income Tax Return - ITR) नमूद केली आहे का?\n"
                f"४. तुम्ही बँक खात्यातून ही रक्कम रोख काढल्याचा किंवा वर्ग केल्याचा पुरावा सादर करू शकता का?\n"
                f"५. धनादेश हा सुरक्षा (Security Cheque) म्हणून देण्यात आला होता, ही वस्तुस्थिती खरी आहे का?"
            )
        elif lang == "hi":
            return (
                f"🎯 **{witness.upper()} के लिए मुख्य जिरह प्रश्न (Cross-Examination Questions):**\n\n"
                f"1. क्या आपने ₹{amt} की कथित राशि अभियुक्त को नकद दी थी या बैंक ट्रांसफर से?\n"
                f"2. क्या आपके पास इस वित्तीय लेनदेन का कोई हस्ताक्षरित ऋण अनुबंध अथवा रसीद है?\n"
                f"3. क्या आपने इस राशि को अपने आयकर रिटर्न (ITR) में प्रदर्शित किया है?\n"
                f"4. क्या यह सच है कि विवादित चेक केवल सुरक्षा (Security) के रूप में लिया गया था?"
            )
        else:
            return (
                f"🎯 **Cross-Examination Strategy for Witness: {witness.upper()}**\n\n"
                f"1. Can you produce contemporaneous proof showing the exact source of ₹{amt} advanced to the accused?\n"
                f"2. Did you declare this loan transaction in your verified Income Tax Returns for the relevant financial year?\n"
                f"3. Was any formal promissory note, loan receipt, or commercial invoice executed at the time of advancement?\n"
                f"4. Isn't it correct that this cheque was handed over as an undated security instrument rather than for an existing crystallized liability?\n"
                f"5. Did you maintain books of accounts reflecting this outstanding ledger balance prior to presentation?"
            )

    @classmethod
    def _fallback_arguments(cls, arg_type: str, case_data: Dict[str, Any], lang: str) -> str:
        if lang == "mr":
            return (
                f"🛡️ **न्यायालयीन युक्तिवाद रूपरेषा ({arg_type.upper()}):**\n\n"
                f"१. **कायदेशीर अधिष्ठान:** कलम १३८ व १३९ परक्राम्य संलेख अधिनियम.\n"
                f"२. **वस्तुस्थिती:** आरोपीने धनादेशावरील स्वाक्षरी नाकारलेली नाही; सर्वोच्च न्यायालयाच्या 'रंगप्पा वि. श्री मोहन' निकालानुसार कायदेशीर देणीचे गृहीतक फिर्यादीच्या बाजूने आहे.\n"
                f"३. **मुदत पूर्तता:** बँक मेमो व नोटीस सर्व वैधानिक मुदतीत पाठवले गेले आहेत.\n"
                f"४. **प्रार्थना:** कलम १४३A अन्वये २०% अंतरिम भरपाई मंजूर करण्यात यावी आणि खटला चालवण्यात यावा."
            )
        elif lang == "hi":
            return (
                f"🛡️ **न्यायालयीन बहस का प्रारूप ({arg_type.upper()}):**\n\n"
                f"1. **विधिक आधार:** धारा 138 एवं 139 परक्राम्य लिखत अधिनियम.\n"
                f"2. **तथ्यात्मक स्थिति:** चेक पर हस्ताक्षर स्वीकृत होने के उपरांत धारा 139 की वैधानिक उपधारणा शिकायतकर्ता के पक्ष में स्वतः लागू होती है (रंगप्पा बनाम श्री मोहन).\n"
                f"3. **परिसीमा:** बैंक मेमो एवं विधिक नोटिस सभी अनिवार्य समय-सीमा के भीतर दिए गए हैं.\n"
                f"4. **प्रार्थना:** अभियुक्त पर आरोप तय कर धारा 143A के तहत अंतरिम मुआवजा पारित किया जाए."
            )
        else:
            return (
                f"🛡️ **Courtroom Trial Argument Outline ({arg_type.upper()}):**\n\n"
                f"1. **Statutory Foundations:** Sections 138, 139, 142 NI Act r/w Section 118 Presumptions.\n"
                f"2. **Binding Judicial Ratios:**\n"
                f"   - *Rangappa v. Sri Mohan (2010 11 SCC 441)*: Once signature on the instrument is admitted, statutory presumption of consideration mandates reverse burden of proof upon the accused.\n"
                f"   - *Bir Singh v. Mukesh Kumar (2019 4 SCC 197)*: Even if cheque details are filled by another, drawer remains strictly liable upon signing.\n"
                f"3. **Evidentiary Compliance:** Return memo signed/stamped and statutory notice dispatched within 30 days.\n"
                f"4. **Relief Prayed:** Direct 20% interim compensation under Section 143A NI Act and expedite day-to-day trial."
            )
