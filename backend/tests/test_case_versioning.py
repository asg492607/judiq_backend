import pytest
import json
from fastapi.testclient import TestClient
from main import app
from session import DatabaseManager

import uuid

client = TestClient(app)


def test_case_versioning_lifecycle():
    DatabaseManager.init_db()
    case_id = f"TEST_LAWYER_CASE_{uuid.uuid4().hex[:6]}"
    user_id = "advocate_sharma@delhibar.in"

    case_data_v1 = {
        "case_id": case_id,
        "case_title": "M/s Apex Logistics vs BlueStar Traders",
        "complainant_name": "M/s Apex Logistics",
        "accused_name": "BlueStar Traders",
        "case_type": "Cheque Bounce",
        "cheque_amount": 750000.0,
        "cheque_date": "2024-03-01",
        "memo_date": "2024-03-10",
        "notice_date": "2024-03-25",
        "filing_date": "2024-05-02",
        "court_name": "Patiala House Courts, New Delhi",
        "notes": "Initial draft without postal tracking report"
    }
    analysis_v1 = {
        "score": 62.5,
        "verdict": "CONDITIONAL_SUCCESS",
        "risk_level": "MODERATE",
        "defence_risk": "Lack of postal acknowledgment proof",
        "summary": "Limitation periods met, but evidence proof is incomplete."
    }

    # 1. Save Initial Case & Version 1
    saved = DatabaseManager.save_case(
        case_id=case_id,
        user_id=user_id,
        case_data=case_data_v1,
        analysis_result=analysis_v1,
        score=62.5,
        verdict="CONDITIONAL_SUCCESS"
    )
    assert saved is True

    # 2. Query versions list via API
    resp = client.get(f"/api/v1/cases/{case_id}/versions")
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) >= 1
    assert versions[0]["version_num"] == 1
    assert versions[0]["score"] == 62.5

    # 3. Advocate receives postal tracking receipt and re-analyzes -> Save Version 2
    case_data_v2 = dict(case_data_v1)
    case_data_v2["postal_tracking_attached"] = True
    case_data_v2["notes"] = "Added SpeedPost tracking POD delivered on 2024-03-28 + S.65B Certificate"
    analysis_v2 = {
        "score": 88.0,
        "verdict": "STRONG_PROBABLE_CONVICTION",
        "risk_level": "LOW",
        "summary": "Complete documentary chain established with statutory presumption u/s 139 NI Act."
    }

    resp_v2 = client.post(f"/api/v1/cases/{case_id}/versions", json={
        "case_data": case_data_v2,
        "analysis_result": analysis_v2,
        "score": 88.0,
        "verdict": "STRONG_PROBABLE_CONVICTION",
        "version_title": "Added SpeedPost POD & S.65B Cert",
        "version_note": "POD tracking confirmed delivery on 2024-03-28. Pre-trial readiness raised."
    })
    assert resp_v2.status_code == 200
    v2_data = resp_v2.json()
    assert v2_data["version_num"] == 2
    assert v2_data["score"] == 88.0
    assert v2_data["delta_score"] == 25.5  # 88.0 - 62.5 = +25.5

    # 4. Check versions list has 2 versions
    resp_list = client.get(f"/api/v1/cases/{case_id}/versions")
    assert resp_list.status_code == 200
    all_versions = resp_list.json()
    assert len(all_versions) >= 2
    assert all_versions[0]["version_num"] == 2
    assert all_versions[0]["delta_score"] == 25.5

    # 5. Fetch details of historical Version 1
    resp_get_v1 = client.get(f"/api/v1/cases/{case_id}/versions/1")
    assert resp_get_v1.status_code == 200
    v1_body = resp_get_v1.json()
    assert v1_body["version_num"] == 1
    assert v1_body["score"] == 62.5
    assert v1_body["case_data"]["case_title"] == "M/s Apex Logistics vs BlueStar Traders"

    # 6. Restore Version 1 snapshot
    resp_restore = client.post(f"/api/v1/cases/{case_id}/restore/1")
    assert resp_restore.status_code == 200
    restored_body = resp_restore.json()
    assert restored_body["success"] is True
