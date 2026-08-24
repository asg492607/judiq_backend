from typing import Dict, List, Any

class CriminalRulesEngine:
    """
    Evaluates statutory rules, mandatory procedural bars, and constitutional/statutory rights
    under both IPC/CrPC/IEA (Old Framework) and BNS/BNSS/BSA (New Framework 2023).
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
        "ELECTRONIC_EVIDENCE_CERT": {"old": "S.65B IEA", "new": "S.63 BSA"},
        "ALIBI_PLEA": {"old": "S.11 IEA", "new": "S.11 BSA"},
        "DISCOVERY_STATEMENT": {"old": "S.27 IEA", "new": "S.23 BSA"},
    }

    @classmethod
    def evaluate_rules(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        triggered_rules = []

        # 1. Juvenile Justice Act Check
        age_at_incident = case_data.get("age_at_incident")
        if age_at_incident is not None:
            try:
                age = int(age_at_incident)
                if age < 18:
                    triggered_rules.append({
                        "rule_name": "Juvenile Justice (Care & Protection) Act, 2015",
                        "severity": "ABSOLUTE BAR",
                        "status": "FATAL TO TRIAL JURISDICTION",
                        "description": f"Accused was {age} years old at the time of the incident.",
                        "legal_effect": "The regular criminal court has zero jurisdiction. Proceedings must be transferred to the Juvenile Justice Board (JJB). Maximum confinement cannot exceed 3 years in a Special Home.",
                        "action": "File an immediate application under Section 94 of the JJ Act for age determination (Matriculation Certificate / Ossification Test)."
                    })
            except (ValueError, TypeError):
                pass

        # 2. Public Servant Sanction Check (S.197 CrPC / S.218 BNSS & S.17A PCA)
        if case_data.get("is_public_servant") and not case_data.get("sanction_obtained"):
            triggered_rules.append({
                "rule_name": "S.197 CrPC / S.218 BNSS & S.17A PC Act (Want of Sanction)",
                "severity": "ABSOLUTE BAR",
                "status": "COGNIZANCE VOID AB INITIO",
                "description": "Accused is a public servant acting in discharge of official duties, but no prior government sanction was obtained.",
                "legal_effect": "Taking cognizance without prior sanction is strictly prohibited. The entire proceeding is null and void ab initio.",
                "action": "File an application for discharge or S.482 CrPC / S.528 BNSS Quashing citing lack of valid sanction (D. Devaraja v. Owais Sabeer Hussain)."
            })

        # 3. Satender Kumar Antil Guidelines (Arnesh Kumar Compliance)
        max_punishment = case_data.get("max_punishment_years") or case_data.get("punishment_years")
        arrested_during_investigation = case_data.get("arrested_during_investigation")
        cooperated_with_io = case_data.get("cooperated_with_io", True)
        if max_punishment is not None:
            try:
                punishment = int(max_punishment)
                if punishment <= 7:
                    if arrested_during_investigation is False:
                        triggered_rules.append({
                            "rule_name": "Satender Kumar Antil Guidelines (Category A)",
                            "severity": "SUPREME COURT DIRECTIVE",
                            "status": "MANDATORY BAIL",
                            "description": f"Offence is punishable up to {punishment} years. Accused was not arrested during investigation.",
                            "legal_effect": "Under Category A of the Antil Guidelines & Arnesh Kumar mandate, the Magistrate must accept appearance without taking the accused into physical custody.",
                            "action": "Submit a bail application citing Satender Kumar Antil v. CBI (2022) Category A guidelines on first appearance."
                        })
                    elif case_data.get("no_s41a_notice"):
                        triggered_rules.append({
                            "rule_name": "Violation of S.41A CrPC / S.35 BNSS Mandatory Notice",
                            "severity": "CRITICAL PROCEDURAL LAPSE",
                            "status": "ILLEGAL ARREST",
                            "description": "Offence carries <= 7 years imprisonment, but police failed to serve S.41A/S.35 notice prior to arrest.",
                            "legal_effect": "Arrest without recording specific reasons under S.41(1)(b) renders custody unlawful.",
                            "action": "Seek immediate bail and initiate departmental inquiry against IO per Arnesh Kumar v. State of Bihar guidelines."
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
                        "severity": "ABSOLUTE BAR",
                        "status": "COGNIZANCE BARRED",
                        "description": f"Offence is punishable up to {punishment} years, establishing a limitation period of {bar_limit} year(s). However, {years_passed} years have elapsed.",
                        "legal_effect": "Court is legally barred from taking cognizance post limitation period.",
                        "action": "File application for immediate discharge/quashing citing S.468 CrPC / S.514 BNSS (State of Punjab v. Sarwan Singh)."
                    })
            except (ValueError, TypeError):
                pass

        # 5. Electronic Evidence Mandatory Certification (S.65B IEA / S.63 BSA)
        if case_data.get("electronic_evidence") and not case_data.get("s65b_certificate"):
            triggered_rules.append({
                "rule_name": "S.65B IEA / S.63 BSA Mandatory Certificate Mandate",
                "severity": "EVIDENTIARY BAR",
                "status": "INADMISSIBLE EVIDENCE",
                "description": "Electronic records (call recordings, WhatsApp chats, CCTV footage) produced without requisite statutory certificate.",
                "legal_effect": "Secondary electronic evidence is completely inadmissible without contemporaneous certificate (Arjun Panditrao Khotkar v. Kailash Kushanrao Gorantyal).",
                "action": "Object to exhibit marking of electronic evidence during trial stage."
            })

        # 6. Undertrial Prisoner Maximum Detention Period (S.436A CrPC / S.479 BNSS)
        days_in_custody = int(case_data.get("days_in_custody") or 0)
        chargesheet_filed = case_data.get("chargesheet_filed", False)
        chargesheet_date = case_data.get("chargesheet_date")
        if chargesheet_date:
            chargesheet_filed = True

        if days_in_custody > 0 and max_punishment:
            try:
                max_days = (int(max_punishment) * 365) / 2 # 1/2 of max sentence
                if days_in_custody >= max_days:
                    triggered_rules.append({
                        "rule_name": "S.436A CrPC / S.479 BNSS (Maximum Period of Undertrial Detention)",
                        "severity": "MANDATORY RELEASE",
                        "status": "RIGHT TO RELEASE ON BAIL",
                        "description": f"Accused has undergone {days_in_custody} days in custody, exceeding one-half of maximum imprisonment.",
                        "legal_effect": "Accused is entitled to be released on personal bond with or without sureties.",
                        "action": "File application under S.436A CrPC / S.479 BNSS for mandatory release."
                    })
            except (ValueError, TypeError):
                pass

        # 7. Statutory Default Bail Check (S.167(2) CrPC / S.187 BNSS)
        if days_in_custody > 0 and not chargesheet_filed:
            try:
                punishment = int(max_punishment or 3)
                statutory_days = 90 if punishment >= 10 else 60
                if days_in_custody >= statutory_days:
                    triggered_rules.append({
                        "rule_name": f"S.167(2) CrPC / S.187 BNSS Indefeasible Right to Default Bail ({statutory_days} Days Exceeded)",
                        "severity": "ABSOLUTE STATUTORY RIGHT",
                        "status": "MANDATORY BAIL",
                        "description": f"Accused has been in custody for {days_in_custody} days. The statutory limit of {statutory_days} days for completing investigation has expired without police report/chargesheet filed.",
                        "legal_effect": "Accused has acquired an indefeasible right to statutory default bail. The Magistrate has zero discretion to extend judicial remand (Ritu Chhabaria v. Union of India, 2023; Bikramjit Singh v. State of Punjab).",
                        "action": f"Immediately file S.167(2) Default Bail Application before the chargesheet is submitted to prevent extinguishing the right."
                    })
            except (ValueError, TypeError):
                pass

        # 8. Civil Dispute Disguised as Criminal Offense (S.420 / 406 IPC ↔ S.318 / 316 BNS)
        offense = str(case_data.get("offense_type") or case_data.get("ipc_section") or "").upper()
        if (case_data.get("contract_exists") or case_data.get("commercial_dispute") or case_data.get("recovery_suit_pending")) and any(x in offense for x in ["420", "406", "318", "316", "CHEATING", "BREACH"]):
            triggered_rules.append({
                "rule_name": "Disguised Civil Dispute / Absence of Mens Rea at Inception",
                "severity": "CRITICAL QUASHING GROUND",
                "status": "BHATIA / HRIDAYA RANJAN PARADIGM",
                "description": "Criminal proceedings instituted for pure breach of commercial contract/debt recovery without establishing fraudulent intent at the inception of the transaction.",
                "legal_effect": "Supreme Court holds that mere failure to keep a promise or pay money does not constitute S.420/406. Criminal courts cannot be used as recovery agencies (Hridaya Ranjan Prasad Verma v. State of Bihar; Dalip Kaur v. Jagnar Singh).",
                "action": "File Petition under Section 482 CrPC / Section 528 BNSS before the High Court for quashing of FIR and all consequential proceedings."
            })

        # 9. Omnibus Family Impleadment (S.498A IPC ↔ S.85 BNS)
        if ("498A" in offense or "85" in offense or "DOWRY" in offense) and (case_data.get("relative_impleaded") or case_data.get("separate_residence")):
            triggered_rules.append({
                "rule_name": "Omnibus Allegations Against In-Laws / Distant Relatives (S.498A)",
                "severity": "HIGH QUASHING GROUND",
                "status": "KAHKASHAN KAUSAR COMPLIANCE",
                "description": "General and omnibus allegations leveled against relatives of husband without attributing specific overt acts of harassment or cruelty.",
                "legal_effect": "Proceedings against extended family members residing separately or roped in casually are liable to be quashed to prevent abuse of judicial process (Kahkashan Kausar v. State of Bihar, 2022; Geeta Mehrotra v. State of UP).",
                "action": "File S.482 / S.528 Quashing Petition highlighting independent residence and lack of specific date-time attribution."
            })

        # 10. NDPS Section 50 Personal Search Protocol
        if "NDPS" in offense and case_data.get("s50_violation"):
            triggered_rules.append({
                "rule_name": "Section 50 NDPS Act Mandatory Search Violation",
                "severity": "FATAL TO PROSECUTION",
                "status": "INADMISSIBLE RECOVERY",
                "description": "Personal search of accused conducted without offering mandatory option to be searched in presence of a Gazetted Officer or Magistrate.",
                "legal_effect": "Section 50 is strictly mandatory. Failure to comply vitiates recovery and entitles accused to acquittal (Vijaysinh Chandubha Jadeja v. State of Gujarat, Constitution Bench).",
                "action": "File discharge application under S.227 or urge S.50 violation during bail hearing."
            })

        return triggered_rules
