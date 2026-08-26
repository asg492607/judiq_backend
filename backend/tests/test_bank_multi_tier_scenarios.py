import pytest
from backend.banking.recovery_engine import BankRecoveryEngine
from backend.banking.rule_registry import STATUTORY_RULE_REGISTRY, DefectSeverity


class TestBankMultiTierScenarios:
    """
    Exhaustive Multi-Tier Scenario Testing Suite for JudiQ Bank Recovery OS.
    Covers Tier 1 (Basic Standard) to Tier 5 (Ultra-Hard Critical Procedural Traps).
    """

    def test_tier_1_basic_clean_standard(self):
        """
        Tier 1 (Basic Standard): 100% statutory compliant ₹8.5L default.
        All 6 milestones passed, 0 defects, full evidence pack.
        """
        case_data = {
            "case_type": "Cheque Bounce (S.138)",
            "borrower_name": "M/s Apex Retailers Pvt Ltd",
            "loan_account_no": "SBI/SARB/MUM/2026/85012",
            "default_amount": 850000.0,
            "cheque_date": "2024-01-10",
            "dishonour_date": "2024-01-18",
            "notice_date": "2024-01-30",
            "delivery_date": "2024-02-04",
            "complaint_date": "2024-02-28",
            "condonation_attached": False,
            "is_secured": False,
            "cersai_registered": True,
            "is_agricultural_land": False,
            "has_original_cheque": True,
            "has_return_memo": True,
            "has_sanction_letter": True,
            "has_speed_post_receipt": True,
            "has_delivery_report": True,
            "has_account_statement": True
        }
        result = BankRecoveryEngine.evaluate_recovery_case(case_data)

        assert result["recovery_score"] >= 90.0
        assert result["verdict"] == "READY_FOR_ADVOCATE_DISPATCH"
        assert len(result["fatal_defects"]) == 0
        assert len(result["curable_defects"]) == 0
        assert result["compliance_ledger_record"]["audit_hash"] is not None
        assert "Section 143A" in result["advocate_dossier"]["action_instructions"]
        assert result["advocate_dossier"]["interim_relief_u_s_143a"]["estimated_interim_recovery"] == 170000.0

    def test_tier_2_curable_evidence_gaps(self):
        """
        Tier 2 (Intermediate): Missing India Post tracking report & Banker's Book 65B statement.
        Identifies curable defects and suggests General Clauses Act S.27 presumption.
        """
        case_data = {
            "case_type": "Cheque Bounce (S.138)",
            "borrower_name": "Rathore Logistics Services",
            "loan_account_no": "PNB/CFS/DEL/2026/14092",
            "default_amount": 1400000.0,
            "cheque_date": "2024-01-12",
            "dishonour_date": "2024-01-20",
            "notice_date": "2024-02-02",
            "delivery_date": "2024-02-07",
            "complaint_date": "2024-03-02",
            "condonation_attached": False,
            "is_secured": False,
            "cersai_registered": True,
            "is_agricultural_land": False,
            "has_original_cheque": True,
            "has_return_memo": True,
            "has_sanction_letter": True,
            "has_speed_post_receipt": True,
            "has_delivery_report": False,
            "has_account_statement": False
        }
        result = BankRecoveryEngine.evaluate_recovery_case(case_data)

        assert 50.0 <= result["recovery_score"] < 80.0
        assert result["verdict"] == "REMEDIATION_REQUIRED"
        assert len(result["fatal_defects"]) == 0
        assert len(result["curable_defects"]) >= 1

    def test_tier_3_critical_premature_filing_trap(self):
        """
        Tier 3 (Critical Procedural Trap): Complaint filed on Day 8 of 15-day cure window.
        Must trigger fatal Yogendra Pratap Singh bar (premature filing).
        """
        case_data = {
            "case_type": "Cheque Bounce (S.138)",
            "borrower_name": "Kaveri Textiles & Apparels Pvt Ltd",
            "loan_account_no": "HDFC/WLR/CHE/2026/25041",
            "default_amount": 2500000.0,
            "cheque_date": "2024-02-01",
            "dishonour_date": "2024-02-08",
            "notice_date": "2024-02-15",
            "delivery_date": "2024-02-19",
            "complaint_date": "2024-02-27",  # Only 8 days after delivery (15 days required)
            "condonation_attached": False
        }
        result = BankRecoveryEngine.evaluate_recovery_case(case_data)

        assert result["recovery_score"] <= 30.0
        assert result["verdict"] == "FATAL_STATUTORY_BAR"
        fatal_titles = [f["title"] for f in result["fatal_defects"]]
        assert any("Premature" in t or "15-Day" in t for t in fatal_titles)

    def test_tier_4_sarfaesi_cersai_and_agri_land_bar(self):
        """
        Tier 4 (High Risk / SARFAESI Bar):
        1. Security interest not registered on CERSAI portal (S.26D bar).
        2. Mortgaged asset is agricultural land (S.31(i) exemption).
        Must flag dual fatal bars under SARFAESI and direct DRT / Civil / S.138 route.
        """
        case_data = {
            "case_type": "SARFAESI & Cheque Bounce Concurrent Recovery",
            "borrower_name": "Greenfield Agro Infrastructure Pvt Ltd",
            "loan_account_no": "BOB/SAMB/PUN/2026/18023",
            "default_amount": 18000000.0,
            "cheque_date": "2024-01-05",
            "dishonour_date": "2024-01-14",
            "notice_date": "2024-01-28",
            "delivery_date": "2024-02-02",
            "complaint_date": "2024-02-26",
            "is_secured": True,
            "cersai_registered": False,
            "is_agricultural_land": True,
            "has_original_cheque": True,
            "has_return_memo": True,
            "has_sanction_letter": True,
            "has_speed_post_receipt": True,
            "has_delivery_report": True,
            "has_account_statement": True
        }
        result = BankRecoveryEngine.evaluate_recovery_case(case_data)

        assert result["verdict"] == "FATAL_STATUTORY_BAR"
        fatal_rules = [f["rule_id"] for f in result["fatal_defects"]]
        assert "RULE_SARFAESI_26D_CERSAI_BAR" in fatal_rules
        assert "RULE_SARFAESI_31_AGRI_EXEMPTION" in fatal_rules

    def test_tier_5_limitation_delayed_with_and_without_condonation(self):
        """
        Tier 5 (Ultra-Hard / Limitation Expiry):
        Complaint filed on Day 65 (past 30-day S.142 limitation window).
        - Without condonation: Fatal bar.
        - With S.142 condonation application + affidavit: Viability salvaged as Remediable.
        """
        # Case A: Without Condonation
        case_no_condonation = {
            "case_type": "Cheque Bounce (S.138)",
            "borrower_name": "Vanguard Precision Tools Pvt Ltd",
            "loan_account_no": "SBI/SARB/BLR/2026/65088",
            "default_amount": 6500000.0,
            "cheque_date": "2024-01-08",
            "dishonour_date": "2024-01-15",
            "notice_date": "2024-01-26",
            "delivery_date": "2024-01-30",
            "complaint_date": "2024-04-05",  # Over 2 months later (exceeds 30-day S.142 window)
            "condonation_attached": False
        }
        result_a = BankRecoveryEngine.evaluate_recovery_case(case_no_condonation)
        assert result_a["verdict"] == "FATAL_STATUTORY_BAR"
        assert result_a["recovery_score"] <= 30.0

        # Case B: With S.142 Condonation Application attached
        case_with_condonation = dict(case_no_condonation)
        case_with_condonation["condonation_attached"] = True
        result_b = BankRecoveryEngine.evaluate_recovery_case(case_with_condonation)
        assert result_b["verdict"] == "REMEDIATION_REQUIRED"
        assert result_b["recovery_score"] >= 50.0

    def test_stale_cheque_presentation_beyond_3_months(self):
        """
        Stale Cheque: Cheque dated 2024-01-01 presented on 2024-05-10 (> 120 days).
        Violates RBI 3-month presentation rule and Section 138(a).
        """
        case_data = {
            "cheque_date": "2024-01-01",
            "dishonour_date": "2024-05-10",
            "notice_date": "2024-05-20",
            "delivery_date": "2024-05-25",
            "complaint_date": "2024-06-15"
        }
        result = BankRecoveryEngine.evaluate_recovery_case(case_data)
        assert result["verdict"] == "FATAL_STATUTORY_BAR"
        fatal_rules = [f["rule_id"] for f in result["fatal_defects"]]
        assert "RULE_RBI_CHEQUE_3M_VALIDITY" in fatal_rules

    def test_delayed_notice_dispatch_beyond_30_days(self):
        """
        Delayed Notice: Return memo received 2024-01-10, notice dispatched 2024-02-25 (> 45 days).
        Violates Section 138(b) 30-day statutory notice dispatch mandate.
        """
        case_data = {
            "cheque_date": "2024-01-05",
            "dishonour_date": "2024-01-10",
            "notice_date": "2024-02-25",  # 46 days later (> 30 days)
            "delivery_date": "2024-03-01",
            "complaint_date": "2024-03-20"
        }
        result = BankRecoveryEngine.evaluate_recovery_case(case_data)
        assert result["verdict"] == "FATAL_STATUTORY_BAR"
        fatal_rules = [f["rule_id"] for f in result["fatal_defects"]]
        assert "RULE_NI_138B_NOTICE_30D" in fatal_rules
