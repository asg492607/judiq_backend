from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional, Any
import re
class CaseInput(BaseModel):
    case_id: Optional[str] = Field(default="ANON", max_length=100, description="Unique identifier for the case")
    case_type: Optional[str] = Field(default="unknown", max_length=50, description="Type of case (e.g., cheque_bounce, criminal)")
    description: Optional[str] = Field(default="", max_length=10000, description="Free-text narrative of the case")
    offense_type: Optional[str] = Field(None, max_length=200)
    cheque_present: bool = False
    dishonour_memo: bool = False
    notice_sent: bool = False
    debt_proven: bool = False
    amount: float = Field(default=0.0, ge=0.0, le=1000000000.0)                      
    cheque_amount: Optional[float] = Field(default=None, ge=0.0, le=1000000000.0)
    loan_via_bank: bool = False
    complainant_itr_available: bool = False
    date_of_dishonour: Optional[str] = Field(None, max_length=20)
    date_of_notice: Optional[str] = Field(None, max_length=20)
    date_of_complaint: Optional[str] = Field(None, max_length=20)
    contract_exists: bool = False
    partial_performance_done: bool = False
    entrustment_proven: bool = False
    relatives_implicated: bool = False
    sudden_provocation: bool = False
    prior_relationship: bool = False
    personal_search_done: bool = False
    superficial_injuries: bool = False
    injury_dispute: bool = False
    fsl_report_positive: bool = False
    title_dispute: bool = False
    violence_used: bool = False
    tip_failed: bool = False
    good_faith_complaint: bool = False
    common_object_shared: bool = False
    victim_contributory_negligence: bool = False
    claim_of_right: bool = False
    no_imminent_fear: bool = False
    civil_possession_dispute: bool = False
    private_complaint: bool = False
    good_faith_exception: bool = False
    no_proximate_cause: bool = False
    no_sexual_intent: bool = False
    soon_before_death_nexus: bool = False
    essential_ceremonies_proven: bool = False
    # SARFAESI & DRT specific fields
    npa_date: Optional[str] = Field(None, max_length=20)
    notice_13_2_date: Optional[str] = Field(None, max_length=20)
    borrower_representation_date: Optional[str] = Field(None, max_length=20)
    bank_reply_13_3a_date: Optional[str] = Field(None, max_length=20)
    possession_13_4_date: Optional[str] = Field(None, max_length=20)
    auction_notice_date: Optional[str] = Field(None, max_length=20)
    sa_filing_date: Optional[str] = Field(None, max_length=20)
    cersai_registered: bool = False
    is_agricultural_land: bool = False
    perspective: str = Field(default="creditor", max_length=20) # creditor or borrower
    outstanding_amount: Optional[float] = Field(default=None, ge=0.0, le=10000000000.0)

    model_config = {
        "extra": "allow",
        "json_schema_extra": {
            "example": {
                "case_id": "CASE-2026-001",
                "case_type": "cheque_bounce",
                "description": "The accused issued a cheque of Rs. 5,00,000 which dishonoured due to insufficient funds. Notice sent within 30 days.",
                "cheque_present": True,
                "dishonour_memo": True,
                "notice_sent": True,
                "debt_proven": True,
                "amount": 500000.0,
                "date_of_dishonour": "2026-01-15",
                "date_of_notice": "2026-02-05"
            }
        }
    }
    @model_validator(mode='before')
    @classmethod
    def sanitize_and_map(cls, values):
        """
        Single consolidated 'before' validator that:
        1. Strips HTML tags from all string fields (security hardening).
        2. Normalises amount aliases (cheque_amount -> amount, empty strings -> 0.0).

        NOTE: Having two @model_validator(mode='before') on the same class in Pydantic v2
        causes the first to be silently overridden. This merged validator fixes that.
        """
        html_tag_re = re.compile(r'<[^>]+>')
        sanitized = {}
        for k, v in values.items():
            if isinstance(v, str):
                cleaned_str = html_tag_re.sub('', v).strip()
                # Intelligent boolean conversion for select dropdown strings
                v_lower = cleaned_str.lower()
                if v_lower in ("true", "1") or v_lower.startswith("yes") or "violation" in v_lower or "unlawful" in v_lower or "missing" in v_lower:
                    if k in cls.model_fields and cls.model_fields[k].annotation is bool:
                        sanitized[k] = True
                        continue
                elif v_lower in ("false", "0") or v_lower.startswith("no") or "not applicable" in v_lower:
                    if k in cls.model_fields and cls.model_fields[k].annotation is bool:
                        sanitized[k] = False
                        continue
                sanitized[k] = cleaned_str
            elif isinstance(v, dict):
                sanitized[k] = {
                    dk: html_tag_re.sub('', dv).strip() if isinstance(dv, str) else dv
                    for dk, dv in v.items()
                }
            else:
                sanitized[k] = v
        # Normalize empty string amounts to 0.0
        for k in ['amount', 'cheque_amount', 'debt_amount']:
            if k in sanitized and sanitized[k] == "":
                sanitized[k] = 0.0
        # Alias cheque_amount -> amount if amount is missing
        if 'cheque_amount' in sanitized and 'amount' not in sanitized:
            try:
                sanitized['amount'] = float(sanitized['cheque_amount'])
            except (ValueError, TypeError):
                pass
        return sanitized

class EngineResponse(BaseModel):
    status: str = "success"
    message: str = ""
    success: bool = True
    request_id: Optional[str] = None
    caseroom_id: Optional[str] = None
    jurisdiction: Optional[Dict[str, Any]] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    model_config = {"extra": "allow"}
class ScoringResult(BaseModel):
    score: int
    reasoning_trail: List[str]
    win_probability: str
    risk_level: str
class AdversarialOutput(BaseModel):
    risks_and_rebuttals: List[Dict[str, Any]]
    contradictions: List[Dict[str, Any]]
    adversarial_risk: float
class DraftRequest(BaseModel):
    case_data: CaseInput
    draft_type: str
    tone: str = "standard"
