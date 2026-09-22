from fastapi import APIRouter, HTTPException, Depends, Query, Body, Request
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
import logging
from datetime import datetime

from gemini_service import GeminiCaseRAGService, normalize_fact_presentation, extract_clean_citations
from session import DatabaseManager
from security import get_current_user_optional

logger = logging.getLogger("judiq.case_chat_router")

router = APIRouter()


class ChatInitPayload(BaseModel):
    case_id: Optional[str] = None
    case_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    doc_intel: Optional[Dict[str, Any]] = Field(default_factory=dict)
    language: Optional[str] = "en"


class ChatQueryPayload(BaseModel):
    case_id: Optional[str] = None
    query: str
    case_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    doc_intel: Optional[Dict[str, Any]] = Field(default_factory=dict)
    chat_history: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    language: Optional[str] = "en"


class FactUpdatePayload(BaseModel):
    case_id: str
    field: str
    value: Any
    reason: Optional[str] = "Updated via Case AI Chat"


class CrossExamPayload(BaseModel):
    case_id: Optional[str] = None
    witness_role: str = "complainant"
    case_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    doc_intel: Optional[Dict[str, Any]] = Field(default_factory=dict)
    language: Optional[str] = "en"


class ArgumentsPayload(BaseModel):
    case_id: Optional[str] = None
    argument_type: str = "framing_notice"
    case_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    doc_intel: Optional[Dict[str, Any]] = Field(default_factory=dict)
    language: Optional[str] = "en"


def _resolve_session_doc_intel(case_id: str, doc_intel: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback to in-memory Document Intelligence session cache or saved_cases if all_facts is empty."""
    resolved = dict(doc_intel or {})
    if not resolved.get("all_facts") and case_id:
        try:
            from case_fact_intelligence import _sessions
            if case_id in _sessions:
                cached = _sessions[case_id]
                resolved["all_facts"] = cached.get("all_facts", {})
                if not resolved.get("documents"):
                    resolved["documents"] = cached.get("documents", [])
                if not resolved.get("contradictions"):
                    resolved["contradictions"] = cached.get("contradictions", [])
                if not resolved.get("timeline"):
                    resolved["timeline"] = cached.get("timeline", [])
        except Exception as e:
            logger.debug(f"Session fallback resolution note for {case_id}: {e}")

    # Fallback to saved_cases in database
    if not resolved.get("all_facts") and case_id:
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()
            p = DatabaseManager.get_dialect_placeholder()
            cursor.execute(f"SELECT case_data FROM saved_cases WHERE case_id = {p}", (case_id,))
            row = cursor.fetchone()
            if row and row[0]:
                cdata = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                if isinstance(cdata, dict):
                    resolved["all_facts"] = cdata.get("all_facts") or cdata
        except Exception as db_err:
            logger.debug(f"Database fallback resolution note for {case_id}: {db_err}")

    return resolved



@router.post("/init")
def init_case_chat(
    payload: ChatInitPayload,
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Initializes a multilingual RAG chat workspace for the active case facts and documents.
    Normalizes raw document candidate lists into clean, presentation-ready facts.
    Loads persistent chat history for the case.
    """
    effective_user = user_id or "ANONYMOUS"
    lang = payload.language or "en"
    case_id = payload.case_id or f"CASE_{int(datetime.now().timestamp())}"
    doc_intel = _resolve_session_doc_intel(case_id, payload.doc_intel)
    case_data = payload.case_data or {}
    facts = {}
    for k, v in doc_intel.get("all_facts", {}).items():
        if v is not None and v != "":
            facts[k] = v
    for k, v in case_data.items():
        if v is not None and v != "" and v != "Not specified" and v != "null":
            if k in ("complainant_name", "accused_name") and v in ("Complainant", "Accused") and k in facts:
                continue
            facts[k] = v

    # Extract clean, normalized metrics
    chq_amt = normalize_fact_presentation(facts.get("cheque_amount"), "cheque_amount")
    chq_no = normalize_fact_presentation(facts.get("cheque_number"), "cheque_number")
    chq_dt = normalize_fact_presentation(facts.get("cheque_date"), "cheque_date")
    complainant = normalize_fact_presentation(facts.get("complainant_name"), "complainant_name")
    if complainant == "Not specified":
        complainant = "Complainant"
    accused = normalize_fact_presentation(facts.get("accused_name"), "accused_name")
    if accused == "Not specified":
        accused = "Accused"

    citations = extract_clean_citations(doc_intel, facts)
    citations_str = ", ".join(citations[:3]) if citations else "Uploaded case files"

    # Multilingual greeting with clean presentation
    if lang == "mr":
        greeting = (
            f"नमस्कार! मी **JudiQ AI कायदेतज्ज्ञ सह-सल्लागार (Legal Co-Counsel)** आहे.\n\n"
            f"मी तुमच्या केसची कागदपत्रे आणि वस्तुस्थिती तपासली आहे:\n"
            f"• **फिर्यादी:** {complainant} | **आरोपी:** {accused}\n"
            f"• **धनादेश तपशील:** #{chq_no} | {chq_amt} (तारीख: {chq_dt})\n"
            f"• **सत्यापित कागदपत्रे:** {citations_str}\n\n"
            f"तुम्ही मला या केसच्या मुदतीबाबत (Limitation), पुरावा कायद्याबाबत (BSA), उलट तपासणीबाबत (Cross-Exam) "
            f"किंवा न्यायालयीन युक्तिवादाबाबत मराठीत कोणताही प्रश्न विचारू शकता. जर एखाद्या माहितीत दुरुस्ती करायची असेल, तर थेट सांगा."
        )
    elif lang == "hi":
        greeting = (
            f"नमस्ते! मैं **JudiQ AI विधिक सह-सलाहकार (Legal Co-Counsel)** हूँ।\n\n"
            f"मैंने आपके केस के सभी दस्तावेज और तथ्य लोड कर लिए हैं:\n"
            f"• **पक्षकार:** {complainant} बनाम {accused}\n"
            f"• **चेक विवरण:** #{chq_no} | {chq_amt} (दिनांक: {chq_dt})\n"
            f"• **सत्यापित दस्तावेज:** {citations_str}\n\n"
            f"आप धारा 138 की समय-सीमा, बैंक मेमो की वैधता, गवाहों की जिरह (Cross-Examination), "
            f"या अदालती बहस के बारे में हिंदी में कोई भी प्रश्न पूछ सकते हैं। आप चैट में ही किसी तथ्य को अपडेट भी कर सकते हैं।"
        )
    else:
        greeting = (
            f"Welcome to the **JudiQ Case Intelligence Workspace**.\n\n"
            f"I have synchronized the verified case facts from your intake:\n"
            f"• **Parties:** {complainant} vs {accused}\n"
            f"• **Cheque Instrument:** #{chq_no} | {chq_amt} ({chq_dt})\n"
            f"• **Verified Sources:** {citations_str}\n\n"
            f"I am fully grounded in your case documents, statutory Section 138 benchmarks, and Indian evidentiary rules. "
            f"Ask about statutory timelines, contradictions, cross-examination strategy, or update any case facts directly."
        )

    # Fetch persistent chat history for this case
    saved_history = DatabaseManager.get_case_chat_history(case_id, limit=50)

    return {
        "success": True,
        "case_id": case_id,
        "language": lang,
        "greeting": greeting,
        "active_facts": {
            "complainant_name": complainant,
            "accused_name": accused,
            "cheque_number": chq_no,
            "cheque_amount": chq_amt,
            "cheque_date": chq_dt,
            "verified_sources": citations
        },
        "all_facts": doc_intel.get("all_facts", {}),
        "case_data": facts,
        "citations": citations,
        "history": saved_history,
        "has_saved_history": len(saved_history) > 0,
        "contradictions_count": len(doc_intel.get("contradictions", []))
    }


@router.post("/query")
def query_case_chat(
    payload: ChatQueryPayload,
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Executes a grounded RAG query over the case facts, returning citations and proposed fact changes.
    Persists user query and assistant response for continuous chat sessions.
    """
    effective_user = user_id or "ANONYMOUS"
    case_data = payload.case_data or {}
    case_id = payload.case_id or f"CASE_{int(datetime.now().timestamp())}"
    doc_intel = _resolve_session_doc_intel(case_id, payload.doc_intel)
    lang = payload.language or "en"

    # Save user query to persistent history
    DatabaseManager.save_case_chat_message(
        case_id=case_id,
        role="user",
        content=payload.query,
        language=lang
    )

    res = GeminiCaseRAGService.query_case_rag(
        query=payload.query,
        case_data=case_data,
        doc_intel=doc_intel,
        chat_history=payload.chat_history or [],
        lang=lang
    )

    # Combine statutory citations with relevant verified source documents
    statutory_citations = res.get("citations", [])
    doc_citations = extract_clean_citations(doc_intel, case_data)
    combined_citations = statutory_citations + [d for d in doc_citations if d not in statutory_citations]

    answer = res.get("answer", "")
    proposed_updates = res.get("proposed_updates", [])
    resp_lang = res.get("language", lang)

    # Save assistant response to persistent history
    DatabaseManager.save_case_chat_message(
        case_id=case_id,
        role="assistant",
        content=answer,
        citations=combined_citations,
        proposed_updates=proposed_updates,
        language=resp_lang
    )

    return {
        "success": True,
        "case_id": case_id,
        "answer": answer,
        "citations": combined_citations,
        "proposed_updates": proposed_updates,
        "language": resp_lang,
        "timestamp": res.get("timestamp")
    }


@router.post("/clear-history")
def clear_case_chat(
    payload: Dict[str, Any] = Body(...),
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Clears the stored conversation history for a given case.
    """
    case_id = payload.get("case_id")
    if not case_id:
        raise HTTPException(status_code=400, detail="case_id required")
    DatabaseManager.clear_case_chat_history(case_id)
    return {"success": True, "message": f"Cleared history for {case_id}"}


@router.post("/update-fact")
def update_case_fact(
    payload: FactUpdatePayload,
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Directly updates a case fact in the active database session so downstream analysis recalculates.
    """
    effective_user = user_id or "ANONYMOUS"
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        p = DatabaseManager.get_dialect_placeholder()

        # Check in saved_cases
        cursor.execute(f"SELECT id, case_data FROM saved_cases WHERE case_id = {p}", (payload.case_id,))
        row = cursor.fetchone()
        if row:
            try:
                cdata = json.loads(row[1]) if row[1] else {}
            except Exception:
                cdata = {}
            cdata[payload.field] = payload.value
            now = datetime.now().isoformat()
            cursor.execute(
                f"UPDATE saved_cases SET case_data = {p}, updated_at = {p} WHERE case_id = {p}",
                (json.dumps(cdata), now, payload.case_id)
            )
            conn.commit()
        else:
            cdata = {payload.field: payload.value}
            now = datetime.now().isoformat()
            cursor.execute(
                f"INSERT INTO saved_cases (case_id, user_id, case_data, created_at, updated_at) VALUES ({p}, {p}, {p}, {p}, {p})",
                (payload.case_id, effective_user, json.dumps(cdata), now, now)
            )
            conn.commit()

        # Check in cms_cases if exists
        try:
            cursor.execute(f"SELECT case_id FROM cms_cases WHERE case_id = {p}", (payload.case_id,))
            if cursor.fetchone():
                DatabaseManager.cms_update_case(case_id=payload.case_id, updates={payload.field: payload.value})
        except Exception:
            pass

        return {
            "success": True,
            "case_id": payload.case_id,
            "field": payload.field,
            "value": payload.value,
            "message": f"Successfully updated {payload.field} to {payload.value}"
        }
    except Exception as e:
        logger.error(f"Failed to update fact: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            DatabaseManager.release_connection(conn)


@router.post("/cross-exam")
def generate_cross_examination(
    payload: CrossExamPayload,
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Generates tailored cross-examination questions for Complainant, Accused, or Bank Manager.
    """
    case_data = payload.case_data or {}
    case_id = payload.case_id or f"CASE_{int(datetime.now().timestamp())}"
    doc_intel = _resolve_session_doc_intel(case_id, payload.doc_intel)
    res = GeminiCaseRAGService.generate_cross_examination(
        witness_role=payload.witness_role,
        case_data=case_data,
        doc_intel=doc_intel,
        lang=payload.language or "en"
    )
    return {
        "success": True,
        "case_id": case_id,
        **res
    }


@router.post("/arguments")
def generate_courtroom_arguments(
    payload: ArgumentsPayload,
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Generates courtroom trial arguments or quashing grounds.
    """
    case_data = payload.case_data or {}
    case_id = payload.case_id or f"CASE_{int(datetime.now().timestamp())}"
    doc_intel = _resolve_session_doc_intel(case_id, payload.doc_intel)
    res = GeminiCaseRAGService.generate_courtroom_arguments(
        argument_type=payload.argument_type,
        case_data=case_data,
        doc_intel=doc_intel,
        lang=payload.language or "en"
    )
    return {
        "success": True,
        "case_id": case_id,
        **res
    }


@router.post("/export")
def export_facts(
    payload: ChatInitPayload,
    user_id: Optional[str] = Depends(get_current_user_optional)
):
    """
    Exports the verified fact sheet and litigation dossier.
    """
    case_data = payload.case_data or {}
    case_id = payload.case_id or f"CASE_{int(datetime.now().timestamp())}"
    doc_intel = _resolve_session_doc_intel(case_id, payload.doc_intel)
    res = GeminiCaseRAGService.export_case_dossier(
        case_data=case_data,
        doc_intel=doc_intel,
        lang=payload.language or "en"
    )
    return {
        "success": True,
        **res
    }
