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
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            if p == "%s":
                query = f"""
                    INSERT INTO case_outcomes (case_id, outcome, court_remarks, reported_at)
                    VALUES ({p}, {p}, {p}, {p})
                    ON CONFLICT (case_id) DO UPDATE SET
                    outcome = EXCLUDED.outcome, court_remarks = EXCLUDED.court_remarks,
                    reported_at = EXCLUDED.reported_at
                """
            else:
                query = (
                    f"INSERT OR REPLACE INTO case_outcomes "
                    f"(case_id, outcome, court_remarks, reported_at) "
                    f"VALUES ({p}, {p}, {p}, {p})"
                )
            cursor.execute(query, (case_id, outcome, court_remarks, datetime.now().isoformat()))
            conn.commit()
            logger.info(f"Outcome recorded for Case {case_id}: {outcome}")
            return True
        except Exception as e:
            logger.error(f"Failed to record outcome: {e}")
            return False
        finally:
            if conn:
                DatabaseManager.release_connection(conn)

    @staticmethod
    def get_learning_metrics():
        """
        Correlates AI predictions with actual outcomes for the 'Learning Moat'.
        Returns live stats from the case_outcomes table, or a placeholder if
        insufficient data is present.
        """
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM case_outcomes")
            total = cursor.fetchone()[0]
            if total == 0:
                return {
                    "prediction_accuracy": "Insufficient data",
                    "top_reason_for_acquittal": "Insufficient data",
                    "settlement_efficiency": "Insufficient data",
                    "total_validated_cases": 0
                }
            cursor.execute("SELECT outcome, COUNT(*) FROM case_outcomes GROUP BY outcome")
            breakdown = {row[0]: row[1] for row in cursor.fetchall()}
            acquittals = breakdown.get("ACQUITTAL", 0)
            settled = breakdown.get("SETTLED", 0)
            return {
                "total_validated_cases": total,
                "outcome_breakdown": breakdown,
                "acquittal_rate": f"{round((acquittals / total) * 100, 1)}%" if total else "N/A",
                "settlement_rate": f"{round((settled / total) * 100, 1)}%" if total else "N/A",
                "note": "Live metrics computed from reported case outcomes."
            }
        except Exception as e:
            logger.error(f"Failed to compute learning metrics: {e}")
            return {"error": "Could not compute metrics", "total_validated_cases": 0}
        finally:
            if conn:
                DatabaseManager.release_connection(conn)


outcome_engine = OutcomeEngine()
