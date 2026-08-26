import sqlite3
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = os.environ.get("SQLITE_DB_PATH", "analytics.db")
# SECURITY: DATABASE_URL must be set via environment variable.
# No credentials are hardcoded. Falls back to SQLite if not provided.
DATABASE_URL = os.environ.get("DATABASE_URL", "")


class DatabaseManager:
    _active_dialect = "sqlite"
    _pg_pool = None

    @classmethod
    def _get_pg_pool(cls):
        if cls._pg_pool is None and DATABASE_URL and ("postgres" in DATABASE_URL or "postgresql" in DATABASE_URL):
            try:
                import psycopg2.pool
                cls._pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=20,
                    dsn=DATABASE_URL
                )
                logger.info("🐘 Production PostgreSQL Connection Pool Initialized (maxconn=20).")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize PostgreSQL pool: {e}. Falling back to single connections.")
        return cls._pg_pool

    @staticmethod
    def get_connection():
        # Priority 1: Production PostgreSQL Database (if DATABASE_URL is configured)
        if DATABASE_URL and ("postgres" in DATABASE_URL or "postgresql" in DATABASE_URL):
            try:
                import psycopg2
                pool = DatabaseManager._get_pg_pool()
                if pool:
                    conn = pool.getconn()
                    conn.autocommit = True
                    DatabaseManager._active_dialect = "postgres"
                    return conn
                else:
                    conn = psycopg2.connect(DATABASE_URL)
                    DatabaseManager._active_dialect = "postgres"
                    logger.info("📡 Production PostgreSQL Connected.")
                    return conn
            except ImportError:
                logger.warning("⚠️ psycopg2 not installed. Falling back to local SQLite.")
            except Exception as pg_err:
                logger.warning(f"⚠️ Production PostgreSQL connection failed: {pg_err}. Falling back to local SQLite.")

        # Priority 2: Local Development SQLite Database
        try:
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            DatabaseManager._active_dialect = "sqlite"
            logger.info("📁 Local Development Database (SQLite) Connected.")
            return conn
        except Exception as sqlite_err:
            logger.error(f"❌ SQLite connection failed: {sqlite_err}")
            raise sqlite_err

    @staticmethod
    def get_dialect_placeholder():
        if DatabaseManager._active_dialect == "postgres":
            return "%s"
        return "?"

    @staticmethod
    def init_db():
        """
        Initialize all required database tables.
        Uses a single try/finally block to ensure the connection is always closed.
        serial_primary is resolved AFTER get_connection() so the dialect is known.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            # Dialect is now set by get_connection(); resolve the serial type here
            serial_primary = (
                "SERIAL PRIMARY KEY"
                if DatabaseManager._active_dialect == "postgres"
                else "INTEGER PRIMARY KEY AUTOINCREMENT"
            )
            cursor = conn.cursor()

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS saved_cases (
                    id {serial_primary},
                    case_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    case_data TEXT,
                    analysis_result TEXT,
                    score REAL,
                    verdict TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    tags TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS saved_drafts (
                    id {serial_primary},
                    case_id TEXT NOT NULL,
                    draft_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    created_at TEXT,
                    UNIQUE(case_id, draft_type, version)
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS caserooms (
                    id {serial_primary},
                    caseroom_id TEXT UNIQUE NOT NULL,
                    case_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    status TEXT DEFAULT 'ACTIVE',
                    created_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS caseroom_participants (
                    id {serial_primary},
                    caseroom_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT DEFAULT 'RESEARCHER',
                    joined_at TEXT,
                    UNIQUE(caseroom_id, user_id)
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS caseroom_messages (
                    id {serial_primary},
                    caseroom_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS caseroom_documents (
                    id {serial_primary},
                    caseroom_id TEXT NOT NULL,
                    uploader_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    doc_type TEXT,
                    validation_status TEXT DEFAULT 'PENDING',
                    extracted_data TEXT,
                    version INTEGER DEFAULT 1,
                    created_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS caseroom_tasks (
                    id {serial_primary},
                    caseroom_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    status TEXT DEFAULT 'PENDING',
                    created_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id {serial_primary},
                    user_id TEXT NOT NULL,
                    case_id TEXT,
                    action TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_quotas (
                    user_id TEXT PRIMARY KEY,
                    email TEXT,
                    role TEXT DEFAULT 'law_firm',
                    monthly_report_limit INTEGER DEFAULT 25,
                    reports_used_this_month INTEGER DEFAULT 0,
                    current_month_period TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()
            logger.info("Database, Caseroom, and User Quota tables initialized successfully.")
        except Exception as e:
            logger.error(f"Database init failed: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def save_case(case_id, user_id, case_data, analysis_result, score, verdict):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            p = DatabaseManager.get_dialect_placeholder()
            tags = [verdict]
            if case_data.get("accused_type") != "Individual":
                tags.append("CORPORATE")
            if score > 75:
                tags.append("HIGH_STRENGTH")
            elif score < 40:
                tags.append("WEAK_DEFENCE")
            if p == "%s":
                # PostgreSQL upsert
                query = f"""
                    INSERT INTO saved_cases
                    (case_id, user_id, case_data, analysis_result, score, verdict, created_at, updated_at, tags)
                    VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                    ON CONFLICT (case_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id, case_data = EXCLUDED.case_data,
                    analysis_result = EXCLUDED.analysis_result, score = EXCLUDED.score,
                    verdict = EXCLUDED.verdict, updated_at = EXCLUDED.updated_at, tags = EXCLUDED.tags
                """
            else:
                # SQLite upsert
                query = f"""
                    INSERT INTO saved_cases
                    (case_id, user_id, case_data, analysis_result, score, verdict, created_at, updated_at, tags)
                    VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                    ON CONFLICT(case_id) DO UPDATE SET
                    user_id = excluded.user_id, case_data = excluded.case_data,
                    analysis_result = excluded.analysis_result, score = excluded.score,
                    verdict = excluded.verdict, updated_at = excluded.updated_at, tags = excluded.tags
                """
            cursor.execute(query, (
                case_id,
                user_id,
                json.dumps(case_data),
                json.dumps(analysis_result),
                score,
                verdict,
                now,
                now,
                ",".join(tags)
            ))
            draft_content = analysis_result.get("draft") or analysis_result.get("draft_raw")
            if draft_content:
                draft_type = analysis_result.get("draft_type", "LEGAL_OPINION")
                cursor.execute(
                    f"SELECT MAX(version) FROM saved_drafts WHERE case_id = {p} AND draft_type = {p}",
                    (case_id, draft_type)
                )
                row = cursor.fetchone()
                next_version = (row[0] or 0) + 1
                cursor.execute(
                    f"SELECT content FROM saved_drafts WHERE case_id = {p} AND draft_type = {p} AND version = {p}",
                    (case_id, draft_type, next_version - 1)
                )
                prev_row = cursor.fetchone()
                if not prev_row or prev_row[0] != draft_content:
                    cursor.execute(f"""
                        INSERT INTO saved_drafts (case_id, draft_type, content, version, created_at)
                        VALUES ({p}, {p}, {p}, {p}, {p})
                    """, (case_id, draft_type, draft_content, next_version, now))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save case {case_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_case(case_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"SELECT * FROM saved_cases WHERE case_id = {p}", (case_id,))
            row = cursor.fetchone()
            return row
        except Exception as e:
            logger.error(f"Failed to fetch case {case_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_caseroom_by_case_id(case_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"SELECT caseroom_id FROM caserooms WHERE case_id = {p}", (case_id,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to fetch caseroom by case_id {case_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def create_caseroom(caseroom_id, case_id, owner_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO caserooms (caseroom_id, case_id, owner_id, created_at)
                VALUES ({p}, {p}, {p}, {p})
            """, (caseroom_id, case_id, owner_id, now))
            if p == "%s":
                query = f"INSERT INTO caseroom_participants (caseroom_id, user_id, role, joined_at) VALUES ({p}, {p}, {p}, {p}) ON CONFLICT DO NOTHING"
            else:
                query = f"INSERT OR IGNORE INTO caseroom_participants (caseroom_id, user_id, role, joined_at) VALUES ({p}, {p}, {p}, {p})"
            cursor.execute(query, (caseroom_id, owner_id, 'Lead Counsel', now))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to create caseroom {caseroom_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def add_participant(caseroom_id, user_id, role="RESEARCHER"):
        """
        Add a participant to a caseroom. Ignores/no-ops on duplicate.
        Called by CaseroomManager.invite_collaborator().
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            if DatabaseManager._active_dialect == "postgres":
                query = f"INSERT INTO caseroom_participants (caseroom_id, user_id, role, joined_at) VALUES ({p}, {p}, {p}, {p}) ON CONFLICT DO NOTHING"
            else:
                query = f"INSERT OR IGNORE INTO caseroom_participants (caseroom_id, user_id, role, joined_at) VALUES ({p}, {p}, {p}, {p})"
            cursor.execute(query, (caseroom_id, user_id, role, now))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add participant {user_id} to caseroom {caseroom_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_caseroom_data(caseroom_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"SELECT * FROM caserooms WHERE caseroom_id = {p}", (caseroom_id,))
            room = cursor.fetchone()
            if not room:
                return None
            cursor.execute(f"SELECT user_id, role FROM caseroom_participants WHERE caseroom_id = {p}", (caseroom_id,))
            participants = [{"user_id": r[0], "role": r[1]} for r in cursor.fetchall()]
            cursor.execute(
                f"SELECT user_id, content, created_at FROM caseroom_messages WHERE caseroom_id = {p} ORDER BY created_at ASC",
                (caseroom_id,)
            )
            messages = [{"user_id": r[0], "content": r[1], "timestamp": r[2]} for r in cursor.fetchall()]
            cursor.execute(
                f"SELECT id, title, status, due_date FROM caseroom_tasks WHERE caseroom_id = {p}",
                (caseroom_id,)
            )
            tasks = [{"id": r[0], "title": r[1], "status": r[2], "due_date": r[3]} for r in cursor.fetchall()]
            cursor.execute(
                f"SELECT id, uploader_id, file_name, file_path, doc_type, validation_status, extracted_data, created_at FROM caseroom_documents WHERE caseroom_id = {p}",
                (caseroom_id,)
            )
            documents = []
            for r in cursor.fetchall():
                ext_data = {}
                if r[6]:
                    try:
                        ext_data = json.loads(r[6])
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Invalid extracted_data JSON for document {r[0]}: {e}")
                documents.append({
                    "id": r[0], "uploader_id": r[1], "file_name": r[2],
                    "file_path": r[3], "doc_type": r[4], "validation_status": r[5],
                    "extracted_data": ext_data, "created_at": r[7]
                })
            return {
                "room_info": room,
                "participants": participants,
                "messages": messages,
                "tasks": tasks,
                "documents": documents
            }
        except Exception as e:
            logger.error(f"Failed to fetch caseroom data for {caseroom_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def send_message(caseroom_id, user_id, content):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO caseroom_messages (caseroom_id, user_id, content, created_at)
                VALUES ({p}, {p}, {p}, {p})
            """, (caseroom_id, user_id, content, now))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to send message in {caseroom_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def save_document(caseroom_id, uploader_id, file_name, file_path, doc_type, validation_status="PENDING", extracted_data=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            ext_json = json.dumps(extracted_data) if extracted_data else None
            cursor.execute(f"""
                INSERT INTO caseroom_documents
                (caseroom_id, uploader_id, file_name, file_path, doc_type, validation_status, extracted_data, created_at)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """, (caseroom_id, uploader_id, file_name, file_path, doc_type, validation_status, ext_json, now))
            doc_id = cursor.lastrowid
            conn.commit()
            return doc_id
        except Exception as e:
            logger.error(f"Failed to save document in {caseroom_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_caseroom_documents(caseroom_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(
                f"SELECT id, uploader_id, file_name, file_path, doc_type, validation_status, created_at FROM caseroom_documents WHERE caseroom_id = {p}",
                (caseroom_id,)
            )
            docs = [
                {"id": r[0], "uploader_id": r[1], "file_name": r[2], "file_path": r[3],
                 "doc_type": r[4], "validation_status": r[5], "created_at": r[6]}
                for r in cursor.fetchall()
            ]
            return docs
        except Exception as e:
            logger.error(f"Failed to fetch documents for {caseroom_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def save_interaction(log_entry):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"""
                INSERT INTO audit_logs (user_id, case_id, action, metadata, timestamp)
                VALUES ({p}, {p}, {p}, {p}, {p})
            """, (
                log_entry.get("user_id"),
                log_entry.get("case_id"),
                log_entry.get("action"),
                json.dumps(log_entry.get("metadata", {})),
                log_entry.get("timestamp")
            ))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_draft_history(case_id, draft_type):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"""
                SELECT version, content, created_at
                FROM saved_drafts
                WHERE case_id = {p} AND draft_type = {p}
                ORDER BY version DESC
            """, (case_id, draft_type))
            rows = cursor.fetchall()
            return [{"version": r[0], "content": r[1], "created_at": r[2]} for r in rows]
        except Exception as e:
            logger.error(f"Failed to fetch draft history: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_or_create_user_quota(user_id: str, email: str = "", role: str = "law_firm", default_limit: int = 25) -> dict:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            current_month = datetime.now().strftime("%Y-%m")
            now_iso = datetime.now().isoformat()

            cursor.execute(f"""
                SELECT user_id, email, role, monthly_report_limit, reports_used_this_month, current_month_period, is_active, created_at, updated_at
                FROM user_quotas
                WHERE user_id = {p}
            """, (user_id,))
            row = cursor.fetchone()

            if not row:
                cursor.execute(f"""
                    INSERT INTO user_quotas
                    (user_id, email, role, monthly_report_limit, reports_used_this_month, current_month_period, is_active, created_at, updated_at)
                    VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """, (user_id, email, role, default_limit, 0, current_month, 1, now_iso, now_iso))
                conn.commit()
                return {
                    "user_id": user_id,
                    "email": email,
                    "role": role,
                    "monthly_report_limit": default_limit,
                    "reports_used_this_month": 0,
                    "remaining_reports": default_limit if default_limit != -1 else 999999,
                    "current_month_period": current_month,
                    "is_active": True,
                    "created_at": now_iso,
                    "updated_at": now_iso
                }

            # If existing user, check if month period rolled over
            db_user_id, db_email, db_role, db_limit, db_used, db_period, db_active, db_created, db_updated = row
            if db_period != current_month:
                db_used = 0
                cursor.execute(f"""
                    UPDATE user_quotas
                    SET reports_used_this_month = 0, current_month_period = {p}, updated_at = {p}
                    WHERE user_id = {p}
                """, (current_month, now_iso, user_id))
                conn.commit()

            # Update email or role if provided and changed
            if email and email != db_email:
                cursor.execute(f"UPDATE user_quotas SET email = {p}, updated_at = {p} WHERE user_id = {p}", (email, now_iso, user_id))
                conn.commit()
                db_email = email

            limit = int(db_limit)
            used = int(db_used)
            remaining = (limit - used) if limit != -1 else 999999

            return {
                "user_id": db_user_id,
                "email": db_email or email,
                "role": db_role,
                "monthly_report_limit": limit,
                "reports_used_this_month": used,
                "remaining_reports": max(0, remaining),
                "current_month_period": current_month,
                "is_active": bool(db_active),
                "created_at": db_created,
                "updated_at": db_updated
            }
        except Exception as e:
            logger.error(f"Error in get_or_create_user_quota: {e}")
            return {
                "user_id": user_id,
                "email": email,
                "role": role,
                "monthly_report_limit": default_limit,
                "reports_used_this_month": 0,
                "remaining_reports": default_limit,
                "current_month_period": datetime.now().strftime("%Y-%m"),
                "is_active": True
            }
        finally:
            if conn:
                conn.close()

    @staticmethod
    def check_and_consume_report_quota(user_id: str, email: str = "", cost: int = 1) -> dict:
        """
        Atomically checks if the user has available monthly report quota and consumes `cost` units.
        Returns dict with `allowed`, `current_usage`, `monthly_limit`, `remaining`.
        """
        quota = DatabaseManager.get_or_create_user_quota(user_id, email)
        if not quota["is_active"]:
            return {
                "allowed": False,
                "reason": "USER_SUSPENDED",
                "message": "Your account has been suspended by the administrator.",
                "quota": quota
            }

        limit = quota["monthly_report_limit"]
        used = quota["reports_used_this_month"]

        # -1 represents unlimited reports
        if limit != -1 and (used + cost) > limit:
            return {
                "allowed": False,
                "reason": "QUOTA_EXCEEDED",
                "message": f"Monthly report limit reached ({used}/{limit} reports used). Please contact your administrator for an allocation increase.",
                "quota": quota
            }

        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()
            new_used = used + cost

            cursor.execute(f"""
                UPDATE user_quotas
                SET reports_used_this_month = {p}, updated_at = {p}
                WHERE user_id = {p}
            """, (new_used, now_iso, user_id))
            conn.commit()

            quota["reports_used_this_month"] = new_used
            quota["remaining_reports"] = (limit - new_used) if limit != -1 else 999999
            return {
                "allowed": True,
                "reason": "OK",
                "quota": quota
            }
        except Exception as e:
            logger.error(f"Error consuming report quota: {e}")
            return {
                "allowed": True,
                "reason": "FALLBACK_ALLOWED",
                "quota": quota
            }
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_users_quotas() -> list:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, email, role, monthly_report_limit, reports_used_this_month, current_month_period, is_active, created_at, updated_at
                FROM user_quotas
                ORDER BY updated_at DESC
            """)
            rows = cursor.fetchall()
            current_month = datetime.now().strftime("%Y-%m")
            users = []
            for r in rows:
                limit = int(r[3])
                used = int(r[4]) if r[5] == current_month else 0
                remaining = (limit - used) if limit != -1 else 999999
                users.append({
                    "user_id": r[0],
                    "email": r[1] or "N/A",
                    "role": r[2] or "law_firm",
                    "monthly_report_limit": limit,
                    "reports_used_this_month": used,
                    "remaining_reports": max(0, remaining),
                    "current_month_period": current_month,
                    "is_active": bool(r[6]),
                    "created_at": r[7],
                    "updated_at": r[8]
                })
            return users
        except Exception as e:
            logger.error(f"Error fetching all user quotas: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_user_quota_allocation(user_id: str, monthly_limit: int = None, is_active: bool = None, role: str = None, email: str = None) -> bool:
        conn = None
        try:
            # Ensure user exists first
            DatabaseManager.get_or_create_user_quota(user_id, email or "")
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()

            updates = ["updated_at = " + p]
            params = [now_iso]

            if monthly_limit is not None:
                updates.append("monthly_report_limit = " + p)
                params.append(int(monthly_limit))
            if is_active is not None:
                updates.append("is_active = " + p)
                params.append(1 if is_active else 0)
            if role is not None:
                updates.append("role = " + p)
                params.append(str(role))
            if email is not None and email.strip():
                updates.append("email = " + p)
                params.append(str(email).strip())

            params.append(user_id)
            query = f"UPDATE user_quotas SET {', '.join(updates)} WHERE user_id = {p}"
            cursor.execute(query, tuple(params))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user quota: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def reset_user_monthly_usage(user_id: str) -> bool:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()
            cursor.execute(f"""
                UPDATE user_quotas
                SET reports_used_this_month = 0, updated_at = {p}
                WHERE user_id = {p}
            """, (now_iso, user_id))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error resetting user monthly usage: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_platform_admin_stats() -> dict:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            current_month = datetime.now().strftime("%Y-%m")

            cursor.execute("SELECT COUNT(*) FROM user_quotas")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM user_quotas WHERE is_active = 1")
            active_users = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(reports_used_this_month) FROM user_quotas WHERE current_month_period = ?", (current_month,))
            res = cursor.fetchone()[0]
            total_reports_this_month = int(res) if res is not None else 0

            cursor.execute("SELECT COUNT(*) FROM saved_cases")
            total_saved_cases = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            total_audit_events = cursor.fetchone()[0]

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_reports_this_month": total_reports_this_month,
                "total_saved_cases": total_saved_cases,
                "total_audit_events": total_audit_events,
                "current_period": current_month
            }
        except Exception as e:
            logger.error(f"Error getting platform admin stats: {e}")
            return {
                "total_users": 0,
                "active_users": 0,
                "total_reports_this_month": 0,
                "total_saved_cases": 0,
                "total_audit_events": 0,
                "current_period": datetime.now().strftime("%Y-%m")
            }
        finally:
            if conn:
                conn.close()
