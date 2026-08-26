import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from utils import days_between, parse_date
from .rule_registry import STATUTORY_RULE_REGISTRY, RuleDefinition, DefectSeverity

logger = logging.getLogger("JudiQ.BankRecovery")


class BankRecoveryEngine:
    """
    Deterministic, Rule-Based Recovery & Statutory Compliance Engine for Banking & NBFC Operations.
    Evaluates default files against statutory rules (NI Act, SARFAESI, RBI Master Directions),
    identifies fatal legal defects, computes recovery viability scores, generates empaneled advocate dossiers,
    and produces tamper-evident Regulatory Audit Trail / Compliance Evidence Ledgers.
    """

    @classmethod
    def evaluate_recovery_case(cls, case_data: Dict[str, Any], officer_id: str = "BANK_OFFICER_DEFAULT", branch_name: str = "Main Branch") -> Dict[str, Any]:
        """
        Executes a 100% deterministic statutory audit of a banking recovery or default matter.
        """
        case_type = case_data.get("case_type", "Cheque Bounce (S.138)")
        borrower_name = case_data.get("borrower_name") or case_data.get("accused_name", "Borrower Entity")
        loan_account_no = case_data.get("loan_account_no") or case_data.get("case_id", "LN/REC/2026/001")
        default_amount = float(case_data.get("default_amount") or case_data.get("cheque_amount") or 0.0)

        # Dates extraction
        cheque_date = case_data.get("cheque_date")
        dishonour_date = case_data.get("dishonour_date") or case_data.get("date_of_dishonour")
        notice_date = case_data.get("notice_date") or case_data.get("date_of_notice")
        delivery_date = case_data.get("delivery_date") or case_data.get("notice_delivered_date")
        complaint_date = case_data.get("complaint_date") or case_data.get("date_of_complaint")

        # Fallback date inference if not explicitly provided
        if notice_date and not delivery_date:
            # Presume statutory postal delivery window of 3 days
            try:
                parsed_n = parse_date(notice_date)
                if parsed_n:
                    from datetime import timedelta
                    delivery_date = (parsed_n + timedelta(days=3)).strftime("%Y-%m-%d")
            except Exception:
                pass

        rule_evaluations: List[Dict[str, Any]] = []
        milestones: List[Dict[str, Any]] = []
        fatal_defects: List[Dict[str, Any]] = []
        limitation_warnings: List[Dict[str, Any]] = []
        curable_defects: List[Dict[str, Any]] = []

        # ======================================================================
        # 1. CHEQUE PRESENTATION STATUTORY VALIDITY AUDIT (3 MONTHS)
        # ======================================================================
        pres_days = None
        pres_status = "COMPLIANT"
        pres_defect_text = None

        if cheque_date and dishonour_date:
            pres_days = days_between(cheque_date, dishonour_date)
            if pres_days is not None and pres_days > 92: # > 3 calendar months
                rule = STATUTORY_RULE_REGISTRY["RULE_RBI_CHEQUE_3M_VALIDITY"]
                pres_status = rule.defect_severity.value
                pres_defect_text = f"Cheque presented after {pres_days} days (Statutory Limit: 3 calendar months u/s 138(a) & RBI DBOD Circular). Cheque is legally stale."
                fatal_defects.append({
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "statute": rule.section_provision,
                    "severity": rule.defect_severity.value,
                    "finding": pres_defect_text,
                    "precedent": rule.authoritative_precedent,
                    "remediation": rule.remediation_guidance
                })

        milestones.append({
            "milestone_id": "M1_CHEQUE_PRESENTATION",
            "name": "Cheque Presentation & 3-Month Validity",
            "statute": "Section 138(a) NI Act & RBI DBOD Circular",
            "event_date": dishonour_date,
            "interval_days": pres_days,
            "status": "PASSED" if pres_status == "COMPLIANT" else "FATAL_BAR",
            "defect": pres_defect_text
        })

        # ======================================================================
        # 2. DISHONOUR MEMO & SECTION 146 PRESUMPTION AUDIT
        # ======================================================================
        has_dishonour_memo = case_data.get("dishonour_memo", True)
        if not has_dishonour_memo:
            rule = STATUTORY_RULE_REGISTRY["RULE_NI_138_DISHONOUR_MEMO"]
            curable_defects.append({
                "rule_id": rule.rule_id,
                "title": rule.title,
                "statute": rule.section_provision,
                "severity": rule.defect_severity.value,
                "finding": "Original stamped bank dishonour memo not attached in case file.",
                "precedent": rule.authoritative_precedent,
                "remediation": rule.remediation_guidance
            })

        # ======================================================================
        # 3. SECTION 138(b) 30-DAY STATUTORY NOTICE AUDIT
        # ======================================================================
        notice_days = None
        notice_status = "COMPLIANT"
        notice_defect_text = None

        if dishonour_date and notice_date:
            notice_days = days_between(dishonour_date, notice_date)
            if notice_days is not None and notice_days > 30:
                rule = STATUTORY_RULE_REGISTRY["RULE_NI_138B_NOTICE_30D"]
                notice_status = rule.defect_severity.value
                notice_defect_text = f"Statutory Demand Notice dispatched on day {notice_days} post-dishonour. Exceeds mandatory 30-day statutory window u/s 138(b)."
                fatal_defects.append({
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "statute": rule.section_provision,
                    "severity": rule.defect_severity.value,
                    "finding": notice_defect_text,
                    "precedent": rule.authoritative_precedent,
                    "remediation": rule.remediation_guidance
                })

        milestones.append({
            "milestone_id": "M2_STATUTORY_NOTICE",
            "name": "Section 138(b) 30-Day Demand Notice Dispatch",
            "statute": "Section 138(b) NI Act",
            "event_date": notice_date,
            "interval_days": notice_days,
            "status": "PASSED" if notice_status == "COMPLIANT" else "FATAL_BAR",
            "defect": notice_defect_text
        })

        # ======================================================================
        # 4. SECTION 138(c) 15-DAY MANDATORY CURE WINDOW AUDIT
        # ======================================================================
        cure_status = "PASSED"
        cure_defect_text = None
        days_from_delivery = None

        if delivery_date and complaint_date:
            days_from_delivery = days_between(delivery_date, complaint_date)
            if days_from_delivery is not None and days_from_delivery < 15:
                rule = STATUTORY_RULE_REGISTRY["RULE_NI_138C_CURE_15D"]
                cure_status = "FATAL_BAR"
                cure_defect_text = f"Complaint filed prematurely on day {days_from_delivery} post-receipt. Cause of action only matures on day 16 u/s 138(c) per Yogendra Pratap Singh."
                fatal_defects.append({
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "statute": rule.section_provision,
                    "severity": rule.defect_severity.value,
                    "finding": cure_defect_text,
                    "precedent": rule.authoritative_precedent,
                    "remediation": rule.remediation_guidance
                })

        milestones.append({
            "milestone_id": "M3_CURE_WINDOW",
            "name": "15-Day Mandatory Payment Cure Window",
            "statute": "Section 138(c) NI Act",
            "event_date": delivery_date,
            "interval_days": 15,
            "status": cure_status,
            "defect": cure_defect_text
        })

        # ======================================================================
        # 5. SECTION 142(1)(b) 1-MONTH LIMITATION FOR COMPLAINT FILING
        # ======================================================================
        filing_status = "PASSED"
        filing_defect_text = None

        if delivery_date and complaint_date:
            days_post_cure = days_from_delivery - 15 if days_from_delivery is not None else None
            if days_post_cure is not None and days_post_cure > 30:
                rule = STATUTORY_RULE_REGISTRY["RULE_NI_142_LIMITATION_30D"]
                filing_status = "LIMITATION_LAPSE"
                condonation_attached = case_data.get("condonation_attached", False)
                
                if condonation_attached:
                    filing_defect_text = f"Complaint filed {days_post_cure} days post cure window (Limit: 30 days). Condonation Application u/s 142(1)(b) Proviso is attached."
                    curable_defects.append({
                        "rule_id": rule.rule_id,
                        "title": rule.title,
                        "statute": rule.section_provision,
                        "severity": DefectSeverity.PROCEDURAL_CURABLE.value,
                        "finding": filing_defect_text,
                        "precedent": rule.authoritative_precedent,
                        "remediation": "Argue sufficient cause under S.142(1)(b) proviso during pre-summoning verification."
                    })
                    limitation_warnings.append({
                        "rule_id": rule.rule_id,
                        "title": rule.title,
                        "statute": rule.section_provision,
                        "severity": DefectSeverity.PROCEDURAL_CURABLE.value,
                        "finding": filing_defect_text,
                        "precedent": rule.authoritative_precedent,
                        "remediation": "Argue sufficient cause under S.142(1)(b) proviso during pre-summoning verification."
                    })
                else:
                    filing_defect_text = f"Complaint filed {days_post_cure} days post cure window without S.142(1)(b) Condonation Application. Cognizance barred by limitation."
                    fatal_defects.append({
                        "rule_id": rule.rule_id,
                        "title": rule.title,
                        "statute": rule.section_provision,
                        "severity": rule.defect_severity.value,
                        "finding": filing_defect_text,
                        "precedent": rule.authoritative_precedent,
                        "remediation": rule.remediation_guidance
                    })
                    limitation_warnings.append({
                        "rule_id": rule.rule_id,
                        "title": rule.title,
                        "statute": rule.section_provision,
                        "severity": rule.defect_severity.value,
                        "finding": filing_defect_text,
                        "precedent": rule.authoritative_precedent,
                        "remediation": rule.remediation_guidance
                    })
                    filing_status = "FATAL_BAR"

        milestones.append({
            "milestone_id": "M4_COMPLAINT_FILING",
            "name": "Section 142 Criminal Complaint Institution",
            "statute": "Section 142(1)(b) NI Act",
            "event_date": complaint_date,
            "interval_days": days_from_delivery,
            "status": "PASSED" if filing_status == "PASSED" else ("LIMITATION_LAPSE" if case_data.get("condonation_attached") else "FATAL_BAR"),
            "defect": filing_defect_text
        })

        # ======================================================================
        # 6. SARFAESI & SECURITY ENFORCEMENT AUDIT (IF APPLICABLE)
        # ======================================================================
        is_sarfaesi = "SARFAESI" in case_type or case_data.get("is_secured", False)
        if is_sarfaesi:
            if not case_data.get("cersai_registered", True):
                rule = STATUTORY_RULE_REGISTRY["RULE_SARFAESI_26D_CERSAI_BAR"]
                fatal_defects.append({
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "statute": rule.section_provision,
                    "severity": rule.defect_severity.value,
                    "finding": "Security interest not registered on CERSAI portal. Statutory bar u/s 26D SARFAESI prohibits enforcement.",
                    "precedent": rule.authoritative_precedent,
                    "remediation": rule.remediation_guidance
                })

            if case_data.get("is_agricultural_land", False):
                rule = STATUTORY_RULE_REGISTRY["RULE_SARFAESI_31_AGRI_EXEMPTION"]
                fatal_defects.append({
                    "rule_id": rule.rule_id,
                    "title": rule.title,
                    "statute": rule.section_provision,
                    "severity": rule.defect_severity.value,
                    "finding": "Collateral is agricultural land. Section 31(i) explicitly bars SARFAESI enforcement. Initiate DRT Section 19 OA.",
                    "precedent": rule.authoritative_precedent,
                    "remediation": rule.remediation_guidance
                })

        # ======================================================================
        # 7. EVIDENTIARY ASSETS COMPLETENESS AUDIT
        # ======================================================================
        evidence_checklist = [
            {
                "asset_name": "Original Dishonoured Cheque",
                "required_by": "Section 138 & 118 NI Act",
                "available": bool(case_data.get("has_original_cheque", True)),
                "status": "VERIFIED" if case_data.get("has_original_cheque", True) else "MISSING",
                "criticality": "HIGH"
            },
            {
                "asset_name": "Bank Return Memo (with Official Stamp)",
                "required_by": "Section 146 NI Act (Presumption)",
                "available": bool(case_data.get("has_return_memo", True)),
                "status": "VERIFIED" if case_data.get("has_return_memo", True) else "MISSING",
                "criticality": "CRITICAL"
            },
            {
                "asset_name": "Loan Agreement & Stamped Sanction Letter",
                "required_by": "Section 138 Explanation (Enforceable Debt)",
                "available": bool(case_data.get("has_sanction_letter", True)),
                "status": "VERIFIED" if case_data.get("has_sanction_letter", True) else "MISSING",
                "criticality": "HIGH"
            },
            {
                "asset_name": "Speed Post Consignment Receipt",
                "required_by": "Section 27 General Clauses Act (Proof of Dispatch)",
                "available": bool(case_data.get("has_speed_post_receipt", True)),
                "status": "VERIFIED" if case_data.get("has_speed_post_receipt", True) else "MISSING",
                "criticality": "CRITICAL"
            },
            {
                "asset_name": "India Post Tracking / Delivery Confirmation Report",
                "required_by": "C.C. Alavi Haji (2007) SC (Presumption of Service)",
                "available": bool(case_data.get("has_delivery_report", True)),
                "status": "VERIFIED" if case_data.get("has_delivery_report", True) else "MISSING",
                "criticality": "HIGH"
            },
            {
                "asset_name": "Section 65B Certificate / Banker's Books Evidence",
                "required_by": "Banker's Books Evidence Act 1891 / BSA 2023",
                "available": bool(case_data.get("has_account_statement", True)),
                "status": "VERIFIED" if case_data.get("has_account_statement", True) else "MISSING",
                "criticality": "MEDIUM"
            }
        ]

        missing_evidence_count = sum(1 for e in evidence_checklist if not e["available"])
        if missing_evidence_count > 0:
            for item in evidence_checklist:
                if not item["available"]:
                    curable_defects.append({
                        "rule_id": "RULE_EVIDENCE_ASSET_MISSING",
                        "title": f"Missing Evidentiary Asset: {item['asset_name']}",
                        "statute": item["required_by"],
                        "severity": DefectSeverity.EVIDENTIARY_GAP.value,
                        "finding": f"Required evidence '{item['asset_name']}' is not attached to recovery file.",
                        "precedent": "State of MP v. Man Singh (2019)",
                        "remediation": f"Obtain and verify {item['asset_name']} before filing complaint."
                    })

        # ======================================================================
        # 8. DETERMINISTIC RECOVERY VIABILITY SCORE (0–100)
        # ======================================================================
        base_score = 95.0
        # Deductions
        base_score -= len(fatal_defects) * 65.0
        base_score -= len(limitation_warnings) * 25.0
        base_score -= len(curable_defects) * 10.0

        # Clamp between 5.0 and 98.0
        recovery_score = max(5.0, min(98.0, base_score))

        if fatal_defects:
            readiness_verdict = "FATAL_STATUTORY_BAR"
            verdict_badge = "Fatal Legal Defect (Alternate Recovery Track Required)"
        elif recovery_score >= 80.0 and not limitation_warnings:
            readiness_verdict = "READY_FOR_ADVOCATE_DISPATCH"
            verdict_badge = "Statutorily Compliant (Ready for Advocate Dispatch)"
        else:
            readiness_verdict = "REMEDIATION_REQUIRED"
            verdict_badge = "Remediable Defects (Condonation / Evidence Needed)"

        # ======================================================================
        # 9. STRUCTURED EMPANELED ADVOCATE CASE DOSSIER
        # ======================================================================
        advocate_dossier = {
            "case_reference": loan_account_no,
            "borrower_title": borrower_name,
            "default_amount_inr": default_amount,
            "court_jurisdiction": case_data.get("court_name", "Court of Metropolitan Magistrate / Judicial Magistrate 1st Class"),
            "statutory_track": case_type,
            "case_chronology": [
                {"date": cheque_date or "N/A", "event": "Cheque Drawn / Issued by Debtor"},
                {"date": dishonour_date or "N/A", "event": "Cheque Dishonour via Bank Clearing (Memo Issued)"},
                {"date": notice_date or "N/A", "event": "Section 138(b) Statutory Demand Notice Dispatched"},
                {"date": delivery_date or "N/A", "event": "Notice Delivered to Accused (15-Day Cure Window Commenced)"},
                {"date": complaint_date or "Pending", "event": "Criminal Complaint Institution Date"}
            ],
            "statutory_anchors": [
                "Section 138, 139, 141, 142 Negotiable Instruments Act, 1881",
                "Section 146 NI Act (Presumption of Bank Slip)",
                "Section 143A NI Act (Mandatory Application for 20% Interim Deposit)",
                "Bir Singh v. Mukesh Kumar (2019) 4 SCC 197 (Strict S.139 Presumption)"
            ],
            "action_instructions": (
                "File Section 138 complaint before the competent jurisdictional Magistrate. "
                "Concurrently move an interim application under Section 143A for 20% interim deposit within 60 days. "
                "Attach certified account statement under Banker's Books Evidence Act."
                if not fatal_defects else
                "CAUTION: Fatal statutory defect detected. Do not institute S.138 criminal complaint without addressing defect. Review civil/SARFAESI concurrent remedies."
            ),
            "interim_relief_u_s_143a": {
                "applicable": True,
                "provision": "Section 143A NI Act",
                "claimable_percentage": "20%",
                "estimated_interim_recovery": round(default_amount * 0.20, 2),
                "ruling": "Rakesh Ranjan Shahi v. State of UP (2024)"
            }
        }

        # ======================================================================
        # 10. REGULATORY AUDIT TRAIL / COMPLIANCE EVIDENCE LEDGER
        # ======================================================================
        audit_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "officer_id": officer_id,
            "branch_name": branch_name,
            "loan_account_no": loan_account_no,
            "default_amount": default_amount,
            "recovery_score": recovery_score,
            "verdict": readiness_verdict,
            "fatal_defects_count": len(fatal_defects),
            "limitation_warnings_count": len(limitation_warnings),
            "curable_defects_count": len(curable_defects),
            "rules_evaluated": [m["milestone_id"] for m in milestones]
        }

        raw_bytes = json.dumps(audit_payload, sort_keys=True).encode("utf-8")
        audit_hash = hashlib.sha256(raw_bytes).hexdigest()

        compliance_ledger_record = {
            "ledger_title": "Regulatory Audit Trail / Compliance Evidence Ledger",
            "audit_hash": f"SHA256:{audit_hash}",
            "generated_at_utc": audit_payload["timestamp"],
            "reviewing_officer": officer_id,
            "bank_branch": branch_name,
            "case_reference": loan_account_no,
            "verdict_recorded": readiness_verdict,
            "statutory_compliance_status": "VERIFIED_COMPLIANT" if not fatal_defects else "DEFECTS_IDENTIFIED",
            "governance_note": (
                "Generates an auditable record supporting the bank's internal IT governance, "
                "compliance reviews, and legal handoff processes under RBI Master Directions on Outsourcing and IT Risk Management."
            )
        }

        return {
            "success": True,
            "case_reference": loan_account_no,
            "borrower_name": borrower_name,
            "default_amount": default_amount,
            "recovery_score": recovery_score,
            "verdict": readiness_verdict,
            "verdict_badge": verdict_badge,
            "milestones": milestones,
            "fatal_defects": fatal_defects,
            "limitation_warnings": limitation_warnings,
            "curable_defects": curable_defects,
            "evidence_checklist": evidence_checklist,
            "advocate_dossier": advocate_dossier,
            "compliance_ledger_record": compliance_ledger_record
        }
