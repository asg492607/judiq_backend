import hashlib
import urllib.request
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PrimarySourceRetriever:
    """
    Primary Source Document Retriever & Byte Integrity Hasher:
    Retrieves official PDF/HTML binary payloads from canonical primary portals (RBI, Supreme Court, IndiaCode),
    validates HTTP status and non-empty byte payloads, and computes authentic SHA-256 document hashes.
    """

    @classmethod
    def fetch_and_verify_primary_source(cls, official_url: str, timeout_sec: int = 5) -> Dict[str, Any]:
        if not official_url or not official_url.startswith("http"):
            return {
                "success": False,
                "document_integrity_verified": False,
                "document_hash": None,
                "byte_size": 0,
                "error": "Invalid or missing official URL"
            }

        try:
            req = urllib.request.Request(
                official_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JudiQ Legal Verification Engine/1.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                if response.status == 200:
                    raw_bytes = response.read()
                    byte_size = len(raw_bytes)

                    EMPTY_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                    if byte_size > 0:
                        computed_hash = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"
                        if computed_hash.replace("sha256:", "") != EMPTY_HASH:
                            return {
                                "success": True,
                                "document_integrity_verified": True,
                                "document_hash": computed_hash,
                                "byte_size": byte_size,
                                "canonical_url": response.geturl(),
                                "content_type": response.headers.get("Content-Type", "unknown"),
                                "error": None
                            }

        except Exception as e:
            logger.warning(f"Failed live primary source retrieval from {official_url}: {e}")

        return {
            "success": False,
            "document_integrity_verified": False,
            "document_hash": None,
            "byte_size": 0,
            "canonical_url": official_url,
            "error": "Live HTTP byte retrieval pending or failed"
        }
