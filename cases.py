from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any
from session import DatabaseManager
from security import get_current_user_optional
import json

router = APIRouter()


@router.get("")
def get_recent_cases(user_id: str = Depends(get_current_user_optional)) -> List[Dict[str, Any]]:
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        p = DatabaseManager.get_dialect_placeholder()
        cursor.execute(
            f"SELECT case_id, user_id, case_data, analysis_result, score, verdict, created_at, updated_at, tags "
            f"FROM saved_cases WHERE user_id = {p} ORDER BY updated_at DESC LIMIT 20",
            (user_id,)
        )
        rows = cursor.fetchall()
        cases = []
        for row in rows:
            try:
                cdata = json.loads(row[2]) if row[2] else {}
            except (json.JSONDecodeError, TypeError):
                cdata = {}
            try:
                analysis = json.loads(row[3]) if row[3] else {}
            except (json.JSONDecodeError, TypeError):
                analysis = {}
            cases.append({
                "id": row[0],
                "user_id": row[1],
                "title": cdata.get("case_title", "Untitled Case"),
                "date": row[7],
                "score": row[4],
                "risk_level": analysis.get("risk_level") or analysis.get("defence_risk") or "Unknown",
                "verdict": row[5]
            })
        return cases
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@router.get("/detail")
def get_case_details_query(
    case_id: str = Query(...),
    user_id: str = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    return get_case_details(case_id, user_id)


@router.delete("/delete")
def delete_case_query(
    case_id: str = Query(...),
    user_id: str = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    return delete_case(case_id, user_id)


@router.delete("/{case_id}")
def delete_case(case_id: str, user_id: str = Depends(get_current_user_optional)) -> Dict[str, Any]:
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        p = DatabaseManager.get_dialect_placeholder()
        cursor.execute(f"SELECT id FROM saved_cases WHERE case_id = {p} AND user_id = {p}", (case_id, user_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Case not found or unauthorized")
        cursor.execute(f"DELETE FROM saved_cases WHERE case_id = {p} AND user_id = {p}", (case_id, user_id))
        conn.commit()
        return {"success": True, "message": "Case deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()


@router.get("/{case_id}")
def get_case_details(case_id: str, user_id: str = Depends(get_current_user_optional)) -> Dict[str, Any]:
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        p = DatabaseManager.get_dialect_placeholder()
        cursor.execute(
            f"SELECT case_data, analysis_result, score, verdict FROM saved_cases WHERE case_id = {p} AND user_id = {p}",
            (case_id, user_id)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Case not found")
        try:
            cdata = json.loads(row[0]) if row[0] else {}
        except (json.JSONDecodeError, TypeError):
            cdata = {}
        try:
            analysis = json.loads(row[1]) if row[1] else {}
        except (json.JSONDecodeError, TypeError):
            analysis = {}
        return {
            "case_id": case_id,
            "case_data": cdata,
            "analysis_result": analysis,
            "score": row[2],
            "verdict": row[3]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()
