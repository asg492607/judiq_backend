import json
import os
import sys
import logging
from typing import Dict, List, Any

# Ensure backend path is available for standalone execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engine_core import JudiQEngine

logger = logging.getLogger(__name__)

class PractitionerValidationFramework:
    """
    Blind Practitioner Validation v1 Framework:
    Executes unseen anonymized cases blindly against practitioner ground truth assessments.
    Preserves disagreements for evaluation telemetry instead of forcing code overrides.
    """

    @classmethod
    def run_blind_validation(cls, template_path: str = None) -> Dict[str, Any]:
        if template_path is None:
            template_path = os.path.join(os.path.dirname(__file__), "blind_validation_template.json")

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Validation template not found at {template_path}")

        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        matters = data.get("matters", [])
        total_matters = len(matters)
        if total_matters == 0:
            return {"status": "NO_MATTERS_PROVIDED", "summary": "Template contains 0 matters."}

        stage_matches = 0
        limitation_matches = 0
        next_action_matches = 0
        false_alerts = 0
        disagreements = []

        for m in matters:
            mid = m["matter_id"]
            inp = m["case_input"]
            gt = m["practitioner_ground_truth"]

            res = JudiQEngine.analyze_case(inp)
            proc_graph = res.get("procedural_graph", {})
            actual_stage = proc_graph.get("current_stage", "")
            next_actions = [a.get("action", "") for a in res.get("next_best_actions", [])]
            lim_status = res.get("detailed_assessment", {}).get("limitation_status") or res.get("limitation", {}).get("status", "")
            is_fatal = bool(res.get("fatal_defect") or res.get("failure_point"))

            # Metric 1: Stage Accuracy
            if gt.get("expected_stage") and gt["expected_stage"].lower() in actual_stage.lower():
                stage_matches += 1
            else:
                disagreements.append({
                    "matter_id": mid,
                    "metric": "Stage Identification",
                    "practitioner_ground_truth": gt.get("expected_stage"),
                    "judiq_output": actual_stage
                })

            # Metric 2: Limitation Accuracy
            if gt.get("expected_limitation_status") and gt["expected_limitation_status"].lower() in str(lim_status).lower():
                limitation_matches += 1
            else:
                disagreements.append({
                    "matter_id": mid,
                    "metric": "Limitation Calculation",
                    "practitioner_ground_truth": gt.get("expected_limitation_status"),
                    "judiq_output": lim_status
                })

            # Metric 3: Next Action Agreement
            combined_act = " ".join(next_actions)
            if gt.get("expected_next_action") and any(w.lower() in combined_act.lower() for w in gt["expected_next_action"].split()):
                next_action_matches += 1

            # Metric 4: False Critical Alerts (False Positives)
            if is_fatal and not gt.get("critical_alert_justified", False):
                false_alerts += 1
                disagreements.append({
                    "matter_id": mid,
                    "metric": "False Critical Alert",
                    "practitioner_ground_truth": "No Fatal Defect",
                    "judiq_output": res.get("fatal_defect")
                })

        return {
            "validation_title": data.get("validation_suite"),
            "total_matters_evaluated": total_matters,
            "stage_identification_accuracy_pct": round((stage_matches / total_matters) * 100, 2),
            "limitation_accuracy_pct": round((limitation_matches / total_matters) * 100, 2),
            "next_action_agreement_pct": round((next_action_matches / total_matters) * 100, 2),
            "false_critical_alert_count": false_alerts,
            "false_critical_alert_rate_pct": round((false_alerts / total_matters) * 100, 2),
            "disagreement_telemetry": disagreements
        }

if __name__ == "__main__":
    report = PractitionerValidationFramework.run_blind_validation()
    print(json.dumps(report, indent=2))
