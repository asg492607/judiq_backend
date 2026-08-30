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
        if not cases and user_id:
            try:
                from firebase_manager import FirebaseManager
                fb_cases = FirebaseManager.list_user_cases(user_id, limit=20)
                if fb_cases:
                    return fb_cases
            except Exception as fb_err:
                pass
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
            # Fallback to Firebase Firestore
            try:
                from firebase_manager import FirebaseManager
                fb_doc = FirebaseManager.get_case_analysis(case_id)
                if fb_doc:
                    return {
                        "case_id": case_id,
                        "case_data": fb_doc.get("case_data", {}),
                        "analysis": fb_doc.get("analysis_result", {}),
                        "score": fb_doc.get("score", 0),
                        "verdict": fb_doc.get("verdict", "INCONCLUSIVE")
                    }
            except Exception:
                pass
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
            "analysis": analysis,
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


@router.get("/{case_id}/versions")
def get_case_versions_list(
    case_id: str,
    user_id: str = Depends(get_current_user_optional)
) -> List[Dict[str, Any]]:
    """
    Returns the complete version history timeline for a specific case file.
    """
    try:
        versions = DatabaseManager.get_case_versions(case_id)
        return versions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch case versions: {e}")


@router.post("/{case_id}/versions")
def create_case_version_snapshot(
    case_id: str,
    payload: Dict[str, Any],
    user_id: str = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Manually archives a named version snapshot of a lawyer's case and analysis with notes.
    """
    try:
        case_data = payload.get("case_data", {})
        analysis_result = payload.get("analysis_result", {})
        score = float(payload.get("score", 0.0))
        verdict = payload.get("verdict", "ANALYZED")
        version_title = payload.get("version_title")
        version_note = payload.get("version_note")
        uid = user_id or payload.get("user_id", "ANONYMOUS")

        snapshot = DatabaseManager.save_case_version(
            case_id=case_id,
            user_id=uid,
            case_data=case_data,
            analysis_result=analysis_result,
            score=score,
            verdict=verdict,
            version_title=version_title,
            version_note=version_note
        )
        return snapshot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save version snapshot: {e}")


@router.get("/{case_id}/versions/{version_num}")
def get_single_case_version(
    case_id: str,
    version_num: int,
    user_id: str = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Retrieves full case data and analysis report for a specific historical version.
    """
    try:
        version_data = DatabaseManager.get_case_version(case_id, version_num)
        if not version_data:
            raise HTTPException(status_code=404, detail=f"Version {version_num} not found for case {case_id}")
        return version_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{case_id}/restore/{version_num}")
def restore_case_version_endpoint(
    case_id: str,
    version_num: int,
    user_id: str = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """
    Restores active case state to match a historical snapshot version.
    """
    try:
        result = DatabaseManager.restore_case_version(case_id, version_num, user_id or "ANONYMOUS")
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Restore failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
