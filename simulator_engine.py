import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SimulatorEngine:
    """
    Cross-Examination Simulator — Anticipates defense attacks and prepares 
    the Complainant for the witness box.
    """

    STRATEGY_MAP = {
        "financial_capacity_risk": {
            "question": "You claim to have lent ₹4,50,000 in cash. Can you show your Income Tax Returns for that year reflecting this withdrawal?",
            "objective": "To rebut your financial capacity under the Basalingappa rule.",
            "preparation": "Keep bank statements and ITR copies ready. If not available, prepare a 'Source of Funds' affidavit.",
            "suggested_answer": "The loan was advanced from personal savings and family contributions, which is a common practice in our business community. While ITRs are one form of proof, the issuance of the cheque itself by the Accused is an admission of this debt as per Section 139 of the NI Act."
        },
        "security_cheque": {
            "question": "Wasn't this cheque given merely as a blank security cheque at the start of our business relationship, with no debt due at that time?",
            "objective": "To claim the cheque was misused and falls under the Indus Airways exception.",
            "preparation": "Gather invoices or delivery challans dated PRIOR to the cheque date to prove a debt existed.",
            "suggested_answer": "No. The cheque was issued specifically towards the outstanding invoices for goods delivered. The 'security cheque' defense is a standard afterthought to avoid liability. As per 'Sampelly Satyanarayana Rao', once a debt crystallizes, even a security cheque becomes enforceable."
        },
        "signature_dispute": {
            "question": "I suggest to you that the signature on this cheque is a forgery and you have filled in the amount yourself later. What do you say?",
            "objective": "To challenge the authenticity of the instrument.",
            "preparation": "Rely on the S.139 presumption; the burden is on the accused to prove forgery once they admit the account.",
            "suggested_answer": "The cheque was handed over to me duly signed by the Accused in my presence. As per Section 20 of the NI Act, an inchoate instrument gives the holder the authority to fill in the details. The signature matches the account record, and the burden of proving forgery lies entirely on the Accused."
        },
        "no_agreement": {
            "question": "There is no written loan agreement or receipt for this amount. On what basis are you claiming this was a 'legally enforceable debt'?",
            "objective": "To expose the lack of consideration.",
            "preparation": "Produce WhatsApp chats, emails, or witness statements that acknowledge the transaction.",
            "suggested_answer": "The contract between us was an oral agreement followed by performance. The issuance of the cheque in itself constitutes a written acknowledgement of the debt. Section 139 creates a mandatory presumption that the cheque was for the discharge of a debt."
        },
        "limitation_issue": {
            "question": "The notice was served on the 35th day, beyond the statutory 30 days. Isn't this entire prosecution non-maintainable?",
            "objective": "To get the case dismissed on technical jurisdiction.",
            "preparation": "Ensure your S.142(1)(b) Condonation Application is strong and the 'sufficient cause' is documented.",
            "suggested_answer": "The slight delay occurred due to bona fide reasons beyond my control, for which a formal application for condonation has already been filed under Section 142(1)(b). The law supports a liberal approach to condonation to ensure that substantive justice is not defeated by technicalities."
        }
    }

    @classmethod
    def generate_simulation(cls, concepts: List[Dict], amount: float) -> List[Dict[str, Any]]:
        simulation = []
        concept_names = {c["concept"] for c in concepts}
        
        # Add baseline questions
        simulation.append({
            "question": f"When and where exactly was this amount of ₹{amount:,.2f} handed over to the Accused?",
            "objective": "To test the consistency of your story (Factum of Grant).",
            "preparation": "Be specific about the date, time, and mode (Cash/Cheque/Transfer)."
        })

        # Add concept-specific attacks
        for concept in concept_names:
            if concept in cls.STRATEGY_MAP:
                simulation.append(cls.STRATEGY_MAP[concept])

        # High-value cash attack
        if amount > 100000 and "loan_via_bank" not in concept_names:
            simulation.append({
                "question": "Is it not true that according to Income Tax laws, any cash loan above ₹20,000 is illegal and hence not a 'legally enforceable debt'?",
                "objective": "To use S.269SS of the IT Act to invalidate the debt.",
                "preparation": "Cite 'Rangappa v. Mohan' — an IT violation does not automatically invalidate a S.138 prosecution."
            })

        return simulation[:5] # Return top 5 most critical
