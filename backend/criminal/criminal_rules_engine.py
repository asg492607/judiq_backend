from typing import Dict, List, Any

class CriminalRulesEngine:
    """
    Comprehensive statutory rules engine evaluating mandatory procedural bars,
    constitutional protections, and statutory safeguards across ALL categories of Indian Criminal Law
    under both the legacy framework (IPC 1860 / CrPC 1973 / IEA 1872) and
    the modern statutory framework (BNS 2023 / BNSS 2023 / BSA 2023).
    """

    STATUTORY_MAPPINGS = {
        "FIR": {"old": "S.154 CrPC", "new": "S.173 BNSS"},
        "ARREST_NOTICE": {"old": "S.41A CrPC", "new": "S.35 BNSS"},
        "POLICE_STATEMENT": {"old": "S.161 CrPC", "new": "S.180 BNSS"},
        "MAGISTRATE_STATEMENT": {"old": "S.164 CrPC", "new": "S.183 BNSS"},
        "REMAND_DEFAULT_BAIL": {"old": "S.167(2) CrPC", "new": "S.187 BNSS"},
        "SANCTION_PUBLIC_SERVANT": {"old": "S.197 CrPC", "new": "S.218 BNSS"},
        "DISCHARGE_SESSIONS": {"old": "S.227 CrPC", "new": "S.250 BNSS"},
        "DISCHARGE_MAGISTRATE": {"old": "S.239 CrPC", "new": "S.262 BNSS"},
        "REGULAR_BAIL_MAGISTRATE": {"old": "S.437 CrPC", "new": "S.480 BNSS"},
        "REGULAR_BAIL_SESSIONS_HC": {"old": "S.439 CrPC", "new": "S.483 BNSS"},
        "ANTICIPATORY_BAIL": {"old": "S.438 CrPC", "new": "S.484 BNSS"},
        "UNDERTRIAL_MAX_DETENTION": {"old": "S.436A CrPC", "new": "S.479 BNSS"},
        "LIMITATION_BAR": {"old": "S.468 CrPC", "new": "S.514 BNSS"},
        "QUASHING_HIGH_COURT": {"old": "S.482 CrPC", "new": "S.528 BNSS"},
        "SUPERDARI_RELEASE": {"old": "S.451/457 CrPC", "new": "S.497/503 BNSS"},
        "WITNESS_RECALL": {"old": "S.311 CrPC", "new": "S.348 BNSS"},
        "ADDITIONAL_ACCUSED": {"old": "S.319 CrPC", "new": "S.358 BNSS"},
        "ELECTRONIC_EVIDENCE_CERT": {"old": "S.65B IEA", "new": "S.63 BSA"},
        "DISCOVERY_STATEMENT": {"old": "S.27 IEA", "new": "S.23 BSA"},
        "ALIBI_PLEA": {"old": "S.11 IEA", "new": "S.11 BSA"},
        "PRESUMPTION_MARRIED_WOMAN": {"old": "S.113A/113B IEA", "new": "S.117/118 BSA"}
    }

    @classmethod
    def evaluate_rules(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        triggered_rules = []
        offense = str(case_data.get("offense_type") or case_data.get("ipc_section") or "").upper()
        max_punishment = case_data.get("max_punishment_years") or case_data.get("punishment_years")
        days_in_custody = int(case_data.get("days_in_custody") or 0)
        chargesheet_filed = case_data.get("chargesheet_filed", False) or bool(case_data.get("chargesheet_date"))

        # 1. Juvenile Justice Act Check (Absolute Jurisdictional Bar)
        age_at_incident = case_data.get("age_at_incident")
        if age_at_incident is not None:
            try:
                age = int(age_at_incident)
                if age < 18:
                    triggered_rules.append({
                        "rule_name": "Juvenile Justice (Care & Protection) Act, 2015",
                        "severity": "ABSOLUTE JURISDICTIONAL BAR",
                        "status": "FATAL TO REGULAR COURT JURISDICTION",
                        "description": f"Accused was {age} years of age at the time of commission of alleged offense.",
                        "legal_effect": "The regular criminal court has zero jurisdiction. All proceedings must be transferred to the Juvenile Justice Board (JJB). Maximum detention cannot exceed 3 years in a Special Home.",
                        "action": "File an immediate application under Section 94 of the JJ Act for age determination (Matriculation Certificate / Ossification Test)."
                    })
            except (ValueError, TypeError):
                pass

        # 2. Public Servant Sanction Check (S.197 CrPC / S.218 BNSS & S.17A / S.19 PC Act)
        if case_data.get("is_public_servant") and not case_data.get("sanction_obtained"):
            triggered_rules.append({
                "rule_name": "S.197 CrPC / S.218 BNSS & S.17A PC Act (Want of Statutory Sanction)",
                "severity": "ABSOLUTE STATUTORY BAR",
                "status": "COGNIZANCE VOID AB INITIO",
                "description": "Accused is a public servant acting in discharge of official duty, but no prior sanction was obtained from the competent government authority.",
                "legal_effect": "Taking cognizance without prior statutory sanction is strictly prohibited. The entire proceeding is null and void ab initio (D. Devaraja v. Owais Sabeer Hussain).",
                "action": "File application for discharge or S.482 CrPC / S.528 BNSS Quashing citing lack of valid sanction."
            })

        # 3. Satender Kumar Antil Guidelines (Category A Mandate & S.41A CrPC / S.35 BNSS)
        if max_punishment is not None:
            try:
                punishment = int(max_punishment)
                if punishment <= 7:
                    arrested_during_investigation = case_data.get("arrested_during_investigation")
                    if arrested_during_investigation is False:
                        triggered_rules.append({
                            "rule_name": "Satender Kumar Antil Guidelines (Category A Mandate)",
                            "severity": "SUPREME COURT DIRECTIVE",
                            "status": "MANDATORY BAIL WITHOUT CUSTODY",
                            "description": f"Offence carries maximum punishment up to {punishment} years. Accused was not arrested during investigation.",
                            "legal_effect": "Under Category A of Satender Kumar Antil v. CBI (2022) & Arnesh Kumar mandate, the Magistrate must accept appearance without taking the accused into physical custody.",
                            "action": "Submit a bail application citing Satender Kumar Antil v. CBI (2022) Category A guidelines on first appearance."
                        })
                    elif case_data.get("no_s41a_notice"):
                        triggered_rules.append({
                            "rule_name": "Violation of S.41A CrPC / S.35 BNSS Mandatory Notice",
                            "severity": "CRITICAL PROCEDURAL LAPSE",
                            "status": "UNLAWFUL ARREST",
                            "description": "Offence carries <= 7 years imprisonment, but police failed to serve S.41A/S.35 notice prior to arrest.",
                            "legal_effect": "Arrest without recording specific necessity under S.41(1)(b) renders custody unlawful per Arnesh Kumar v. State of Bihar.",
                            "action": "Seek immediate bail and initiate departmental inquiry against IO per Arnesh Kumar guidelines."
                        })
            except (ValueError, TypeError):
                pass

        # 4. Statutory Limitation Check (S.468 CrPC / S.514 BNSS)
        limitation_years = case_data.get("limitation_years_passed")
        if limitation_years is not None and max_punishment is not None:
            try:
                punishment = int(max_punishment)
                years_passed = float(limitation_years)
                barred = False
                bar_limit = 0
                if punishment <= 1 and years_passed > 1:
                    barred = True
                    bar_limit = 1
                elif punishment <= 3 and years_passed > 3:
                    barred = True
                    bar_limit = 3
                if barred:
                    triggered_rules.append({
                        "rule_name": "S.468 CrPC / S.514 BNSS (Statutory Bar of Limitation)",
                        "severity": "ABSOLUTE STATUTORY BAR",
                        "status": "COGNIZANCE BARRED BY LAW",
                        "description": f"Offence carries maximum punishment of {punishment} years (limitation period {bar_limit} year(s)), but {years_passed} years have elapsed.",
                        "legal_effect": "Court is legally barred from taking cognizance post limitation period (State of Punjab v. Sarwan Singh).",
                        "action": "File application for immediate discharge/quashing citing S.468 CrPC / S.514 BNSS."
                    })
            except (ValueError, TypeError):
                pass

        # 5. Electronic Evidence Mandatory Certification (S.65B IEA / S.63 BSA)
        if case_data.get("electronic_evidence") and not case_data.get("s65b_certificate"):
            triggered_rules.append({
                "rule_name": "S.65B(4) IEA / S.63 BSA Mandatory Certificate Mandate",
                "severity": "FATAL EVIDENTIARY DEFECT",
                "status": "INADMISSIBLE EVIDENCE",
                "description": "Electronic records (call recordings, WhatsApp chats, CCTV footage, DVR logs) produced without mandatory contemporaneous certificate.",
                "legal_effect": "Secondary electronic evidence is completely inadmissible without certificate under Section 65B(4) / S.63 (Arjun Panditrao Khotkar v. Kailash Kushanrao Gorantyal, Supreme Court 3-Judge Bench).",
                "action": "Object to exhibit marking of electronic evidence during trial stage."
            })

        # 6. Statutory Default Bail Check (S.167(2) CrPC / S.187 BNSS)
        if days_in_custody > 0 and not chargesheet_filed:
            try:
                punishment = int(max_punishment or 7)
                statutory_days = 90 if punishment >= 10 else 60
                if days_in_custody >= statutory_days:
                    triggered_rules.append({
                        "rule_name": f"S.167(2) CrPC / S.187 BNSS Indefeasible Right to Default Bail ({statutory_days} Days Exceeded)",
                        "severity": "ABSOLUTE CONSTITUTIONAL RIGHT",
                        "status": "MANDATORY STATUTORY BAIL",
                        "description": f"Accused has been in continuous custody for {days_in_custody} days. The outer statutory limit of {statutory_days} days for completing investigation has expired without chargesheet.",
                        "legal_effect": "Accused has acquired an indefeasible right to statutory default bail under Article 21. The Magistrate has zero discretion to extend judicial remand (Ritu Chhabaria v. Union of India, 2023; Bikramjit Singh v. State of Punjab).",
                        "action": "Immediately file S.167(2) Default Bail Application before the chargesheet is submitted."
                    })
            except (ValueError, TypeError):
                pass

        # 7. Disguised Civil Dispute / Absence of Mens Rea at Inception (S.420 / 406 IPC ↔ S.318 / 316 BNS)
        if (case_data.get("contract_exists") or case_data.get("commercial_dispute") or case_data.get("recovery_suit_pending")) and any(x in offense for x in ["420", "406", "318", "316", "CHEATING", "FRAUD", "BREACH"]):
            triggered_rules.append({
                "rule_name": "Disguised Civil Dispute / Absence of Mens Rea at Inception",
                "severity": "CRITICAL QUASHING GROUND",
                "status": "BHATIA / HRIDAYA RANJAN PARADIGM",
                "description": "Criminal proceedings instituted for pure breach of commercial contract or debt recovery without establishing fraudulent intent at the inception of the transaction.",
                "legal_effect": "Supreme Court holds that mere failure to keep a promise or pay money does not constitute S.420/406. Criminal courts cannot be used as recovery agencies (Hridaya Ranjan Prasad Verma v. State of Bihar; Dalip Kaur v. Jagnar Singh; Indian Oil Corp v. NEPC India).",
                "action": "File Petition under Section 482 CrPC / Section 528 BNSS before the High Court for quashing of FIR and all consequential proceedings."
            })

        # 8. Omnibus Family Impleadment in Matrimonial Disputes (S.498A IPC ↔ S.85 BNS)
        if ("498A" in offense or "85" in offense or "DOWRY" in offense or "304B" in offense) and (case_data.get("relative_impleaded") or case_data.get("separate_residence")):
            triggered_rules.append({
                "rule_name": "Omnibus Allegations Against In-Laws / Distant Relatives (S.498A)",
                "severity": "HIGH QUASHING GROUND",
                "status": "KAHKASHAN KAUSAR COMPLIANCE",
                "description": "General and omnibus allegations leveled against relatives of husband without attributing specific overt acts of harassment or cruelty.",
                "legal_effect": "Proceedings against extended family members residing separately or roped in casually are liable to be quashed to prevent abuse of judicial process (Kahkashan Kausar v. State of Bihar, 2022; Geeta Mehrotra v. State of UP).",
                "action": "File S.482 / S.528 Quashing Petition highlighting independent residence and lack of specific date-time attribution."
            })

        # 9. NDPS Act Mandatory Search & Sampling Protocols (S.50, S.42, S.52A NDPS)
        if "NDPS" in offense:
            if case_data.get("s50_violation") or case_data.get("s50_ndps_violation"):
                triggered_rules.append({
                    "rule_name": "Section 50 NDPS Act Mandatory Personal Search Violation",
                    "severity": "FATAL TO PROSECUTION",
                    "status": "INADMISSIBLE RECOVERY / TRIAL VITIATED",
                    "description": "Personal search of accused conducted without offering mandatory option to be searched in presence of a Gazetted Officer or Magistrate.",
                    "legal_effect": "Section 50 is strictly mandatory. Failure to comply vitiates recovery and entitles accused to acquittal (Vijaysinh Chandubha Jadeja v. State of Gujarat, Constitution Bench).",
                    "action": "File discharge application under S.227 or urge S.50 violation during bail hearing."
                })
            if case_data.get("s52a_violation") or case_data.get("inventory_delay"):
                triggered_rules.append({
                    "rule_name": "Section 52A NDPS Act Mandatory Inventory Certification",
                    "severity": "HIGH DEFENSE VECTOR",
                    "status": "SAMPLING PROTOCOL BREACH",
                    "description": "Samples drawn at the spot of seizure instead of before a Judicial Magistrate under Section 52A.",
                    "legal_effect": "Samples not drawn in presence of Magistrate cannot be treated as primary evidence in trial per Mangilal v. State of MP (2023) and Simarnjit Singh v. State of Punjab (2023).",
                    "action": "Challenge admissibility of FSL report in trial cross-examination."
                })

        # 10. False Promise to Marry vs. Consensual Relationship (S.376 IPC ↔ S.64 / S.69 BNS)
        if ("376" in offense or "64" in offense or "69" in offense or "RAPE" in offense) and (case_data.get("consensual_relationship") or case_data.get("promise_to_marry")):
            triggered_rules.append({
                "rule_name": "Consensual Relationship vs. False Promise of Marriage (S.376)",
                "severity": "PRIMARY DEFENSE / QUASHING GROUND",
                "status": "PRAMOD SURYABHAN PAWAR PRECEDENT",
                "description": "Physical relationship entered into voluntarily during courtship where marriage could not materialize due to subsequent unforeseen events.",
                "legal_effect": "A breach of promise to marry is not 'misconception of fact' under Section 90 IPC unless fraudulent intention was present right from inception (Pramod Suryabhan Pawar v. State of Maharashtra; Sonu @ Subhash Kumar v. State of UP).",
                "action": "File Quashing Petition u/s 482 CrPC / S.528 BNSS placing WhatsApp chats, hotel bookings, and mutual travel proof on record."
            })

        # 11. PMLA / Economic Crimes Long Incarceration Exception (S.45 PMLA & Article 21)
        if "PMLA" in offense or "MONEY LAUNDERING" in offense or "ED" in offense:
            if days_in_custody > 180:
                triggered_rules.append({
                    "rule_name": "PMLA Section 45 Twin Conditions Overridden by Article 21 Incarceration",
                    "severity": "CONSTITUTIONAL BAIL GROUND",
                    "status": "MANISH SISODIA / PREM PRAKASH MANDATE",
                    "description": f"Accused has undergone {days_in_custody} days in custody with trial nowhere near conclusion.",
                    "legal_effect": "Supreme Court holds that statutory restrictions under Section 45 PMLA cannot supersede fundamental right to speedy trial and personal liberty under Article 21 (Manish Sisodia v. ED, 2024; Prem Prakash v. ED, 2024).",
                    "action": "File Regular Bail Petition before High Court / Supreme Court urging prolonged pre-trial incarceration."
                })

        # 12. Discovery Memo under S.27 Evidence Act / S.23 BSA
        if case_data.get("joint_recovery") or case_data.get("recovery_open_place"):
            triggered_rules.append({
                "rule_name": "Inadmissible Recovery Memo (S.27 IEA / S.23 BSA)",
                "severity": "MATERIAL EVIDENTIARY DEFECT",
                "status": "JOINT RECOVERY / OPEN PLACE DISCLOSURE",
                "description": "Seizure effected from an open public place accessible to all, or recorded as a joint disclosure of multiple accused persons.",
                "legal_effect": "Joint discovery memos or recoveries from places accessible to public are legally inadmissible under S.27 (Pulukuri Kottaya; Ramanand v. State of UP).",
                "action": "Confront seizing officer and panch witnesses during cross-examination."
            })

        # 13. POCSO Romantic Relationship / Adolescent Age Ambiguity
        if "POCSO" in offense and case_data.get("adolescent_romance"):
            triggered_rules.append({
                "rule_name": "Adolescent Consensual Relationship (POCSO Mitigation)",
                "severity": "JUDICIAL QUASHING / BAIL GROUND",
                "status": "POCSO BENEVOLENT INTERPRETATION",
                "description": "Adolescent consensual romance where parties are of similar age and no sexual exploitation exists.",
                "legal_effect": "High Courts consistently quash POCSO FIRs where the relationship was consensual and marriage/family life is intended (Sabari v. Inspector of Police; Vijayalakshmi v. State).",
                "action": "File S.482 Quashing with joint affidavit of parties."
            })

        return triggered_rules
