"""
JudiQ Analytics Dashboard API Router
Exposes enterprise firm-level, bank-level, and judicial outcome analytics.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any

from analytics_dashboard import AnalyticsDashboardService, FirmExecutiveAnalytics

router = APIRouter()


@router.get("", response_model=FirmExecutiveAnalytics, tags=["Analytics Dashboard"])
@router.get("/executive", response_model=FirmExecutiveAnalytics, tags=["Analytics Dashboard"])
def get_executive_analytics_endpoint(firm_name: Optional[str] = Query(None, description="Firm or Institution Name")):
    """
    Returns high-level executive analytics: compliance scores, 5-tier portfolio breakdown,
    monthly trends, judge benchmark patterns, and ROI metrics.
    """
    return AnalyticsDashboardService.get_firm_analytics(firm_name=firm_name)
