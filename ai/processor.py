import time
import json
from datetime import datetime
from session import DatabaseManager

def process_document_async(case_id: str, file_path: str, document_type: str, user_id: str, org_id: int):
    """
    Simulates asynchronous AI extraction, OCR, and Section 138 validation.
    In a production environment, this would call reasoning_engine.py and external LLMs.
    """
    try:
        # Simulate AI processing delay (10 seconds)
        time.sleep(10)
        
        # Mock AI Extraction based on document type
        extracted_data = {}
        analysis_summary = ""
        score = 0.0
        
        if document_type == "RETURN_MEMO":
            extracted_data = {
                "return_date": datetime.utcnow().isoformat(),
                "reason": "FUNDS INSUFFICIENT"
            }
            analysis_summary = "Return memo validated. Funds Insufficient. 30-day notice window activated."
            score = 85.0
            
        elif document_type == "LEGAL_NOTICE":
            extracted_data = {
                "dispatch_date": datetime.utcnow().isoformat(),
                "tracking_number": "EM123456789IN"
            }
            analysis_summary = "Legal Notice successfully parsed. Awaiting postal receipt to calculate 15-day waiting period."
            score = 90.0
            
        else:
            extracted_data = {"note": "General document processed."}
            analysis_summary = f"{document_type} parsed and stored."
            score = 70.0
            
        # Update database with results
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        # In MVP we simply store the latest analysis_result in saved_cases.
        # In a real scenario, you might append it or store it in a dedicated AI table.
        cursor.execute(
            "UPDATE saved_cases SET analysis_result = ?, score = ?, ai_status = 'COMPLETED' WHERE case_id = ? AND organization_id = ?",
            (analysis_summary, score, case_id, org_id)
        )
        
        # Log Activity
        cursor.execute(
            "INSERT INTO case_activities (case_id, user_id, action, description, created_at) VALUES (?, ?, ?, ?, ?)",
            (case_id, "SYSTEM_AI", "AI_ANALYSIS_COMPLETE", f"AI processed {document_type} and updated case health.", datetime.utcnow().isoformat())
        )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error in background AI processing for case {case_id}: {e}")
