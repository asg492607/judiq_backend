from fastapi import APIRouter, Depends, HTTPException
from session import DatabaseManager
from auth.utils import get_current_user

router = APIRouter(tags=["executive"])

@router.get("/portfolio-summary")
async def get_portfolio_summary(current_user: dict = Depends(get_current_user)):
    # Restrict to FINANCIAL_INSTITUTION
    if current_user.get("org_type") != "FINANCIAL_INSTITUTION":
        raise HTTPException(status_code=403, detail="Access restricted to Enterprise users.")
        
    org_id = current_user.get("org_id")
    
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        # In a real scenario, "Money at Risk" requires a financial exposure column on the case.
        # We will mock the financial extraction based on case_data if possible, 
        # or rely on mock fields for MVP demonstration.
        cursor.execute("""
            SELECT COUNT(*), SUM(cheque_amount) 
            FROM saved_cases 
            WHERE organization_id = ?
        """, (org_id,))
        row = cursor.fetchone()
        
        active_cases = row[0] if row else 0
        money_at_risk = row[1] if (row and row[1]) else 0.0
        
        recovery_pipeline = money_at_risk * 0.25
        nearing_limitation = int(active_cases * 0.05)
        
        return {
            "status": "success",
            "data": {
                "money_at_risk": money_at_risk,
                "recovery_pipeline": recovery_pipeline,
                "active_cases": active_cases,
                "nearing_limitation": nearing_limitation
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

@router.get("/alerts")
async def get_alerts(current_user: dict = Depends(get_current_user)):
    # Restrict to FINANCIAL_INSTITUTION
    if current_user.get("org_type") != "FINANCIAL_INSTITUTION":
        raise HTTPException(status_code=403, detail="Access restricted to Enterprise users.")
        
    org_id = current_user.get("org_id")
    
    # Mocking AI generated insights for MVP dashboard display
    return {
        "status": "success",
        "data": [
            f"📍 {org_id} Headquarters: Limitation on 12 cases expiring in < 7 days.",
            "📈 SARFAESI Module: Recovery probability drops by 12% if Notice is delayed past Day 14."
        ]
    }

@router.get("/compliance")
async def get_compliance(current_user: dict = Depends(get_current_user)):
    if current_user.get("org_type") != "FINANCIAL_INSTITUTION":
        raise HTTPException(status_code=403, detail="Access restricted to Enterprise users.")
        
    org_id = current_user.get("org_id")
    
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM saved_cases WHERE organization_id = ?", (org_id,))
        total_cases = cursor.fetchone()[0] or 0
        
        if total_cases == 0:
            return {"status": "success", "data": {"missing_memos": 0, "missing_notices": 0, "compliance_score": 100}}
            
        # Count cases missing RETURN_MEMO
        cursor.execute("""
            SELECT COUNT(sc.case_id) FROM saved_cases sc
            WHERE sc.organization_id = ? 
            AND NOT EXISTS (
                SELECT 1 FROM case_documents cd WHERE cd.case_id = sc.case_id AND cd.document_type = 'RETURN_MEMO'
            )
        """, (org_id,))
        missing_memos = cursor.fetchone()[0] or 0
        
        # Count cases missing LEGAL_NOTICE
        cursor.execute("""
            SELECT COUNT(sc.case_id) FROM saved_cases sc
            WHERE sc.organization_id = ? 
            AND NOT EXISTS (
                SELECT 1 FROM case_documents cd WHERE cd.case_id = sc.case_id AND cd.document_type = 'LEGAL_NOTICE'
            )
        """, (org_id,))
        missing_notices = cursor.fetchone()[0] or 0
        
        score = 100
        if total_cases > 0:
            deduction = ((missing_memos + missing_notices) / (total_cases * 2)) * 100
            score = max(0, int(100 - deduction))
            
        return {
            "status": "success",
            "data": {
                "missing_memos": missing_memos,
                "missing_notices": missing_notices,
                "compliance_score": score
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()
