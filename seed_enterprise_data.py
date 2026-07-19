import os
import sqlite3
import uuid
from datetime import datetime
from auth.utils import get_password_hash
from session import DatabaseManager

def seed():
    conn = DatabaseManager.get_connection()
    cursor = conn.cursor()
    
    # Check if we already seeded to avoid duplicates
    cursor.execute("SELECT id FROM organizations WHERE name = 'HDFC Bank'")
    if cursor.fetchone():
        print("Data already seeded.")
        return

    # Seed Enterprise Org
    print("Seeding Enterprise Organization...")
    cursor.execute(
        "INSERT INTO organizations (name, type, subtype, created_at) VALUES (?, ?, ?, ?)",
        ('HDFC Bank', 'FINANCIAL_INSTITUTION', 'BANK', datetime.utcnow().isoformat())
    )
    org_id = cursor.lastrowid
    
    # Seed CEO User
    user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash("password123")
    cursor.execute(
        "INSERT INTO users (id, email, password_hash, first_name, last_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, 'ceo@hdfc.test', hashed_pwd, 'Sashidhar', 'Jagdishan', datetime.utcnow().isoformat())
    )
    cursor.execute(
        "INSERT INTO user_workspaces (user_id, org_id, role) VALUES (?, ?, ?)",
        (user_id, org_id, "SUPER_ADMIN")
    )

    # Seed Cases (mock active cases for money at risk calculation)
    # the /portfolio-summary API aggregates by org_id and sums cheque_amount.
    print("Seeding 148 mock active cases for portfolio intelligence...")
    for i in range(148):
        case_id = f"HDFC-TEST-{i}"
        cheque_amount = 1250000.0 + (i * 10000)
        cursor.execute(
            """INSERT INTO saved_cases (
                case_id, user_id, organization_id, litigation_type, workflow_stage, cheque_amount, score, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (case_id, user_id, org_id, 'CHEQUE_BOUNCE', 'REGISTERED', cheque_amount, 75.0, datetime.utcnow().isoformat())
        )
        
    conn.commit()
    conn.close()
    print("Seeding complete. CEO email: ceo@hdfc.test | password: password123")

if __name__ == "__main__":
    seed()
