import logging
from typing import Dict, List, Any
from engine_core import JudiQEngine

logger = logging.getLogger(__name__)

class EngineDiagnostics:
    """
    REGRESSION & ADVERSARIAL TESTING SUITE
    Used to ensure logic consistency and prevent hallucination/regression.
    """
    
    TEST_CASES = [
        {
            "name": "PERFECT_COMPLAINANT_CASE",
            "data": {
                "cheque_present": True,
                "dishonour_memo": True,
                "notice_sent": True,
                "debt_proven": True,
                "amount": 50000,
                "within_30_days": "Yes",
                "complainant_itr_available": True
            },
            "min_score": 85,
            "required_concepts": ["legally_enforceable_debt", "legal_notice_compliance"]
        },
        {
            "name": "FATAL_NOTICE_DEFECT",
            "data": {
                "cheque_present": True,
                "dishonour_memo": True,
                "notice_sent": False,
                "amount": 100000
            },
            "max_score": 30,
            "required_risks": ["notice_defect"]
        },
        {
            "name": "BASALINGAPPA_TRAP",
            "data": {
                "cheque_present": True,
                "dishonour_memo": True,
                "notice_sent": True,
                "amount": 2500000,
                "complainant_itr_available": False,
                "loan_via_bank": False
            },
            "max_score": 50,
            "required_risks": ["financial_capacity_risk"]
        },
        {
            "name": "S141_CORPORATE_DEFECT",
            "data": {
                "cheque_present": True,
                "dishonour_memo": True,
                "notice_sent": True,
                "accused_type": "Pvt Ltd Company",
                "directors_named": False
            },
            "max_score": 40,
            "required_risks": ["s141_defect"]
        },
        {
            "name": "LIMITATION_PERIOD_EXPIRED",
            "data": {
                "cheque_present": True,
                "dishonour_memo": True,
                "notice_sent": True,
                "notice_received_date": "2024-01-01",
                "filing_date": "2024-03-01", # > 30 days after notice period
                "amount": 50000
            },
            "max_score": 35,
            "required_risks": ["limitation_issue"]
        },
        {
            "name": "SIGNATURE_DISPUTE_FATAL",
            "data": {
                "cheque_present": True,
                "dishonour_memo": True,
                "notice_sent": True,
                "signature_dispute": True,
                "handwriting_different": True,
                "amount": 200000
            },
            "max_score": 45,
            "required_risks": ["signature_dispute", "material_alteration"]
        },
        {
            "name": "PREMATURE_FILING_TRAP",
            "data": {
                "cheque_present": True,
                "dishonour_memo": True,
                "notice_sent": True,
                "notice_received_date": "2024-05-01",
                "filing_date": "2024-05-10", # < 15 days
                "amount": 150000
            },
            "max_score": 30,
            "required_risks": ["premature_complaint"]
        },
        {
            "name": "CRIMINAL_S498A_OMNIBUS",
            "data": {
                "case_type": "criminal",
                "offense_type": "498A",
                "relatives_implicated": True
            },
            "max_score": 60,
            "required_risks": []
        },
        {
            "name": "CRIMINAL_S395_TIP_FAILED",
            "data": {
                "case_type": "criminal",
                "offense_type": "395",
                "tip_failed": True
            },
            "max_score": 60,
            "required_risks": []
        },
        {
            "name": "CRIMINAL_S379_TITLE_DISPUTE",
            "data": {
                "case_type": "criminal",
                "offense_type": "379",
                "title_dispute": True
            },
            "max_score": 60,
            "required_risks": []
        },
        {
            "name": "CRIMINAL_S406_NO_ENTRUSTMENT",
            "data": {
                "case_type": "criminal",
                "offense_type": "406",
                "entrustment_proven": False
            },
            "max_score": 60,
            "required_risks": []
        }
    ]

    @classmethod
    async def run_diagnostics(cls) -> Dict[str, Any]:
        results = []
        engine = JudiQEngine()
        
        for case in cls.TEST_CASES:
            try:
                # Mocking the RAG/OCR for pure logic testing
                # pyrefly: ignore [not-async]
                analysis = await engine.analyze_case(case["data"], analysis_mode="detailed")
                score = analysis.get("score", 0)
                
                passed = True
                errors = []
                
                if "min_score" in case and score < case["min_score"]:
                    passed = False
                    errors.append(f"Score {score} below minimum {case['min_score']}")
                
                if "max_score" in case and score > case["max_score"]:
                    passed = False
                    errors.append(f"Score {score} above maximum {case['max_score']}")
                
                results.append({
                    "case": case["name"],
                    "status": "PASS" if passed else "FAIL",
                    "score": score,
                    "errors": errors
                })
            except Exception as e:
                results.append({
                    "case": case["name"],
                    "status": "ERROR",
                    "error": str(e)
                })
        
        return {
            "summary": {
                "total": len(cls.TEST_CASES),
                "passed": len([r for r in results if r["status"] == "PASS"]),
                "failed": len([r for r in results if r["status"] == "FAIL"]),
                "errors": len([r for r in results if r["status"] == "ERROR"])
            },
            "details": results
        }

if __name__ == "__main__":
    import asyncio
    async def main():
        report = await EngineDiagnostics.run_diagnostics()
        print("Engine Diagnostic Report:")
        print(f"Passed: {report['summary']['passed']}/{report['summary']['total']}")
        for detail in report['details']:
            print(f"- {detail['case']}: {detail['status']} (Score: {detail.get('score')}) {detail.get('errors', '')}")
    
    asyncio.run(main())

