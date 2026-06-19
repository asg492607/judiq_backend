"""
JudiQ Jurisdiction Mapping Engine
Implements the post-2015 amendment to Section 142 of the NI Act, 1881
and the Dashrath Rupsingh Rathod vs. State of Maharashtra (2014) ruling.

Legal Background:
-----------------
Pre-2015: Courts in ANY of the 5 locations could take cognizance.
Post-2015 Amendment (Section 142(2)):
    - Complaint MUST be filed where the cheque is delivered for collection
      through the PAYEE'S bank account (i.e., payee bank branch location).
    - If cheque was delivered directly to the drawer's bank:
      court at the drawer's bank branch location.
    - Exceptions: if payee doesn't maintain a bank account, the court where
      the drawer or drawee bank is situated.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


# ── Known Major Bank IFSC Prefix → State/City Mapping ─────────────────────────
# Real-world: would query RBI IFSC API. This is our deterministic fallback map.
IFSC_STATE_MAP = {
    # State Bank of India (SBIN)
    "SBIN0": "SBI Branch (Location per IFSC)",
    # HDFC
    "HDFC0": "HDFC Branch (Location per IFSC)",
    # ICICI
    "ICIC0": "ICICI Branch (Location per IFSC)",
    # Axis
    "UTIB0": "Axis Bank Branch (Location per IFSC)",
    # Punjab National Bank
    "PUNB0": "PNB Branch (Location per IFSC)",
    # Kotak
    "KKBK0": "Kotak Mahindra Branch (Location per IFSC)",
    # Bank of Baroda
    "BARB0": "Bank of Baroda Branch (Location per IFSC)",
}


# ── Court Tier Mapping by City/District ───────────────────────────────────────
METRO_CITIES = {
    "mumbai", "delhi", "new delhi", "kolkata", "calcutta", "chennai", "madras",
    "bangalore", "bengaluru", "hyderabad", "ahmedabad", "pune", "surat",
    "jaipur", "lucknow", "kanpur", "nagpur", "indore", "bhopal", "visakhapatnam"
}


def get_court_tier(city: str) -> str:
    """Determine court tier based on city classification."""
    city_lower = city.strip().lower()
    if city_lower in METRO_CITIES:
        return "Metropolitan Magistrate Court"
    return "Judicial Magistrate First Class (JMFC)"


def map_jurisdiction(case_data: Dict) -> Dict:
    """
    Core jurisdiction mapping function.

    Post-2015 Amendment Priority Order:
    1. Payee's bank branch location (PRIMARY — where cheque was deposited for collection)
    2. Drawer's bank branch location (if cheque handed directly)
    3. Place of business/residence of drawer (exceptional cases)

    Returns a structured jurisdiction recommendation with legal basis.
    """
    payee_bank = case_data.get("payee_bank_name") or case_data.get("bank_name") or ""
    payee_branch = case_data.get("payee_branch") or case_data.get("branch_name") or ""
    payee_bank_city = case_data.get("payee_bank_city") or ""

    if not payee_bank_city and payee_branch:
        payee_bank_city = _extract_city(payee_branch)

    drawer_bank = case_data.get("drawer_bank_name") or ""
    drawer_bank_city = case_data.get("drawer_bank_city") or ""

    accused_city = (
        case_data.get("accused_city")
        or _extract_city(case_data.get("accused_address", ""))
        or ""
    )

    # ── Decision Logic (S.142(2) Post-2015) ──────────────────────────────────
    primary_city = ""
    basis = ""
    confidence = "HIGH"
    warnings = []

    if payee_bank_city:
        primary_city = payee_bank_city
        basis = (
            f"The cheque was deposited at {payee_bank}, {payee_branch} "
            f"({''.join([payee_bank_city])}). Under Section 142(2) of the NI Act "
            f"(post-2015 amendment), the court at the location of the PAYEE'S "
            f"BANK BRANCH where the cheque was deposited for collection has "
            f"exclusive jurisdiction."
        )
    elif drawer_bank_city:
        primary_city = drawer_bank_city
        basis = (
            f"No payee bank city provided. Falling back to the DRAWER'S BANK "
            f"branch location ({drawer_bank}, {drawer_bank_city}). "
            f"Applicable when cheque is presented directly to the drawer's bank."
        )
        confidence = "MEDIUM"
        warnings.append(
            "⚠️ Confirm whether cheque was presented via payee's own bank account "
            "or directly at drawer's bank to ensure correct jurisdiction."
        )
    elif accused_city:
        primary_city = accused_city
        basis = (
            f"Fallback: Using accused's city ({accused_city}). This is the "
            f"court at the drawer's registered place of business/residence."
        )
        confidence = "LOW"
        warnings.append(
            "🚨 LOW CONFIDENCE: Payee bank and drawer bank locations are missing. "
            "Jurisdiction is highly fact-specific — consult the bank's IFSC records."
        )
    else:
        return {
            "status": "INSUFFICIENT_DATA",
            "recommendation": "Cannot determine jurisdiction — bank branch location not provided.",
            "action_required": "Please provide the Payee Bank branch city/district.",
            "legal_basis": "Section 142(2) NI Act (2015 Amendment)",
            "confidence": "NONE",
            "warnings": ["Provide payee bank branch location to enable jurisdiction mapping."]
        }

    supplied_court = str(case_data.get("court_name") or "").strip().lower()
    if supplied_court and primary_city and primary_city.lower() not in supplied_court:
        return {
            "status": "INVALID",
            "recommended_court": f"{get_court_tier(primary_city)}, {primary_city.title()}",
            "primary_city": primary_city.title(),
            "confidence": confidence,
            "legal_basis": basis,
            "reason": f"Filed court '{case_data.get('court_name')}' does not align with S.142(2) territorial jurisdiction at {primary_city.title()}.",
            "warnings": warnings + ["Territorial jurisdiction mismatch triggers a maintainability defect."],
        }

    court_tier = get_court_tier(primary_city)
    court_name = f"{court_tier}, {primary_city.title()}"

    # ── Alternative Courts (For Awareness) ───────────────────────────────────
    alternate_courts = []
    if drawer_bank_city and drawer_bank_city.lower() != primary_city.lower():
        alternate_courts.append({
            "court": f"{get_court_tier(drawer_bank_city)}, {drawer_bank_city.title()}",
            "basis": "Drawer's bank branch (applicable if cheque presented directly)",
            "applicability": "CONDITIONAL"
        })
    if accused_city and accused_city.lower() != primary_city.lower():
        alternate_courts.append({
            "court": f"{get_court_tier(accused_city)}, {accused_city.title()}",
            "basis": "Place of business/residence of drawer (pre-2015 fallback, now overruled)",
            "applicability": "OVERRULED — Do NOT file here post-2015"
        })

    return {
        "status": "RESOLVED",
        "recommended_court": court_name,
        "primary_city": primary_city.title(),
        "court_tier": court_tier,
        "confidence": confidence,
        "legal_basis": basis,
        "key_ruling": "Dashrath Rupsingh Rathod vs. State of Maharashtra (2014) 9 SCC 129 — "
                      "Prospectively overruled by 2015 Amendment to Section 142(2) NI Act.",
        "amendment_year": 2015,
        "section": "Section 142(2), Negotiable Instruments Act, 1881",
        "alternate_courts": alternate_courts,
        "warnings": warnings,
        "filing_checklist": [
            f"✅ File complaint before: {court_name}",
            "✅ Attach bank's IFSC certificate confirming branch location falls within court's jurisdiction",
            "✅ Ensure payee bank statement showing deposit at the above branch is annexed",
            "✅ If jurisdiction is challenged, cite: Nishant Aggarwal vs. Kailash Kumar Sharma (2016) SC"
        ]
    }


def _extract_city(address: str) -> Optional[str]:
    """Heuristic: extract last meaningful token from address as city guess."""
    if not address:
        return None
    parts = [p.strip() for p in address.replace(",", " ").split() if len(p.strip()) > 2]
    # Skip PIN codes
    meaningful = [p for p in parts if not p.isdigit()]
    return meaningful[-1] if meaningful else None

def apply_jurisdiction_guards(jurisdiction_info: Dict, concepts: list, final_score: float) -> float:
    """Applies S.142(2) territorial jurisdiction fatal defect checks."""
    if jurisdiction_info.get("status") == "INVALID":
        # Jurisdiction is territorial and critical under S.142(2) NI Act. Applying severe penalty.
        judicially_adjusted_score = max(0, final_score - 35)
        if "jurisdictional_defect" not in {c.get("concept") for c in concepts}:
            concepts.append({
                "concept": "jurisdictional_defect", 
                "confidence": 0.95, 
                "legal_impact": "FATAL: Wrong territorial jurisdiction. Complaint will be returned under Dashrath Rupsingh Rathod precedent."
            })
        return judicially_adjusted_score
    return final_score
