from typing import Dict, List, Any
import json
import os
from adversarial_engine import AdversarialEngine

class CriminalAdversarialEngine(AdversarialEngine):
    """
    Simulates defense vs prosecution dynamics, evaluates procedural contradictions,
    Bhajan Lal quashing grounds, and generates trial cross-examination strategies
    across all domains of Indian criminal law.
    """

    PROCEDURAL_STAGES = [
        {"id": "bail", "name": "Bail Hearing (S.437/439 CrPC / S.480/483 BNSS)", "baseline_prob": 0.65},
        {"id": "cognizance", "name": "Cognizance/Summoning (S.190 CrPC / S.210 BNSS)", "baseline_prob": 0.85},
        {"id": "charge", "name": "Argument on Charge (Discharge u/s 227/239 CrPC / 250/262 BNSS)", "baseline_prob": 0.70},
        {"id": "chief", "name": "Prosecution Evidence (Chief Examination of Witnesses)", "baseline_prob": 0.80},
        {"id": "cross", "name": "Cross-Examination of I.O. & Key Witnesses", "baseline_prob": 0.40},
        {"id": "s313", "name": "Statement of Accused (S.313 CrPC / S.351 BNSS)", "baseline_prob": 0.90},
        {"id": "defense", "name": "Defense Evidence (S.233/243 CrPC / S.256/266 BNSS)", "baseline_prob": 0.60},
        {"id": "final", "name": "Final Arguments & Judgment", "baseline_prob": 0.50}
    ]

    VULNERABILITY_MODELS = {
        "FINANCIAL_FRAUD": {
            "name": "Cheating & Financial Fraud (S.420/406 IPC ↔ S.318/316 BNS)",
            "severity": "CRITICAL",
            "risk": "Civil dispute or breach of contract disguised as criminal offense without dishonest intention at inception.",
            "chain": [
                "1. Defence establishes existing commercial contract and partial performance.",
                "2. Demonstrates lack of fraudulent intent at the inception of transaction.",
                "3. Proceedings quashed u/s 482 CrPC / S.528 BNSS per Hridaya Ranjan Prasad Verma."
            ],
            "rebuttal_tree": {
                "defence_evidence": "Written agreement, bank transaction logs, email negotiations, notice replies.",
                "prosecution_counter": "Allege forged documents or deceptive representations made prior to funds release.",
                "burden_shift_effect": "Burden remains heavily on prosecution to prove mens rea at the very threshold."
            },
            "cross_exam_questions": [
                "Is it not true that the transaction between the parties was governed by a written commercial agreement?",
                "Did the accused not perform part of the contractual obligations prior to any dispute arising?",
                "Did you issue any civil demand notice or file a summary suit for recovery before lodging this FIR?",
                "Can you show a single document proving that the accused had fraudulent intentions on Day 1?"
            ],
            "quashing_ground": "Bhajan Lal Parameter 1 & 7 (Pure Civil Dispute Clothed with Criminal Color)",
            "probability_collapse": 0.85
        },
        "MATRIMONIAL": {
            "name": "Matrimonial Cruelty & Dowry (S.498A/304B IPC ↔ S.85/80 BNS)",
            "severity": "HIGH",
            "risk": "Omnibus allegations against husband's relatives residing separately or roped in without specific overt acts.",
            "chain": [
                "1. Defence produces proof of separate residence and independent living.",
                "2. Highlights absence of specific dates, times, or distinct roles attributed to in-laws.",
                "3. High Court strikes down proceedings against extended family per Kahkashan Kausar (2022)."
            ],
            "rebuttal_tree": {
                "defence_evidence": "Rent agreements, utility bills showing separate residence, CCTV, flight logs.",
                "prosecution_counter": "Allege continuous conspiracy and collective demand of stridhan/dowry.",
                "burden_shift_effect": "Court strictly deprecates implicating entire family without individual overt acts."
            },
            "cross_exam_questions": [
                "Is it correct that the co-accused in-laws reside in a separate city/dwelling from the matrimonial home?",
                "Can you specify any particular date and time when each individual relative demanded dowry?",
                "Did you make any contemporaneous police complaint regarding harassment prior to the marital breakdown?",
                "Were the alleged articles of stridhan listed with specific inventory at the time of marriage?"
            ],
            "quashing_ground": "Bhajan Lal Parameter 7 (Malicious Prosecution & Omnibus Impleadment)",
            "probability_collapse": 0.80
        },
        "HOMICIDE_BODILY": {
            "name": "Bodily Offences / Murder vs Sudden Quarrel (S.302/307 IPC ↔ S.103/109 BNS)",
            "severity": "FATAL",
            "risk": "Sudden fight without premeditation or grave provocation reducing murder to S.304 Culpable Homicide.",
            "chain": [
                "1. Defence establishes absence of premeditation, sudden quarrel in heat of passion (Exception 4 to S.300).",
                "2. Highlights ocular vs post-mortem medical inconsistencies.",
                "3. Charge downgraded or benefit of doubt given on failure of chain of circumstantial evidence."
            ],
            "rebuttal_tree": {
                "defence_evidence": "Post-mortem report, sudden provocation evidence, cross-examination of doctor.",
                "prosecution_counter": "Rely on weapon recovery u/s 27 and eyewitness statements.",
                "burden_shift_effect": "Doctor's testimony on nature of weapon and single blow can disprove premeditation."
            },
            "cross_exam_questions": [
                "Did the incident occur spontaneously during a sudden heated verbal altercation without prior enmity?",
                "Doctor, is it not possible that the fatal injury could be caused by an accidental fall on a blunt surface?",
                "Was there any independent non-interested eyewitness present at the scene of occurrence?",
                "Was the weapon of offence recovered from an open area accessible to the general public?"
            ],
            "quashing_ground": "Trial defense: S.300 Exception 4 downgrade & ocular-medical divergence",
            "probability_collapse": 0.60
        },
        "SEXUAL_OFFENSES": {
            "name": "Sexual Offences / Consent vs Breach of Promise (S.376 IPC ↔ S.64/69 BNS)",
            "severity": "CRITICAL",
            "risk": "Consensual relationship during courtship where marriage failed due to subsequent circumstances.",
            "chain": [
                "1. Defence places contemporaneous WhatsApp chats, hotel check-ins, and travel tickets on record.",
                "2. Demonstrates genuine courtship without fraudulent intent at inception.",
                "3. Quashed by High Court per Pramod Suryabhan Pawar & Sonu @ Subhash Kumar."
            ],
            "rebuttal_tree": {
                "defence_evidence": "Digital chat logs, mutual gifts, proof of marriage efforts.",
                "prosecution_counter": "Allege false promise made by an already married or deceitful person.",
                "burden_shift_effect": "Consent of adult woman cannot be vitiated by subsequent failure of courtship."
            },
            "cross_exam_questions": [
                "Is it true that the relationship continued consensually over several months/years without any coercion?",
                "Did the accused introduce you to his/her family with an initial genuine intention to marry?",
                "Were the digital chats and photographs produced exchanged voluntarily between the parties?",
                "Was any complaint made to authorities immediately following the first alleged physical intimacy?"
            ],
            "quashing_ground": "Pramod Suryabhan Pawar Paradigm (Consensual Relationship is not Rape)",
            "probability_collapse": 0.85
        },
        "NDPS_OFFENSES": {
            "name": "NDPS Act Offenses (S.50 / S.42 / S.52A Protocols)",
            "severity": "FATAL",
            "risk": "Non-compliance with mandatory statutory search protocols under Section 50 or improper sampling under S.52A.",
            "chain": [
                "1. Defence establishes body search was conducted without informing right to Gazetted Officer/Magistrate.",
                "2. Proves samples were drawn at spot rather than before Judicial Magistrate u/s 52A.",
                "3. Entire recovery vitiated and trial collapses per Vijaysinh Jadeja & Simarnjit Singh."
            ],
            "rebuttal_tree": {
                "defence_evidence": "Seizure memo, search memo, lack of Magistrate inventory order.",
                "prosecution_counter": "Claim recovery was from vehicle/bag (S.43) rather than personal clothing.",
                "burden_shift_effect": "Strict compliance with NDPS procedural safeguards is mandatory; any defect favors accused."
            },
            "cross_exam_questions": [
                "Did you give written option to the accused to be searched before a Gazetted Officer or Magistrate?",
                "Were the representative samples drawn in the physical presence of a Judicial Magistrate under Section 52A?",
                "Were any independent public witnesses from the locality joined during the search and seizure?",
                "What was the exact delay between the seizure and the deposit of the contraband in the Malkhana?"
            ],
            "quashing_ground": "Vijaysinh Jadeja & Mangilal Precedents (Section 50 & 52A NDPS Fatal Lapses)",
            "probability_collapse": 0.90
        },
        "CORRUPTION_PMLA": {
            "name": "Corruption (PC Act) & Money Laundering (PMLA)",
            "severity": "CRITICAL",
            "risk": "Lack of mandatory prior sanction under S.17A/19 PC Act or prolonged incarceration overriding S.45 PMLA.",
            "chain": [
                "1. Defence asserts absence of statutory S.17A prior approval or S.19 sanction for prosecution.",
                "2. For PMLA, urges Article 21 right to speedy trial and long custody per Manish Sisodia (2024).",
                "3. Bail or discharge granted."
            ],
            "rebuttal_tree": {
                "defence_evidence": "Official approval records, trail of predicate offense, custody certificates.",
                "prosecution_counter": "Rely on Section 45 PMLA twin conditions and proceeds of crime tracing.",
                "burden_shift_effect": "Prolonged incarceration without trial commencement overrides twin conditions."
            },
            "cross_exam_questions": [
                "Was prior approval under Section 17A of the PC Act obtained from the competent authority before inquiry?",
                "Did the predicate / scheduled offense result in acquittal or discharge of the accused?",
                "Is there direct forensic evidence of demand, acceptance, and recovery of illegal gratification?",
                "How many witnesses remain to be examined out of the total chargesheeted witnesses?"
            ],
            "quashing_ground": "Want of Section 17A/19 Sanction & Sisodia Article 21 Bail Doctrine",
            "probability_collapse": 0.75
        }
    }

    @classmethod
    def calculate_stage_survivability(cls, severity_score: int, adversarial_risk: float) -> List[Dict[str, Any]]:
        roadmap = []
        current_risk_multiplier = 1.0 - (adversarial_risk * 0.4)
        for stage in cls.PROCEDURAL_STAGES:
            prob = stage["baseline_prob"] * (severity_score / 100.0) * current_risk_multiplier
            if stage["id"] == "cross":
                prob *= 0.65
            roadmap.append({
                "stage": stage["name"],
                "probability": f"{int(max(5, min(95, prob * 100)))}%",
                "status": "Vulnerable" if prob < 0.40 else ("Stable" if prob > 0.65 else "Caution"),
                "risk_factor": "Cross-exam contradiction" if stage["id"] == "cross" else "Procedural/Evidentiary scrutiny"
            })
            current_risk_multiplier *= 0.95
        return roadmap

    @classmethod
    def detect_contradictions(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        contradictions = []
        offense_type = str(case_data.get("offense_type", "")).upper()

        if case_data.get("fir_delay_unexplained"):
            contradictions.append({
                "severity": "Material Credibility Risk",
                "issue": "Unexplained FIR Delay",
                "detail": "Unexplained delay in lodging FIR gives rise to suspicion of deliberation and concoction (Thulia Kali v. State of TN).",
                "remediation": "Cross-examine informant on consultation with police prior to formal statement.",
                "penalty": -30
            })

        if case_data.get("electronic_evidence") and not case_data.get("s65b_certificate"):
            contradictions.append({
                "severity": "Fatal Procedural Defect",
                "issue": "Missing S.65B IEA / S.63 BSA Certificate",
                "detail": "Digital chats, audio recordings, or CCTV footage without statutory certificate are inadmissible per Arjun Panditrao.",
                "remediation": "Object to exhibit marking of electronic evidence during witness examination.",
                "penalty": -45
            })

        if any(x in offense_type for x in ["420", "406", "318", "316"]) and case_data.get("contract_exists"):
            contradictions.append({
                "severity": "Strategic Contradiction",
                "issue": "Civil Dispute Clothed with Criminal Offense",
                "detail": "Transaction arose out of a commercial contract with partial performance, refuting fraudulent intent at inception.",
                "remediation": "File Section 482 CrPC / Section 528 BNSS quashing petition citing Hridaya Ranjan Prasad Verma.",
                "penalty": -40
            })

        if case_data.get("witness_statements_inconsistent") or case_data.get("s161_s164_contradiction"):
            contradictions.append({
                "severity": "Material Ocular Contradiction",
                "issue": "Section 161 vs Section 164 Statement Discrepancies",
                "detail": "Glaring improvements and contradictions between initial police statement and Magistrate deposition.",
                "remediation": "Confront witness under Section 145 Evidence Act / Section 148 BSA.",
                "penalty": -35
            })

        if case_data.get("medical_contradicts_ocular"):
            contradictions.append({
                "severity": "Fatal Evidentiary Contradiction",
                "issue": "Medical vs Ocular Divergence",
                "detail": "Post-mortem / injury report directly contradicts the weapon or assault narrative described by eyewitnesses (Thaman Kumar v. State of UT Chandigarh).",
                "remediation": "Confront prosecution ocular witnesses and lead defence medical expert testimony.",
                "penalty": -40
            })

        return contradictions

    @classmethod
    def evaluate_bhajan_lal_grounds(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluates the 7 landmark quashing parameters laid down by the Supreme Court in
        State of Haryana v. Bhajan Lal (1992 Supp (1) SCC 335).
        """
        grounds = []
        offense_type = str(case_data.get("offense_type", "")).upper()
        description = str(case_data.get("description", "")).lower()

        # Parameter 1 & 7: Civil dispute disguised as criminal
        if any(x in offense_type for x in ["420", "406", "318", "316", "CHEATING", "FRAUD"]) and case_data.get("contract_exists"):
            grounds.append({
                "parameter": "Bhajan Lal Parameter 1 & 7 (Civil Dispute Disguised as Criminal)",
                "viability": "VERY HIGH",
                "rationale": "Allegations relate exclusively to breach of contract or commercial debt without fraudulent intent at inception.",
                "precedent": "State of Haryana v. Bhajan Lal; Dalip Kaur v. Jagnar Singh (2009)"
            })

        # Parameter 3: Absurd or inherently improbable allegations
        if case_data.get("inherently_improbable") or "absurd" in description:
            grounds.append({
                "parameter": "Bhajan Lal Parameter 3 (Inherently Improbable Allegations)",
                "viability": "HIGH",
                "rationale": "Allegations are so absurd and inherently improbable that no prudent person can ever reach a conclusion of sufficient grounds.",
                "precedent": "State of Haryana v. Bhajan Lal"
            })

        # Parameter 6: Express statutory bar (Want of Sanction u/s 197 / S.468 Limitation)
        if case_data.get("is_public_servant") and not case_data.get("sanction_obtained"):
            grounds.append({
                "parameter": "Bhajan Lal Parameter 6 (Express Statutory Bar - Want of Sanction)",
                "viability": "VERY HIGH",
                "rationale": "Proceeding barred for lack of mandatory sanction u/s 197 CrPC / 218 BNSS.",
                "precedent": "D. Devaraja v. Owais Sabeer Hussain; Anil Kumar v. M.K. Aiyappa"
            })

        # Parameter 7: Matrimonial Omnibus allegations
        if any(x in offense_type for x in ["498A", "85", "DOWRY"]) and (case_data.get("relative_impleaded") or case_data.get("separate_residence")):
            grounds.append({
                "parameter": "Bhajan Lal Parameter 7 (Malicious Prosecution / Vexatious Omnibus Claims)",
                "viability": "HIGH",
                "rationale": "Omnibus allegations against distant relatives without specific overt acts or dates.",
                "precedent": "Geeta Mehrotra v. State of UP; Kahkashan Kausar v. State of Bihar (2022)"
            })

        # Consensual relationship false promise
        if any(x in offense_type for x in ["376", "64", "69"]) and case_data.get("consensual_relationship"):
            grounds.append({
                "parameter": "Bhajan Lal Parameter 1 (Consensual Relationship is Not Rape)",
                "viability": "VERY HIGH",
                "rationale": "Breach of promise to marry during courtship does not constitute rape under S.375/376.",
                "precedent": "Pramod Suryabhan Pawar v. State of Maharashtra; Sonu @ Subhash Kumar"
            })

        return grounds

    @classmethod
    def simulate_strategic_stress_test(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        analysis_nodes = []
        offense_type = str(case_data.get("offense_type", "")).upper()

        # Match relevant vulnerability model
        matched_model = None
        if any(x in offense_type for x in ["420", "406", "318", "316", "CHEATING", "FRAUD", "FORGERY", "467", "468"]):
            matched_model = cls.VULNERABILITY_MODELS.get("FINANCIAL_FRAUD")
        elif any(x in offense_type for x in ["498A", "85", "DOWRY", "304B"]):
            matched_model = cls.VULNERABILITY_MODELS.get("MATRIMONIAL")
        elif any(x in offense_type for x in ["302", "307", "323", "324", "326", "103", "109", "115", "118", "MURDER", "HURT"]):
            matched_model = cls.VULNERABILITY_MODELS.get("HOMICIDE_BODILY")
        elif any(x in offense_type for x in ["376", "64", "69", "354", "RAPE", "POCSO"]):
            matched_model = cls.VULNERABILITY_MODELS.get("SEXUAL_OFFENSES")
        elif "NDPS" in offense_type:
            matched_model = cls.VULNERABILITY_MODELS.get("NDPS_OFFENSES")
        elif any(x in offense_type for x in ["PC ACT", "CORRUPTION", "PMLA", "MONEY LAUNDERING", "ED"]):
            matched_model = cls.VULNERABILITY_MODELS.get("CORRUPTION_PMLA")

        if matched_model:
            analysis_nodes.append({
                "adversarial_vector": matched_model["name"],
                "risk": matched_model["risk"],
                "severity": matched_model["severity"],
                "description": matched_model["risk"],
                "strategic_chain": matched_model["chain"],
                "rebuttal_tree": matched_model["rebuttal_tree"],
                "cross_exam_questions": matched_model["cross_exam_questions"],
                "quashing_ground": matched_model["quashing_ground"],
                "discharge_quashing_strategy": f"File S.482 CrPC / S.528 BNSS Quashing Petition. Precedent: {matched_model['quashing_ground']}",
                "survival_probability": f"{int((1.0 - matched_model['probability_collapse']) * 100)}%",
                "collapse_risk": f"{int(matched_model['probability_collapse'] * 100)}%"
            })

        # Bhajan Lal grounds
        bhajan_grounds = cls.evaluate_bhajan_lal_grounds(case_data)
        for bg in bhajan_grounds:
            analysis_nodes.append({
                "adversarial_vector": bg["parameter"],
                "risk": "Quashing Viability",
                "severity": "FATAL TO PROSECUTION",
                "description": bg["rationale"],
                "discharge_quashing_strategy": f"File Section 482 CrPC / Section 528 BNSS petition before High Court. Precedent: {bg['precedent']}",
                "quashing_ground": bg["parameter"]
            })

        if not analysis_nodes:
            analysis_nodes.append({
                "adversarial_vector": f"General Criminal Defense Protocol ({offense_type or 'IPC/BNS'})",
                "risk": "Standard prosecution burden beyond reasonable doubt",
                "severity": "HIGH",
                "description": "Scrutiny of FIR timing, independent panch witnesses, recovery chain of custody, and ocular consistency.",
                "strategic_chain": ["FIR Delay Scrutiny", "Recovery Verification", "Cross-examination of Investigating Officer"],
                "rebuttal_tree": {
                    "defence_evidence": "Documentary proof, alibi witnesses, independent cross-exam.",
                    "prosecution_counter": "Rely on witness consistency and recovery memo."
                },
                "cross_exam_questions": [
                    "Can you establish the exact chronological timeline of the alleged occurrence?",
                    "Were independent non-interested local witnesses joined during the investigation?",
                    "Is it true that no contemporaneous complaint was made immediately after the incident?"
                ],
                "quashing_ground": "No prima facie case disclosed on face of FIR",
                "discharge_quashing_strategy": "Argue discharge u/s 227/239 CrPC / S.250/262 BNSS.",
                "survival_probability": "65%",
                "collapse_risk": "35%"
            })

        return analysis_nodes

    @classmethod
    def audit_case(cls, case_data: Dict[str, Any], concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        contradictions = cls.detect_contradictions(case_data, concepts)
        analysis_nodes = cls.simulate_strategic_stress_test(case_data, concepts)

        base_risk = 0.20
        for node in analysis_nodes:
            try:
                dest_prob = float(str(node.get("collapse_risk", "30%")).strip('%')) / 100.0
                base_risk += (dest_prob * 0.3)
            except Exception:
                base_risk += 0.1

        for c in contradictions:
            if "Fatal" in c.get("severity", ""):
                base_risk += 0.35
            elif "Material" in c.get("severity", ""):
                base_risk += 0.20
            else:
                base_risk += 0.10

        return {
            "risks_and_rebuttals": analysis_nodes,
            "contradictions": contradictions,
            "adversarial_risk": min(0.95, base_risk)
        }

    @classmethod
    def stress_test(cls, case_data: Dict[str, Any], score: int = 50) -> Dict[str, Any]:
        return cls.audit_case(case_data, [])
