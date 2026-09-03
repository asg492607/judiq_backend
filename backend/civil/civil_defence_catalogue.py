"""
JudiQ AI — Civil Adversarial Defense Catalogue & Preliminary Objections Engine
Evaluates Order VII Rule 11 Rejection of Plaint, Order II Rule 2 Bars,
Section 11 Res Judicata, and Section 8 Arbitration Mandatory References.
"""

from typing import Dict, Any, List

class CivilDefenceCatalogue:
    """
    Catalogues substantive preliminary objections, statutory bars,
    and affirmative defenses in Indian Civil & Commercial litigation.
    """

    DEFENCE_PATTERNS = {
        "order_7_rule_11": {
            "name": "Order VII Rule 11 Rejection of Plaint",
            "statute": "Order VII Rule 11 Code of Civil Procedure, 1908",
            "key_precedent": "Dahiben v. Arvindbhai Kalyanji Bhanusali (2020) 7 SCC 366",
            "principle": "Plaint must be rejected at threshold if on plain reading it discloses no cause of action (11a), is undervalued (11b), has deficit court fee uncured (11c), is barred by limitation/statute (11d), or violates Section 12A PIMS.",
            "evidentiary_threshold": "Only statements in the plaint and documents annexed to plaint can be looked at; defendant's WS is immaterial.",
            "counter_strategy": "Draft plaint with clear, chronological disclosure of recurring cause of action and append valuation schedule."
        },
        "order_2_rule_2": {
            "name": "Order II Rule 2 Bar (Splitting Claims / Relinquishment)",
            "statute": "Order II Rule 2 Code of Civil Procedure, 1908",
            "key_precedent": "Virgo Industries (Eng.) Pvt Ltd v. Venturetech Solutions Pvt Ltd (2013) 1 SCC 625",
            "principle": "Where a plaintiff is entitled to more than one relief in respect of the same cause of action, omission to sue for all reliefs without leave of court bars any subsequent suit for the omitted relief.",
            "evidentiary_threshold": "Must establish that cause of action in earlier suit was identical and plaintiff had knowledge of the claim.",
            "counter_strategy": "Plead separate and distinct subsequent cause of action or produce express leave order granted by court in earlier suit."
        },
        "section_11_res_judicata": {
            "name": "Section 11 Res Judicata & Constructive Res Judicata",
            "statute": "Section 11 Code of Civil Procedure, 1908",
            "key_precedent": "Forward Construction Co v. Prabhat Mandal (1986) 1 SCC 100",
            "principle": "No Court shall try any suit or issue in which the matter directly and substantially in issue has been heard and finally decided by a competent court in a former suit between the same parties.",
            "evidentiary_threshold": "Produce certified copy of former plaint, written statement, issues framed, and final judgment/decree.",
            "counter_strategy": "Distinguish title, parties, or subsequent change in law/facts creating fresh cause of action."
        },
        "section_8_arbitration": {
            "name": "Section 8 Mandatory Arbitration Referral",
            "statute": "Section 8 Arbitration & Conciliation Act, 1996",
            "key_precedent": "Booz Allen & Hamilton Inc v. SBI Home Finance Ltd (2011) 5 SCC 532",
            "principle": "Court must refer parties to arbitration if an action is brought in a matter which is the subject of an arbitration agreement, provided application is made not later than submitting first statement on the substance of the dispute.",
            "evidentiary_threshold": "Produce original or certified copy of valid arbitration agreement.",
            "counter_strategy": "Establish dispute is non-arbitrable (in rem rights, insolvency, fraud of serious nature, eviction under rent control laws)."
        },
        "section_10_res_sub_judice": {
            "name": "Section 10 Stay of Suit (Res Sub-Judice)",
            "statute": "Section 10 Code of Civil Procedure, 1908",
            "key_precedent": "National Institute of Mental Health v. C. Parameshwara (2005) 2 SCC 799",
            "principle": "Court shall not proceed with trial of any suit in which the matter in issue is directly and substantially in issue in a previously instituted pending suit in India.",
            "evidentiary_threshold": "Complete identity of subject matter, reliefs, and parties in previous pending suit.",
            "counter_strategy": "Plead distinct subsequent reliefs or establish former court lacks jurisdiction."
        }
    }

    @classmethod
    def analyze_defenses(cls, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifies and ranks active adversarial defenses based on case signals."""
        identified = []

        # 1. Section 8 Arbitration Bar
        if case_data.get("arbitration_clause_exists") or case_data.get("has_arbitration_agreement"):
            identified.append({
                **cls.DEFENCE_PATTERNS["section_8_arbitration"],
                "active_trigger": "Arbitration clause detected in underlying commercial contract.",
                "priority": "CRITICAL"
            })

        # 2. Order VII Rule 11 Rejection of Plaint
        o7r11_ground = case_data.get("order7_rule11_ground") or case_data.get("o7r11_defect")
        if o7r11_ground or case_data.get("s12a_pims_status") in ["Not Initiated (No Urgent Relief - Fatal Defect)", "not initiated"]:
            identified.append({
                **cls.DEFENCE_PATTERNS["order_7_rule_11"],
                "active_trigger": f"Plaint vulnerable to threshold rejection: {o7r11_ground or 'Section 12A PIMS omission'}.",
                "priority": "FATAL"
            })

        # 3. Order II Rule 2 Bar
        if case_data.get("order2_rule2_omission") or case_data.get("prior_injunction_suit_filed"):
            identified.append({
                **cls.DEFENCE_PATTERNS["order_2_rule_2"],
                "active_trigger": "Relief omitted in earlier suit arising from same contractual cause of action.",
                "priority": "HIGH"
            })

        # 4. Section 11 Res Judicata
        if case_data.get("prior_suit_decided_res_judicata") or case_data.get("former_suit_decreed"):
            identified.append({
                **cls.DEFENCE_PATTERNS["section_11_res_judicata"],
                "active_trigger": "Substantially identical issue adjudicated in prior competent decree.",
                "priority": "FATAL"
            })

        return identified
