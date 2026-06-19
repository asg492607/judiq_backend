import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# ── Risk catalogue ─────────────────────────────────────────────────────────────
RISK_CATALOGUE = [
    {
        "concept_trigger": "security_cheque",
        "risk": "Security Cheque Defense (S.138)",
        "severity": "CRITICAL",
        "description": "Accused alleges the instrument was handed over as security for an unliquidated future liability, not for a present debt.",
        "rebuttal": "Counter via S.139 presumption. Per 'Sampelly Satyanarayana Rao v. Indian Renewable Energy Development Agency Ltd (2016) 10 SCC 458', a post-dated cheque for a loan installment is a valid S.138 instrument. Burden is on accused to show no debt existed on date of presentation.",
        "case_law": "Sampelly Satyanarayana Rao (2016)"
    },
    {
        "concept_trigger": "stop_payment",
        "risk": "Stop Payment Instruction Strategy",
        "severity": "HIGH",
        "description": "Accused claims they instructed the bank to 'Stop Payment' for valid reasons (e.g., breach of contract), seeking to bypass S.138.",
        "rebuttal": "Per 'Laxmi Dyechem v. State of Gujarat (2012) 13 SCC 375', Section 138 is attracted even for 'Stop Payment' if there are insufficient funds or if no valid justification is proven. Burden remains on accused to prove debt was not due.",
        "case_law": "Laxmi Dyechem (2012)"
    },
    {
        "concept_trigger": "account_closed",
        "risk": "Account Closed Tactic",
        "severity": "CRITICAL",
        "description": "The cheque was returned because the account was closed prior to presentation.",
        "rebuttal": "Per 'NEPC Micon Ltd. v. Magma Leasing Ltd. (1999) 4 SCC 253', closing an account is equivalent to 'insufficient funds' if the debt was pending. S.138 applies fully.",
        "case_law": "NEPC Micon Ltd. (1999)"
    },
    {
        "concept_trigger": "notice_defect",
        "pillar_trigger": "notice_sent",
        "risk": "Statutory Notice Lapse (S.138b)",
        "severity": "FATAL",
        "description": "Notice must be sent within 30 days of memo receipt. Failure is a non-curable jurisdictional defect.",
        "rebuttal": "If within time: Dispatch immediately. If time has elapsed: Criminal prosecution is barred; evaluate Civil Suit for Recovery (Order 37 CPC) which has a 3-year limitation.",
        "case_law": "Central Bank of India v. Saxons Farms (1999)"
    },
    {
        "concept_trigger": "material_alteration",
        "risk": "The 'Material Alteration' Attack (S.87 Void Cheque)",
        "severity": "FATAL",
        "description": "Enemy tactic: Accused claims the date/amount was filled later or handwriting differs. Under Section 87 of the NI Act, a materially altered cheque without consent is void.",
        "rebuttal": "Ensure the cheque was handed over with consent to fill in details (S.20 Inchoate Instrument). Use S.45 Evidence Act handwriting expert if accused alleges forgery of the signature.",
        "case_law": "Section 87 NI Act / Loonkaran Sethia v. Ivan E. John"
    },
    {
        "concept_trigger": "defective_goods",
        "risk": "The 'Civil Dispute' Camouflage",
        "severity": "HIGH",
        "description": "Enemy tactic: Accused produces emails complaining about goods/services prior to cheque presentation. Argues debt was for a lesser amount, making the demand notice excessive and invalid.",
        "rebuttal": "Produce delivery challans and acceptance emails. Show that the cheque was issued unconditionally post-delivery.",
        "case_law": "Dashrathbhai Trikambhai Patel vs. Hitesh Mahendrabhai Patel (2022)"
    },
    {
        "concept_trigger": "directors_named",
        "pillar_trigger": "directors_named",
        "risk": "Vicarious Liability Defect (S.141)",
        "severity": "CRITICAL",
        "description": "For corporate accused, failure to specifically name and aver the exact role of directors is fatal per Aneeta Hada (2012).",
        "rebuttal": "Ensure the complaint contains specific averments that the named directors were 'in charge of and responsible for the conduct of business' with their exact roles described.",
        "case_law": "Aneeta Hada v. Godfather Travels (2012)"
    },
    {
        "concept_trigger": "unauthorized_complainant",
        "risk": "The 'Authorization' Technical Knockout",
        "severity": "FATAL",
        "description": "Enemy tactic: Challenging the complainant's Board Resolution. If the signer isn't exactly named, or resolution wasn't passed before the notice, case dismissed on day one.",
        "rebuttal": "Ensure a Board Resolution authorizing the exact individual was passed BEFORE the legal notice was sent. Annex original resolution.",
        "case_law": "A.C. Narayanan vs. State of Maharashtra"
    },
    {
        "concept_trigger": "digital_evidence",
        "risk": "The Digital Evidence 'Death Trap' (BSA Section 63)",
        "severity": "HIGH",
        "description": "WhatsApp/Email records are inadmissible without a mandatory certificate under Section 63(4) of the Bharatiya Sakshya Adhiniyam (BSA) (replacing old 65B).",
        "rebuttal": "The certificate is a condition precedent for admissibility. Prepare the Section 63 BSA certificate signed by the person in control of the device at the time of filing, otherwise the court may reject this evidence entirely.",
        "case_law": "BSA Section 63(4) Compliance"
    },
    {
        "concept_trigger": "interim_compensation",
        "risk": "Interim Compensation Opportunity (S.143A)",
        "severity": "MEDIUM",
        "description": "Section 143A allows the court to order the accused to pay up to 20% of the cheque amount as interim compensation.",
        "rebuttal": "Proactively file an application under S.143A at the time of framing of notice/charge. This exerts financial pressure and incentivizes settlement.",
        "case_law": "L.G.R. Enterprises v. P.V. Ramakrishna (2019)"
    },
    {
        "concept_trigger": "financial_capacity_risk",
        "risk": "The 'Financial Capacity' Challenge",
        "severity": "HIGH",
        "description": "Accused challenges the complainant's ability/means to lend the alleged high-value cash amount (₹5 Lakhs+).",
        "rebuttal": "Counter by showing specific source of funds (bank withdrawal receipts, or ITR). Per 'Sushil Kumar v. Sandeep Kumar (2026)', failing to show a source of income allows the accused to successfully rebut the legal presumption of debt.",
        "case_law": "Sushil Kumar v. Sandeep Kumar (2026) / Basalingappa (2019)"
    }
]


# Mapping from score → prediction (Cynical Advocate Tuning)
OUTCOME_MAP = [
    (88, "High Probability of Conviction",      "Exceptional documentary trail. Presumptions are nearly impossible to rebut. Subject to trial technicalities."),
    (75, "Likely Conviction (Trial Risk)",       "Strong pillars, but 'reasonable doubt' remains a tactical weapon for the defense. Successful cross-examination is vital."),
    (60, "Contested Case — 50/50 Outcome",       "Case survives prima facie, but financial capacity or notice technicalities present significant acquittal risks."),
    (45, "High Risk of Acquittal",               "Defense will likely rebut presumptions. Procedural gaps provide multiple 'escape routes' for the accused."),
    ( 0, "Non-Maintainable / Fatal Defects",     "Complaint is procedurally or substantively DOA. Expect dismissal at pre-summoning or discharge stage."),
]

TRANSLATIONS = {
    "hindi": {
        "STRONG":   "मजबूत मामला — अभियोजन संभावित (Strong Case)",
        "MODERATE": "मध्यम मामला — सुधार आवश्यक (Moderate Case)",
        "WEAK":     "कमजोर मामला — वैकल्पिक विकल्प देखें (Weak Case)"
    },
    "marathi": {
        "STRONG":   "भक्कम प्रकरण — खटला फायदेशीर (Strong Case)",
        "MODERATE": "मध्यम प्रकरण — पुरावा बळकट करा (Moderate Case)",
        "WEAK":     "कमकुवत प्रकरण — नागरी दाखल विचारात घ्या (Weak Case)"
    },
    "gujarati": {
        "STRONG":   "મજબૂત કેસ — ફોજદારી ફરિયાદ ફાઈલ કરો",
        "MODERATE": "મધ્યમ કેસ — પુરાવા મજબૂત કરો",
        "WEAK":     "નબળો કેસ — સમાધાન ધ્યાનમાં લો"
    }
}


class DecisionSupportEngine:
    """
    Decision-Support Layer:
    ─ Risk identification with AI-driven rebuttals
    ─ Outcome probability prediction
    ─ Multilingual verdict translation
    ─ Evidence gap suggestions
    """

    @staticmethod
    def identify_risks_and_rebuttals(concepts: List[Dict], case_data: Dict) -> List[Dict]:
        concept_names = {c["concept"] for c in concepts}
        risks: List[Dict] = []
        seen_risks: set = set()

        for rule in RISK_CATALOGUE:
            concept_trigger = rule.get("concept_trigger")
            pillar_trigger  = rule.get("pillar_trigger")
            risk_key        = rule["risk"]

            if risk_key in seen_risks:
                continue

            fired = False

            # Fire if the semantic engine detected the concept
            if concept_trigger and concept_trigger in concept_names:
                fired = True

            # Fire if a boolean pillar is false (for structural risks)
            if pillar_trigger and not case_data.get(pillar_trigger, True):
                # Special case: corporate vicarious liability
                if pillar_trigger == "directors_named":
                    accused_type = case_data.get("accused_type", "Individual")
                    if accused_type in ("Pvt Ltd/Ltd Company", "Company", "Partnership Firm"):
                        fired = True
                else:
                    fired = True

            if fired:
                seen_risks.add(risk_key)
                risks.append({
                    "risk":        risk_key,
                    "severity":    rule["severity"],
                    "description": rule["description"],
                    "rebuttal":    rule["rebuttal"],
                    "case_law":    rule.get("case_law", "")
                })

        # Sort: FATAL → CRITICAL → HIGH → MEDIUM
        order = {"FATAL": 0, "CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}
        risks.sort(key=lambda r: order.get(r["severity"], 99))

        # Hard-coded strategy triggers based on case data (Institutional Hardening)
        risks.append({
            "risk": "Procedural Veracity Protocol",
            "severity": "LOW",
            "description": "Any mismatch between alleged precedents and official records can lead to professional misconduct proceedings.",
            "rebuttal": "Verify every citation against official gazettes or reporters (SCC/AIR) before submission.",
            "case_law": "Bar Council of India Standards"
        })
        
        risks.append({
            "risk": "Boilerplate Pleading Scrutiny",
            "severity": "LOW",
            "description": "Courts are increasingly rejecting e-filed complaints that lack specific transactional details or appear mass-produced.",
            "rebuttal": "Ensure the final draft contains unique transactional facts that demonstrate application of mind.",
            "case_law": "Judicial Protocol 2026"
        })

        if case_data.get("communication_records"):
            risks.append({
                "risk": "BSA Section 63 Admissibility",
                "severity": "HIGH",
                "description": "Electronic records require a strict chain of custody certificate under the new Bharatiya Sakshya Adhiniyam.",
                "rebuttal": "Prepare the mandatory S.63(4) certificate identifying the device and the person in control at the time of retrieval.",
                "case_law": "BSA Section 63(4) Compliance"
            })
        
        if case_data.get("amount", 0) >= 50000:
            risks.append({
                "risk": "Section 143A Discretionary Bar",
                "severity": "MEDIUM",
                "description": "Interim compensation is not an automatic right; it requires a showing of financial necessity or prima facie strength.",
                "rebuttal": "File a separate application u/s 143A detailing the financial impact on the complainant.",
                "case_law": "S.143A Discretionary Guidelines"
            })

        return risks

    @staticmethod
    def predict_outcome(final_score: float) -> Dict[str, Any]:
        for threshold, prediction, rationale in OUTCOME_MAP:
            if final_score >= threshold:
                return {
                    "prediction":  prediction,
                    "probability": f"{round(final_score, 1)}%",
                    "rationale":   rationale,
                    "score_band":  (
                        "STRONG"   if final_score >= 70 else
                        "MODERATE" if final_score >= 45 else
                        "WEAK"
                    )
                }
        return {
            "prediction": "Unable to Determine",
            "probability": "0%",
            "rationale": "Insufficient data to assess outcome.",
            "score_band": "WEAK"
        }

    @staticmethod
    def translate_verdict(verdict: str, target_lang: str = "hindi") -> str:
        lang_map = TRANSLATIONS.get(target_lang.lower(), TRANSLATIONS["hindi"])
        return lang_map.get(verdict.upper(), verdict)

    @staticmethod
    def suggest_evidence_gaps(case_data: Dict) -> List[str]:
        suggestions: List[str] = []
        if not case_data.get("debt_proven"):
            suggestions += [
                "WhatsApp/Email correspondence where accused acknowledges the debt (Requires Section 63(4) BSA Certificate)",
                "Bank transfer records or UPI transaction receipts for the original loan disbursement",
                "Ledger account entries / Tally printout showing receivable",
                "Promissory note or acknowledgement of debt signed by accused",
                "SMS logs discussing repayment timeline or outstanding balance",
            ]
        
        if case_data.get("communication_records"):
            suggestions += [
                "Mandatory: Prepare Section 63(4) BSA Certificate for WhatsApp/Email printouts (Replacing old 65B)",
                "Ensure digital records show a clear admission of liability or acknowledgment of the specific cheque",
            ]
        if not case_data.get("notice_sent"):
            suggestions += [
                "Draft and dispatch demand notice via Registered Post AD within 30 days of dishonour memo",
                "BEWARE 'Notice of Service Ghost': Ensure the A.D. card has the accused's actual signature, and tracking report clearly shows 'Item Delivered' to the correct person.",
            ]
        if case_data.get("accused_type") in ("Pvt Ltd/Ltd Company", "Company", "Partnership Firm") \
                and not case_data.get("directors_named"):
            suggestions += [
                "Obtain Memorandum of Association / Partnership Deed to identify directors/partners",
                "Name all directors in charge of business in the complaint with specific averments",
            ]
        if not case_data.get("dishonour_memo"):
            suggestions += [
                "Obtain certified copy of the dishonour memo from the presenting bank immediately",
                "Ensure the memo clearly states the reason for dishonour (e.g., 'Insufficient Funds')",
            ]
        return suggestions
