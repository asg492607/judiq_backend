"""
JudiQ AI — Dynamic Knowledge Base Ingestion Pipeline
Provides automated ingestion, validation, and hot-reloading of legal precedents and statutory authorities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("JudiQ.KnowledgePipeline")


class VerificationPillars(BaseModel):
    source_verified: bool = True
    textual_integrity: bool = True
    proposition_binding: bool = True
    subsequent_treatment: str = Field(default="Good Law")


class PrecedentIngestionPayload(BaseModel):
    domain: str = Field(..., description="Target domain: 'criminal', 'sarfaesi', 'ni_act', or 'civil'")
    citation: str = Field(..., description="Official citation, e.g., '2026 INSC 142' or '(2022) 10 SCC 51'")
    case_name: str = Field(..., description="Full case title, e.g., 'Satender Kumar Antil v. CBI'")
    court: str = Field(default="Supreme Court of India")
    year: int = Field(..., description="Year of judgment")
    ratio: str = Field(..., description="Core legal proposition and holding")
    sections: List[str] = Field(default_factory=list, description="Statutory sections interpreted")
    favorable_to: str = Field(default="accused", description="'accused', 'complainant', 'borrower', or 'creditor'")
    key_terms: List[str] = Field(default_factory=list, description="Tags and keyword indexing")
    verification: VerificationPillars = Field(default_factory=VerificationPillars)


class PrecedentIngestionService:
    @staticmethod
    def get_knowledge_base_path(domain: str) -> Path:
        base_dir = Path(__file__).resolve().parent
        domain_clean = domain.lower().replace(" ", "_").replace("-", "_")
        
        if "crim" in domain_clean or "bns" in domain_clean or "ipc" in domain_clean:
            return base_dir / "criminal" / "criminal_knowledge_base.json"
        elif "sarfaesi" in domain_clean or "drt" in domain_clean:
            return base_dir / "sarfaesi" / "sarfaesi_knowledge_base.json"
        else:
            return base_dir / "criminal" / "criminal_knowledge_base.json"

    @classmethod
    def validate_precedent(cls, item: PrecedentIngestionPayload) -> Tuple[bool, str]:
        if not item.citation or len(item.citation.strip()) < 4:
            return False, "Citation is too short or invalid."
        if not item.case_name or len(item.case_name.strip()) < 3:
            return False, "Case name is required."
        if not item.ratio or len(item.ratio.strip()) < 10:
            return False, "Ratio decidendi must be a substantial legal proposition (min 10 chars)."
        if item.year < 1950 or item.year > 2030:
            return False, f"Invalid judgment year: {item.year}"
        return True, "Valid"

    @classmethod
    def ingest_precedent(cls, payload: PrecedentIngestionPayload) -> Dict[str, Any]:
        is_valid, reason = cls.validate_precedent(payload)
        if not is_valid:
            return {"success": False, "error": reason}

        kb_path = cls.get_knowledge_base_path(payload.domain)
        if not kb_path.exists():
            return {"success": False, "error": f"Knowledge base file not found at {kb_path}"}

        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            precedents = data.get("precedents", [])
            
            # Check for existing citation to prevent duplicates
            existing_idx = next((i for i, p in enumerate(precedents) if p.get("citation") == payload.citation), None)
            
            new_entry = {
                "citation": payload.citation.strip(),
                "case_name": payload.case_name.strip(),
                "court": payload.court.strip(),
                "year": payload.year,
                "ratio": payload.ratio.strip(),
                "sections": payload.sections,
                "favorable_to": payload.favorable_to,
                "key_terms": payload.key_terms,
                "verification": payload.verification.model_dump()
            }

            if existing_idx is not None:
                precedents[existing_idx] = new_entry
                action = "updated"
            else:
                precedents.append(new_entry)
                action = "inserted"

            data["precedents"] = precedents
            data["last_updated"] = payload.year

            with open(kb_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Precedent '{payload.citation}' ({payload.case_name}) {action} in {kb_path.name}")
            return {
                "success": True,
                "action": action,
                "citation": payload.citation,
                "total_precedents": len(precedents),
                "knowledge_base": kb_path.name
            }
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
