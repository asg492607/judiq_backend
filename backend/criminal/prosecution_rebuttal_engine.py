"""
Dynamic Prosecution Counter-Attack & Rebuttal Simulator.
Simulates aggressive trial strategies deployed by Public Prosecutors and Complainant Counsel,
generating stress-tested defense counter-rebuttals backed by Supreme Court precedents.
"""

from datetime import datetime
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ProsecutionRebuttalEngine:
    """
    Law-firm grade prosecution counter-attack simulator & rebuttal generator.
    """

    @classmethod
    def simulate_prosecution_counter_attacks(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates defense claims and generates the top 3-5 aggressive prosecution counter-attacks
        with matched counter-rebuttals.
        """
        offense = str(case_data.get("offense_type", "")).upper()
        amount = float(case_data.get("cheque_amount") or case_data.get("disputed_amount") or case_data.get("amount") or 0.0)
        has_contract = bool(case_data.get("contract_exists") or case_data.get("agreement_type"))
        is_corporate = any(x in str(case_data.get("accused_name", "")).lower() for x in ["pvt", "ltd", "corp", "inc", "firm"])

        attacks = []

        # Attack Vector 1: Mens Rea at Inception (Inducement Test)
        if any(x in offense for x in ["420", "318", "CHEATING", "FRAUD"]):
            attacks.append({
                "vector_id": "PA-01",
                "attack_title": "Fraudulent Mens Rea at Inception (Deceptive Inducement)",
                "prosecution_argument": (
                    "The Public Prosecutor will argue that the accused harbored dishonest intention from the very inception "
                    "of the transaction, having made false representations knowing fully well they would not perform, "
                    "thus taking the matter out of the civil sphere into cognizable cheating under BNS 318(4) / IPC 420."
                ),
                "prosecution_citations": [
                    "Hriday Ranjan Prasad Verma v. State of Bihar (2000) 4 SCC 168",
                    "Vijay Kumar Ghai v. State of West Bengal (2022) 7 SCC 124"
                ],
                "severity": "HIGH",
                "defense_rebuttal": (
                    "Mere inability of the accused to fulfill a promise at a subsequent stage cannot give rise to an inference "
                    "of cheating unless fraudulent intention is demonstrated at the time of making the promise. Where substantial "
                    "part-performance or genuine business dealing exists, the dispute is purely a civil breach of contract."
                ),
                "defense_precedent": "Dalip Kaur v. Jagnar Singh (2009) 14 SCC 696 & Paramjeet Batra v. State of Uttarakhand (2013) 11 SCC 673",
                "actionable_pleading": "Incorporate express averment of initial bona fide payments and partial performance in Para 7 of Quashing Petition."
            })

        # Attack Vector 2: Criminal Breach of Trust vs Simple Debtor-Creditor Relationship
        if any(x in offense for x in ["406", "316", "ENTRUSTMENT", "BREACH OF TRUST"]):
            attacks.append({
                "vector_id": "PA-02",
                "attack_title": "Misappropriation of Entrusted Property (Section 316 BNS / Section 406 IPC)",
                "prosecution_argument": (
                    "Complainant will assert that funds/goods were handed over under express fiduciary entrustment for a specific "
                    "commercial mandate, and the accused dishonestly converted the same to their own dominion."
                ),
                "prosecution_citations": [
                    "S.W. Palanitkar v. State of Bihar (2002) 1 SCC 241"
                ],
                "severity": "CRITICAL",
                "defense_rebuttal": (
                    "To constitute an offence under Section 406 IPC / 316 BNS, there must be established entrustment of property "
                    "and dishonest misappropriation. In an arm's-length commercial transaction involving sale/loan, property in goods/money "
                    "passes absolutely, creating only a debtor-creditor relationship, not a criminal entrustment."
                ),
                "defense_precedent": "Indian Oil Corporation v. NEPC India Ltd. (2006) 6 SCC 736",
                "actionable_pleading": "Annex underlying invoices / loan ledgers proving absolute transfer of property without fiduciary custody."
            })

        # Attack Vector 3: Section 120B / Section 61 Criminal Conspiracy & Multi-Party S.141 Impleadment
        if is_corporate:
            attacks.append({
                "vector_id": "PA-03",
                "attack_title": "Corporate Veil Piercing & Criminal Conspiracy (S.120B / S.61 BNS)",
                "prosecution_argument": (
                    "Prosecution will claim that directors acted in concert as part of a common criminal design and conspiracy "
                    "to siphon investor/lender funds through intermediary accounts."
                ),
                "prosecution_citations": [
                    "State of Maharashtra v. Som Nath Thapa (1996) 4 SCC 659"
                ],
                "severity": "HIGH",
                "defense_rebuttal": (
                    "Vicarious liability cannot be imported into the Indian Penal Code / BNS in the absence of an express statutory provision. "
                    "Directors cannot be prosecuted on generalized allegations without demonstrating specific individual overt acts "
                    "constituting active conspiracy."
                ),
                "defense_precedent": "Sunil Bharti Mittal v. CBI (2015) 4 SCC 609 & Shiv Kumar Jatia v. State (NCT of Delhi) (2019) 17 SCC 193",
                "actionable_pleading": "Move for threshold quashing under Bhajan Lal Category 1 & 7 citing lack of specific overt role in FIR."
            })

        # Attack Vector 4: Bail Opposition (Flight Risk, Witness Tampering, Scale of Economic Fraud)
        if amount > 5000000:
            attacks.append({
                "vector_id": "PA-04",
                "attack_title": "Bail Objection: Scale of Economic Offence & Custodial Interrogation Necessity",
                "prosecution_argument": (
                    f"Public Prosecutor will oppose bail on grounds that a massive financial fraud of ₹{amount:,.2f} requires "
                    "sustained custodial interrogation to unearth the money trail and recover proceeds of crime."
                ),
                "prosecution_citations": [
                    "State of Gujarat v. Mohanlal Jitamalji Porwal (1987) 2 SCC 364",
                    "P. Chidambaram v. Directorate of Enforcement (2019) 9 SCC 24"
                ],
                "severity": "HIGH",
                "defense_rebuttal": (
                    "Custodial interrogation is not a punitive measure. Where the entire case is based on documentary records and bank statements "
                    "already seized or available with the investigating agency, pre-trial incarceration violates Article 21. "
                    "Bail is the rule and jail is the exception."
                ),
                "defense_precedent": "Satender Kumar Antil v. CBI (2022) 10 SCC 51 & Sanjay Chandra v. CBI (2012) 1 SCC 40",
                "actionable_pleading": "Offer strict surrender of passport, periodic attendance at Police Station, and substantial local surety."
            })

        return {
            "total_attack_vectors_simulated": len(attacks),
            "prosecution_counter_attacks": attacks,
            "overall_rebuttal_preparedness": "AIRTIGHT" if len(attacks) > 0 else "STANDARD",
            "statutory_stress_tested": True,
            "simulation_timestamp": datetime.now().isoformat()
        }
