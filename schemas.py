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
    mere_bystander: bool = False
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
    def map_aliases(cls, values):
        for k in ['amount', 'cheque_amount', 'debt_amount']:
            if k in values and values[k] == "":
                values[k] = 0.0
        if 'cheque_amount' in values and 'amount' not in values:
            try:
                values['amount'] = float(values['cheque_amount'])
            except (ValueError, TypeError):
                pass
        return values
    @model_validator(mode='before')
    @classmethod
    def sanitize_html(cls, values):
        html_tag_re = re.compile(r'<[^>]+>')
        sanitized = {}
        for k, v in values.items():
            if isinstance(v, str):
                sanitized[k] = html_tag_re.sub('', v)
            elif isinstance(v, dict):
                sanitized[k] = {
                    dk: html_tag_re.sub('', dv) if isinstance(dv, str) else dv 
                    for dk, dv in v.items()
                }
            else:
                sanitized[k] = v
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
