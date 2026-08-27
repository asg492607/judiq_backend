"""
JudiQ Multi-Track Statutory Recovery Orchestrator
Evaluates concurrent legal enforcement viability across 5 Indian statutory recovery tracks:
Track 1: Negotiable Instruments Act 1881 (Section 138 Criminal Leverage & S.143A Interim Relief)
Track 2: SARFAESI Act 2002 (Section 13(2) Demand, S.13(3A) 15-day SLA, Section 14 CMM/DM Physical Possession)
Track 3: Recovery of Debts and Bankruptcy (RDB) Act 1993 (DRT Section 19 Original Application)
Track 4: Insolvency & Bankruptcy Code (IBC) 2016 (Section 7 Corporate Debtor & Section 95 Personal Guarantor)
Track 5: Regulatory Measures (Look-Out Circulars & RBI Master Circular Wilful Defaulter Tagging)
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field


class MultiTrackEvaluationRequest(BaseModel):
    borrower_name: str
    loan_account_no: str
    default_amount: float
    is_corporate: bool = True
    is_secured: bool = False
    cersai_registered: bool = True
    is_agricultural_land: bool = False
    has_personal_guarantors: bool = True
    has_dishonoured_cheques: bool = True
    cheque_dishonour_date: str = ""
    npa_classification_date: str = ""
    is_wilful_diversion_suspected: bool = False
    has_foreign_travel_flight_risk: bool = False
    current_ots_offer_amount: float = 0.0


class StatutoryTrackResult(BaseModel):
    track_id: str
    track_name: str
    forum_authority: str
    viability_score: int  # 0 to 100
    statutory_status: str  # VIABLE, CONDITIONAL, BARRED, HIGH_LEVERAGE
    limitation_period: str
    primary_legal_provision: str
    authoritative_precedents: List[str]
    immediate_procedural_step: str
    statutory_prerequisites: List[str]
    potential_statutory_traps: List[str]


class MultiTrackStrategyReport(BaseModel):
    case_reference: str
    borrower_name: str
    default_amount: float
    optimal_primary_track: str
    recommended_concurrent_tracks: List[str]
    tracks: Dict[str, StatutoryTrackResult]
    concurrent_forum_compatibility: str
    executive_strategy_summary: str


def evaluate_multi_track_recovery(req: MultiTrackEvaluationRequest) -> MultiTrackStrategyReport:
    """
    Evaluates concurrent viability across 5 statutory recovery tracks with binding Indian legal precedents.
    """
    tracks: Dict[str, StatutoryTrackResult] = {}
    default_amt = float(req.default_amount)

    # -------------------------------------------------------------------------
    # TRACK 1: S.138 NI ACT (CRIMINAL PRESSURE ON DIRECTORS)
    # -------------------------------------------------------------------------
    t1_score = 90 if req.has_dishonoured_cheques else 10
    t1_status = "HIGH_LEVERAGE" if req.has_dishonoured_cheques else "INELIGIBLE"
    t1_prereqs = [
        "Cheque issued for discharge of legally enforceable debt (S.139 presumption)",
        "Presented within 3 months validity window (S.138 proviso a)",
        "Statutory Demand Notice dispatched within 30 days of dishonour memo (S.138 proviso b)"
    ]
    t1_traps = [
        "Filing before 15-day cure window expires creates fatal statutory bar (Yogendra Pratap Singh)",
        "Filing past 30-day window without S.142(1)(b) condonation affidavit causes dismissal"
    ]
    tracks["track_1_s138"] = StatutoryTrackResult(
        track_id="TRACK_S138_CRIMINAL",
        track_name="Section 138 NI Act (Criminal Director Prosecution)",
        forum_authority="Court of Judicial Magistrate First Class (JMFC) / Metropolitan Magistrate (CMM)",
        viability_score=t1_score,
        statutory_status=t1_status,
        limitation_period="30 days from expiry of 15-day statutory notice cure period (S.142)",
        primary_legal_provision="Section 138, 141, 142 & 143A of Negotiable Instruments Act, 1881",
        authoritative_precedents=[
            "Yogendra Pratap Singh v. Savitri Pandey (2014) 10 SCC 713 (SC Full Bench)",
            "Sunil Todi v. State of Gujarat (2021) SCC OnLine SC 1174",
            "M/s Meters and Instruments Pvt Ltd v. Kanchan Mehta (2018) 1 SCC 560"
        ],
        immediate_procedural_step="Issue Section 138(b) Statutory Demand Notice & Petition for 20% Interim Compensation u/s 143A.",
        statutory_prerequisites=t1_prereqs,
        potential_statutory_traps=t1_traps
    )

    # -------------------------------------------------------------------------
    # TRACK 2: SARFAESI ACT (PHYSICAL ASSET SEIZURE)
    # -------------------------------------------------------------------------
    t2_score = 85
    t2_status = "VIABLE"
    t2_prereqs = [
        "Account formally classified as NPA as per RBI prudential norms (S.2(1)(o))",
        "Security interest registered with CERSAI (S.26D mandatory condition precedent)",
        "Debt exceeds ₹1.0 Lakh and outstanding exceeds 20% of principal + interest (S.31(j))"
    ]
    t2_traps = []

    if not req.is_secured:
        t2_score = 0
        t2_status = "BARRED"
        t2_traps.append("Unsecured facility: SARFAESI is inapplicable without an underlying mortgage or hypothecation.")
    elif req.is_agricultural_land:
        t2_score = 10
        t2_status = "BARRED"
        t2_traps.append("Absolute statutory bar u/s 31(i): Security enforcement prohibited over agricultural land (ITC v. Blue Coast Hotels).")
    elif not req.cersai_registered:
        t2_score = 25
        t2_status = "CONDITIONAL"
        t2_traps.append("CERSAI non-registration bar u/s 26D: Bank cannot exercise S.13(4) possession without completed CERSAI registration.")

    tracks["track_2_sarfaesi"] = StatutoryTrackResult(
        track_id="TRACK_SARFAESI_SECURED",
        track_name="SARFAESI Act 2002 (Secured Asset Seizure & Sale)",
        forum_authority="Authorized Officer / Chief Metropolitan Magistrate (CMM) / District Magistrate (DM) u/s 14",
        viability_score=t2_score,
        statutory_status=t2_status,
        limitation_period="Section 36: 12 years for mortgaged immovable property (Article 62 Limitation Act)",
        primary_legal_provision="Section 13(2), 13(3A), 13(4), 14 & 26D of SARFAESI Act, 2002",
        authoritative_precedents=[
            "Transcore v. Union of India (2008) 1 SCC 125 (SC on concurrent S.138 & SARFAESI remedies)",
            "ITC Limited v. Blue Coast Hotels Ltd (2018) 15 SCC 99",
            "Mardia Chemicals Ltd v. Union of India (2004) 4 SCC 311"
        ],
        immediate_procedural_step="Issue formal Section 13(2) Demand Notice with 60-day schedule; monitor 15-day S.13(3A) reply SLA.",
        statutory_prerequisites=t2_prereqs,
        potential_statutory_traps=t2_traps if t2_traps else ["Failure to reply to S.13(3A) representation within 15 days renders subsequent S.14 order void."]
    )

    # -------------------------------------------------------------------------
    # TRACK 3: DEBTS RECOVERY TRIBUNAL (RDB ACT S.19 ORIGINAL APPLICATION)
    # -------------------------------------------------------------------------
    t3_score = 90 if default_amt >= 2000000.0 else 0
    t3_status = "VIABLE" if default_amt >= 2000000.0 else "BARRED"
    t3_traps = []
    if default_amt < 2000000.0:
        t3_traps.append("Pecuniary jurisdiction bar: Minimum debt threshold for DRT is ₹20.0 Lakhs (Ministry of Finance Notification 2018).")

    tracks["track_3_drt"] = StatutoryTrackResult(
        track_id="TRACK_DRT_RDB_ACT",
        track_name="DRT Original Application (RDB Act 1993 S.19 Money Decree)",
        forum_authority="Debts Recovery Tribunal (DRT) / Debts Recovery Appellate Tribunal (DRAT)",
        viability_score=t3_score,
        statutory_status=t3_status,
        limitation_period="3 years from date of default/NPA or last acknowledgement of debt u/s 18 Limitation Act",
        primary_legal_provision="Section 19 of Recovery of Debts and Bankruptcy (RDB) Act, 1993",
        authoritative_precedents=[
            "Mathew Varghese v. M. Amritha Kumar (2014) 5 SCC 610",
            "State Bank of India v. Ranjan Chemicals Ltd (2007) 1 SCC 97"
        ],
        immediate_procedural_step="File Original Application (OA) with interim attachment before judgment (OA Schedule A, B, C).",
        statutory_prerequisites=[
            "Outstanding balance equal to or exceeding ₹20.00 Lakhs",
            "Statement of account certified under Banker's Books Evidence Act 1891 / Section 63 BSA 2023",
            "Loan agreements and revival letters within active limitation"
        ],
        potential_statutory_traps=t3_traps if t3_traps else ["Ensure limitation is kept alive through written debt acknowledgements or revival letters."]
    )

    # -------------------------------------------------------------------------
    # TRACK 4: INSOLVENCY & BANKRUPTCY CODE (IBC S.7 & S.95)
    # -------------------------------------------------------------------------
    t4_score = 70
    t4_status = "CONDITIONAL"
    t4_prereqs = []
    t4_traps = []

    if req.is_corporate:
        if default_amt >= 10000000.0:  # ₹1.00 Crore IBC threshold
            t4_score = 80
            t4_status = "HIGH_LEVERAGE"
            t4_prereqs.append("Default amount meets ₹1.00 Crore Section 4 IBC pecuniary threshold")
            t4_prereqs.append("Default is undisputed on NeSL / Information Utility record")
        else:
            t4_score = 40
            t4_status = "CONDITIONAL"
            t4_traps.append(f"Corporate CIRP u/s 7 requires ₹1.00 Cr minimum default. Current claim is ₹{default_amt/100000:.2f}L.")
            if req.has_personal_guarantors:
                t4_score = 75
                t4_status = "VIABLE"
                t4_prereqs.append("Section 95 Insolvency against Personal Guarantors viable (No ₹1 Cr bar applies to S.95).")

    tracks["track_4_ibc"] = StatutoryTrackResult(
        track_id="TRACK_IBC_INSOLVENCY",
        track_name="Insolvency & Bankruptcy Code (IBC 2016 S.7 CIRP / S.95 Guarantor)",
        forum_authority="National Company Law Tribunal (NCLT) / NCLAT",
        viability_score=t4_score,
        statutory_status=t4_status,
        limitation_period="3 years from date of default (Article 137 Limitation Act / BK Educational Services)",
        primary_legal_provision="Section 7 (Corporate Debtor) & Section 95 (Personal Guarantor) of IBC, 2016",
        authoritative_precedents=[
            "Lalit Kumar Jain v. Union of India (2021) 9 SCC 321 (SC upheld personal guarantor insolvency)",
            "Innoventive Industries Ltd v. ICICI Bank (2018) 1 SCC 407",
            "Dena Bank v. C. Shivakumar Reddy (2021) 10 SCC 330"
        ],
        immediate_procedural_step="Serve Form B Demand Notice u/s 95 on Personal Guarantors & file NeSL default record.",
        statutory_prerequisites=t4_prereqs if t4_prereqs else ["NeSL default authentication certificate", "Valid Personal Guarantee Deed"],
        potential_statutory_traps=t4_traps if t4_traps else ["Moratorium u/s 14 pauses SARFAESI once Section 7 CIRP is admitted."]
    )

    # -------------------------------------------------------------------------
    # TRACK 5: WILFUL DEFAULTER & LOOK-OUT CIRCULAR (LOC)
    # -------------------------------------------------------------------------
    t5_score = 65 if (req.is_wilful_diversion_suspected or req.has_foreign_travel_flight_risk) else 35
    t5_status = "HIGH_LEVERAGE" if req.is_wilful_diversion_suspected else "STANDARD"
    tracks["track_5_loc_wilful"] = StatutoryTrackResult(
        track_id="TRACK_LOC_WILFUL_DEFAULTER",
        track_name="Regulatory Coercion (RBI Wilful Defaulter & Look-Out Circular)",
        forum_authority="Bank Identification Committee & Review Committee / Ministry of Home Affairs & Bureau of Immigration",
        viability_score=t5_score,
        statutory_status=t5_status,
        limitation_period="Applicable throughout loan subsistence during active default",
        primary_legal_provision="RBI Master Circular on Wilful Defaulters (2015/2024) & MHA LOC Guidelines",
        authoritative_precedents=[
            "State Bank of India v. Jah Developers Pvt Ltd (2019) 6 SCC 787 (Right to legal representation in Wilful Defaulter proceedings)",
            "Milind Patel v. Union of India (2024) Bombay High Court (LOC guidelines for public sector banks)"
        ],
        immediate_procedural_step="Issue Show Cause Notice by Identification Committee for diversion of working capital funds.",
        statutory_prerequisites=[
            "Forensic Audit / Transaction Audit showing siphoning or disposal of hypothecated stock",
            "Default threshold of ₹25.0 Lakhs or more (Wilful Defaulter)",
            "Quantifiable flight risk or threat to economic interest of India (LOC request)"
        ],
        potential_statutory_traps=[
            "Failure to grant personal hearing before Review Committee violates Jah Developers natural justice doctrine."
        ]
    )

    # Calculate optimal primary and concurrent tracks
    scores = {k: v.viability_score for k, v in tracks.items()}
    optimal_track = max(scores, key=scores.get)

    recommended_concurrent = [k for k, v in tracks.items() if v.viability_score >= 70 and k != optimal_track]

    compatibility_text = (
        "Concurrent Enforcement Validated: As settled by the Supreme Court in Transcore (2008) and "
        "V.M. Salgaocar (2014), prosecution under Section 138 NI Act (criminal personal remedy) and "
        "SARFAESI/DRT enforcement (civil security recovery) operate in completely distinct statutory fields "
        "and can proceed concurrently without constituting double jeopardy or election of remedies."
    )

    summary = (
        f"Multi-track recovery analysis for account {req.loan_account_no} (Claim: ₹{default_amt/100000:.2f} Lakhs): "
        f"Primary track recommendation is '{tracks[optimal_track].track_name}' (Viability: {tracks[optimal_track].viability_score}%). "
        f"Simultaneous deployment of {len(recommended_concurrent)} secondary tracks will maximize recovery pressure."
    )

    return MultiTrackStrategyReport(
        case_reference=req.loan_account_no,
        borrower_name=req.borrower_name,
        default_amount=default_amt,
        optimal_primary_track=tracks[optimal_track].track_name,
        recommended_concurrent_tracks=[tracks[k].track_name for k in recommended_concurrent],
        tracks=tracks,
        concurrent_forum_compatibility=compatibility_text,
        executive_strategy_summary=summary
    )
