import logging
import json
import os
import re

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """
    Singleton manager for the Data Layer.
    Loads and serves: knowledge_base.json + statutes.json

    Key responsibility: normalise the semantic_patterns / legal_concepts
    stored in knowledge_base.json into the regex-ready 'patterns' format
    consumed by SemanticEngineV12.
    """
    _instance = None
    _data     = None
    _statutes = None
    _legal_concepts_cache = None   # computed once on first access

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeBaseManager, cls).__new__(cls)
            cls._instance._load_all()
        return cls._instance

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load_all(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cwd = os.getcwd()
        
        # Search priority: Current file's dir, then CWD
        kb_candidates = [
            os.path.join(base_dir, "knowledge_base.json"),
            os.path.join(cwd, "knowledge_base.json")
        ]
        statutes_candidates = [
            os.path.join(base_dir, "statutes.json"),
            os.path.join(cwd, "statutes.json"),
            os.path.join(base_dir, "status.json"),
            os.path.join(cwd, "status.json")
        ]
        
        kb_path = next((p for p in kb_candidates if os.path.exists(p)), kb_candidates[0])
        statutes_path = next((p for p in statutes_candidates if os.path.exists(p)), statutes_candidates[0])

        try:
            with open(kb_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            logger.info("Knowledge Base loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load knowledge_base.json: {e}")
            self._data = {}

        try:
            with open(statutes_path, "r", encoding="utf-8") as f:
                self._statutes = json.load(f)
            logger.info("Statutes loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load statutes.json: {e}")
            self._statutes = {}

    # ── Statutes ──────────────────────────────────────────────────────────────

    def get_statutes(self) -> dict:
        return self._statutes

    def get_ni_act_section(self, section: str) -> dict:
        return (
            self._statutes
            .get("NI_ACT_1881", {})
            .get("sections", {})
            .get(section, {})
        )

    def get_precedents_for_concept(self, concept: str) -> list:
        return (
            self._statutes
            .get("LANDMARK_PRECEDENTS", {})
            .get(concept, [])
        )

    # ── Knowledge Base ────────────────────────────────────────────────────────

    def get_semantic_patterns(self) -> dict:
        return self._data.get("semantic_patterns", {})

    def get_legal_concepts(self) -> dict:
        """
        Return the concept registry in the format SemanticEngineV12 expects:
            { concept_key: { "patterns": [regex_str, ...], "weight": float,
                             "legal_impact": str }, ... }

        Resolution order:
        1. 'legal_concepts' key  — new canonical format
        2. 'semantic_patterns'   — old format; phrases are compiled to regex here
        3. Empty dict            — logged as a warning
        """
        if self._legal_concepts_cache is not None:
            return self._legal_concepts_cache

        # Try new canonical format first
        if "legal_concepts" in self._data and self._data["legal_concepts"]:
            self._legal_concepts_cache = self._data["legal_concepts"]
            logger.debug(f"[KB] legal_concepts loaded: {len(self._legal_concepts_cache)} entries")
            return self._legal_concepts_cache

        # Fall back to semantic_patterns and build regex patterns on the fly
        raw = self._data.get("semantic_patterns", {})
        if not raw:
            logger.warning("[KB] Neither 'legal_concepts' nor 'semantic_patterns' found in KB. "
                           "Concept detection will be empty.")
            self._legal_concepts_cache = {}
            return {}

        converted = {}
        for concept_key, cfg in raw.items():
            # Collect all phrase lists
            all_phrases = (
                cfg.get("patterns", []) +
                cfg.get("exact_phrases", []) +
                cfg.get("synonyms", []) +
                cfg.get("related_terms", []) +
                cfg.get("negation_phrases", [])
            )
            # Convert to safe regex alternation patterns
            regex_patterns = []
            for phrase in all_phrases:
                if not phrase or not isinstance(phrase, str):
                    continue
                escaped = re.escape(phrase.strip().lower())
                regex_patterns.append(escaped)

            if not regex_patterns:
                continue

            weight  = cfg.get("legal_weight", cfg.get("confidence_threshold", 0.5))
            impact  = cfg.get("legal_impact", "")

            converted[concept_key] = {
                "patterns":     regex_patterns,
                "weight":       float(weight),
                "legal_impact": impact,
            }

        logger.info(f"[KB] Converted {len(converted)} semantic_patterns → legal_concepts format.")
        self._legal_concepts_cache = converted
        return converted

    def get_knowledge_base(self) -> dict:
        return self._data.get("knowledge_base", {})

    def get_scoring_catalogue(self) -> dict:
        return self._data.get("scoring_catalogue", {})

    def get_defence_templates(self) -> dict:
        return self._data.get("defence_templates", {})

    def get_defence_legal_weights(self) -> dict:
        return self._data.get("defence_legal_weights", {})

    def get_score_impact(self, concept: str) -> float:
        return self.get_knowledge_base().get(concept, {}).get("score_impact", 0)

    def get_risk_level(self, concept: str) -> str:
        return self.get_knowledge_base().get(concept, {}).get("risk_level", "LOW")


kb_manager = KnowledgeBaseManager()
