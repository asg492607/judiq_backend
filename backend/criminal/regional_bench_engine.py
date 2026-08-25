"""
Jurisdiction-Specific High Court & Trial Court Customizer Engine.
Tailors Quashing Petitions (Section 482 CrPC / Section 528 BNSS) and Bail Applications
to regional High Court Appellate Side Rules, registry checklists, and division bench precedents.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

HIGH_COURT_RULES = {
    "BOMBAY_HIGH_COURT": {
        "court_name": "HIGH COURT OF JUDICATURE AT BOMBAY",
        "bench_options": ["Principal Seat at Mumbai", "Nagpur Bench", "Aurangabad Bench", "Goa Bench at Panaji"],
        "governing_rules": "Bombay High Court Appellate Side Rules, 1960 & Criminal Manual",
        "mandatory_registry_declarations": [
            "Declaration that no similar application / petition has previously been filed before this Hon'ble Court or the Supreme Court of India.",
            "Declaration that search in the Caveat Register has been made and no caveat is found registered by the Complainant/State.",
            "Application for exemption from filing certified copies of the impugned FIR / charge-sheet (Rule 3 Chapter XXVI)."
        ],
        "statutory_quashing_format": "CRIMINAL WRIT PETITION / CRIMINAL APPLICATION UNDER SECTION 482 CrPC / SECTION 528 BNSS",
        "key_regional_precedents": [
            {"case": "Arun Sharma v. State of Maharashtra", "citation": "2023 Bom CR (Cri) 412", "ratio": "Commercial disputes dressed as criminal cheating must be quashed at inception."}
        ]
    },
    "DELHI_HIGH_COURT": {
        "court_name": "HIGH COURT OF DELHI AT NEW DELHI",
        "bench_options": ["Principal Seat at New Delhi"],
        "governing_rules": "Delhi High Court Rules (Volume III) & Practice Directions for Criminal Matters (2018)",
        "mandatory_registry_declarations": [
            "Advance Service to Standing Counsel (Criminal) for GNCTD / CBI 48 hours prior to listing.",
            "Specific declaration under Delhi High Court e-Filing Practice Directions regarding digital signature verification.",
            "Pagination Certificate and Index of Documents conforming to DHC PDF/A guidelines."
        ],
        "statutory_quashing_format": "CRIMINAL MISCELLANEOUS CASE (CRL.M.C.) UNDER SECTION 482 CrPC / 528 BNSS",
        "key_regional_precedents": [
            {"case": "G. Sagar Suri v. State of U.P.", "citation": "(2000) 2 SCC 636", "ratio": "Duty of court to see criminal proceedings are not used as an instrument of harassment."}
        ]
    },
    "ALLAHABAD_HIGH_COURT": {
        "court_name": "HIGH COURT OF JUDICATURE AT ALLAHABAD",
        "bench_options": ["Principal Seat at Allahabad (Prayagraj)", "Lucknow Bench"],
        "governing_rules": "Allahabad High Court Rules, 1952 (Chapter XXII)",
        "mandatory_registry_declarations": [
            "Declaration regarding personal knowledge and certified annexures under Rule 1 Chapter XXII.",
            "Affidavit of Pairokar / Deponent specifically disclosing relationship with the accused.",
            "Declaration that mediation possibilities under Section 89 have been explored."
        ],
        "statutory_quashing_format": "APPLICATION UNDER SECTION 482 CrPC / 528 BNSS (U/S 482 APPLICATION)",
        "key_regional_precedents": [
            {"case": "Asian Resurfacing of Road Agency v. CBI", "citation": "(2018) 16 SCC 299", "ratio": "Stay on trial proceedings in Section 482 must specify speaking reasons."}
        ]
    },
    "KARNATAKA_HIGH_COURT": {
        "court_name": "HIGH COURT OF KARNATAKA AT BENGALURU",
        "bench_options": ["Principal Bench at Bengaluru", "Dharwad Bench", "Kalaburagi Bench"],
        "governing_rules": "High Court of Karnataka Rules, 1959 & Criminal Practice Directions",
        "mandatory_registry_declarations": [
            "Declaration of service on the State Public Prosecutor (SPP) with acknowledgment memo.",
            "Affidavit verifying English translation of Kannada police records/complaints."
        ],
        "statutory_quashing_format": "CRIMINAL PETITION (CRL.P) UNDER SECTION 482 CrPC / SECTION 528 BNSS",
        "key_regional_precedents": [
            {"case": "U.P. Pollution Control Board v. Modi Distillery", "citation": "(1987) 3 SCC 684", "ratio": "Purely technical curable defects do not warrant quashing where prima facie case exists."}
        ]
    },
    "MADRAS_HIGH_COURT": {
        "court_name": "HIGH COURT OF JUDICATURE AT MADRAS",
        "bench_options": ["Principal Seat at Chennai", "Madurai Bench"],
        "governing_rules": "Madras High Court Appellate Side Rules & Criminal Rules of Practice, 2019",
        "mandatory_registry_declarations": [
            "Criminal Rules of Practice Form No. 1 compliance declaration.",
            "Advance copy served on the Public Prosecutor, High Court Madras."
        ],
        "statutory_quashing_format": "CRIMINAL ORIGINAL PETITION (CRL.O.P.) UNDER SECTION 482 CrPC / 528 BNSS",
        "key_regional_precedents": [
            {"case": "Dr. V.G. Santhosam v. State", "citation": "2021 (2) MWN (Cr.) 19", "ratio": "FIRs filed with oblique motive to coerce civil settlements are liable to be quashed."}
        ]
    }
}

class RegionalBenchEngine:
    """
    Law-firm grade High Court jurisdiction customizer for appellate pleadings.
    """

    @classmethod
    def resolve_high_court_rules(cls, court_str: str, city_str: str) -> Dict[str, Any]:
        """
        Resolves High Court rules based on court or city string.
        """
        combined = f"{court_str} {city_str}".upper()

        if any(x in combined for x in ["DELHI", "NEW DELHI", "NCR"]):
            return HIGH_COURT_RULES["DELHI_HIGH_COURT"]
        elif any(x in combined for x in ["MUMBAI", "BOMBAY", "PUNE", "NAGPUR", "AURANGABAD", "MAHARASHTRA", "THANE"]):
            return HIGH_COURT_RULES["BOMBAY_HIGH_COURT"]
        elif any(x in combined for x in ["ALLAHABAD", "LUCKNOW", "KANPUR", "PRAYAGRAJ", "UTTAR PRADESH", "NOIDA"]):
            return HIGH_COURT_RULES["ALLAHABAD_HIGH_COURT"]
        elif any(x in combined for x in ["BENGALURU", "BANGALORE", "KARNATAKA", "DHARWAD"]):
            return HIGH_COURT_RULES["KARNATAKA_HIGH_COURT"]
        elif any(x in combined for x in ["MADRAS", "CHENNAI", "TAMIL NADU", "MADURAI"]):
            return HIGH_COURT_RULES["MADRAS_HIGH_COURT"]

        return HIGH_COURT_RULES["BOMBAY_HIGH_COURT"]

    @classmethod
    def format_quashing_petition_header(cls, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates bench-specific petition title, heading, and mandatory registry declarations.
        """
        court = case_data.get("court_name", "")
        city = case_data.get("accused_city", case_data.get("complainant_city", "Mumbai"))
        rules = cls.resolve_high_court_rules(court, city)

        return {
            "high_court_name": rules["court_name"],
            "statutory_petition_format": rules["statutory_quashing_format"],
            "governing_rules": rules["governing_rules"],
            "mandatory_registry_declarations": rules["mandatory_registry_declarations"],
            "regional_precedents": rules["key_regional_precedents"],
            "bench_options": rules["bench_options"]
        }
