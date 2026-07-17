import logging
import uuid
import sqlite3
from datetime import datetime
from session import DatabaseManager
logger = logging.getLogger(__name__)
class CaseroomManager:
    @staticmethod
    def initialize_caseroom_for_case(case_id, owner_id):
        caseroom_id = f"CR_{uuid.uuid4().hex[:8].upper()}"
        success = DatabaseManager.create_caseroom(caseroom_id, case_id, owner_id)
        if success:
            logger.info(f"âœ… Caseroom {caseroom_id} initialized for case {case_id}")
            DatabaseManager.send_message(caseroom_id, "SYSTEM", f"Welcome to the Caseroom for Case {case_id}. Strategy discussions and evidence management starts here.")
            return caseroom_id
        return None
    @staticmethod
    def invite_collaborator(caseroom_id, user_id, role):
        return DatabaseManager.add_participant(caseroom_id, user_id, role)
    @staticmethod
    def get_full_caseroom_state(caseroom_id):
        state = DatabaseManager.get_caseroom_data(caseroom_id)
        if not state:
            logger.warning(f"Caseroom {caseroom_id} missing from DB. Attempting ghost recovery...")
            if str(caseroom_id).startswith("CR_"):
                logger.info(f"ðŸ‘» Re-hydrating ghost state for Caseroom {caseroom_id}")
                DatabaseManager.create_caseroom(caseroom_id, "CASE_RECOVERED", "RECOVERED_USER")
                DatabaseManager.send_message(caseroom_id, "SYSTEM", "Session recovered after server restart. Previous history cleared.")
                state = DatabaseManager.get_caseroom_data(caseroom_id)
        if state and state.get("room_info"):
            case_id = state["room_info"][1]
            case_record = DatabaseManager.get_case(case_id)
            if case_record:
                import json
                try:
                    state["latest_analysis"] = json.loads(case_record[4])                             
                except:
                    state["latest_analysis"] = None
        return state
    @staticmethod
    def post_comment(caseroom_id, user_id, text):
        return DatabaseManager.send_message(caseroom_id, user_id, text)
    @staticmethod
    def add_milestone(caseroom_id, title, due_date, description=""):
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO caseroom_tasks (caseroom_id, title, description, due_date, created_at)
                VALUES ({p}, {p}, {p}, {p}, {p})
            """, (caseroom_id, title, description, due_date, now))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to add task: {e}")
            return False
    @staticmethod
    def upload_document(caseroom_id, user_id, file_name, file_path, doc_type, validation_status="PENDING", raw_text=None):
        from document_intelligence import doc_intel
        extracted_data = {}
        intelligence_audit = {}
        if raw_text:
            if doc_type == "BANK_MEMO":
                extracted_data = doc_intel.extract_memo_data(raw_text)
                intelligence_audit = doc_intel.perform_forensic_audit("BANK_MEMO", extracted_data)
            elif doc_type == "BSA_CERTIFICATE" or "63(4)" in raw_text:
                intelligence_audit = doc_intel.perform_forensic_audit("BSA_CERTIFICATE", {})
        metadata = {
            "extracted": extracted_data,
            "audit": intelligence_audit,
            "processed_at": datetime.now().isoformat()
        }
        caseroom_state = DatabaseManager.get_caseroom_data(caseroom_id)
        if caseroom_state and "documents" in caseroom_state:
            for doc in caseroom_state["documents"]:
                if doc["file_name"] == file_name and doc["doc_type"] == doc_type:
                    logger.warning(f"Duplicate upload blocked: {file_name}")
                    return None 
        return DatabaseManager.save_document(caseroom_id, user_id, file_name, file_path, doc_type, validation_status, metadata)
    @staticmethod
    def reanalyze_case_from_documents(caseroom_id, user_id="SYSTEM"):
        import json
        from engine_core import JudiQEngine
        caseroom_data = DatabaseManager.get_caseroom_data(caseroom_id)
        if not caseroom_data or not caseroom_data.get("room_info"):
            return False, "Caseroom not found"
        case_id = caseroom_data["room_info"][1]                                                                
        original_case = DatabaseManager.get_case(case_id)
        if not original_case:
            return False, "Original case not found"
        try:
            case_data = json.loads(original_case[3])                        
        except:
            return False, "Invalid case data format"
        documents = caseroom_data.get("documents", [])
        updates = []
        for doc in documents:
            dtype = str(doc.get("doc_type")).upper()
            ext = doc.get("extracted_data") or {}
            dates = ext.get("extracted_dates", [])
            amounts = ext.get("extracted_amounts", [])
            if dtype == "CHEQUE":
                if amounts:
                    case_data["amount"] = amounts[0]
                    updates.append(f"Cheque Amount -> {amounts[0]}")
                if dates:
                    case_data["cheque_date"] = dates[0]
                    updates.append(f"Cheque Date -> {dates[0]}")
                chq_nums = ext.get("extracted_cheque_numbers", [])
                if chq_nums:
                    case_data["cheque_number"] = chq_nums[0]
                    updates.append(f"Cheque Number -> {chq_nums[0]}")
            elif dtype == "MEMO":
                if dates:
                    case_data["dishonour_date"] = dates[0]
                    updates.append(f"Dishonour Date -> {dates[0]}")
                reasons = ext.get("detected_reasons", [])
                if reasons:
                    case_data["dishonour_reason"] = reasons[0]
                    updates.append(f"Dishonour Reason -> {reasons[0]}")
            elif dtype == "NOTICE":
                if dates:
                    case_data["notice_date"] = dates[0]
                    updates.append(f"Notice Date -> {dates[0]}")
                tracking = ext.get("postal_tracking_numbers", [])
                if tracking:
                    case_data["notice_tracking_number"] = tracking[0]
                    updates.append(f"Postal Tracking -> {tracking[0]}")
                compliance = ext.get("notice_compliance", {})
                if compliance and not compliance.get("is_statutorily_valid"):
                    if "concepts" not in case_data:
                        case_data["concepts"] = []
                    case_data["concepts"].append({"concept": "notice_defect"})
                    updates.append("FATAL STATUTORY DEFECT: Notice missing '15-day' demand mandate.")
            elif dtype == "DEBT_PROOF":
                dp_class = ext.get("debt_proof_class")
                is_stamped = ext.get("has_stamp_duty", False)
                if dp_class:
                    case_data["debt_proof_type"] = dp_class
                    updates.append(f"Debt Proof Classification -> {dp_class}")
                if dp_class == "FORMAL_AGREEMENT" and not is_stamped:
                    if "concepts" not in case_data: case_data["concepts"] = []
                    case_data["concepts"].append({"concept": "unstamped_agreement"})
                    updates.append("WARNING: Formal agreement appears unstamped/unregistered. Inadmissible under Sec 35 Indian Stamp Act.")
        has_bsa_cert = any(str(d.get("doc_type")).upper() == "BSA_CERTIFICATE" for d in documents)
        if case_data.get("debt_proof_type") == "ELECTRONIC_COMMUNICATION" and not has_bsa_cert:
            if "concepts" not in case_data: case_data["concepts"] = []
            case_data["concepts"].append({"concept": "missing_bsa_certificate"})
            updates.append("FATAL DEFECT: Electronic evidence relied upon, but Section 63(4) BSA Certificate is missing!")
        if not updates:
            return True, "No new data extracted from documents to update."
        case_data["analysis_mode"] = "reality_verified"
        new_result = JudiQEngine.analyze_case(case_data)
        DatabaseManager.save_case(
            case_id=case_id,
            user_id=original_case[2],
            case_data=case_data,
            analysis_result=new_result,
            score=new_result.get("score", 0),
            verdict=new_result.get("verdict", "Unknown")
        )
        msg = f"Re-analyzed case using physical documents. Verified Facts:\n" + "\n".join(updates)
        DatabaseManager.send_message(caseroom_id, user_id, msg)
        return True, new_result
