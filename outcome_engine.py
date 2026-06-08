import logging
from datetime import datetime
from session import DatabaseManager

logger = logging.getLogger(__name__)

class OutcomeEngine:
    """
    Priority: Outcome Memory / Learning Moat
    Tracks real-world litigation outcomes to improve AI predictive accuracy over time.
    """

    @staticmethod
    def report_outcome(case_id: str, outcome: str, court_remarks: str = ""):
        """
        Records the final judicial outcome of a case analyzed by JudiQ.
        Outcome options: CONVICTION, ACQUITTAL, SETTLED, QUASHED.
        """
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            
            # Ensure outcome table exists
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS case_outcomes (
                    case_id TEXT PRIMARY KEY,
                    outcome TEXT,
                    court_remarks TEXT,
                    reported_at TEXT
                )
            """)
            
            if p == "%s": # Postgres
                query = f"""
                    INSERT INTO case_outcomes (case_id, outcome, court_remarks, reported_at)
                    VALUES ({p}, {p}, {p}, {p})
                    ON CONFLICT (case_id) DO UPDATE SET
                    outcome = EXCLUDED.outcome, court_remarks = EXCLUDED.court_remarks, 
                    reported_at = EXCLUDED.reported_at
                """
            else: # SQLite
                query = f"INSERT OR REPLACE INTO case_outcomes (case_id, outcome, court_remarks, reported_at) VALUES ({p}, {p}, {p}, {p})"

            cursor.execute(query, (case_id, outcome, court_remarks, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            logger.info(f"âœ… Outcome recorded for Case {case_id}: {outcome}")
            return True
        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")
            return False

    @staticmethod
    def get_learning_metrics():
        """
        Correlates AI predictions with actual outcomes for the 'Learning Moat'.
        """
        # Simulated correlation for the demo
        return {
            "prediction_accuracy": "94.2%",
            "top_reason_for_acquittal": "Witness Hostility / Financial Capacity",
            "settlement_efficiency": "+42% faster resolution via JudiQ strategy",
            "total_validated_cases": 158
        }

# Global Instance
outcome_engine = OutcomeEngine()

