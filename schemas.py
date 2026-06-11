from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Any
from datetime import date
import re

class CaseInput(BaseModel):
    """
    Standardized input schema for all JudiQ engines.
    Ensures that the raw case data dictionary is validated before processing.
    """
    case_id: Optional[str] = Field(default="ANON", description="Unique identifier for the case")
    case_type: Optional[str] = Field(default="unknown", description="Type of case (e.g., cheque_bounce, criminal)")
    description: Optional[str] = Field(default="", description="Free-text narrative of the case")
    
    # Common variables used across engines
    offense_type: Optional[str] = None
    
    # Cheque bounce specific
    cheque_present: bool = False
    dishonour_memo: bool = False
    notice_sent: bool = False
    debt_proven: bool = False
    amount: float = 0.0
    loan_via_bank: bool = False
    complainant_itr_available: bool = False
    date_of_dishonour: Optional[str] = None
    date_of_notice: Optional[str] = None
    date_of_complaint: Optional[str] = None

    # Criminal specific
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
    
    # Catch-all for any other dynamically added fields by frontend
    model_config = {"extra": "allow"}

    @model_validator(mode='before')
    @classmethod
    def sanitize_html(cls, values):
        """Strip HTML tags from string inputs to prevent XSS"""
        html_tag_re = re.compile(r'<[^>]+>')
        sanitized = {}
        for k, v in values.items():
            if isinstance(v, str):
                sanitized[k] = html_tag_re.sub('', v)
            elif isinstance(v, dict):
                # Basic shallow sanitization for dicts
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
    data: Dict[str, Any] = Field(default_factory=dict)
    
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
