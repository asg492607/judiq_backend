import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from criminal.criminal_engine import CriminalEngine
from criminal.criminal_adversarial_engine import CriminalAdversarialEngine
from criminal.criminal_scoring_engine import CriminalScoringEngine
from criminal.criminal_timeline_engine import CriminalTimelineEngine
from criminal.criminal_rules_engine import CriminalRulesEngine
from criminal.criminal_economics_engine import CriminalEconomicsEngine
from engine_core import JudiQEngine
from limiter import limiter

router = APIRouter()
logger = logging.getLogger("JudiQ.Criminal")

class CriminalAnalysisRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=10000)
    offense_type: Optional[str] = Field("General", max_length=200)
    client_role: Optional[str] = Field("Accused", max_length=50) # Accused or Complainant
    ipc_section: Optional[str] = Field(None, max_length=50)
    bns_section: Optional[str] = Field(None, max_length=50)
    incident_date: Optional[str] = Field(None, max_length=20)
    fir_date: Optional[str] = Field(None, max_length=20)
    arrest_date: Optional[str] = Field(None, max_length=20)
    chargesheet_date: Optional[str] = Field(None, max_length=20)
    flight_risk: bool = False
    evidence_tampering_risk: bool = False
    contract_exists: bool = False
    delay_explanation: Optional[str] = Field(None, max_length=500)
    electronic_evidence: bool = False
    s65b_certificate: bool = False
    is_public_servant: bool = False
    sanction_obtained: bool = False
    age_at_incident: Optional[int] = None
    
    model_config = {"extra": "allow"}

class BailAssessmentRequest(BaseModel):
    offense_type: str = "General"
    flight_risk: bool = False
    evidence_tampering_risk: bool = False
    in_custody: bool = False
    days_in_custody: int = 0
    punishment_years: int = 3
    client_role: str = "Accused"

@router.post(
    "/analyze",
    summary="Analyze Criminal Litigation Case",
    description="Full strategic evaluation of criminal cases under IPC / BNS & CrPC / BNSS frameworks."
)
@limiter.limit("10/minute")
async def analyze_criminal_case(request_data: CriminalAnalysisRequest, request: Request):
    try:
        data = request_data.model_dump()
        data["case_type"] = "criminal"
        result = await asyncio.to_thread(JudiQEngine.analyze_case, data)
        return {"success": True, "data": result, **result}
    except Exception as e:
        logger.error(f"Criminal analysis error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "user_message": "Failed to process criminal case analysis."}
        )

@router.post(
    "/bail",
    summary="Assess Bail Probability & Strategy",
    description="Evaluates anticipatory bail (S.438 CrPC / 484 BNSS) and regular bail (S.437/439 CrPC / 480/483 BNSS) viability."
)
def evaluate_bail(request_data: BailAssessmentRequest):
    case_data = request_data.model_dump()
    concepts = []
    if case_data.get("offense_type") in ["302", "376", "MURDER", "RAPE", "NDPS", "103", "64"]:
        concepts.append({"concept": "heinous_crime"})
    bail_info = CriminalEngine.assess_bail_probability(case_data, concepts)
    economics = CriminalEconomicsEngine.calculate_economics(case_data)
    timeline_info = CriminalTimelineEngine.analyze_timelines(case_data)
    return {
        "success": True,
        "bail_assessment": bail_info,
        "economics": economics.get("bail_economics", {}),
        "timeline_health": timeline_info.get("timeline_health")
    }

@router.post(
    "/quashing",
    summary="Evaluate Quashing & Discharge Viability",
    description="Evaluates S.482 CrPC / S.528 BNSS quashing grounds (Bhajan Lal parameters) and S.227/239 CrPC discharge."
)
def evaluate_quashing(case_data: Dict[str, Any]):
    concepts = case_data.get("concepts", [])
    contradictions = CriminalAdversarialEngine.detect_contradictions(case_data, concepts)
    stress_test = CriminalAdversarialEngine.simulate_strategic_stress_test(case_data, concepts)
    rules = CriminalRulesEngine.evaluate_rules(case_data)
    bhajan_grounds = CriminalAdversarialEngine.evaluate_bhajan_lal_grounds(case_data)
    
    quashing_grounds = [node.get("discharge_quashing_strategy") for node in stress_test if node.get("discharge_quashing_strategy")]
    return {
        "success": True,
        "quashing_viable": len(quashing_grounds) > 0 or len(contradictions) > 0 or len(bhajan_grounds) > 0,
        "quashing_grounds": quashing_grounds,
        "bhajan_lal_grounds": bhajan_grounds,
        "contradictions": contradictions,
        "statutory_bars": rules
    }

@router.post(
    "/draft",
    summary="Generate Court-Ready Criminal Pleadings",
    description="Generates court-ready drafts for Anticipatory Bail, Regular Bail, Default Bail, Quashing, Discharge, FIR, Suspension of Sentence, etc."
)
def generate_criminal_draft(request_data: Dict[str, Any]):
    from draft_engine import DraftEngine
    draft_type = request_data.get("draft_type", "REGULAR_BAIL")
    score = request_data.get("score", 75)
    concepts = request_data.get("concepts", [])
    case_data = request_data.get("case_data", request_data)
    
    draft_text = DraftEngine.generate_draft(draft_type, score, concepts, case_data)
    return {
        "success": True,
        "draft_type": draft_type,
        "draft": draft_text
    }

@router.post(
    "/cross-exam",
    summary="Generate Trial Cross-Examination Question Bank",
    description="Generates tailored deposition cross-examination toolkits for I.O., Medical Doctors, and Informants."
)
def generate_cross_examination(request_data: Dict[str, Any]):
    case_data = request_data.get("case_data", request_data)
    nodes = CriminalAdversarialEngine.simulate_strategic_stress_test(case_data, [])
    cross_exam_questions = []
    rebuttal_trees = []
    matched_vector = None
    for n in nodes:
        if not matched_vector:
            matched_vector = n.get("adversarial_vector")
        if n.get("cross_exam_questions"):
            cross_exam_questions.extend(n.get("cross_exam_questions"))
        if n.get("rebuttal_tree"):
            rebuttal_trees.append(n.get("rebuttal_tree"))
    
    return {
        "success": True,
        "matched_vector": matched_vector or "General Criminal Offense",
        "cross_examination_toolkit": cross_exam_questions,
        "rebuttal_trees": rebuttal_trees,
        "total_questions": len(cross_exam_questions)
    }


