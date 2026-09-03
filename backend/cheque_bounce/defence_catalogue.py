"""
JudiQ AI — Section 138 NI Act Defense Catalogue & Rebuttal Matrix
Structured defense arguments, evidentiary thresholds, and precedent authorities for NI Act litigation.
"""

from typing import Dict, Any, List

class Section138DefenceCatalogue:
    """
    Catalogues substantive and procedural defenses in Section 138 proceedings
    with corresponding statutory precedents and counter-strategies.
    """

    DEFENCE_PATTERNS = {
        "security_cheque": {
            "name": "Security Cheque Defense",
            "statutory_basis": "Section 138 Explanation (Legally Enforceable Debt)",
            "key_precedent": "Sunil Todi v. State of Gujarat (2021) 16 SCC 293 / Indus Airways v. Magnum Aviation (2014) 12 SCC 539",
            "principle": "A cheque issued as security for an existing or contingent liability is enforceable once the liability crystallizes prior to presentation.",
            "evidentiary_burden": "Accused must demonstrate that on the date of cheque presentation, no crystallized debt had matured.",
            "complainant_counter": "Produce ledger statements, invoices, and purchase orders confirming liability crystallised prior to presentation."
        },
        "signature_dispute": {
            "name": "Signature Dispute / Forgery Defense",
            "statutory_basis": "Section 138 (Cheque drawn on an account maintained by drawer)",
            "key_precedent": "Ajitsinh Cheharsinh Rathod v. G.V. Brahmbhatt (2024) 4 SCC 341",
            "principle": "Merely denying signature is insufficient. Accused must apply under Section 45 IEA / Section 39 BSA for Forensic Hand-writing Expert comparison.",
            "evidentiary_burden": "Accused must produce contemporaneous specimen signatures and file an expert examination application before defense evidence closes.",
            "complainant_counter": "Rely on Section 146 bank memo (which cited 'Funds Insufficient', not 'Signature Differs') to create strong presumption."
        },
        "time_barred_debt": {
            "name": "Time-Barred Debt Defense",
            "statutory_basis": "Section 138 Explanation read with Section 25(3) Indian Contract Act, 1872",
            "key_precedent": "K. Hymavathi v. State of A.P. (2023) SCC OnLine SC 1128",
            "principle": "A cheque issued for a time-barred debt constitutes a valid promise to pay under Section 25(3) ICA if signed by drawer.",
            "evidentiary_burden": "Accused must prove the underlying debt exceeded 3 years limitation without written acknowledgement.",
            "complainant_counter": "Argue that execution of signed cheque constitutes fresh written acknowledgment of liability u/s 25(3) ICA."
        },
        "notice_non_service": {
            "name": "Non-Service of Statutory Notice",
            "statutory_basis": "Section 138(b) read with Section 27 General Clauses Act, 1897",
            "key_precedent": "C.C. Alavi Haji v. Palapetty Muhammed (2007) 6 SCC 555",
            "principle": "Where notice is sent to correct address by Registered Post / Speed Post, valid service is presumed. Drawer cannot claim non-receipt without paying within 15 days of summons.",
            "evidentiary_burden": "Accused must establish notice was sent to a bogus or incorrect address.",
            "complainant_counter": "Furnish postal dispatch receipt, tracking delivery confirmation, and address proof from KYC/contracts."
        },
        "lack_of_financial_capacity": {
            "name": "Lack of Financial Capacity of Complainant",
            "statutory_basis": "Section 139 Rebuttal of Presumption",
            "key_precedent": "Tedhi Singh v. Narayan Dass (2020) 6 SCC 738 / APS Forex Services v. Shakti International (2020) 12 SCC 724",
            "principle": "Accused must raise a probable defense in cross-examination questioning source of funds before complainant is required to prove financial capacity.",
            "evidentiary_burden": "Accused must elicit material admissions during complainant cross-examination regarding absence of ITR declaration or bank withdrawal.",
            "complainant_counter": "Place Income Tax Returns (ITR), audited balance sheets, and bank account withdrawal slips on record."
        }
    }

    @classmethod
    def get_defense_intel(cls, defense_key: str) -> Dict[str, Any]:
        """Returns comprehensive defense strategy for given posture."""
        return cls.DEFENCE_PATTERNS.get(defense_key, {
            "name": "General Section 138 Defense",
            "statutory_basis": "Section 138/139 NI Act",
            "key_precedent": "Rangappa v. Sri Mohan (2010) 11 SCC 441",
            "principle": "Rebut presumption by preponderance of probabilities.",
            "evidentiary_burden": "Raise credible doubts on legal liability.",
            "complainant_counter": "Rely on documentary contracts and bank dishonour memo."
        })

    @classmethod
    def analyze_case_defenses(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifies applicable defenses based on case signals."""
        identified = []
        is_security = case_data.get("is_security_cheque") or case_data.get("security_cheque")
        if is_security:
            identified.append(cls.get_defense_intel("security_cheque"))

        if case_data.get("disputed_signature") or case_data.get("signature_mismatch"):
            identified.append(cls.get_defense_intel("signature_dispute"))

        if case_data.get("notice_served") is False or case_data.get("notice_delivery_disputed"):
            identified.append(cls.get_defense_intel("notice_non_service"))

        if case_data.get("time_barred") or case_data.get("debt_older_than_3_years"):
            identified.append(cls.get_defense_intel("time_barred_debt"))

        return identified
