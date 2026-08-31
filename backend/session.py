import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List, Union

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
                CREATE TABLE IF NOT EXISTS case_versions (
                    id {serial_primary},
                    case_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    version_num INTEGER NOT NULL,
                    version_title TEXT,
                    version_note TEXT,
                    case_data TEXT,
                    analysis_result TEXT,
                    score REAL,
                    verdict TEXT,
                    delta_score REAL DEFAULT 0.0,
                    created_at TEXT,
                    UNIQUE(case_id, version_num)
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bank_officers (
                    officer_id TEXT PRIMARY KEY,
                    name TEXT,
                    bank_name TEXT,
                    branch_name TEXT,
                    role TEXT DEFAULT 'bank_officer',
                    email TEXT,
                    password_hash TEXT,
                    ifsc_code TEXT,
                    department TEXT,
                    monthly_audit_limit INTEGER DEFAULT 100,
                    audits_used_this_month INTEGER DEFAULT 0,
                    current_month_period TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            # Migration check for existing databases
            for col, col_type in [("password_hash", "TEXT"), ("ifsc_code", "TEXT"), ("department", "TEXT")]:
                try:
                    cursor.execute(f"ALTER TABLE bank_officers ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            for col, col_type in [
                ("plan_status", "TEXT DEFAULT 'APPROVED'"),
                ("selected_modules", "TEXT DEFAULT '[\"s138\"]'"),
                ("monthly_price_inr", "REAL DEFAULT 500"),
                ("requested_quota", "INTEGER DEFAULT 10"),
                ("approved_by", "TEXT"),
                ("approved_at", "TEXT")
            ]:
                try:
                    cursor.execute(f"ALTER TABLE user_quotas ADD COLUMN {col} {col_type}")
                except Exception:
                    pass

            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS bank_recovery_audits (
                    id {serial_primary},
                    audit_id TEXT UNIQUE NOT NULL,
                    officer_id TEXT NOT NULL,
                    bank_name TEXT,
                    branch_name TEXT,
                    case_type TEXT,
                    borrower_name TEXT,
                    loan_account_no TEXT,
                    default_amount REAL,
                    viability_score REAL,
                    verdict TEXT,
                    defect_count INTEGER DEFAULT 0,
                    details_json TEXT,
                    timestamp TEXT
                )
            """)

            # ── CMS Tables ──────────────────────────────────────────
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS cases_v2 (
                    id {serial_primary},
                    case_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    org_id TEXT,
                    case_name TEXT NOT NULL,
                    case_type TEXT DEFAULT 'section_138',
                    case_status TEXT DEFAULT 'draft',
                    priority TEXT DEFAULT 'medium',
                    tags TEXT,
                    description TEXT,
                    creditor_data TEXT,
                    debtor_data TEXT,
                    company_data TEXT,
                    financial_data TEXT,
                    collateral_data TEXT,
                    court_data TEXT,
                    analysis_result TEXT,
                    compliance_score REAL,
                    verdict TEXT,
                    access_level TEXT DEFAULT 'private',
                    shared_with TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    archived_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS clients (
                    id {serial_primary},
                    client_id TEXT UNIQUE NOT NULL,
                    org_id TEXT,
                    client_type TEXT NOT NULL,
                    role_type TEXT DEFAULT 'creditor',
                    name TEXT NOT NULL,
                    legal_name TEXT,
                    email TEXT,
                    phone TEXT,
                    mobile TEXT,
                    company_info TEXT,
                    address_data TEXT,
                    tax_info TEXT,
                    banking_info TEXT,
                    comm_prefs TEXT,
                    notes TEXT,
                    total_cases INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,
                    created_at TEXT,
                    updated_at TEXT,
                    created_by TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS case_client_links (
                    id {serial_primary},
                    case_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    linked_at TEXT,
                    linked_by TEXT,
                    UNIQUE(case_id, client_id, role)
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS case_documents (
                    id {serial_primary},
                    document_id TEXT UNIQUE NOT NULL,
                    case_id TEXT NOT NULL,
                    uploader_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    doc_type TEXT,
                    encryption_hash TEXT,
                    encrypted INTEGER DEFAULT 1,
                    ocr_text TEXT,
                    extracted_data TEXT,
                    s65b_status TEXT DEFAULT 'not_applicable',
                    s65b_cert_data TEXT,
                    tags TEXT,
                    notes TEXT,
                    validation_status TEXT DEFAULT 'pending',
                    version INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS draft_workflows (
                    id {serial_primary},
                    workflow_id TEXT UNIQUE NOT NULL,
                    case_id TEXT NOT NULL,
                    draft_type TEXT NOT NULL,
                    draft_content TEXT,
                    current_version INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'DRAFT',
                    created_by TEXT,
                    assigned_reviewer TEXT,
                    reviewer_comments TEXT,
                    approved_by TEXT,
                    approved_at TEXT,
                    filed_at TEXT,
                    filed_reference TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS case_deadlines (
                    id {serial_primary},
                    deadline_id TEXT UNIQUE NOT NULL,
                    case_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    statutory_basis TEXT,
                    due_date TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    urgency_level TEXT,
                    mandatory_action TEXT,
                    consequence TEXT,
                    reminder_14d_sent INTEGER DEFAULT 0,
                    reminder_7d_sent INTEGER DEFAULT 0,
                    reminder_3d_sent INTEGER DEFAULT 0,
                    reminder_1d_sent INTEGER DEFAULT 0,
                    completed_at TEXT,
                    created_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS team_members (
                    id {serial_primary},
                    member_id TEXT UNIQUE NOT NULL,
                    org_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    role TEXT DEFAULT 'officer',
                    department TEXT,
                    supervisor_id TEXT,
                    permissions TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS audit_log_v2 (
                    id {serial_primary},
                    log_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    case_id TEXT,
                    action TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id TEXT,
                    before_state TEXT,
                    after_state TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    note TEXT,
                    timestamp TEXT NOT NULL
                )
            """)

            conn.commit()
            logger.info("Database, Caseroom, User Quota, and Bank Recovery tables initialized successfully.")
            DatabaseManager._seed_initial_litigators(cursor, conn)
            DatabaseManager._seed_initial_bank_officers(cursor, conn)
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

            # Real-Time Cloud Sync: Firebase Firestore
            try:
                from firebase_manager import FirebaseManager
                FirebaseManager.save_case_analysis(case_id, user_id, case_data, analysis_result, score, verdict, tags)
            except Exception as fb_err:
                logger.debug(f"Firebase case sync notice: {fb_err}")

            # Automatically record version snapshot
            try:
                DatabaseManager.save_case_version(
                    case_id=case_id,
                    user_id=user_id,
                    case_data=case_data,
                    analysis_result=analysis_result,
                    score=score,
                    verdict=verdict,
                    version_title=case_data.get("version_title"),
                    version_note=case_data.get("version_note")
                )
            except Exception as v_err:
                logger.debug(f"Automatic version snapshot notice: {v_err}")

            return True
        except Exception as e:
            logger.error(f"Failed to save case {case_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def save_case_version(
        case_id: str,
        user_id: str,
        case_data: dict,
        analysis_result: dict,
        score: float,
        verdict: str,
        version_title: str = None,
        version_note: str = None
    ) -> dict:
        """
        Archives a versioned snapshot of a case and its analysis report.
        Automatically assigns sequential version numbers and computes score deltas.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()

            # Find latest version number & previous score
            cursor.execute(f"SELECT MAX(version_num), score FROM case_versions WHERE case_id = {p} GROUP BY case_id", (case_id,))
            row = cursor.fetchone()
            if row and row[0]:
                next_version = row[0] + 1
                prev_score = float(row[1]) if row[1] is not None else float(score)
            else:
                next_version = 1
                prev_score = float(score)

            delta_score = round(float(score) - prev_score, 1)
            v_title = version_title or f"Version {next_version}"
            v_note = version_note or ("Initial Case Intake Analysis" if next_version == 1 else "Updated Case Re-Analysis")

            cursor.execute(f"""
                INSERT INTO case_versions
                (case_id, user_id, version_num, version_title, version_note, case_data, analysis_result, score, verdict, delta_score, created_at)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """, (
                case_id, user_id, next_version, v_title, v_note,
                json.dumps(case_data), json.dumps(analysis_result),
                float(score), verdict, delta_score, now
            ))
            conn.commit()

            # Real-Time Cloud Sync: Firebase Firestore
            try:
                from firebase_manager import FirebaseManager
                FirebaseManager.save_case_version(
                    case_id=case_id,
                    user_id=user_id,
                    version_num=next_version,
                    version_title=v_title,
                    version_note=v_note,
                    case_data=case_data,
                    analysis_result=analysis_result,
                    score=float(score),
                    verdict=verdict,
                    delta_score=delta_score
                )
            except Exception as fb_err:
                logger.debug(f"Firebase case version sync notice: {fb_err}")

            return {
                "success": True,
                "case_id": case_id,
                "version_num": next_version,
                "version_title": v_title,
                "version_note": v_note,
                "score": float(score),
                "delta_score": delta_score,
                "verdict": verdict,
                "created_at": now
            }
        except Exception as e:
            logger.error(f"Error saving case version: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_case_versions(case_id: str) -> list:
        """
        Lists all version snapshots for a case with metadata, score progression, and notes.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"""
                SELECT version_num, version_title, version_note, score, delta_score, verdict, created_at, user_id
                FROM case_versions
                WHERE case_id = {p}
                ORDER BY version_num DESC
            """, (case_id,))
            rows = cursor.fetchall()
            versions = []
            for r in rows:
                versions.append({
                    "version_num": r[0],
                    "version_title": r[1] or f"Version {r[0]}",
                    "version_note": r[2] or "",
                    "score": float(r[3]) if r[3] is not None else 0.0,
                    "delta_score": float(r[4]) if r[4] is not None else 0.0,
                    "verdict": r[5] or "Unknown",
                    "created_at": r[6],
                    "user_id": r[7]
                })

            if not versions:
                # Fallback to Firebase Firestore
                try:
                    from firebase_manager import FirebaseManager
                    fb_versions = FirebaseManager.get_case_versions(case_id)
                    if fb_versions:
                        return fb_versions
                except Exception:
                    pass

            return versions
        except Exception as e:
            logger.error(f"Error fetching case versions for {case_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_case_version(case_id: str, version_num: int) -> dict:
        """
        Fetches the complete case data and analysis snapshot for a specific version number.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"""
                SELECT case_id, user_id, version_num, version_title, version_note, case_data, analysis_result, score, verdict, delta_score, created_at
                FROM case_versions
                WHERE case_id = {p} AND version_num = {p}
            """, (case_id, int(version_num)))
            r = cursor.fetchone()
            if not r:
                # Fallback to Firebase
                try:
                    from firebase_manager import FirebaseManager
                    fb_v = FirebaseManager.get_case_version(case_id, int(version_num))
                    if fb_v:
                        return fb_v
                except Exception:
                    pass
                return None

            try:
                cdata = json.loads(r[5]) if r[5] else {}
            except Exception:
                cdata = {}
            try:
                aresult = json.loads(r[6]) if r[6] else {}
            except Exception:
                aresult = {}

            return {
                "case_id": r[0],
                "user_id": r[1],
                "version_num": r[2],
                "version_title": r[3],
                "version_note": r[4],
                "case_data": cdata,
                "analysis_result": aresult,
                "score": float(r[7]) if r[7] is not None else 0.0,
                "verdict": r[8],
                "delta_score": float(r[9]) if r[9] is not None else 0.0,
                "created_at": r[10]
            }
        except Exception as e:
            logger.error(f"Error fetching version {version_num} for case {case_id}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def restore_case_version(case_id: str, version_num: int, user_id: str) -> dict:
        """
        Restores the active case record in saved_cases to match a historical snapshot version.
        """
        version_data = DatabaseManager.get_case_version(case_id, version_num)
        if not version_data:
            return {"success": False, "error": f"Version {version_num} not found"}

        # Save as current case
        DatabaseManager.save_case(
            case_id=case_id,
            user_id=user_id or version_data.get("user_id", "ANONYMOUS"),
            case_data=version_data.get("case_data", {}),
            analysis_result=version_data.get("analysis_result", {}),
            score=version_data.get("score", 0.0),
            verdict=version_data.get("verdict", "Unknown")
        )
        return {
            "success": True,
            "message": f"Successfully restored case {case_id} to Version {version_num}",
            "version": version_data
        }

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
                SELECT user_id, email, role, monthly_report_limit, reports_used_this_month, current_month_period, is_active, created_at, updated_at,
                       plan_status, selected_modules, monthly_price_inr, requested_quota, approved_by, approved_at
                FROM user_quotas
                WHERE user_id = {p}
            """, (user_id,))
            row = cursor.fetchone()

            if not row:
                cursor.execute(f"""
                    INSERT INTO user_quotas
                    (user_id, email, role, monthly_report_limit, reports_used_this_month, current_month_period, is_active, created_at, updated_at, plan_status, selected_modules, monthly_price_inr, requested_quota)
                    VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """, (user_id, email, role, default_limit, 0, current_month, 1, now_iso, now_iso, "APPROVED", json.dumps(["s138"]), 500.0, default_limit))
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
                    "updated_at": now_iso,
                    "plan_status": "APPROVED",
                    "selected_modules": ["s138"],
                    "monthly_price_inr": 500.0,
                    "requested_quota": default_limit,
                    "approved_by": "system",
                    "approved_at": now_iso
                }

            # If existing user, check if month period rolled over
            db_user_id, db_email, db_role, db_limit, db_used, db_period, db_active, db_created, db_updated = row[0:9]
            plan_status = row[9] if len(row) > 9 and row[9] else "APPROVED"
            raw_modules = row[10] if len(row) > 10 and row[10] else "[]"
            try:
                selected_modules = json.loads(raw_modules) if isinstance(raw_modules, str) else raw_modules
            except Exception:
                selected_modules = ["s138"]
            monthly_price = float(row[11]) if len(row) > 11 and row[11] is not None else 500.0
            req_quota = int(row[12]) if len(row) > 12 and row[12] is not None else int(db_limit)
            approved_by = row[13] if len(row) > 13 else ""
            approved_at = row[14] if len(row) > 14 else ""

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
                "updated_at": db_updated,
                "plan_status": plan_status,
                "selected_modules": selected_modules,
                "monthly_price_inr": monthly_price,
                "requested_quota": req_quota,
                "approved_by": approved_by,
                "approved_at": approved_at
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
                "is_active": True,
                "plan_status": "APPROVED",
                "selected_modules": ["s138"],
                "monthly_price_inr": 500.0,
                "requested_quota": default_limit
            }
        finally:
            if conn:
                conn.close()

    @staticmethod
    def check_and_consume_report_quota(user_id: str, email: str = "", cost: int = 1) -> dict:
        """
        Atomically checks if the user has an approved active plan and available monthly report quota.
        If pending admin approval or suspended, strictly blocks execution with detailed reason.
        """
        # Admin bypass
        if user_id.startswith("admin") or email.lower().startswith("admin@"):
            return {"allowed": True, "reason": "ADMIN_BYPASS", "quota": {"is_active": True, "plan_status": "APPROVED", "remaining_reports": 99999}}

        quota = DatabaseManager.get_or_create_user_quota(user_id, email)
        
        # Strict Admin Approval Gate Check
        if quota.get("plan_status") == "PENDING_APPROVAL":
            return {
                "allowed": False,
                "reason": "PENDING_ADMIN_APPROVAL",
                "message": "Account pending administrative approval. Your subscription plan request has been submitted to the Admin Control Center. No case analyses or legal drafts can be generated until an administrator approves your plan.",
                "quota": quota
            }

        if not quota.get("is_active"):
            return {
                "allowed": False,
                "reason": "USER_SUSPENDED",
                "message": "Your account access has been suspended by the administrator.",
                "quota": quota
            }

        limit = quota["monthly_report_limit"]
        used = quota["reports_used_this_month"]

        # -1 represents unlimited reports
        if limit != -1 and (used + cost) > limit:
            return {
                "allowed": False,
                "reason": "QUOTA_EXCEEDED",
                "message": f"Monthly case analysis quota limit reached ({used}/{limit} reports used). Please request a plan increase in the Admin Control Center.",
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
    def submit_subscription_plan(user_id: str, email: str, selected_modules: list, monthly_price_inr: float, requested_quota: int, role: str = "law_firm") -> dict:
        """
        Registers or updates a user subscription plan in PENDING_APPROVAL status, queuing it for admin review.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            current_month = datetime.now().strftime("%Y-%m")
            now_iso = datetime.now().isoformat()
            modules_json = json.dumps(selected_modules)

            cursor.execute(f"SELECT user_id FROM user_quotas WHERE user_id = {p}", (user_id,))
            exists = cursor.fetchone()

            if exists:
                cursor.execute(f"""
                    UPDATE user_quotas
                    SET email = {p}, role = {p}, plan_status = 'PENDING_APPROVAL', is_active = 0,
                        monthly_report_limit = 0, requested_quota = {p}, monthly_price_inr = {p},
                        selected_modules = {p}, updated_at = {p}
                    WHERE user_id = {p}
                """, (email, role, requested_quota, monthly_price_inr, modules_json, now_iso, user_id))
            else:
                cursor.execute(f"""
                    INSERT INTO user_quotas
                    (user_id, email, role, monthly_report_limit, reports_used_this_month, current_month_period, is_active, created_at, updated_at, plan_status, selected_modules, monthly_price_inr, requested_quota)
                    VALUES ({p}, {p}, {p}, 0, 0, {p}, 0, {p}, {p}, 'PENDING_APPROVAL', {p}, {p}, {p})
                """, (user_id, email, role, current_month, now_iso, now_iso, modules_json, monthly_price_inr, requested_quota))
            
            conn.commit()
            return DatabaseManager.get_or_create_user_quota(user_id, email)
        except Exception as e:
            logger.error(f"Error submitting subscription plan: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def approve_user_plan(user_id: str, admin_email: str = "admin@judiq.ai") -> dict:
        """
        Admin approves a pending subscription plan, allocating the requested case quota and activating the account.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()

            cursor.execute(f"SELECT requested_quota FROM user_quotas WHERE user_id = {p}", (user_id,))
            row = cursor.fetchone()
            req_quota = int(row[0]) if row and row[0] is not None else 25

            cursor.execute(f"""
                UPDATE user_quotas
                SET plan_status = 'APPROVED', is_active = 1, monthly_report_limit = {p},
                    approved_by = {p}, approved_at = {p}, updated_at = {p}
                WHERE user_id = {p}
            """, (req_quota, admin_email, now_iso, now_iso, user_id))
            conn.commit()

            # Real-Time Cloud Sync: Firebase Firestore
            try:
                from firebase_manager import FirebaseManager
                FirebaseManager.save_user_profile(
                    user_id=user_id,
                    email="",
                    plan_status="APPROVED",
                    monthly_report_limit=req_quota,
                    is_active=True
                )
            except Exception as fb_err:
                logger.debug(f"Firebase approval sync notice: {fb_err}")

            return DatabaseManager.get_or_create_user_quota(user_id)
        except Exception as e:
            logger.error(f"Error approving user plan: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def reject_user_plan(user_id: str, admin_email: str = "admin@judiq.ai", reason: str = "") -> dict:
        """
        Admin rejects a subscription plan request, keeping account locked.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()

            cursor.execute(f"""
                UPDATE user_quotas
                SET plan_status = 'REJECTED', is_active = 0, monthly_report_limit = 0,
                    approved_by = {p}, updated_at = {p}
                WHERE user_id = {p}
            """, (f"{admin_email} (REJECTED: {reason})", now_iso, user_id))
            conn.commit()

            # Real-Time Cloud Sync: Firebase Firestore
            try:
                from firebase_manager import FirebaseManager
                FirebaseManager.save_user_profile(
                    user_id=user_id,
                    email="",
                    plan_status="REJECTED",
                    monthly_report_limit=0,
                    is_active=False
                )
            except Exception as fb_err:
                logger.debug(f"Firebase rejection sync notice: {fb_err}")

            return DatabaseManager.get_or_create_user_quota(user_id)
        except Exception as e:
            logger.error(f"Error rejecting user plan: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def create_or_update_full_user(
        user_id: str,
        email: str,
        role: str = "law_firm",
        monthly_limit: int = 25,
        selected_modules: list = None,
        monthly_price_inr: float = 500.0,
        plan_status: str = "APPROVED",
        approved_by: str = None
    ) -> dict:
        """
        Creates or updates a litigator account with full subscription parameters.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()
            current_month = datetime.now().strftime("%Y-%m")
            mods = selected_modules or ["s138"]
            mods_json = json.dumps(mods)
            is_active = 1 if plan_status == "APPROVED" else 0
            approved_at = now_iso if plan_status == "APPROVED" else None

            cursor.execute(f"SELECT user_id FROM user_quotas WHERE user_id = {p}", (user_id,))
            exists = cursor.fetchone()

            if exists:
                cursor.execute(f"""
                    UPDATE user_quotas
                    SET email = {p}, role = {p}, monthly_report_limit = {p},
                        selected_modules = {p}, monthly_price_inr = {p}, plan_status = {p},
                        is_active = {p}, approved_by = {p}, approved_at = {p}, updated_at = {p}
                    WHERE user_id = {p}
                """, (email, role, monthly_limit, mods_json, monthly_price_inr, plan_status, is_active, approved_by, approved_at, now_iso, user_id))
            else:
                cursor.execute(f"""
                    INSERT INTO user_quotas (
                        user_id, email, role, monthly_report_limit, reports_used_this_month,
                        current_month_period, is_active, created_at, updated_at,
                        plan_status, selected_modules, monthly_price_inr, requested_quota,
                        approved_by, approved_at
                    ) VALUES ({p}, {p}, {p}, {p}, 0, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """, (
                    user_id, email, role, monthly_limit, current_month, is_active,
                    now_iso, now_iso, plan_status, mods_json, monthly_price_inr,
                    monthly_limit, approved_by, approved_at
                ))
            conn.commit()

            # Real-Time Cloud Sync: Firebase Firestore
            try:
                from firebase_manager import FirebaseManager
                FirebaseManager.save_user_profile(
                    user_id=user_id,
                    email=email,
                    role=role,
                    monthly_report_limit=monthly_limit,
                    plan_status=plan_status,
                    selected_modules=mods,
                    monthly_price_inr=monthly_price_inr,
                    is_active=(plan_status == "APPROVED")
                )
            except Exception as fb_err:
                logger.debug(f"Firebase user sync notice: {fb_err}")

            return DatabaseManager.get_or_create_user_quota(user_id, email)
        except Exception as e:
            logger.error(f"Error creating/updating full user: {e}")
            raise e
        finally:
            if conn:
                conn.close()


    @staticmethod
    def get_pending_plan_requests() -> list:
        """
        Returns all user accounts with PENDING_APPROVAL status.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, email, role, requested_quota, monthly_price_inr, selected_modules, plan_status, created_at, updated_at
                FROM user_quotas
                WHERE plan_status = 'PENDING_APPROVAL' OR is_active = 0
                ORDER BY updated_at DESC
            """)
            rows = cursor.fetchall()
            pending = []
            for r in rows:
                raw_mod = r[5] or "[]"
                try:
                    mods = json.loads(raw_mod) if isinstance(raw_mod, str) else raw_mod
                except Exception:
                    mods = []
                pending.append({
                    "user_id": r[0],
                    "email": r[1] or "N/A",
                    "role": r[2] or "law_firm",
                    "requested_quota": int(r[3]) if r[3] is not None else 10,
                    "monthly_price_inr": float(r[4]) if r[4] is not None else 500.0,
                    "selected_modules": mods,
                    "plan_status": r[6] or "PENDING_APPROVAL",
                    "created_at": r[7],
                    "updated_at": r[8]
                })
            return pending
        except Exception as e:
            logger.error(f"Error fetching pending plan requests: {e}")
            return []
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
                SELECT user_id, email, role, monthly_report_limit, reports_used_this_month, current_month_period, is_active, created_at, updated_at,
                       plan_status, selected_modules, monthly_price_inr, requested_quota, approved_by, approved_at
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
                raw_mod = r[10] if len(r) > 10 and r[10] else "[]"
                try:
                    mods = json.loads(raw_mod) if isinstance(raw_mod, str) else raw_mod
                except Exception:
                    mods = []
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
                    "updated_at": r[8],
                    "plan_status": r[9] if len(r) > 9 and r[9] else "APPROVED",
                    "selected_modules": mods,
                    "monthly_price_inr": float(r[11]) if len(r) > 11 and r[11] is not None else 500.0,
                    "requested_quota": int(r[12]) if len(r) > 12 and r[12] is not None else limit,
                    "approved_by": r[13] if len(r) > 13 else "",
                    "approved_at": r[14] if len(r) > 14 else ""
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
            p = DatabaseManager.get_dialect_placeholder()
            current_month = datetime.now().strftime("%Y-%m")

            cursor.execute("SELECT COUNT(*) FROM user_quotas")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM user_quotas WHERE is_active = 1")
            active_users = cursor.fetchone()[0]

            cursor.execute(f"SELECT SUM(reports_used_this_month) FROM user_quotas WHERE current_month_period = {p}", (current_month,))
            res = cursor.fetchone()[0]
            total_reports_this_month = int(res) if res is not None else 0

            cursor.execute("SELECT COUNT(*) FROM saved_cases")
            total_saved_cases = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM audit_logs")
            total_audit_events = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM user_quotas WHERE plan_status = 'PENDING_APPROVAL'")
            pending_plans = cursor.fetchone()[0]

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_reports_this_month": total_reports_this_month,
                "total_saved_cases": total_saved_cases,
                "total_audit_events": total_audit_events,
                "pending_plans": pending_plans,
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
                "pending_plans": 0,
                "current_period": datetime.now().strftime("%Y-%m")
            }
        finally:
            if conn:
                conn.close()

    @staticmethod
    def _seed_initial_litigators(cursor, conn):
        try:
            now_iso = datetime.now().isoformat()
            current_month = datetime.now().strftime("%Y-%m")
            seed_litigators = [
                ("admin@judiq.ai", "admin@judiq.ai", "admin", -1, 4, current_month, 1, now_iso, now_iso, "APPROVED", json.dumps(["s138", "sarfaesi", "criminal", "civil", "bank_recovery", "counsel_intel"]), 0.0, -1, "SYSTEM", now_iso),
                ("gandhiatharv565@gmail.com", "gandhiatharv565@gmail.com", "admin", -1, 2, current_month, 1, now_iso, now_iso, "APPROVED", json.dumps(["s138", "sarfaesi", "criminal", "civil", "bank_recovery", "counsel_intel"]), 0.0, -1, "SYSTEM", now_iso),
                ("USR_DEL_VERMA_88", "advocate.verma@delhibar.in", "law_firm", 50, 14, current_month, 1, now_iso, now_iso, "APPROVED", json.dumps(["s138", "sarfaesi", "criminal"]), 1500.0, 50, "admin@judiq.ai", now_iso),
                ("USR_MUM_TATA_CORP", "corp.legal@tatacapital.com", "enterprise", 100, 42, current_month, 1, now_iso, now_iso, "APPROVED", json.dumps(["s138", "sarfaesi", "criminal", "civil", "bank_recovery"]), 2500.0, 100, "admin@judiq.ai", now_iso),
                ("USR_BOM_MEHTA_HC", "counsel.mehta@bombayhc.in", "citizen", 25, 6, current_month, 1, now_iso, now_iso, "APPROVED", json.dumps(["s138", "civil"]), 1000.0, 25, "admin@judiq.ai", now_iso),
                ("USR_PUN_SINGH_SOL", "contact@singhpartners.in", "law_firm", 75, 19, current_month, 1, now_iso, now_iso, "APPROVED", json.dumps(["s138", "sarfaesi", "bank_recovery"]), 1500.0, 75, "admin@judiq.ai", now_iso),
                ("USR_BLR_KAPOOR_LAW", "verma.associates@lawfirm.in", "law_firm", 20, 0, current_month, 0, now_iso, now_iso, "PENDING_APPROVAL", json.dumps(["s138", "sarfaesi"]), 1000.0, 20, "", "")
            ]
            for lit in seed_litigators:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_quotas
                    (user_id, email, role, monthly_report_limit, reports_used_this_month, current_month_period, is_active, created_at, updated_at, plan_status, selected_modules, monthly_price_inr, requested_quota, approved_by, approved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, lit)
            conn.commit()
        except Exception as e:
            logger.warning(f"Seed litigators skipped or failed: {e}")

    @staticmethod
    def _seed_initial_bank_officers(cursor, conn):
        try:
            now_iso = datetime.now().isoformat()
            current_month = datetime.now().strftime("%Y-%m")
            seed_officers = [
                ("OFFICER_SARB_842", "Rajesh Nambiar", "State Bank of India", "SBI — Stressed Asset Recovery Branch (SARB Mumbai)", "sarb_manager", "rajesh.nambiar@sbi.co.in", 250, 18, current_month, 1, now_iso, now_iso),
                ("OFFICER_MUM_SARB_104", "Ananya Deshmukh", "State Bank of India", "SBI — Stressed Asset Recovery Cell (SARB Mumbai)", "bank_officer", "ananya.d@sbi.co.in", 150, 12, current_month, 1, now_iso, now_iso),
                ("OFFICER_DEL_LCR_419", "Vikram Rathore", "Punjab National Bank", "PNB — Large Corporate Recovery Division (Delhi)", "bank_officer", "vikram.rathore@pnb.co.in", 100, 8, current_month, 1, now_iso, now_iso),
                ("OFFICER_MUM_WLR_302", "Anand Kulkarni", "HDFC Bank", "HDFC Bank — Wholesale Recovery Dept (Mumbai)", "recovery_head", "anand.kulkarni@hdfcbank.com", 300, 24, current_month, 1, now_iso, now_iso),
                ("OFFICER_PUN_SAMB_512", "Priya Patel", "Bank of Baroda", "BOB — Stressed Assets Management Branch (SAMB Ahmedabad)", "bank_officer", "priya.patel@bankofbaroda.co.in", 100, 5, current_month, 1, now_iso, now_iso),
            ]
            for off in seed_officers:
                cursor.execute("""
                    INSERT OR IGNORE INTO bank_officers
                    (officer_id, name, bank_name, branch_name, role, email, monthly_audit_limit, audits_used_this_month, current_month_period, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, off)
            conn.commit()
        except Exception as e:
            logger.warning(f"Seed bank officers skipped or failed: {e}")

    @staticmethod
    def get_or_create_bank_officer(officer_id: str, name: str = "", bank_name: str = "", branch_name: str = "", email: str = "") -> dict:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            current_month = datetime.now().strftime("%Y-%m")
            now_iso = datetime.now().isoformat()

            cursor.execute(f"SELECT officer_id, name, bank_name, branch_name, role, email, monthly_audit_limit, audits_used_this_month, current_month_period, is_active FROM bank_officers WHERE officer_id = {p}", (officer_id,))
            row = cursor.fetchone()

            if not row:
                default_name = name or officer_id.replace("_", " ").title()
                default_bank = bank_name or "Institutional Bank Partner"
                default_branch = branch_name or "Stressed Asset Recovery Branch"
                default_email = email or f"{officer_id.lower()}@bankpartner.in"

                cursor.execute(f"""
                    INSERT INTO bank_officers
                    (officer_id, name, bank_name, branch_name, role, email, monthly_audit_limit, audits_used_this_month, current_month_period, is_active, created_at, updated_at)
                    VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """, (officer_id, default_name, default_bank, default_branch, "bank_officer", default_email, 100, 0, current_month, 1, now_iso, now_iso))
                conn.commit()

                return {
                    "officer_id": officer_id,
                    "name": default_name,
                    "bank_name": default_bank,
                    "branch_name": default_branch,
                    "role": "bank_officer",
                    "email": default_email,
                    "monthly_audit_limit": 100,
                    "audits_used_this_month": 0,
                    "current_month_period": current_month,
                    "is_active": True,
                    "remaining_audits": 100
                }

            off_id, o_name, o_bank, o_branch, o_role, o_email, limit_val, used_val, month_period, active_val = row
            if month_period != current_month:
                cursor.execute(f"UPDATE bank_officers SET audits_used_this_month = 0, current_month_period = {p}, updated_at = {p} WHERE officer_id = {p}", (current_month, now_iso, officer_id))
                conn.commit()
                used_val = 0

            rem = -1 if limit_val == -1 else max(0, limit_val - used_val)
            return {
                "officer_id": off_id,
                "name": o_name,
                "bank_name": o_bank,
                "branch_name": o_branch,
                "role": o_role,
                "email": o_email,
                "monthly_audit_limit": limit_val,
                "audits_used_this_month": used_val,
                "current_month_period": current_month,
                "is_active": bool(active_val),
                "remaining_audits": rem
            }
        except Exception as e:
            logger.error(f"Error in get_or_create_bank_officer: {e}")
            return {
                "officer_id": officer_id,
                "name": name or officer_id,
                "bank_name": bank_name or "Institutional Partner",
                "branch_name": branch_name or "SARB Recovery Branch",
                "role": "bank_officer",
                "email": email or "",
                "monthly_audit_limit": 100,
                "audits_used_this_month": 0,
                "current_month_period": datetime.now().strftime("%Y-%m"),
                "is_active": True,
                "remaining_audits": 100
            }
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_bank_officers() -> list:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            current_month = datetime.now().strftime("%Y-%m")
            cursor.execute("SELECT officer_id, name, bank_name, branch_name, role, email, monthly_audit_limit, audits_used_this_month, current_month_period, is_active, created_at, ifsc_code, department FROM bank_officers ORDER BY created_at DESC")
            rows = cursor.fetchall()
            officers = []
            for r in rows:
                off_id, name, bank, branch, role, email, limit_val, used_val, period, is_active, created, ifsc, dept = r
                if period != current_month:
                    used_val = 0
                rem = -1 if limit_val == -1 else max(0, limit_val - used_val)
                officers.append({
                    "officer_id": off_id,
                    "name": name,
                    "bank_name": bank,
                    "branch_name": branch,
                    "role": role,
                    "email": email or "",
                    "monthly_audit_limit": limit_val,
                    "audits_used_this_month": used_val,
                    "current_month_period": current_month,
                    "is_active": bool(is_active),
                    "remaining_audits": rem,
                    "created_at": created,
                    "ifsc_code": ifsc or "N/A",
                    "department": dept or "SARB / Recovery"
                })
            return officers
        except Exception as e:
            logger.error(f"Error getting all bank officers: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_bank_officer_allocation(officer_id: str, monthly_limit: int = None, is_active: bool = None, role: str = None, name: str = None, bank_name: str = None, branch_name: str = None, email: str = None) -> bool:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()

            updates = [f"updated_at = {p}"]
            params = [now_iso]

            if monthly_limit is not None:
                updates.append(f"monthly_audit_limit = {p}")
                params.append(int(monthly_limit))
            if is_active is not None:
                updates.append(f"is_active = {p}")
                params.append(1 if is_active else 0)
            if role is not None:
                updates.append(f"role = {p}")
                params.append(str(role))
            if name is not None and name.strip():
                updates.append(f"name = {p}")
                params.append(str(name).strip())
            if bank_name is not None and bank_name.strip():
                updates.append(f"bank_name = {p}")
                params.append(str(bank_name).strip())
            if branch_name is not None and branch_name.strip():
                updates.append(f"branch_name = {p}")
                params.append(str(branch_name).strip())
            if email is not None and email.strip():
                updates.append(f"email = {p}")
                params.append(str(email).strip())

            params.append(officer_id)
            query = f"UPDATE bank_officers SET {', '.join(updates)} WHERE officer_id = {p}"
            cursor.execute(query, tuple(params))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating bank officer: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def register_bank_officer(
        officer_id: str,
        name: str,
        bank_name: str,
        branch_name: str,
        email: str,
        password: str,
        ifsc_code: str = "",
        role: str = "bank_officer",
        department: str = "Stressed Asset Recovery Branch (SARB)",
        monthly_limit: int = 150
    ) -> dict:
        """
        Registers a new institutional bank officer / recovery unit account with hashed credentials.
        """
        import hashlib
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            current_month = datetime.now().strftime("%Y-%m")
            now_iso = datetime.now().isoformat()

            # Hash password with SHA-256 for secure constant-time verification
            pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest() if password else ""

            # Check if officer_id or email already exists
            cursor.execute(
                f"SELECT officer_id, email FROM bank_officers WHERE officer_id = {p} OR LOWER(email) = {p}",
                (officer_id.strip(), email.strip().lower())
            )
            existing = cursor.fetchone()
            if existing:
                # Update existing officer
                cursor.execute(f"""
                    UPDATE bank_officers 
                    SET name = {p}, bank_name = {p}, branch_name = {p}, email = {p}, 
                        password_hash = {p}, ifsc_code = {p}, department = {p}, role = {p},
                        updated_at = {p}, is_active = 1
                    WHERE officer_id = {p}
                """, (
                    name.strip(), bank_name.strip(), branch_name.strip(), email.strip(),
                    pwd_hash, ifsc_code.strip().upper(), department.strip(), role,
                    now_iso, existing[0]
                ))
                conn.commit()
                return DatabaseManager.get_or_create_bank_officer(existing[0])

            # Insert new record
            cursor.execute(f"""
                INSERT INTO bank_officers
                (officer_id, name, bank_name, branch_name, role, email, password_hash, ifsc_code, department, monthly_audit_limit, audits_used_this_month, current_month_period, is_active, created_at, updated_at)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """, (
                officer_id.strip(), name.strip(), bank_name.strip(), branch_name.strip(),
                role, email.strip(), pwd_hash, ifsc_code.strip().upper(), department.strip(),
                monthly_limit, 0, current_month, 1, now_iso, now_iso
            ))
            conn.commit()

            return {
                "officer_id": officer_id.strip(),
                "name": name.strip(),
                "bank_name": bank_name.strip(),
                "branch_name": branch_name.strip(),
                "ifsc_code": ifsc_code.strip().upper(),
                "department": department.strip(),
                "role": role,
                "email": email.strip(),
                "monthly_audit_limit": monthly_limit,
                "audits_used_this_month": 0,
                "current_month_period": current_month,
                "is_active": True,
                "remaining_audits": monthly_limit
            }
        except Exception as e:
            logger.error(f"Error registering bank officer: {e}")
            raise e
        finally:
            if conn:
                conn.close()

    @staticmethod
    def verify_bank_officer_credentials(identifier: str, password: str = "") -> Optional[dict]:
        """
        Verifies bank officer credentials by officer_id or email, validating password hash if set.
        """
        import hashlib
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            clean_id = identifier.strip()

            cursor.execute(
                f"SELECT officer_id, name, bank_name, branch_name, role, email, monthly_audit_limit, audits_used_this_month, current_month_period, is_active, password_hash, ifsc_code, department FROM bank_officers WHERE officer_id = {p} OR LOWER(email) = {p}",
                (clean_id, clean_id.lower())
            )
            row = cursor.fetchone()
            if not row:
                return None

            off_id, name, bank, branch, role, email, limit_val, used_val, period, is_active, pwd_hash, ifsc, dept = row
            if not is_active:
                return None

            # Verify password if a password_hash is stored and password provided
            if pwd_hash and password:
                cand_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                if cand_hash != pwd_hash:
                    return None

            current_month = datetime.now().strftime("%Y-%m")
            if period != current_month:
                used_val = 0

            rem = -1 if limit_val == -1 else max(0, limit_val - used_val)
            return {
                "officer_id": off_id,
                "name": name,
                "bank_name": bank,
                "branch_name": branch,
                "ifsc_code": ifsc or "",
                "department": dept or "Stressed Asset Recovery",
                "role": role,
                "email": email or "",
                "monthly_audit_limit": limit_val,
                "audits_used_this_month": used_val,
                "current_month_period": current_month,
                "is_active": bool(is_active),
                "remaining_audits": rem
            }
        except Exception as e:
            logger.error(f"Error verifying bank officer credentials: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def log_bank_audit(officer_id: str, bank_name: str, branch_name: str, case_type: str, borrower_name: str, loan_account_no: str, default_amount: float, viability_score: float, verdict: str, defect_count: int, details_json: dict = None) -> str:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()
            current_month = datetime.now().strftime("%Y-%m")
            import uuid
            audit_id = f"AUD_BANK_{uuid.uuid4().hex[:10].upper()}"

            cursor.execute(f"""
                INSERT INTO bank_recovery_audits
                (audit_id, officer_id, bank_name, branch_name, case_type, borrower_name, loan_account_no, default_amount, viability_score, verdict, defect_count, details_json, timestamp)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
            """, (audit_id, officer_id, bank_name, branch_name, case_type, borrower_name, loan_account_no, default_amount, viability_score, verdict, defect_count, json.dumps(details_json or {}), now_iso))

            # Increment audits_used_this_month for officer
            cursor.execute(f"""
                UPDATE bank_officers
                SET audits_used_this_month = audits_used_this_month + 1, updated_at = {p}
                WHERE officer_id = {p}
            """, (now_iso, officer_id))

            conn.commit()
            return audit_id
        except Exception as e:
            logger.error(f"Error logging bank audit: {e}")
            return ""
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_bank_audits(limit: int = 50) -> list:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"""
                SELECT audit_id, officer_id, bank_name, branch_name, case_type, borrower_name, loan_account_no, default_amount, viability_score, verdict, defect_count, timestamp
                FROM bank_recovery_audits
                ORDER BY timestamp DESC
                LIMIT {limit}
            """)
            rows = cursor.fetchall()
            audits = []
            for r in rows:
                a_id, off_id, b_name, br_name, c_type, b_borrower, acc_no, amount, score, verdict, defects, ts = r
                audits.append({
                    "audit_id": a_id,
                    "officer_id": off_id,
                    "bank_name": b_name,
                    "branch_name": br_name,
                    "case_type": c_type,
                    "borrower_name": b_borrower,
                    "loan_account_no": acc_no,
                    "default_amount": amount,
                    "viability_score": score,
                    "verdict": verdict,
                    "defect_count": defects,
                    "timestamp": ts
                })
            return audits
        except Exception as e:
            logger.error(f"Error fetching bank audits: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_bank_admin_stats() -> dict:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            current_month = datetime.now().strftime("%Y-%m")

            cursor.execute("SELECT COUNT(*) FROM bank_officers")
            total_officers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM bank_officers WHERE is_active = 1")
            active_officers = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT bank_name) FROM bank_officers")
            total_banks = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM bank_recovery_audits")
            total_audits = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(default_amount) FROM bank_recovery_audits")
            res_amt = cursor.fetchone()[0]
            total_recovery_volume = float(res_amt) if res_amt is not None else 0.0

            cursor.execute("SELECT SUM(audits_used_this_month) FROM bank_officers WHERE current_month_period = ?", (current_month,))
            res_aud = cursor.fetchone()[0]
            audits_this_month = int(res_aud) if res_aud is not None else 0

            return {
                "total_bank_officers": total_officers,
                "active_bank_officers": active_officers,
                "total_institutional_partners": max(1, total_banks),
                "total_audits_performed": total_audits,
                "audits_this_month": audits_this_month,
                "total_recovery_volume_evaluated": total_recovery_volume,
                "current_period": current_month
            }
        except Exception as e:
            logger.error(f"Error fetching bank admin stats: {e}")
            return {
                "total_bank_officers": 0,
                "active_bank_officers": 0,
                "total_institutional_partners": 0,
                "total_audits_performed": 0,
                "audits_this_month": 0,
                "total_recovery_volume_evaluated": 0.0,
                "current_period": datetime.now().strftime("%Y-%m")
            }
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_recent_audit_logs(limit: int = 50) -> list:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"""
                SELECT id, user_id, case_id, action, metadata, timestamp
                FROM audit_logs
                ORDER BY id DESC
                LIMIT {limit}
            """)
            logs = []
            for r in cursor.fetchall():
                try:
                    meta = json.loads(r[4]) if r[4] else {}
                except Exception:
                    meta = {}
                logs.append({
                    "id": r[0],
                    "user_id": r[1] or "ANON",
                    "case_id": r[2] or "SYS",
                    "action": r[3] or "UNKNOWN",
                    "metadata": meta,
                    "timestamp": r[5]
                })
            return logs
        except Exception as e:
            logger.error(f"Error fetching audit logs: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def bulk_add_user_quotas(bonus: int = 10) -> int:
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now_iso = datetime.now().isoformat()
            cursor.execute(f"""
                UPDATE user_quotas
                SET monthly_report_limit = CASE WHEN monthly_report_limit = -1 THEN -1 ELSE monthly_report_limit + {p} END,
                    updated_at = {p}
                WHERE is_active = 1
            """, (bonus, now_iso))
            affected = cursor.rowcount
            conn.commit()
            return affected
        except Exception as e:
            logger.error(f"Error bulk adding quotas: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    # ────────────────────────────────────────────────────────────────
    # CMS — cases_v2 CRUD
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_create_case(case_id, user_id, case_name, case_type='section_138',
                        priority='medium', description='', tags=None,
                        creditor_data=None, debtor_data=None, company_data=None,
                        financial_data=None, collateral_data=None, court_data=None,
                        access_level='private', org_id=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO cases_v2
                (case_id, user_id, org_id, case_name, case_type, case_status, priority,
                 tags, description, creditor_data, debtor_data, company_data,
                 financial_data, collateral_data, court_data, access_level, created_at, updated_at)
                VALUES ({p},{p},{p},{p},{p},'draft',{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (
                case_id, user_id, org_id, case_name, case_type, priority,
                json.dumps(tags or []), description,
                json.dumps(creditor_data or {}), json.dumps(debtor_data or {}),
                json.dumps(company_data or {}), json.dumps(financial_data or {}),
                json.dumps(collateral_data or {}), json.dumps(court_data or {}),
                access_level, now, now
            ))
            conn.commit()
            return {"success": True, "case_id": case_id, "created_at": now}
        except Exception as e:
            logger.error(f"CMS create case failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_list_cases(user_id, status=None, case_type=None, priority=None,
                       search=None, page=1, limit=20):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            conditions = [f"(user_id = {p} OR shared_with LIKE {p})"]
            params = [user_id, f"%{user_id}%"]
            if status and status != 'all':
                conditions.append(f"case_status = {p}")
                params.append(status)
            if case_type and case_type != 'all':
                conditions.append(f"case_type = {p}")
                params.append(case_type)
            if priority and priority != 'all':
                conditions.append(f"priority = {p}")
                params.append(priority)
            if search:
                conditions.append(f"(case_name LIKE {p} OR case_id LIKE {p} OR description LIKE {p})")
                s = f"%{search}%"
                params.extend([s, s, s])
            where = " AND ".join(conditions)
            offset = (page - 1) * limit
            cursor.execute(f"""
                SELECT case_id, case_name, case_type, case_status, priority,
                       compliance_score, verdict, tags, created_at, updated_at
                FROM cases_v2
                WHERE {where} AND case_status != 'archived'
                ORDER BY updated_at DESC
                LIMIT {limit} OFFSET {offset}
            """, tuple(params))
            rows = cursor.fetchall()
            cases = []
            for r in rows:
                cases.append({
                    "case_id": r[0], "case_name": r[1], "case_type": r[2],
                    "case_status": r[3], "priority": r[4],
                    "compliance_score": r[5], "verdict": r[6],
                    "tags": json.loads(r[7]) if r[7] else [],
                    "created_at": r[8], "updated_at": r[9]
                })
            cursor.execute(f"SELECT COUNT(*) FROM cases_v2 WHERE {where} AND case_status != 'archived'", tuple(params))
            total = cursor.fetchone()[0]
            return {"cases": cases, "total": total, "page": page, "limit": limit}
        except Exception as e:
            logger.error(f"CMS list cases failed: {e}")
            return {"cases": [], "total": 0, "page": 1, "limit": limit}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_get_case(case_id, user_id=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"SELECT * FROM cases_v2 WHERE case_id = {p}", (case_id,))
            r = cursor.fetchone()
            if not r:
                return None
            cols = [desc[0] for desc in cursor.description]
            case = dict(zip(cols, r))
            for k in ['tags', 'creditor_data', 'debtor_data', 'company_data',
                       'financial_data', 'collateral_data', 'court_data',
                       'analysis_result', 'shared_with']:
                if case.get(k):
                    try:
                        case[k] = json.loads(case[k])
                    except Exception:
                        pass
            cursor.execute(f"""
                SELECT cl.client_id, cl.role, c.name, c.client_type, c.email
                FROM case_client_links cl
                JOIN clients c ON cl.client_id = c.client_id
                WHERE cl.case_id = {p}
            """, (case_id,))
            case["linked_clients"] = [
                {"client_id": cr[0], "role": cr[1], "name": cr[2],
                 "client_type": cr[3], "email": cr[4]}
                for cr in cursor.fetchall()
            ]
            cursor.execute(f"SELECT COUNT(*) FROM case_documents WHERE case_id = {p}", (case_id,))
            case["document_count"] = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM case_deadlines WHERE case_id = {p} AND status = 'pending'", (case_id,))
            case["pending_deadlines"] = cursor.fetchone()[0]
            return case
        except Exception as e:
            logger.error(f"CMS get case failed: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_update_case(case_id, updates: dict):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            json_fields = ['tags', 'creditor_data', 'debtor_data', 'company_data',
                           'financial_data', 'collateral_data', 'court_data',
                           'analysis_result', 'shared_with']
            set_parts = []
            params = []
            for k, v in updates.items():
                if k in ('case_id', 'id', 'created_at'):
                    continue
                if k in json_fields and isinstance(v, (dict, list)):
                    v = json.dumps(v)
                set_parts.append(f"{k} = {p}")
                params.append(v)
            set_parts.append(f"updated_at = {p}")
            params.append(now)
            params.append(case_id)
            cursor.execute(f"UPDATE cases_v2 SET {', '.join(set_parts)} WHERE case_id = {p}", tuple(params))
            conn.commit()
            return {"success": True, "case_id": case_id, "updated_at": now}
        except Exception as e:
            logger.error(f"CMS update case failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_update_case_status(case_id, new_status):
        now = datetime.now().isoformat()
        updates = {"case_status": new_status}
        if new_status == 'archived':
            updates["archived_at"] = now
        return DatabaseManager.cms_update_case(case_id, updates)

    # ────────────────────────────────────────────────────────────────
    # CMS — clients CRUD
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_create_client(client_id, user_id, name, client_type, role_type='creditor',
                          legal_name=None, email=None, phone=None, mobile=None,
                          company_info=None, address_data=None, tax_info=None,
                          banking_info=None, comm_prefs=None, notes=None, org_id=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO clients
                (client_id, org_id, client_type, role_type, name, legal_name, email,
                 phone, mobile, company_info, address_data, tax_info, banking_info,
                 comm_prefs, notes, created_at, updated_at, created_by)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (
                client_id, org_id, client_type, role_type, name, legal_name, email,
                phone, mobile,
                json.dumps(company_info or {}), json.dumps(address_data or {}),
                json.dumps(tax_info or {}), json.dumps(banking_info or {}),
                json.dumps(comm_prefs or {}), notes, now, now, user_id
            ))
            conn.commit()
            return {"success": True, "client_id": client_id, "created_at": now}
        except Exception as e:
            logger.error(f"CMS create client failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_list_clients(user_id=None, search=None, client_type=None, page=1, limit=20):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            conditions = []
            params = []
            if user_id:
                conditions.append(f"created_by = {p}")
                params.append(user_id)
            if client_type and client_type != 'all':
                conditions.append(f"client_type = {p}")
                params.append(client_type)
            if search:
                conditions.append(f"(name LIKE {p} OR email LIKE {p} OR client_id LIKE {p})")
                s = f"%{search}%"
                params.extend([s, s, s])
            where = " AND ".join(conditions) if conditions else "1=1"
            offset = (page - 1) * limit
            cursor.execute(f"""
                SELECT client_id, name, client_type, role_type, email, phone,
                       total_cases, success_rate, created_at
                FROM clients WHERE {where}
                ORDER BY updated_at DESC LIMIT {limit} OFFSET {offset}
            """, tuple(params))
            clients = [
                {"client_id": r[0], "name": r[1], "client_type": r[2],
                 "role_type": r[3], "email": r[4], "phone": r[5],
                 "total_cases": r[6], "success_rate": r[7], "created_at": r[8]}
                for r in cursor.fetchall()
            ]
            cursor.execute(f"SELECT COUNT(*) FROM clients WHERE {where}", tuple(params))
            total = cursor.fetchone()[0]
            return {"clients": clients, "total": total, "page": page}
        except Exception as e:
            logger.error(f"CMS list clients failed: {e}")
            return {"clients": [], "total": 0, "page": 1}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_get_client(client_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"SELECT * FROM clients WHERE client_id = {p}", (client_id,))
            r = cursor.fetchone()
            if not r:
                return None
            cols = [desc[0] for desc in cursor.description]
            client = dict(zip(cols, r))
            for k in ['company_info', 'address_data', 'tax_info', 'banking_info', 'comm_prefs']:
                if client.get(k):
                    try:
                        client[k] = json.loads(client[k])
                    except Exception:
                        pass
            cursor.execute(f"""
                SELECT cl.case_id, cl.role, c.case_name, c.case_type, c.case_status, c.compliance_score
                FROM case_client_links cl
                JOIN cases_v2 c ON cl.case_id = c.case_id
                WHERE cl.client_id = {p}
            """, (client_id,))
            client["linked_cases"] = [
                {"case_id": cr[0], "role": cr[1], "case_name": cr[2],
                 "case_type": cr[3], "case_status": cr[4], "compliance_score": cr[5]}
                for cr in cursor.fetchall()
            ]
            return client
        except Exception as e:
            logger.error(f"CMS get client failed: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_update_client(client_id, updates: dict):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            json_fields = ['company_info', 'address_data', 'tax_info', 'banking_info', 'comm_prefs']
            set_parts = []
            params = []
            for k, v in updates.items():
                if k in ('client_id', 'id', 'created_at'):
                    continue
                if k in json_fields and isinstance(v, (dict, list)):
                    v = json.dumps(v)
                set_parts.append(f"{k} = {p}")
                params.append(v)
            set_parts.append(f"updated_at = {p}")
            params.append(now)
            params.append(client_id)
            cursor.execute(f"UPDATE clients SET {', '.join(set_parts)} WHERE client_id = {p}", tuple(params))
            conn.commit()
            return {"success": True, "client_id": client_id}
        except Exception as e:
            logger.error(f"CMS update client failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    # ────────────────────────────────────────────────────────────────
    # CMS — case_client_links
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_link_client(case_id, client_id, role, linked_by=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO case_client_links (case_id, client_id, role, linked_at, linked_by)
                VALUES ({p},{p},{p},{p},{p})
            """, (case_id, client_id, role, now, linked_by))
            cursor.execute(f"""
                UPDATE clients SET total_cases = (
                    SELECT COUNT(DISTINCT case_id) FROM case_client_links WHERE client_id = {p}
                ) WHERE client_id = {p}
            """, (client_id, client_id))
            conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"CMS link client failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_unlink_client(case_id, client_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"DELETE FROM case_client_links WHERE case_id = {p} AND client_id = {p}", (case_id, client_id))
            cursor.execute(f"""
                UPDATE clients SET total_cases = (
                    SELECT COUNT(DISTINCT case_id) FROM case_client_links WHERE client_id = {p}
                ) WHERE client_id = {p}
            """, (client_id, client_id))
            conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"CMS unlink client failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    # ────────────────────────────────────────────────────────────────
    # CMS — case_documents CRUD
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_save_document(document_id, case_id, uploader_id, file_name, file_path,
                          file_size=0, mime_type='', doc_type='other',
                          encryption_hash='', ocr_text='', extracted_data=None,
                          tags=None, notes=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO case_documents
                (document_id, case_id, uploader_id, file_name, file_path, file_size,
                 mime_type, doc_type, encryption_hash, ocr_text, extracted_data,
                 tags, notes, created_at, updated_at)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (
                document_id, case_id, uploader_id, file_name, file_path, file_size,
                mime_type, doc_type, encryption_hash, ocr_text,
                json.dumps(extracted_data or {}), json.dumps(tags or []),
                notes, now, now
            ))
            conn.commit()
            return {"success": True, "document_id": document_id, "created_at": now}
        except Exception as e:
            logger.error(f"CMS save document failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_list_documents(case_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"""
                SELECT document_id, file_name, doc_type, file_size, mime_type,
                       validation_status, s65b_status, created_at
                FROM case_documents WHERE case_id = {p}
                ORDER BY created_at DESC
            """, (case_id,))
            return [
                {"document_id": r[0], "file_name": r[1], "doc_type": r[2],
                 "file_size": r[3], "mime_type": r[4],
                 "validation_status": r[5], "s65b_status": r[6], "created_at": r[7]}
                for r in cursor.fetchall()
            ]
        except Exception as e:
            logger.error(f"CMS list documents failed: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_get_document(document_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"SELECT * FROM case_documents WHERE document_id = {p}", (document_id,))
            r = cursor.fetchone()
            if not r:
                return None
            cols = [desc[0] for desc in cursor.description]
            doc = dict(zip(cols, r))
            for k in ['extracted_data', 'tags', 's65b_cert_data']:
                if doc.get(k):
                    try:
                        doc[k] = json.loads(doc[k])
                    except Exception:
                        pass
            return doc
        except Exception as e:
            logger.error(f"CMS get document failed: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_update_document(document_id, updates: dict):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            set_parts = []
            params = []
            json_fields = ['extracted_data', 'tags', 's65b_cert_data']
            for k, v in updates.items():
                if k in ('document_id', 'id'):
                    continue
                if k in json_fields and isinstance(v, (dict, list)):
                    v = json.dumps(v)
                set_parts.append(f"{k} = {p}")
                params.append(v)
            set_parts.append(f"updated_at = {p}")
            params.append(now)
            params.append(document_id)
            cursor.execute(f"UPDATE case_documents SET {', '.join(set_parts)} WHERE document_id = {p}", tuple(params))
            conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"CMS update document failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_delete_document(document_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"DELETE FROM case_documents WHERE document_id = {p}", (document_id,))
            conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"CMS delete document failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    # ────────────────────────────────────────────────────────────────
    # CMS — draft_workflows CRUD
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_create_draft_workflow(workflow_id, case_id, draft_type, draft_content,
                                  created_by=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO draft_workflows
                (workflow_id, case_id, draft_type, draft_content, status, created_by, created_at, updated_at)
                VALUES ({p},{p},{p},{p},'DRAFT',{p},{p},{p})
            """, (workflow_id, case_id, draft_type, draft_content, created_by, now, now))
            conn.commit()
            return {"success": True, "workflow_id": workflow_id, "status": "DRAFT", "created_at": now}
        except Exception as e:
            logger.error(f"CMS create draft workflow failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_list_drafts(case_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"""
                SELECT workflow_id, draft_type, current_version, status, created_by,
                       assigned_reviewer, approved_by, created_at, updated_at
                FROM draft_workflows WHERE case_id = {p}
                ORDER BY updated_at DESC
            """, (case_id,))
            return [
                {"workflow_id": r[0], "draft_type": r[1], "current_version": r[2],
                 "status": r[3], "created_by": r[4], "assigned_reviewer": r[5],
                 "approved_by": r[6], "created_at": r[7], "updated_at": r[8]}
                for r in cursor.fetchall()
            ]
        except Exception as e:
            logger.error(f"CMS list drafts failed: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_update_draft_workflow(workflow_id, updates: dict):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            set_parts = []
            params = []
            for k, v in updates.items():
                if k in ('workflow_id', 'id'):
                    continue
                if k == 'reviewer_comments' and isinstance(v, list):
                    v = json.dumps(v)
                set_parts.append(f"{k} = {p}")
                params.append(v)
            set_parts.append(f"updated_at = {p}")
            params.append(now)
            params.append(workflow_id)
            cursor.execute(f"UPDATE draft_workflows SET {', '.join(set_parts)} WHERE workflow_id = {p}", tuple(params))
            conn.commit()
            return {"success": True, "workflow_id": workflow_id}
        except Exception as e:
            logger.error(f"CMS update draft workflow failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_get_draft_workflow(workflow_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"SELECT * FROM draft_workflows WHERE workflow_id = {p}", (workflow_id,))
            r = cursor.fetchone()
            if not r:
                return None
            cols = [desc[0] for desc in cursor.description]
            wf = dict(zip(cols, r))
            if wf.get('reviewer_comments'):
                try:
                    wf['reviewer_comments'] = json.loads(wf['reviewer_comments'])
                except Exception:
                    pass
            return wf
        except Exception as e:
            logger.error(f"CMS get draft workflow failed: {e}")
            return None
        finally:
            if conn:
                conn.close()

    # ────────────────────────────────────────────────────────────────
    # CMS — case_deadlines CRUD
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_save_deadline(deadline_id, case_id, title, due_date, statutory_basis='',
                          urgency_level='SAFE', mandatory_action='', consequence=''):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            if DatabaseManager._active_dialect == "postgres":
                cursor.execute(f"""
                    INSERT INTO case_deadlines
                    (deadline_id, case_id, title, due_date, statutory_basis,
                     urgency_level, mandatory_action, consequence, created_at)
                    VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})
                    ON CONFLICT (deadline_id) DO UPDATE SET
                    urgency_level = EXCLUDED.urgency_level,
                    mandatory_action = EXCLUDED.mandatory_action,
                    consequence = EXCLUDED.consequence
                """, (deadline_id, case_id, title, due_date, statutory_basis,
                      urgency_level, mandatory_action, consequence, now))
            else:
                cursor.execute(f"""
                    INSERT OR REPLACE INTO case_deadlines
                    (deadline_id, case_id, title, due_date, statutory_basis,
                     urgency_level, mandatory_action, consequence, created_at)
                    VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})
                """, (deadline_id, case_id, title, due_date, statutory_basis,
                      urgency_level, mandatory_action, consequence, now))
            conn.commit()
            return {"success": True, "deadline_id": deadline_id}
        except Exception as e:
            logger.error(f"CMS save deadline failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_list_deadlines(case_id=None, user_id=None, status='pending'):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            if case_id:
                cursor.execute(f"""
                    SELECT deadline_id, case_id, title, due_date, status,
                           urgency_level, mandatory_action, consequence, completed_at, created_at
                    FROM case_deadlines WHERE case_id = {p}
                    ORDER BY due_date ASC
                """, (case_id,))
            elif user_id:
                cursor.execute(f"""
                    SELECT d.deadline_id, d.case_id, d.title, d.due_date, d.status,
                           d.urgency_level, d.mandatory_action, d.consequence, d.completed_at, d.created_at
                    FROM case_deadlines d
                    JOIN cases_v2 c ON d.case_id = c.case_id
                    WHERE c.user_id = {p} AND d.status = {p}
                    ORDER BY d.due_date ASC
                    LIMIT 50
                """, (user_id, status))
            else:
                return []
            return [
                {"deadline_id": r[0], "case_id": r[1], "title": r[2],
                 "due_date": r[3], "status": r[4], "urgency_level": r[5],
                 "mandatory_action": r[6], "consequence": r[7],
                 "completed_at": r[8], "created_at": r[9]}
                for r in cursor.fetchall()
            ]
        except Exception as e:
            logger.error(f"CMS list deadlines failed: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_complete_deadline(deadline_id):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"UPDATE case_deadlines SET status = 'completed', completed_at = {p} WHERE deadline_id = {p}",
                           (now, deadline_id))
            conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"CMS complete deadline failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    # ────────────────────────────────────────────────────────────────
    # CMS — team_members CRUD
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_add_team_member(member_id, org_id, user_id, name, email,
                            phone=None, role='officer', department=None,
                            supervisor_id=None, permissions=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO team_members
                (member_id, org_id, user_id, name, email, phone, role, department,
                 supervisor_id, permissions, created_at, updated_at)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (member_id, org_id, user_id, name, email, phone, role, department,
                  supervisor_id, json.dumps(permissions or {}), now, now))
            conn.commit()
            return {"success": True, "member_id": member_id}
        except Exception as e:
            logger.error(f"CMS add team member failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_list_team_members(org_id=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            if org_id:
                cursor.execute(f"""
                    SELECT member_id, user_id, name, email, phone, role,
                           department, is_active, created_at
                    FROM team_members WHERE org_id = {p}
                    ORDER BY name ASC
                """, (org_id,))
            else:
                cursor.execute("""
                    SELECT member_id, user_id, name, email, phone, role,
                           department, is_active, created_at
                    FROM team_members ORDER BY name ASC
                """)
            return [
                {"member_id": r[0], "user_id": r[1], "name": r[2], "email": r[3],
                 "phone": r[4], "role": r[5], "department": r[6],
                 "is_active": bool(r[7]), "created_at": r[8]}
                for r in cursor.fetchall()
            ]
        except Exception as e:
            logger.error(f"CMS list team members failed: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_update_team_member(member_id, updates: dict):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            set_parts = []
            params = []
            for k, v in updates.items():
                if k in ('member_id', 'id'):
                    continue
                if k == 'permissions' and isinstance(v, dict):
                    v = json.dumps(v)
                set_parts.append(f"{k} = {p}")
                params.append(v)
            set_parts.append(f"updated_at = {p}")
            params.append(now)
            params.append(member_id)
            cursor.execute(f"UPDATE team_members SET {', '.join(set_parts)} WHERE member_id = {p}", tuple(params))
            conn.commit()
            return {"success": True}
        except Exception as e:
            logger.error(f"CMS update team member failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if conn:
                conn.close()

    # ────────────────────────────────────────────────────────────────
    # CMS — audit_log_v2
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_log_audit(log_id, user_id, action, entity_type=None, entity_id=None,
                      case_id=None, before_state=None, after_state=None,
                      ip_address=None, user_agent=None, note=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            now = datetime.now().isoformat()
            cursor.execute(f"""
                INSERT INTO audit_log_v2
                (log_id, user_id, case_id, action, entity_type, entity_id,
                 before_state, after_state, ip_address, user_agent, note, timestamp)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (log_id, user_id, case_id, action, entity_type, entity_id,
                  json.dumps(before_state) if before_state else None,
                  json.dumps(after_state) if after_state else None,
                  ip_address, user_agent, note, now))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"CMS audit log failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_get_audit_trail(case_id=None, user_id=None, limit=100):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            if case_id:
                cursor.execute(f"""
                    SELECT log_id, user_id, case_id, action, entity_type, entity_id,
                           note, timestamp
                    FROM audit_log_v2 WHERE case_id = {p}
                    ORDER BY timestamp DESC LIMIT {limit}
                """, (case_id,))
            elif user_id:
                cursor.execute(f"""
                    SELECT log_id, user_id, case_id, action, entity_type, entity_id,
                           note, timestamp
                    FROM audit_log_v2 WHERE user_id = {p}
                    ORDER BY timestamp DESC LIMIT {limit}
                """, (user_id,))
            else:
                cursor.execute(f"""
                    SELECT log_id, user_id, case_id, action, entity_type, entity_id,
                           note, timestamp
                    FROM audit_log_v2 ORDER BY timestamp DESC LIMIT {limit}
                """)
            return [
                {"log_id": r[0], "user_id": r[1], "case_id": r[2], "action": r[3],
                 "entity_type": r[4], "entity_id": r[5], "note": r[6], "timestamp": r[7]}
                for r in cursor.fetchall()
            ]
        except Exception as e:
            logger.error(f"CMS get audit trail failed: {e}")
            return []
        finally:
            if conn:
                conn.close()

    # ────────────────────────────────────────────────────────────────
    # CMS — Analytics Aggregations
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def cms_get_portfolio_stats(user_id=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            base_cond = f"user_id = {p}" if user_id else "1=1"
            params = (user_id,) if user_id else ()
            cursor.execute(f"SELECT COUNT(*) FROM cases_v2 WHERE {base_cond}", params)
            total = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM cases_v2 WHERE {base_cond} AND case_status = 'ongoing'", params)
            ongoing = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM cases_v2 WHERE {base_cond} AND case_status = 'resolved'", params)
            resolved = cursor.fetchone()[0]
            cursor.execute(f"SELECT AVG(compliance_score) FROM cases_v2 WHERE {base_cond} AND compliance_score IS NOT NULL", params)
            avg_row = cursor.fetchone()
            avg_score = round(avg_row[0], 1) if avg_row and avg_row[0] else 0.0
            return {
                "total_cases": total, "ongoing_cases": ongoing,
                "resolved_cases": resolved, "avg_compliance_score": avg_score,
                "success_rate": round((resolved / total * 100), 1) if total > 0 else 0.0
            }
        except Exception as e:
            logger.error(f"CMS portfolio stats failed: {e}")
            return {"total_cases": 0, "ongoing_cases": 0, "resolved_cases": 0,
                    "avg_compliance_score": 0.0, "success_rate": 0.0}
        finally:
            if conn:
                conn.close()

    @staticmethod
    def cms_get_case_type_breakdown(user_id=None):
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            if user_id:
                cursor.execute(f"SELECT case_type, COUNT(*) FROM cases_v2 WHERE user_id = {p} GROUP BY case_type", (user_id,))
            else:
                cursor.execute("SELECT case_type, COUNT(*) FROM cases_v2 GROUP BY case_type")
            return {r[0]: r[1] for r in cursor.fetchall()}
        except Exception as e:
            logger.error(f"CMS case type breakdown failed: {e}")
            return {}
        finally:
            if conn:
                conn.close()
