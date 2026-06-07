from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from session import DatabaseManager
import json

router = APIRouter()

@router.get("/")
async def get_recent_cases(user_id: str = Query(..., description="The ID of the user")):
    """Fetch recent cases for a specific user from the database."""
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        p = DatabaseManager.get_dialect_placeholder()
        
        cursor.execute(f"SELECT case_id, user_id, case_data, analysis_result, score, verdict, created_at, updated_at, tags FROM saved_cases WHERE user_id = {p} ORDER BY updated_at DESC LIMIT 20", (user_id,))
        rows = cursor.fetchall()
        
        cases = []
        for row in rows:
            try:
                cdata = json.loads(row[2]) if row[2] else {}
            except:
                cdata = {}
                
            cases.append({
                "id": row[0],
                "user_id": row[1],
                "title": cdata.get("case_title", "Untitled Case"),
                "date": row[7],
                "score": row[4],
                "risk_level": cdata.get("defence_risk", "Unknown"),
                "verdict": row[5]
            })
            
        conn.close()
        return cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{case_id}")
async def delete_case(case_id: str, user_id: str = Query(...)):
    """Delete a specific case for a user."""
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        p = DatabaseManager.get_dialect_placeholder()
        
        cursor.execute(f"DELETE FROM saved_cases WHERE case_id = {p} AND user_id = {p}", (case_id, user_id))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Case not found or unauthorized")
        return {"status": "success", "message": "Case deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{case_id}")
async def get_case_details(case_id: str, user_id: str = Query(...)):
    """Fetch full case details."""
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        p = DatabaseManager.get_dialect_placeholder()
        
        cursor.execute(f"SELECT case_data, analysis_result FROM saved_cases WHERE case_id = {p} AND user_id = {p}", (case_id, user_id))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Case not found or unauthorized")
            
        return {
            "case_data": json.loads(row[0]) if row[0] else {},
            "analysis_result": json.loads(row[1]) if row[1] else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
