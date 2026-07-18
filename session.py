import sqlite3
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)
DB_PATH = "analytics.db"
DATABASE_URL = os.environ.get("DATABASE_URL")


class DatabaseManager:
    _active_dialect = "sqlite"

    @staticmethod
    def get_connection():
        if DATABASE_URL and "postgres" in DATABASE_URL:
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                DatabaseManager._active_dialect = "postgres"
                logger.info("📡 Production Database (Postgres) Connected.")
                return conn
            except ImportError:
                logger.error("❌ psycopg2 not found. Falling back to SQLite.")
            except Exception as e:
                logger.error(f"❌ Postgres connection failed: {e}. Falling back to SQLite.")
        DatabaseManager._active_dialect = "sqlite"
        return sqlite3.connect(DB_PATH, check_same_thread=False)

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
            conn.commit()
            logger.info("Database and Caseroom tables initialized successfully.")
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
