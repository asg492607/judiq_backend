from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class DefectSeverity(str, Enum):
    FATAL_STATUTORY_BAR = "FATAL_STATUTORY_BAR"       # Non-curable legal defect or statutory bar
    LIMITATION_LAPSE = "LIMITATION_LAPSE"             # Limitation period expired (requires condonation application)
    PROCEDURAL_CURABLE = "PROCEDURAL_CURABLE"         # Procedural defect that can be remedied
    EVIDENTIARY_GAP = "EVIDENTIARY_GAP"               # Missing document / proof of service
    COMPLIANT = "COMPLIANT"                           # Fully compliant with statutory mandate


@dataclass
class RuleDefinition:
    rule_id: str
    title: str
    statute_source: str
    section_provision: str
    effective_date: str
    governing_body: str
    defect_severity: DefectSeverity
    authoritative_precedent: str
    statutory_mandate: str
    remediation_guidance: str


# ==============================================================================
# STATUTORY LEGAL-RULE REGISTRY FOR RECOVERY & BANKING LITIGATION
# ==============================================================================

STATUTORY_RULE_REGISTRY: Dict[str, RuleDefinition] = {
    # --------------------------------------------------------------------------
    # SECTION 138 NI ACT STATUTORY RULES
    # --------------------------------------------------------------------------
    "RULE_RBI_CHEQUE_3M_VALIDITY": RuleDefinition(
        rule_id="RULE_RBI_CHEQUE_3M_VALIDITY",
        title="3-Month Cheque Presentation Statutory Validity Window",
        statute_source="RBI Master Circular on Cheque Validity / NI Act Section 138 Proviso (a)",
        section_provision="Section 138(a) NI Act read with RBI Circular DBOD.AML.BC.No.47/14.01.001/2011-12",
        effective_date="2012-04-01",
        governing_body="Reserve Bank of India & Supreme Court of India",
        defect_severity=DefectSeverity.FATAL_STATUTORY_BAR,
        authoritative_precedent="Rameshchandra Joshi v. Bank of Baroda (2014) SC",
        statutory_mandate="Cheque must be presented to the drawee bank within 3 months from the date on which it is drawn.",
        remediation_guidance="Cheque is stale/invalid for S.138 criminal prosecution. Bank must pursue civil recovery suit or seek fresh instrument/mandate."
    ),

    "RULE_NI_138_DISHONOUR_MEMO": RuleDefinition(
        rule_id="RULE_NI_138_DISHONOUR_MEMO",
        title="Bank Return Memo Statutory Presumption",
        statute_source="Negotiable Instruments Act, 1881",
        section_provision="Section 146 NI Act",
        effective_date="1881-12-09",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.EVIDENTIARY_GAP,
        authoritative_precedent="M.M.T.C. Ltd. v. Medchl Chemicals and Pharma (P) Ltd. (2002) 1 SCC 234",
        statutory_mandate="Official bank return slip/memo with bank seal constitutes presumptive proof of dishonour u/s 146.",
        remediation_guidance="Obtain original stamped bank dishonour memo from the clearing branch before issuing legal notice or filing complaint."
    ),

    "RULE_NI_138B_NOTICE_30D": RuleDefinition(
        rule_id="RULE_NI_138B_NOTICE_30D",
        title="Mandatory 30-Day Statutory Demand Notice Window",
        statute_source="Negotiable Instruments Act, 1881",
        section_provision="Section 138(b) NI Act",
        effective_date="2003-02-06",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.FATAL_STATUTORY_BAR,
        authoritative_precedent="Central Bank of India v. Saxons Farms (1999) 8 SCC 221",
        statutory_mandate="Statutory demand notice in writing must be dispatched within 30 days of receiving the bank dishonour memo.",
        remediation_guidance="Fatal statutory defect if missed. Criminal complaint u/s 138 will be quashed. Recovery must proceed via civil suit / DRT / SARFAESI."
    ),

    "RULE_NI_138C_CURE_15D": RuleDefinition(
        rule_id="RULE_NI_138C_CURE_15D",
        title="15-Day Statutory Cure Window for Drawer Payment",
        statute_source="Negotiable Instruments Act, 1881",
        section_provision="Section 138(c) NI Act",
        effective_date="1881-12-09",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.FATAL_STATUTORY_BAR,
        authoritative_precedent="Subodh S. Salaskar v. Jayprakash M. Shah (2008) 13 SCC 689",
        statutory_mandate="Cause of action for filing criminal complaint arises only upon failure of drawer to make payment within 15 days of notice receipt.",
        remediation_guidance="Do not file complaint before expiry of 15 full days from notice delivery date. Premature filing is fatal per Yogendra Pratap Singh."
    ),

    "RULE_NI_142_LIMITATION_30D": RuleDefinition(
        rule_id="RULE_NI_142_LIMITATION_30D",
        title="Section 142(1)(b) 1-Month Limitation for Criminal Complaint Filing",
        statute_source="Negotiable Instruments Act, 1881",
        section_provision="Section 142(1)(b) NI Act",
        effective_date="2003-02-06",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.LIMITATION_LAPSE,
        authoritative_precedent="Yogendra Pratap Singh v. Savitri Pandey (2014) 10 SCC 713",
        statutory_mandate="Complaint must be instituted within 1 month (30 days) from the date on which the 15-day cure window expires.",
        remediation_guidance="If delayed past 30 days, draft and file a formal Application for Condonation of Delay under Section 142(1)(b) Proviso citing sufficient cause."
    ),

    "RULE_NI_141_VICARIOUS_LIABILITY": RuleDefinition(
        rule_id="RULE_NI_141_VICARIOUS_LIABILITY",
        title="Company Arraignment & Director Vicarious Liability Standards",
        statute_source="Negotiable Instruments Act, 1881",
        section_provision="Section 141 NI Act",
        effective_date="1881-12-09",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.FATAL_STATUTORY_BAR,
        authoritative_precedent="Aneeta Hada v. Godfather Travels & Tours Pvt. Ltd. (2012) 5 SCC 661 & S.M.S. Pharmaceuticals (2005)",
        statutory_mandate="Where the drawer is a company, the company must be arraigned as prime accused and specific averments of day-to-day management must be pled.",
        remediation_guidance="Ensure the corporate borrower entity is named as Accused No. 1 and signatory / managing directors are specifically averred."
    ),

    # --------------------------------------------------------------------------
    # SARFAESI ACT 2002 & DRT RECOVERY RULES
    # --------------------------------------------------------------------------
    "RULE_SARFAESI_26D_CERSAI_BAR": RuleDefinition(
        rule_id="RULE_SARFAESI_26D_CERSAI_BAR",
        title="Section 26D CERSAI Security Interest Registration Condition Precedent",
        statute_source="Securitisation and Reconstruction of Financial Assets and Enforcement of Security Interest Act, 2002",
        section_provision="Section 26D SARFAESI Act, 2002",
        effective_date="2020-01-24",
        governing_body="Central Registry of Securitisation Asset Reconstruction and Security Interest (CERSAI) / Ministry of Finance",
        defect_severity=DefectSeverity.FATAL_STATUTORY_BAR,
        authoritative_precedent="Union of India v. CERSAI Compliance Benches (2020)",
        statutory_mandate="Secured creditor cannot exercise any Chapter III enforcement rights (including S.13(2) and physical possession) unless the security interest is registered with CERSAI.",
        remediation_guidance="Register security interest on CERSAI portal immediately and attach the CERSAI registration certificate before proceeding."
    ),

    "RULE_SARFAESI_13_2_DEMAND": RuleDefinition(
        rule_id="RULE_SARFAESI_13_2_DEMAND",
        title="Section 13(2) 60-Day Statutory Demand Notice",
        statute_source="SARFAESI Act, 2002",
        section_provision="Section 13(2) SARFAESI Act",
        effective_date="2002-06-21",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.FATAL_STATUTORY_BAR,
        authoritative_precedent="Mardia Chemicals Ltd. v. Union of India (2004) 4 SCC 311",
        statutory_mandate="Creditor must serve a 60-day demand notice detailing outstanding debt and secured assets upon NPA classification.",
        remediation_guidance="Issue formal S.13(2) statutory demand notice to borrower and all corporate/personal guarantors with precise asset schedules."
    ),

    "RULE_SARFAESI_13_3A_REPLY": RuleDefinition(
        rule_id="RULE_SARFAESI_13_3A_REPLY",
        title="Mandatory 15-Day Reasoned Objection Disposal",
        statute_source="SARFAESI Act, 2002",
        section_provision="Section 13(3A) SARFAESI Act",
        effective_date="2004-11-11",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.FATAL_STATUTORY_BAR,
        authoritative_precedent="ITC Ltd. v. Blue Coast Hotels Ltd. (2018) 15 SCC 99",
        statutory_mandate="Bank must consider borrower representation/objection and communicate reasoned rejection within 15 days.",
        remediation_guidance="Ensure authorized officer issues reasoned reply within 15 days of borrower's representation before taking Section 13(4) measures."
    ),

    "RULE_SARFAESI_31_AGRI_EXEMPTION": RuleDefinition(
        rule_id="RULE_SARFAESI_31_AGRI_EXEMPTION",
        title="Section 31(i) Agricultural Land Statutory Exemption Audit",
        statute_source="SARFAESI Act, 2002",
        section_provision="Section 31(i) SARFAESI Act",
        effective_date="2002-06-21",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.FATAL_STATUTORY_BAR,
        authoritative_precedent="ITC Ltd. v. Blue Coast Hotels Ltd. (2018) & K. Sreedhar v. R.M. Muthiah (2023)",
        statutory_mandate="Provisions of SARFAESI Act do not apply to any security interest created in agricultural land.",
        remediation_guidance="Verify revenue records (7/12 extract / RTC / Jamabandi). If land is non-agricultural, obtain NA conversion order to avoid S.17 DRT quashing."
    ),

    # --------------------------------------------------------------------------
    # EVIDENTIARY COMPLETENESS RULES
    # --------------------------------------------------------------------------
    "RULE_EVIDENCE_POSTAL_PROOF": RuleDefinition(
        rule_id="RULE_EVIDENCE_POSTAL_PROOF",
        title="Speed Post Consignment & Delivery Proof Audit",
        statute_source="Indian Evidence Act, 1872 / Section 27 General Clauses Act",
        section_provision="Section 27 General Clauses Act read with Section 114 Indian Evidence Act",
        effective_date="1897-03-11",
        governing_body="Supreme Court of India",
        defect_severity=DefectSeverity.EVIDENTIARY_GAP,
        authoritative_precedent="C.C. Alavi Haji v. Palapetty Muhammed (2007) 6 SCC 555",
        statutory_mandate="Registered Speed Post postal receipt with India Post tracking report proving dispatch to correct address establishes presumptive delivery.",
        remediation_guidance="Download and attach official India Post delivery confirmation track report with date/time stamp to prove receipt."
    ),

    "RULE_EVIDENCE_LOAN_SANCTION": RuleDefinition(
        rule_id="RULE_EVIDENCE_LOAN_SANCTION",
        title="Sanction Letter & Legally Enforceable Debt Documentation",
        statute_source="Negotiable Instruments Act, 1881 / Indian Contract Act, 1872",
        section_provision="Section 138 Explanation & Section 139 NI Act",
        effective_date="1881-12-09",
        governing_body="Parliament of India",
        defect_severity=DefectSeverity.EVIDENTIARY_GAP,
        authoritative_precedent="Bir Singh v. Mukesh Kumar (2019) 4 SCC 197",
        statutory_mandate="Existence of legally enforceable debt must be supported by sanction letter, loan agreement, and certified account statement.",
        remediation_guidance="Attach stamped loan sanction letter, promissory note / facility agreement, and certified Banker's Books Evidence ledger."
    )
}
