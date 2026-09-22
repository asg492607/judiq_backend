import pytest
from fastapi.testclient import TestClient
import json
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from gemini_service import GeminiCaseRAGService

client = TestClient(app)

SAMPLE_CASE_DATA = {
    "case_id": "TEST_CHAT_CASE_001",
    "case_title": "Apex Traders vs Zenith Infra",
    "complainant_name": "Apex Traders Pvt Ltd",
    "accused_name": "Zenith Infrastructure Ltd",
    "cheque_number": "654321",
    "cheque_amount": 500000.0,
    "cheque_date": "2026-01-15",
    "bank_name": "HDFC Bank, Fort Branch",
    "dishonour_date": "2026-01-18",
    "dishonour_reason": "Insufficient Funds",
    "memo_date": "2026-01-20",
    "notice_date": "2026-02-10",
    "notice_received_date": "2026-02-14",
    "notice_mode": "Speed Post"
}


def test_gemini_service_detect_language():
    assert GeminiCaseRAGService.detect_language("What is the cheque date?") == "en"
    assert GeminiCaseRAGService.detect_language("धनादेश अनादर तारीख काय आहे?") == "mr"
    assert GeminiCaseRAGService.detect_language("चेक बाउंस होने की कानूनी नोटिस की तारीख क्या है?") == "hi"


def test_case_chat_init_english():
    resp = client.post("/api/v1/case-chat/init", json={
        "case_id": "TEST_CHAT_CASE_001",
        "case_data": SAMPLE_CASE_DATA,
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "Apex Traders" in data["greeting"]
    assert "654321" in data["greeting"]


def test_case_chat_init_marathi():
    resp = client.post("/api/v1/case-chat/init", json={
        "case_id": "TEST_CHAT_CASE_001",
        "case_data": SAMPLE_CASE_DATA,
        "language": "mr"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "धनादेश" in data["greeting"]
    assert data["language"] == "mr"


def test_case_chat_init_normalizes_raw_candidate_lists():
    raw_doc_intel = {
        "all_facts": {
            "complainant_name": [
                {"value": "ASTERON COMPONENTS PRIVATE LIMITED", "confidence": 0.75, "source_document": "03_Cheque_582914.jpg"},
                {"value": "Asteron Components Private Limited", "confidence": 0.75, "source_document": "05_Legal_Demand_Notice.pdf"}
            ],
            "accused_name": [
                {"value": "BluePeak Industrial Systems Private Limited", "confidence": 0.75, "source_document": "05_Legal_Demand_Notice.pdf"}
            ],
            "cheque_number": [
                {"value": "582914", "confidence": 0.88, "source_document": "03_Cheque_582914.jpg"}
            ],
            "cheque_amount": [
                {"value": 1500000, "confidence": 0.88, "source_document": "03_Cheque_582914.jpg"},
                {"value": 1450000, "confidence": 0.88, "source_document": "05_Legal_Demand_Notice.pdf"}
            ],
            "cheque_date": [
                {"value": "2026-03-24", "confidence": 0.8, "source_document": "05_Legal_Demand_Notice.pdf"}
            ]
        }
    }
    resp = client.post("/api/v1/case-chat/init", json={
        "case_id": "TEST_RAW_DOCS_001",
        "doc_intel": raw_doc_intel,
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    greeting = data["greeting"]
    # Ensure NO raw dict or list strings appear in greeting
    assert "{'value'" not in greeting
    assert "[{" not in greeting
    assert "Asteron Components Private Limited" in greeting
    assert "BluePeak Industrial Systems Private Limited" in greeting
    assert "582914" in greeting
    assert "15,00,000" in greeting


def test_case_chat_persistence_and_clear():
    case_id = "TEST_PERSIST_CASE_099"
    # 1. Clear any prior history
    client.post("/api/v1/case-chat/clear-history", json={"case_id": case_id})

    # 2. Send query
    q_resp = client.post("/api/v1/case-chat/query", json={
        "case_id": case_id,
        "query": "What is the limitation period for issuing Section 138 notice?",
        "case_data": SAMPLE_CASE_DATA,
        "language": "en"
    })
    assert q_resp.status_code == 200

    # 3. Call init again and verify persistent history is loaded
    init_resp = client.post("/api/v1/case-chat/init", json={
        "case_id": case_id,
        "case_data": SAMPLE_CASE_DATA,
        "language": "en"
    })
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    assert init_data["has_saved_history"] is True
    assert len(init_data["history"]) >= 2  # user message + assistant response
    assert init_data["history"][0]["role"] == "user"
    assert "limitation period" in init_data["history"][0]["content"]

    # 4. Clear history
    clear_resp = client.post("/api/v1/case-chat/clear-history", json={"case_id": case_id})
    assert clear_resp.status_code == 200

    # 5. Verify history is empty
    init_after = client.post("/api/v1/case-chat/init", json={
        "case_id": case_id,
        "case_data": SAMPLE_CASE_DATA,
        "language": "en"
    })
    assert init_after.json()["has_saved_history"] is False


def test_case_chat_query_with_fallback():
    resp = client.post("/api/v1/case-chat/query", json={
        "case_id": "TEST_CHAT_CASE_001",
        "query": "Is the demand notice dispatched within 30 days of return memo?",
        "case_data": SAMPLE_CASE_DATA,
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "answer" in data
    assert len(data["answer"]) > 20


def test_case_chat_query_marathi():
    resp = client.post("/api/v1/case-chat/query", json={
        "case_id": "TEST_CHAT_CASE_001",
        "query": "नोटीस कधी पाठवली आणि मुदत काय आहे?",
        "case_data": SAMPLE_CASE_DATA,
        "language": "mr"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["language"] == "mr"
    assert "कलम १३८" in data["answer"]


def test_fact_update_detection():
    # Test query specifying a new amount
    res = GeminiCaseRAGService.query_case_rag(
        query="Actually the cheque amount is changed to 750000",
        case_data=SAMPLE_CASE_DATA,
        lang="en"
    )
    updates = res.get("proposed_updates", [])
    assert len(updates) > 0
    assert updates[0]["field"] == "cheque_amount"
    assert updates[0]["value"] == 750000.0


def test_case_chat_cross_exam():
    resp = client.post("/api/v1/case-chat/cross-exam", json={
        "case_id": "TEST_CHAT_CASE_001",
        "witness_role": "complainant",
        "case_data": SAMPLE_CASE_DATA,
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "questions_text" in data
    assert len(data["questions_text"]) > 30


def test_case_chat_arguments():
    resp = client.post("/api/v1/case-chat/arguments", json={
        "case_id": "TEST_CHAT_CASE_001",
        "argument_type": "framing_notice",
        "case_data": SAMPLE_CASE_DATA,
        "language": "mr"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "arguments_text" in data
    assert "कलम" in data["arguments_text"]


def test_case_chat_export():
    resp = client.post("/api/v1/case-chat/export", json={
        "case_id": "TEST_CHAT_CASE_001",
        "case_data": SAMPLE_CASE_DATA,
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "# JUDIQ AI" in data["markdown"]
    assert "654321" in data["markdown"]


def test_case_chat_update_fact():
    resp = client.post("/api/v1/case-chat/update-fact", json={
        "case_id": "TEST_CHAT_CASE_001",
        "field": "cheque_amount",
        "value": 900000.0,
        "reason": "Updated via lawyer test"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["field"] == "cheque_amount"
    assert data["value"] == 900000.0

