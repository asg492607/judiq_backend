import pytest
import os
import sys

# Ensure backend root is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from citation.citation_verifier import CitationVerifierEngine

def test_authority_object_structure_verified_judgment():
    auth = CitationVerifierEngine.verify_citation("United Bank of India v. Satyawati Tondon (2010)")
    assert auth["status"] in ["VERIFIED", "DISTINGUISHABLE"]
    assert "source" in auth
    assert auth["source"]["official_url"] is not None
    assert auth["source"]["integrity_status"] == "PENDING_LIVE_HTTP_RETRIEVAL"
    assert auth["verification"]["primary_source_verified"] is True
    assert auth["verification"]["document_integrity_verified"] is False

def test_authority_object_rbi_master_circular():
    auth = CitationVerifierEngine.verify_citation("RBI IRAC Master Circular 2025")
    assert auth["type"] == "RBI_DIRECTION"
    assert auth["source"]["source_domain"] == "rbi.org.in"
    assert auth["source"]["official_url"] == "https://rbi.org.in/scripts/NotificationUser.aspx?Id=12822"
    assert auth["source"]["integrity_status"] == "PENDING_LIVE_HTTP_RETRIEVAL"
    assert auth["verification"]["primary_source_verified"] is True
    assert auth["verification"]["proposition_mapped"] is True
    assert auth["verification"]["proposition_verified"] is False

def test_authority_object_superseded_trap():
    auth = CitationVerifierEngine.verify_citation("Mardia Chemicals 2004 pre-deposit rule for Sec 17")
    assert auth["status"] == "SUPERSEDED"
    assert auth["treatment"] == "SUPERSEDED"
    assert auth["verification"]["proposition_mapped"] is False
    assert auth["verification"]["current_treatment_checked"] is True

def test_authority_object_unknown_citation():
    auth = CitationVerifierEngine.verify_citation("Fake Case v. Unknown Bank AIR 2099 SC 9999")
    assert auth["status"] == "UNKNOWN"
    assert auth["source"]["official_url"] is None
    assert auth["source"]["document_hash"] is None
    assert auth["verification"]["primary_source_verified"] is False
    assert auth["verification"]["document_integrity_verified"] is False

def test_primary_source_retriever_interface():
    from citation.source_retriever import PrimarySourceRetriever
    res = PrimarySourceRetriever.fetch_and_verify_primary_source("invalid_url")
    assert res["success"] is False
    assert res["document_integrity_verified"] is False
    assert res["document_hash"] is None
