"""
JudiQ AI Cheque Bounce (S.138 NI Act) Engine Package
===================================================
Negotiable Instruments Act, Section 138/139/141 statutory notices,
cheque dishonour analysis, statutory presumptions, and defense strategies.
"""

from cheque_bounce.cheque_bounce_engine import ChequeBounceEngine
from cheque_bounce.ni_act_statutory_rules import NIActStatutoryRules
from cheque_bounce.defence_catalogue import Section138DefenceCatalogue

__all__ = [
    "ChequeBounceEngine",
    "NIActStatutoryRules",
    "Section138DefenceCatalogue"
]
