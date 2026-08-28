"""
JudiQ Empaneled Advocate SLA & Performance Tracker
Manages legal counsel empanelment, recovery win rates, SLA tracking,
and court brief dispatch handoffs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EmpaneledAdvocate(BaseModel):
    advocate_id: str
    name: str
    firm_name: str
    bar_council_no: str
    city_jurisdiction: str
    primary_courts: List[str]
    specialization: str
    experience_years: int
    sla_rating: float  # 1.0 to 5.0
    recovery_win_rate_pct: float
    avg_days_to_file_after_brief: int
    active_cases_count: int
    fee_structure: Dict[str, float]
    contact_email: str
    contact_phone: str


EMPANELLED_ADVOCATES_REGISTRY: Dict[str, EmpaneledAdvocate] = {
    "ADV_MUM_01": EmpaneledAdvocate(
        advocate_id="ADV_MUM_01",
        name="Senior Panel Counsel (Mumbai Recovery Cell)",
        firm_name="Institutional Banking Panel Chambers",
        bar_council_no="BAR-MUM-PANEL-01",
        city_jurisdiction="Mumbai / MMR",
        primary_courts=["Bombay High Court", "DRT-I Mumbai", "CMM Esplanade Court"],
        specialization="SARFAESI Section 14 & S.138 Commercial Litigation",
        experience_years=20,
        sla_rating=4.9,
        recovery_win_rate_pct=94.5,
        avg_days_to_file_after_brief=3,
        active_cases_count=18,
        fee_structure={"notice_drafting": 7500.0, "complaint_filing": 25000.0, "hearing_appearance": 5000.0, "final_decree": 35000.0},
        contact_email="panel.mumbai@bank-legaldesk.in",
        contact_phone="+91 22 2200 1101"
    ),
    "ADV_DEL_02": EmpaneledAdvocate(
        advocate_id="ADV_DEL_02",
        name="Senior Panel Counsel (Delhi Commercial Panel)",
        firm_name="Institutional Corporate Law Panel",
        bar_council_no="BAR-DEL-PANEL-02",
        city_jurisdiction="New Delhi / NCR",
        primary_courts=["Delhi High Court", "DRT-II Delhi", "NCLT Principal Bench"],
        specialization="Corporate Debt Recovery (RDB Act S.19 & IBC S.95)",
        experience_years=18,
        sla_rating=4.8,
        recovery_win_rate_pct=91.8,
        avg_days_to_file_after_brief=4,
        active_cases_count=14,
        fee_structure={"notice_drafting": 10000.0, "complaint_filing": 35000.0, "hearing_appearance": 7500.0, "final_decree": 50000.0},
        contact_email="panel.delhi@bank-legaldesk.in",
        contact_phone="+91 11 2330 4402"
    ),
    "ADV_BLR_03": EmpaneledAdvocate(
        advocate_id="ADV_BLR_03",
        name="Designated Panel Counsel (Bangalore SARB)",
        firm_name="Special Recovery Panel Chambers",
        bar_council_no="BAR-KAR-PANEL-03",
        city_jurisdiction="Bangalore / Karnataka",
        primary_courts=["Karnataka High Court", "DRT Bangalore", "City Civil Court"],
        specialization="S.138 Cheque Bounce & S.142 Delay Condonation",
        experience_years=15,
        sla_rating=4.7,
        recovery_win_rate_pct=89.2,
        avg_days_to_file_after_brief=2,
        active_cases_count=22,
        fee_structure={"notice_drafting": 5000.0, "complaint_filing": 18000.0, "hearing_appearance": 4000.0, "final_decree": 25000.0},
        contact_email="panel.bangalore@bank-legaldesk.in",
        contact_phone="+91 80 2550 7703"
    ),
    "ADV_AHM_04": EmpaneledAdvocate(
        advocate_id="ADV_AHM_04",
        name="Designated Panel Counsel (Gujarat Zonal Panel)",
        firm_name="Institutional NPA Enforcement Panel",
        bar_council_no="BAR-GUJ-PANEL-04",
        city_jurisdiction="Ahmedabad / Gujarat",
        primary_courts=["Gujarat High Court", "DRT Ahmedabad", "Chief Judicial Magistrate"],
        specialization="Industrial NPA & SARFAESI Chapter III Asset Enforcement",
        experience_years=19,
        sla_rating=4.9,
        recovery_win_rate_pct=93.0,
        avg_days_to_file_after_brief=3,
        active_cases_count=16,
        fee_structure={"notice_drafting": 6500.0, "complaint_filing": 22000.0, "hearing_appearance": 4500.0, "final_decree": 30000.0},
        contact_email="panel.ahmedabad@bank-legaldesk.in",
        contact_phone="+91 79 2650 8804"
    )
}


def get_empaneled_advocates_list() -> List[Dict[str, Any]]:
    return [adv.model_dump() for adv in EMPANELLED_ADVOCATES_REGISTRY.values()]


def get_advocate_by_id(adv_id: str) -> Optional[EmpaneledAdvocate]:
    return EMPANELLED_ADVOCATES_REGISTRY.get(adv_id)
