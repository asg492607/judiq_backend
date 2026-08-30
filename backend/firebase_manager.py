"""
JudiQ AI — Firebase & Google Cloud Firestore Integration Layer
Handles real-time cloud persistence for User Profiles, Quotas, Case Analyses,
Bank Recovery Audits, and Caseroom Telemetry.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

logger = logging.getLogger("JudiQ.Firebase")

# Firebase Configuration Constants
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "idcourt-cb58f")
FIREBASE_STORAGE_BUCKET = os.environ.get("FIREBASE_STORAGE_BUCKET", "idcourt-cb58f.firebasestorage.app")
FIREBASE_SERVICE_ACCOUNT_JSON = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")


class FirebaseManager:
    """
    Singleton Manager for Firebase Admin SDK & Cloud Firestore.
    Provides dual-write and cloud sync for users, analyses, and audit logs.
    """
    _initialized: bool = False
    _firestore_client = None
    _is_available: bool = False

    @classmethod
    def initialize(cls):
        """Initializes Firebase Admin SDK if not already active."""
        if cls._initialized:
            return cls._firestore_client

        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                cred = None
                # Check for Service Account JSON credential string or file path
                if FIREBASE_SERVICE_ACCOUNT_JSON:
                    if os.path.isfile(FIREBASE_SERVICE_ACCOUNT_JSON):
                        cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_JSON)
                    else:
                        try:
                            cert_dict = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
                            cred = credentials.Certificate(cert_dict)
                        except Exception as e:
                            logger.warning(f"Could not parse FIREBASE_SERVICE_ACCOUNT_JSON string: {e}")

                options = {
                    "projectId": FIREBASE_PROJECT_ID,
                    "storageBucket": FIREBASE_STORAGE_BUCKET
                }

                if cred:
                    firebase_admin.initialize_app(cred, options)
                else:
                    # Attempt Application Default Credentials / Project ID fallback
                    try:
                        firebase_admin.initialize_app(options=options)
                    except Exception as fallback_err:
                        logger.warning(f"Firebase app init with options only: {fallback_err}")
                        try:
                            firebase_admin.initialize_app()
                        except Exception:
                            pass

            cls._firestore_client = firestore.client()
            cls._is_available = True
            cls._initialized = True
            logger.info(f"🔥 Firebase Firestore initialized successfully (Project: {FIREBASE_PROJECT_ID}).")
            return cls._firestore_client
        except Exception as e:
            cls._is_available = False
            cls._initialized = True
            logger.warning(f"⚠️ Firebase Firestore initialization skipped/failed: {e}. (Local SQL active).")
            return None

    @classmethod
    def get_firestore(cls):
        """Returns the active Firestore client or None if unavailable."""
        if not cls._initialized:
            cls.initialize()
        return cls._firestore_client

    @classmethod
    def save_user_profile(cls, user_id: str, email: str, role: str = "citizen",
                          monthly_report_limit: int = 10, reports_used_this_month: int = 0,
                          plan_status: str = "APPROVED", selected_modules: Optional[List[str]] = None,
                          monthly_price_inr: float = 0.0, is_active: bool = True,
                          extra_data: Optional[Dict[str, Any]] = None) -> bool:
        """Saves or updates a user profile in Firestore `users` collection."""
        try:
            db = cls.get_firestore()
            if not db:
                return False

            now = datetime.utcnow().isoformat()
            user_doc = {
                "user_id": user_id,
                "email": email,
                "role": role,
                "monthly_report_limit": monthly_report_limit,
                "reports_used_this_month": reports_used_this_month,
                "plan_status": plan_status,
                "selected_modules": selected_modules or ["s138"],
                "monthly_price_inr": monthly_price_inr,
                "is_active": is_active,
                "updated_at": now
            }
            if extra_data:
                user_doc.update(extra_data)

            # Upsert into 'users' collection
            db.collection("users").document(user_id).set(user_doc, merge=True)
            logger.debug(f"🔥 User {user_id} synced to Firebase Firestore.")
            return True
        except Exception as e:
            logger.warning(f"Failed to sync user {user_id} to Firebase: {e}")
            return False

    @classmethod
    def get_user_profile(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user profile from Firestore."""
        try:
            db = cls.get_firestore()
            if not db:
                return None
            doc = db.collection("users").document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch user {user_id} from Firebase: {e}")
            return None

    @classmethod
    def save_case_analysis(cls, case_id: str, user_id: str, case_data: Dict[str, Any],
                           analysis_result: Dict[str, Any], score: float, verdict: str,
                           tags: Optional[List[str]] = None) -> bool:
        """
        Saves case intake data and complete analytical report to Firebase Firestore:
        1. `/cases/{case_id}` (Global analysis index)
        2. `/users/{user_id}/cases/{case_id}` (User's personal case portfolio)
        """
        try:
            db = cls.get_firestore()
            if not db:
                return False

            now = datetime.utcnow().isoformat()
            payload = {
                "case_id": case_id,
                "user_id": user_id,
                "case_title": case_data.get("case_title", "Untitled Matter"),
                "complainant_name": case_data.get("complainant_name", ""),
                "accused_name": case_data.get("accused_name", ""),
                "case_type": case_data.get("case_type", "Cheque Bounce"),
                "score": float(score),
                "verdict": verdict,
                "tags": tags or [verdict],
                "case_data": case_data,
                "analysis_result": analysis_result,
                "created_at": now,
                "updated_at": now
            }

            # 1. Write to global cases collection
            db.collection("cases").document(case_id).set(payload, merge=True)

            # 2. Write to user sub-collection
            db.collection("users").document(user_id).collection("cases").document(case_id).set({
                "case_id": case_id,
                "case_title": payload["case_title"],
                "score": payload["score"],
                "verdict": payload["verdict"],
                "case_type": payload["case_type"],
                "updated_at": now,
                "created_at": now
            }, merge=True)

            logger.info(f"🔥 Case analysis {case_id} successfully stored in Firebase Firestore.")
            return True
        except Exception as e:
            logger.warning(f"Failed to save case {case_id} to Firebase: {e}")
            return False

    @classmethod
    def get_case_analysis(cls, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a full case analysis payload from Firestore."""
        try:
            db = cls.get_firestore()
            if not db:
                return None
            doc = db.collection("cases").document(case_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch case {case_id} from Firebase: {e}")
            return None

    @classmethod
    def list_user_cases(cls, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Lists recent case files for a user from Firestore."""
        try:
            db = cls.get_firestore()
            if not db:
                return []
            cases_ref = db.collection("cases").where("user_id", "==", user_id).limit(limit)
            docs = cases_ref.stream()
            results = []
            for doc in docs:
                data = doc.to_dict()
                results.append({
                    "id": data.get("case_id"),
                    "user_id": data.get("user_id"),
                    "title": data.get("case_title", "Untitled Case"),
                    "date": data.get("updated_at", data.get("created_at", "")),
                    "score": data.get("score", 0),
                    "verdict": data.get("verdict", ""),
                    "case_type": data.get("case_type", "Cheque Bounce")
                })
            return results
        except Exception as e:
            logger.warning(f"Failed to list user cases from Firebase: {e}")
            return []

    @classmethod
    def save_bank_audit(cls, audit_id: str, officer_id: str, case_reference: str,
                        borrower_name: str, total_overdue_inr: float,
                        primary_recommendation: str, statutory_viability_score: float,
                        ots_recommended: bool, advocate_sla_days: int,
                        timestamp: str, audit_payload: Dict[str, Any]) -> bool:
        """Saves institutional recovery audit to Firestore `bank_audits` collection."""
        try:
            db = cls.get_firestore()
            if not db:
                return False

            doc = {
                "audit_id": audit_id,
                "officer_id": officer_id,
                "case_reference": case_reference,
                "borrower_name": borrower_name,
                "total_overdue_inr": float(total_overdue_inr),
                "primary_recommendation": primary_recommendation,
                "statutory_viability_score": float(statutory_viability_score),
                "ots_recommended": ots_recommended,
                "advocate_sla_days": advocate_sla_days,
                "timestamp": timestamp,
                "audit_payload": audit_payload,
                "created_at": datetime.utcnow().isoformat()
            }
            db.collection("bank_audits").document(audit_id).set(doc, merge=True)
            logger.info(f"🔥 Bank Recovery Audit {audit_id} stored in Firebase Firestore.")
            return True
        except Exception as e:
            logger.warning(f"Failed to save bank audit {audit_id} to Firebase: {e}")
            return False

    @classmethod
    def save_bank_officer(cls, officer_id: str, name: str, bank_name: str, branch_name: str,
                          role: str, email: str, ifsc_code: str = "", department: str = "",
                          monthly_audit_limit: int = 50, is_active: bool = True) -> bool:
        """Saves institutional bank officer profile to Firestore `bank_officers` collection."""
        try:
            db = cls.get_firestore()
            if not db:
                return False

            doc = {
                "officer_id": officer_id,
                "name": name,
                "bank_name": bank_name,
                "branch_name": branch_name,
                "role": role,
                "email": email,
                "ifsc_code": ifsc_code,
                "department": department,
                "monthly_audit_limit": monthly_audit_limit,
                "is_active": is_active,
                "updated_at": datetime.utcnow().isoformat()
            }
            db.collection("bank_officers").document(officer_id).set(doc, merge=True)
            return True
        except Exception as e:
            logger.warning(f"Failed to save bank officer {officer_id} to Firebase: {e}")
            return False

    @classmethod
    def save_case_version(cls, case_id: str, user_id: str, version_num: int,
                          version_title: str, version_note: str,
                          case_data: Dict[str, Any], analysis_result: Dict[str, Any],
                          score: float, verdict: str, delta_score: float = 0.0) -> bool:
        """
        Saves a distinct historical snapshot version of a case analysis to Firestore.
        Collection path: `/cases/{case_id}/versions/{version_num}`
        """
        try:
            db = cls.get_firestore()
            if not db:
                return False

            now = datetime.utcnow().isoformat()
            version_doc = {
                "case_id": case_id,
                "user_id": user_id,
                "version_num": version_num,
                "version_title": version_title or f"Version {version_num}",
                "version_note": version_note or "Analysis Snapshot",
                "case_data": case_data,
                "analysis_result": analysis_result,
                "score": float(score),
                "verdict": verdict,
                "delta_score": float(delta_score),
                "created_at": now
            }

            # 1. Store in global case subcollection
            db.collection("cases").document(case_id).collection("versions").document(str(version_num)).set(version_doc, merge=True)

            # 2. Store in user's case version subcollection if user_id is provided
            if user_id and user_id != "ANONYMOUS":
                db.collection("users").document(user_id).collection("cases").document(case_id).collection("versions").document(str(version_num)).set({
                    "version_num": version_num,
                    "version_title": version_doc["version_title"],
                    "version_note": version_doc["version_note"],
                    "score": version_doc["score"],
                    "delta_score": version_doc["delta_score"],
                    "verdict": version_doc["verdict"],
                    "created_at": now
                }, merge=True)

            logger.info(f"🔥 Case {case_id} Version {version_num} successfully archived in Firestore.")
            return True
        except Exception as e:
            logger.warning(f"Failed to save case version {case_id} v{version_num} to Firebase: {e}")
            return False

    @classmethod
    def get_case_versions(cls, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves list of all saved version metadata from Firestore."""
        try:
            db = cls.get_firestore()
            if not db:
                return []
            versions_ref = db.collection("cases").document(case_id).collection("versions").order_by("version_num", direction=firestore.Query.DESCENDING)
            docs = versions_ref.stream()
            versions = []
            for doc in docs:
                data = doc.to_dict()
                versions.append({
                    "version_num": data.get("version_num"),
                    "version_title": data.get("version_title"),
                    "version_note": data.get("version_note"),
                    "score": data.get("score"),
                    "delta_score": data.get("delta_score", 0.0),
                    "verdict": data.get("verdict"),
                    "created_at": data.get("created_at")
                })
            return versions
        except Exception as e:
            logger.warning(f"Failed to fetch case versions for {case_id} from Firebase: {e}")
            return []

    @classmethod
    def get_case_version(cls, case_id: str, version_num: int) -> Optional[Dict[str, Any]]:
        """Retrieves a specific case version payload from Firestore."""
        try:
            db = cls.get_firestore()
            if not db:
                return None
            doc = db.collection("cases").document(case_id).collection("versions").document(str(version_num)).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch case {case_id} v{version_num} from Firebase: {e}")
            return None

