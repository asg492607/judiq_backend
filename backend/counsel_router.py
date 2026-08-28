"""
JudiQ Opposing Counsel Intelligence API Router
Exposes endpoints for querying opposing counsel profiles, matchup analysis,
and community crowdsourced intelligence contributions.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Optional, List, Dict, Any

from opposing_counsel_intel import (
    OpposingCounselIntelService,
    OpposingCounselProfile,
    MatchupAnalysisRequest,
    MatchupAnalysisResponse,
    IntelContributionRequest
)

router = APIRouter()


@router.get("", response_model=Dict[str, Any], tags=["Opposing Counsel Intel"])
@router.get("/list", response_model=Dict[str, Any], tags=["Opposing Counsel Intel"])
def list_counsel_endpoint(
    jurisdiction: Optional[str] = Query(None, description="Filter by High Court or District Court"),
    search: Optional[str] = Query(None, description="Search by name, bar ID, or keyword")
):
    """
    Retrieves directory of tracked opposing defense counsel with win rates,
    signature tactics, and crowdsourced tactical observations.
    """
    counsel_list = OpposingCounselIntelService.get_all_counsel(jurisdiction=jurisdiction, search=search)
    return {
        "success": True,
        "total": len(counsel_list),
        "counsel": counsel_list
    }


@router.get("/{counsel_id}", response_model=OpposingCounselProfile, tags=["Opposing Counsel Intel"])
def get_counsel_detail_endpoint(counsel_id: str):
    """
    Retrieves detailed opposing counsel dossier including judge track record,
    defense strategies, and recommended prosecution counters.
    """
    profile = OpposingCounselIntelService.get_counsel_by_id(counsel_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Opposing counsel profile '{counsel_id}' not found.")
    return profile


@router.post("/analyze-matchup", response_model=MatchupAnalysisResponse, tags=["Opposing Counsel Intel"])
def analyze_counsel_matchup_endpoint(req: MatchupAnalysisRequest = Body(...)):
    """
    Performs tactical matchup analysis against an opposing defense counsel,
    predicting their primary defense vectors and providing counter-pleadings roadmap.
    """
    return OpposingCounselIntelService.analyze_matchup(req)


@router.post("/contribute", response_model=Dict[str, Any], tags=["Opposing Counsel Intel"])
def contribute_counsel_intel_endpoint(req: IntelContributionRequest = Body(...)):
    """
    Allows practicing advocates to submit peer observations, defense tactics,
    and verified outcomes for community crowdsourced intelligence.
    """
    return OpposingCounselIntelService.record_crowdsource_contribution(req)
