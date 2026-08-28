import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_simulation_plan_approval_workflow():
    print("\n--- 1. Authenticate Admin ---")
    admin_auth_res = requests.post(f"{BASE_URL}/api/v1/admin/auth/verify", json={
        "email": "admin@judiq.ai",
        "password": "492607"
    })
    assert admin_auth_res.status_code == 200, f"Admin auth failed: {admin_auth_res.text}"
    auth_data = admin_auth_res.json()
    assert auth_data.get("is_admin") is True, f"Admin check failed: {auth_data}"
    admin_token = auth_data["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    print("Admin token acquired successfully.")

    import uuid
    uid_suffix = uuid.uuid4().hex[:6]
    test_user_id = f"USR_TEST_ADVOCATE_{uid_suffix}"
    test_email = f"advocate.test_{uid_suffix}@lawfirm.in"
    submit_res = requests.post(f"{BASE_URL}/api/v1/admin/subscription/submit-plan", json={
        "user_id": test_user_id,
        "email": test_email,
        "selected_modules": ["s138", "sarfaesi"],
        "monthly_price_inr": 1000.0,
        "requested_quota": 20,
        "role": "law_firm"
    })
    assert submit_res.status_code == 200, f"Submit plan failed: {submit_res.text}"
    data = submit_res.json()
    assert data["status"] == "PENDING_APPROVAL"
    assert data["quota"]["plan_status"] == "PENDING_APPROVAL"
    assert data["quota"]["is_active"] is False
    print(f"Plan submitted: status={data['status']}, is_active={data['quota']['is_active']}")

    print("\n--- 3. Verify Analysis is BLOCKED for Unapproved User ---")
    analyze_payload = {
        "user_id": test_user_id,
        "email": test_email,
        "case_description": "Cheque dishonoured due to insufficient funds. Statutory demand notice issued within 30 days.",
        "cheque_amount": 500000,
        "cheque_date": "2026-05-01",
        "dishonour_date": "2026-05-10",
        "notice_date": "2026-05-20",
        "recipient_received_date": "2026-05-25",
        "complaint_date": "2026-06-15",
        "complainant_type": "company",
        "accused_type": "individual"
    }
    analyze_res = requests.post(f"{BASE_URL}/api/v1/analyze", json=analyze_payload)
    print(f"Analyze response status: {analyze_res.status_code}")
    assert analyze_res.status_code == 403, f"Expected 403 Forbidden for pending user, got {analyze_res.status_code}: {analyze_res.text}"
    err = analyze_res.json()
    print(f"Blocked reason: {err.get('error_code')} - {err.get('error')}")
    assert "PENDING_ADMIN_APPROVAL" in err.get("error_code", "")

    print("\n--- 4. Verify Document Draft is BLOCKED for Unapproved User ---")
    draft_res = requests.post(f"{BASE_URL}/api/v1/documents/draft-word", json={
        "user_id": test_user_id,
        "email": test_email,
        "title": "Test_Notice",
        "content": "Sample notice draft"
    })
    print(f"Draft Word response status: {draft_res.status_code}")
    assert draft_res.status_code == 403, f"Expected 403 Forbidden for draft generation, got {draft_res.status_code}: {draft_res.text}"
    print("Draft generation successfully blocked.")

    print("\n--- 5. Admin Inspects Pending Plans Queue ---")
    pending_res = requests.get(f"{BASE_URL}/api/v1/admin/pending-plans", headers=headers)
    assert pending_res.status_code == 200
    pending_list = pending_res.json()["pending_plans"]
    matching = [p for p in pending_list if p["user_id"] == test_user_id]
    assert len(matching) > 0, "Submitted plan not found in admin pending queue"
    print(f"Found {len(matching)} pending request for {test_user_id}: {matching[0]['selected_modules']}, INR {matching[0]['monthly_price_inr']}")

    print("\n--- 6. Admin Approves Plan ---")
    approve_res = requests.post(f"{BASE_URL}/api/v1/admin/approve-plan", headers=headers, json={
        "user_id": test_user_id
    })
    assert approve_res.status_code == 200, f"Approve failed: {approve_res.text}"
    app_data = approve_res.json()
    assert app_data["quota"]["plan_status"] == "APPROVED"
    assert app_data["quota"]["is_active"] is True
    assert app_data["quota"]["monthly_report_limit"] == 20
    print(f"Plan approved! Status: {app_data['quota']['plan_status']}, Monthly Limit: {app_data['quota']['monthly_report_limit']}")

    print("\n--- 7. Verify Analysis NOW SUCCEEDS for Approved User ---")
    analyze_res2 = requests.post(f"{BASE_URL}/api/v1/analyze", json=analyze_payload)
    assert analyze_res2.status_code == 200, f"Expected 200 OK after approval, got {analyze_res2.status_code}: {analyze_res2.text}"
    res2_data = analyze_res2.json()
    print(f"Analysis successful! Case score: {res2_data.get('score')}, Merit: {res2_data.get('verdict')}")

    print("\n--- 8. Verify Document Draft NOW SUCCEEDS for Approved User ---")
    draft_res2 = requests.post(f"{BASE_URL}/api/v1/documents/draft-word", json={
        "user_id": test_user_id,
        "email": test_email,
        "title": "Approved_Notice",
        "content": "Sample statutory notice content"
    })
    assert draft_res2.status_code == 200, f"Expected 200 OK for draft after approval, got {draft_res2.status_code}"
    print("Draft Word generated successfully (200 OK, bytes returned).")

    print("\n=======================================================")
    print("ALL TESTS PASSED: Admin Approval Gate is 100% strictly enforced!")
    print("=======================================================")

if __name__ == "__main__":
    test_simulation_plan_approval_workflow()
