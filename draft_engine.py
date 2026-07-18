import logging
from datetime import datetime
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
import os
logger = logging.getLogger(__name__)
templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader=FileSystemLoader(templates_dir))
def _get_criminal_precedent(offense_type: str) -> dict:
    if not offense_type:
        return {}
    try:
        import json
        kb_path = os.path.join(os.path.dirname(__file__), 'criminal_knowledge_base.json')
        with open(kb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            kb_models = data.get("vulnerability_models", {})
            for key, val in kb_models.items():
                if offense_type.upper() in key or key in offense_type.upper():
                    return val
    except (OSError, ValueError, TypeError) as e:
        logger.warning("Could not load criminal precedent data: %s", e)
    return {}
def decide_draft_type(score: int, concepts: List[Dict], case_data: Dict) -> str:
    concept_names = {c.get("concept", "") for c in concepts if isinstance(c, dict)}
    case_type = str(case_data.get("case_type", "")).upper()
    role = case_data.get("client_role", "Accused")
    if case_type == "CRIMINAL":
        if case_data.get("seek_quashing"):
            return "QUASHING_PETITION"
        if case_data.get("seek_suspension_sentence"):
            return "SUSPENSION_SENTENCE"
        if case_data.get("appeal_filed") or case_data.get("seek_appeal"):
            return "CRIMINAL_APPEAL"
        if case_data.get("recall_witness"):
            return "RECALL_WITNESS"
        if case_data.get("add_accused"):
            return "ADD_ACCUSED"
        if case_data.get("seek_exemption"):
            return "EXEMPTION_APPEARANCE"
        if case_data.get("seek_superdari"):
            return "SUPERDARI_APPLICATION"
        if case_data.get("file_protest_petition"):
            return "PROTEST_PETITION"
        if (role or "").lower() == "complainant":
            return "FIR_DRAFT"
        else:
            arrested = str(case_data.get("arrested_during_investigation")).lower()
            if arrested in ("yes", "true", "1") or case_data.get("in_custody"):
                return "REGULAR_BAIL"
            elif case_data.get("anticipate_arrest") or case_data.get("flight_risk"):
                return "ANTICIPATORY_BAIL"
            else:
                return "DISCHARGE_APPLICATION"
    if score < 40 and (role or "").lower() != "accused":
        return "LEGAL_OPINION"
    if not case_data.get("notice_sent"):
        return "LEGAL_NOTICE"
    if "limitation_issue" in concept_names:
        return "DELAY_CONDONATION"
    if score >= 65:
        return "COMPLAINT"
    if score < 45:
        if (role or "").lower() == "accused":
            if concept_names & {"security_cheque", "cheque_misuse", "signature_dispute", "no_agreement"}:
                return "DEFENCE_STRATEGY"
            return "DEFENCE_REPLY"
        return "LEGAL_OPINION"
    if 45 <= score < 65:
        return "SETTLEMENT"
    return "COMPLAINT"                                                      
def _header(title: str) -> str:
    line = "=" * 70
    return f"{line}\n{title}\n{line}"
def _case_meta(case_data: Dict):
    today = datetime.now().strftime("%d %B %Y")
    amount = case_data.get("amount", "________ (Amount)")
    if isinstance(amount, (int, float)) and amount > 0:
        if amount >= 100000:
            amount_str = f"Rs. {amount:,.0f}/- (Rupees {_num_to_words(int(amount))} only)"
        else:
            amount_str = f"Rs. {amount:,.0f}/-"
    else:
        amount_str = "Rs. ___________/-"
    return today, amount_str
def _num_to_words(n: int) -> str:
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    if n == 0: return "Zero"
    if n < 20: return ones[n]
    if n < 100: return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
    if n < 1000: return ones[n // 100] + " Hundred" + (" and " + _num_to_words(n % 100) if n % 100 else "")
    if n < 100000: return _num_to_words(n // 1000) + " Thousand" + (" " + _num_to_words(n % 1000) if n % 1000 else "")
    if n < 10000000: return _num_to_words(n // 100000) + " Lakh" + (" " + _num_to_words(n % 100000) if n % 100000 else "")
    return _num_to_words(n // 10000000) + " Crore" + (" " + _num_to_words(n % 10000000) if n % 10000000 else "")
def generate_legal_notice(case_data: Dict, tone: str = "standard") -> str:
    today, amount_str = _case_meta(case_data)
    is_aggressive = (tone or "").lower() == "aggressive"
    complainant = case_data.get("complainant_name") or case_data.get("complainantName") or "________ (Complainant Name)"
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Accused Name)"
    accused_addr = case_data.get("accused_address") or case_data.get("accusedAddress") or "________ (Accused Address)"
    cheque_no = case_data.get("cheque_number") or case_data.get("chequeNumber") or "________"
    cheque_date = case_data.get("cheque_date") or case_data.get("chequeDate") or "________ (Cheque Date)"
    bank = case_data.get("bank_name") or case_data.get("bankName") or "________ (Bank Name)"
    branch = case_data.get("branch_name") or case_data.get("branchName") or ""
    bank_full = f"{bank}, {branch}" if branch else bank
    dishonour_date = case_data.get("dishonour_date") or case_data.get("dishonourDate") or "________ (Date)"
    dishonour_reason = case_data.get("dishonour_reason") or case_data.get("dishonourReason") or "Funds Insufficient"
    description = case_data.get("description", "")
    purpose = case_data.get("purpose", "")
    transaction_nature = "a legally enforceable debt/liability"
    if "loan" in (description or "").lower() or "loan" in purpose.lower():
        transaction_nature = "a loan advanced"
    elif "goods" in (description or "").lower() or "supply" in purpose.lower():
        transaction_nature = "goods supplied"
    elif "service" in (description or "").lower():
        transaction_nature = "services rendered"
    elif purpose:
        transaction_nature = purpose[:100]
    transaction_nature = transaction_nature.rstrip('.')
    amount_val = float(case_data.get("cheque_amount") or case_data.get("amount") or 0)
    loan_via_bank = str(case_data.get("loan_via_bank", "yes")).lower()
    is_cash = loan_via_bank not in ("yes", "true", "1")
    if amount_val > 150000 and is_cash:
        transaction_nature += f". My client specifically asserts possessing sufficient source of funds to the tune of {amount_str} at the time of the transaction, advanced from accumulated personal savings/agricultural income, fully satisfying their financial capacity"
    template = env.get_template("legal_notice.jinja")
    return template.render(
        header=_header("LEGAL NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881"),
        today=today,
        amount_str=amount_str,
        complainant=complainant,
        accused=accused,
        accused_addr=accused_addr,
        cheque_no=cheque_no,
        cheque_date=cheque_date,
        bank_full=bank_full,
        dishonour_date=dishonour_date,
        dishonour_reason=dishonour_reason,
        transaction_nature=transaction_nature,
        tone=(tone or "").lower()
    )
def generate_certificate_63_bsa(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    complainant = case_data.get("complainant_name") or case_data.get("complainantName") or "________ (Your Name)"
    device_type = case_data.get("device_type", "Smartphone / Personal Computer")
    return f"""{_header("CERTIFICATE UNDER SECTION 63(4) OF THE BHARATIYA SAKSHYA ADHINIYAM (BSA)")}
IN THE COURT OF THE LEARNED JUDICIAL MAGISTRATE / METROPOLITAN MAGISTRATE
AT ________ (Court Location)
COMPLAINT NO.: _____ / {datetime.now().year}
IN THE MATTER OF:
{complainant}                                              ... COMPLAINANT
VERSUS
________ (Accused Name)                                             ... ACCUSED
AFFIDAVIT / CERTIFICATE UNDER SECTION 63(4) OF THE BHARATIYA SAKSHYA ADHINIYAM (BSA) FOR ADMISSIBILITY OF ELECTRONIC RECORDS
I, {complainant}, adult, residing at ________ (Address), do hereby solemnly affirm and state as under:
1. That I am the Complainant in the present case and I am fully conversant with the facts and circumstances of the case and am competent to depose to this affidavit.
2. That for the purpose of the present case, I am relying upon electronic records in the form of ________ (Digital Evidence) exchanged between me and the Accused.
3. That the said electronic records were produced by a computer/communication device, namely a {device_type}, which was owned/operated by me and was used regularly to store or process information for the purposes of my activities.
4. That during the period to which the electronic records relate, information was regularly fed into the device in the ordinary course of the said activities.
5. That throughout the material part of the said period, the computer/device was operating properly or, if not, that in respect of any period in which it was not operating properly or was out of operation during that part of that period, was not such as to affect the electronic record or the accuracy of its contents.
6. That the information contained in the electronic record reproduces or is derived from information fed into the device in the ordinary course of the said activities.
7. That the printouts/digital copies of the ________ (Digital Medium) records produced herewith as ANNEXURE-____ are true and faithful reproductions of the originals stored in the electronic device and have been prepared under my personal supervision.
8. That the contents of this certificate are true to the best of my knowledge and belief.
DEPONENT
VERIFICATION:
Verified at ________ (Place) on this {today} that the contents of the above affidavit are true and correct to my knowledge and nothing material has been concealed therefrom.
                                                            DEPONENT
"""
def generate_complaint(case_data: Dict, concepts: List[Dict], tone: str = "standard") -> str:
    today, amount_str = _case_meta(case_data)
    place_val = case_data.get("payee_bank_city") or ((case_data.get("complainant_address") or "").split(",")[-1].strip() if "," in case_data.get("complainant_address", "") else "") or "________ (Place)"
    is_aggressive = (tone or "").lower() == "aggressive"
    is_conciliatory = (tone or "").lower() == "conciliatory"
    complainant = case_data.get("complainant_name") or case_data.get("complainantName") or "________ (Complainant Name)"
    complainant_addr = case_data.get("complainant_address") or case_data.get("complainantAddress") or "________ (Complainant Address)"
    complainant_phone = case_data.get("complainant_phone") or case_data.get("complainantPhone") or "________ (Contact Number)"
    complainant_type = case_data.get("complainant_type", "Individual")
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Accused Name)"
    accused_addr = case_data.get("accused_address") or case_data.get("accusedAddress") or "________ (Accused Address)"
    accused_type = case_data.get("accused_type", "Individual")
    cheque_no = case_data.get("cheque_number") or case_data.get("chequeNumber") or "________"
    cheque_date = case_data.get("cheque_date") or case_data.get("chequeDate") or "________ (Cheque Date)"
    bank = case_data.get("bank_name") or case_data.get("bankName") or "________ (Bank Name)"
    branch = case_data.get("branch_name") or case_data.get("branchName") or ""
    bank_full = f"{bank}, {branch}" if branch else bank
    dishonour_date = case_data.get("dishonour_date") or case_data.get("dishonourDate") or "________ (Date)"
    dishonour_reason = case_data.get("dishonour_reason") or case_data.get("dishonourReason") or "Insufficient Funds"
    notice_date = case_data.get("notice_date") or case_data.get("noticeDate") or "________ (Notice Date)"
    court_name = case_data.get("court_name") or case_data.get("courtName") or "District Court"
    description = case_data.get("description", "")
    purpose = case_data.get("purpose", "")
    transaction_nature = "a legally enforceable debt"
    occupation = "business/profession"
    if "loan" in (description or "").lower() or "loan" in purpose.lower():
        transaction_nature = "a loan transaction"
        occupation = "lending/financing business"
    elif "goods" in (description or "").lower() or "supply" in purpose.lower():
        transaction_nature = "supply of goods"
        occupation = "trade and commerce"
    elif "service" in (description or "").lower():
        transaction_nature = "provision of services"
        occupation = "service provider"
    elif purpose:
        transaction_nature = purpose[:100]
    transaction_nature = transaction_nature.rstrip('.')
    occupation = occupation.rstrip('.')
    auth_clause = ""
    if complainant_type != "Individual":
        is_auth = case_data.get("is_authorized", False)
        auth_name = case_data.get("authorized_person_name", "________ (Name of Authorized Person)")
        board_res_date = case_data.get("board_resolution_date", "________ (Date prior to notice)")
        if is_auth:
            auth_clause = f"The Complainant is a {complainant_type} and is represented by its Authorized Signatory, Mr./Ms. {auth_name}, who is duly empowered by way of a Board Resolution dated {board_res_date} and a Letter of Authority, produced herewith as ANNEXURE-A. The said representative is fully conversant with the facts and circumstances of the present case and is competent to depose on behalf of the Complainant per the mandate of 'A.C. Narayanan vs. State of Maharashtra'."
        else:
            auth_clause = f"The Complainant is a {complainant_type} filing through its representative. [🚨 FATAL DEFECT WARNING: A.C. Narayanan Trap. You MUST annex a Board Resolution naming the exact person signing this complaint, and it MUST have been passed BEFORE the legal notice was sent]."
    liability_clause = ""
    if accused_type != "Individual":
        has_directors = case_data.get("directors_named", False)
        director_names = case_data.get("director_names") or case_data.get("accused_directors", "")
        director_roles = case_data.get("director_roles") or "Directors actively responsible for the day-to-day conduct and business of the accused company"
        resignation_date = case_data.get("director_resignation_date")
        cheque_date_val = case_data.get("cheque_date")
        resignation_averment = ""
        if resignation_date and cheque_date_val:
            resignation_averment = " The Complainant categorically asserts that at the time of the issuance of the subject cheque, the Accused Nos. 2 onwards were fully active Directors and had NOT resigned from the company, thereby attracting unmitigated liability."
        if has_directors and director_names:
            liability_clause = f"""3. THE VICARIOUS LIABILITY (SEC. 141):
    That the Accused No. 1 is a {accused_type}, and Accused Nos. 2 onwards, namely {director_names}, are the Directors/Partners/Officers of the said Accused No. 1.
    That at the time the offence was committed, the said Accused Nos. 2 onwards were in charge of, and were responsible to the Accused No. 1 for the conduct of its business. 
    Specifically, the Accused Nos. 2 onwards were, at the time of the commission of the offence, in charge of and responsible to the Accused No. 1 for the day-to-day conduct of its business, and are thus vicariously liable under Section 141 of the Negotiable Instruments Act, 1881.{resignation_averment}"""
        elif has_directors:
            liability_clause = f"3. THE VICARIOUS LIABILITY (SEC. 141): That the Accused No. 1 is a {accused_type} and the other Accused persons are its Directors/Officers who were in charge of and responsible for the conduct of the business (Exact roles: ________ (Specify Roles)) as per Section 141 of the NI Act."
        else:
            liability_clause = f"3. That the Accused is a {accused_type}. [🚨 FATAL DEFECT WARNING: You must name the specific Directors/Officers in charge of the company and describe their EXACT ROLES to satisfy Section 141 and avoid dismissal at the threshold stage per 'Aneeta Hada' ruling]."
    delay_para = ""
    within_30_days = str(case_data.get("within_30_days", "yes")).lower() in ("yes", "true", "1")
    if not within_30_days:
        delay_para = f"There has been a technical delay of ____ days in issuing the statutory demand notice, for which a condonation of delay application under Section 142(1)(b) of the NI Act has been filed herewith."
    if is_aggressive:
        debt_pleading = f"""The Complainant submits that the Accused is bound by an incontrovertible liability of {amount_str}, arising out of {transaction_nature}. 
    This liability is securely established by contemporaneous commercial records. The issuance of the subject cheque by the Accused was an explicit acknowledgment of this debt. Its subsequent dishonour is a clear demonstration of the Accused's mala fide intent to evade lawful obligations, compelling the Complainant to invoke the strict provisions of Section 138 of the NI Act."""
    else:
        debt_pleading = f"The Complainant states that the Accused is indebted to the Complainant for a sum of {amount_str} arising from {transaction_nature}. The said debt is legally enforceable and constitutes a valid liability under law."
    amount_val = float(case_data.get("cheque_amount") or case_data.get("amount") or 0)
    loan_via_bank = str(case_data.get("loan_via_bank", "yes")).lower()
    is_cash = loan_via_bank not in ("yes", "true", "1")
    if amount_val > 150000 and is_cash:
        debt_pleading += f" It is specifically averred that the Complainant possessed sufficient source of funds to the tune of {amount_str} at the time of the transaction, which was advanced from accumulated personal savings/agricultural income, and the Complainant has the requisite financial capacity, fully satisfying the legal mandate of 'Basalingappa v. Mudibasappa'."
    dynamic_rebuttal = ""
    failure_point = str(case_data.get("failure_point_injected", "")).lower()
    if "signature" in failure_point or "handwriting" in failure_point:
        dynamic_rebuttal = f"Any anticipated defence regarding variation in handwriting or ink is completely frivolous and legally untenable. Under Section 20 of the NI Act, the Accused had granted implied authority to the Complainant to fill the inchoate instrument, and the signature is explicitly admitted, barring any forensic delay tactics (Bir Singh v. Mukesh Kumar)."
    elif "limitation" in failure_point or "premature" in failure_point or "notice" in failure_point:
        dynamic_rebuttal = f"The Complainant has meticulously followed the statutory timeline matrix under Section 138/142 of the NI Act. Any alleged procedural irregularity is either curable or a hyper-technicality that does not defeat the substantive cause of justice."
    elif "debt" in failure_point or "capacity" in failure_point:
        dynamic_rebuttal = f"The underlying debt is crystallised and legally enforceable. The statutory presumption under Section 139 is firmly in favour of the Complainant, and the Accused cannot evade liability merely by raising bald denials without discharging the reverse onus of proof (Rangappa v. Mohan)."
    elif is_aggressive and score < 50:
        dynamic_rebuttal = f"The Complainant submits that any defence raised by the Accused is a mere afterthought designed to derail the summary procedure of Section 138. The Accused's silence during the statutory notice period operates as an implied admission of liability, precluding them from springing surprise defences at trial."
    if case_data.get("communication_records"):
        if is_aggressive:
            debt_pleading += f" The Accused's liability is further cemented by a clear digital trail (including WhatsApp/Email exchanges) wherein the debt stands unequivocally admitted. This electronic evidence, supported by a mandatory Section 63(4) BSA Certificate, renders any defense by the Accused legally untenable."
        elif is_conciliatory:
            debt_pleading += f" The Complainant states that the Accused has, in several WhatsApp and Email communications, recognized the outstanding liability. While the Complainant seeks legal recourse, they remain open to amicable resolution if the Accused is willing to perform their commitments."
        else:
            debt_pleading += f" The Accused has repeatedly acknowledged the said debt and liability via various communications, including WhatsApp messages and Emails, which are produced herewith along with the mandatory Certificate under Section 63(4) of the Bharatiya Sakshya Adhiniyam (BSA)."
    elif case_data.get("debt_proof_type") == "verbal_agreement" or case_data.get("agreement_type") == "Verbal Agreement":
        if is_aggressive:
            debt_pleading += " Despite the trust-based nature of the initial transaction, the Accused's subsequent conduct, the issuance of the cheque, and the resulting statutory presumption under Section 139 constitute an unequivocal admission of the debt, which the Accused is now dishonestly attempting to evade."
        elif is_conciliatory:
            debt_pleading += " The said transaction was entered into based on trust and a verbal agreement. The Complainant has repeatedly offered opportunities for repayment, which have unfortunately not materialized, leaving the Complainant no option but to seek judicial recourse."
        else:
            debt_pleading += " The said transaction was entered into based on mutual trust, and the Accused had verbally promised to repay the amount within the stipulated time."
    if case_data.get("handwriting_different") or case_data.get("signature_mismatch") or "material_alteration" in {c.get("concept", "") for c in concepts}:
        debt_pleading += "\n\nFurthermore, the Complainant categorically asserts that the cheque in question was issued by the Accused in discharge of a legally enforceable debt. Any subsequent claim by the Accused regarding differences in handwriting or ink age is entirely frivolous and a mere afterthought. The signature on the cheque is admitted, and under Section 20 of the Negotiable Instruments Act, the Complainant possessed the implied prima facie authority to fill the inchoate instrument. Any attempt to seek an FSL examination under Section 45 of the Indian Evidence Act is a dilatory tactic intended solely to derail the trial, and the Complainain pray that such requests be rejected."
    prayer_compensation = ""
    if is_aggressive:
        prayer_compensation = "(c) Direct the Accused to pay MAXIMUM INTERIM COMPENSATION of 20% under Section 143A of the NI Act, as the defense is ex-facie frivolous and dilatory;"
    elif is_conciliatory:
        prayer_compensation = "(c) Direct the Accused to pay INTERIM COMPENSATION under Section 143A of the NI Act, or encourage the parties to explore an amicable settlement / mediation under Section 89 of the CPC;"
    else:
        prayer_compensation = "(c) Direct the Accused to pay INTERIM COMPENSATION under Section 143A of the NI Act (20% of cheque amount);"
    year_val = datetime.now().year
    transaction_date = case_data.get("transaction_date") or case_data.get("transactionDate") or "________ (Transaction Date)"
    presentation_date = case_data.get("presentation_date") or case_data.get("presentationDate") or "________ (Presentation Date)"
    notice_received_date = case_data.get("notice_received_date") or case_data.get("noticeReceivedDate") or "________ (Notice Received Date)"
    filing_date = case_data.get("filing_date") or case_data.get("filingDate") or "________ (Filing Date)"
    index_section = f"""======================================================================
INDEX OF FILING BUNDLE
======================================================================
IN THE COURT OF THE METROPOLITAN MAGISTRATE AT {court_name}
COMPLAINT NO: _____ / {year_val}
IN THE MATTER OF:
{complainant}                                          ... COMPLAINANT
VERSUS
{accused}                                              ... ACCUSED
INDEX
S.NO.   PARTICULARS                                     PAGE NO.
1.      Synopsis and List of Dates                      1 - 2
2.      Memo of Parties                                 3
3.      Complaint under Section 138 of the NI Act       4 - 7
4.      Affidavit in support of the Complaint           8 - 9
5.      List of Documents / Annexures                   10
6.      Vakalatnama                                     11
Place: {place_val}                                      THROUGH:
Date: {today}                                           __________________, ADVOCATE
                                                        FOR COMPLAINANT
"""
    synopsis_section = f"""======================================================================
SYNOPSIS AND LIST OF DATES
======================================================================
SYNOPSIS:
The present complaint is being filed under Section 138 read with Section 141 of the Negotiable Instruments Act, 1881, against the Accused for the dishonour of cheque bearing No. {cheque_no} for Rs. {amount_str} due to "{dishonour_reason}". Despite the service of the statutory demand notice dated {notice_date}, the Accused has failed to clear the outstanding liability within the statutory period of 15 days, thereby committing an offence under the Negotiable Instruments Act, 1881.
LIST OF DATES:
DATE            PARTICULARS
{transaction_date}  The Accused approached the Complainant and underlying debt/liability of Rs. {amount_str} was established.
{cheque_date}   In discharge of the legal liability, the Accused issued cheque bearing No. {cheque_no} for Rs. {amount_str} drawn on {bank_full}.
{presentation_date} The cheque was presented for encashment by the Complainant.
{dishonour_date}    The cheque was returned/dishonoured by the bank with the memo citing "{dishonour_reason}".
{notice_date}   The Complainant sent the statutory demand notice under Section 138(b) of the NI Act to the Accused.
{notice_received_date}   The statutory demand notice was served/deemed served on the Accused.
{filing_date}   Filing of the present complaint before this Hon'ble Court.
Place: {place_val}                                      THROUGH:
Date: {today}                                           __________________, ADVOCATE
                                                        FOR COMPLAINANT
"""
    memo_section = f"""======================================================================
MEMO OF PARTIES
======================================================================
IN THE COURT OF THE METROPOLITAN MAGISTRATE AT {court_name}
COMPLAINT NO: _____ / {year_val}
IN THE MATTER OF:
COMPLAINANT:    {complainant}
                {complainant_addr}
                {complainant_phone}
                                                        ... COMPLAINANT
VERSUS
ACCUSED:        {accused}
                {accused_addr}
                                                        ... ACCUSED
Place: {place_val}                                      THROUGH:
Date: {today}                                           __________________, ADVOCATE
                                                        FOR COMPLAINANT
"""
    affidavit_section = f"""======================================================================
AFFIDAVIT IN SUPPORT OF THE COMPLAINT
======================================================================
IN THE COURT OF THE METROPOLITAN MAGISTRATE AT {court_name}
COMPLAINT NO: _____ / {year_val}
IN THE MATTER OF:
{complainant}                                          ... COMPLAINANT
VERSUS
{accused}                                              ... ACCUSED
AFFIDAVIT
I, {complainant}, son/daughter/representative of ________, aged about ____ years, residing/having office at {complainant_addr}, do hereby solemnly affirm and state as under:
1. That I am the Complainant in the accompanying complaint and am fully conversant with the facts of the case, and as such, competent to depose to this affidavit.
2. That the accompanying Complaint under Section 138 of the Negotiable Instruments Act, 1881 has been drafted under my instructions, the contents of which may be read as part and parcel of this affidavit for the sake of brevity.
3. That the Accused issued the cheque No. {cheque_no} in discharge of a legally enforceable debt, which was dishonoured upon presentation, and the Accused failed to make payment despite receipt of the statutory demand notice.
4. That the annexures filed along with the complaint are true copies of their respective originals.
                                                        DEPONENT
VERIFICATION:
Verified at {place_val} on this {today} that the contents of the above affidavit are true and correct to the best of my knowledge and belief, and nothing material has been concealed therefrom.
                                                        DEPONENT
"""
    complaint_body = f"""======================================================================
COMPLAINT UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881
======================================================================
IN THE COURT OF THE METROPOLITAN MAGISTRATE
AT {court_name}
COMPLAINT NO.: _____ / {year_val}
IN THE MATTER OF:
COMPLAINANT:    {complainant}
                {complainant_addr}
                {complainant_phone}
                                                        ... COMPLAINANT
VERSUS
ACCUSED:        {accused}
                {accused_addr}
                                                        ... ACCUSED
                THROUGH: __________________, ADVOCATE
                FOR THE COMPLAINANT
COMPLAINT U/S 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881
RESPECTFULLY SHOWETH:
1. THE COMPLAINANT:
   The Complainant, {complainant}, is engaged in the business/occupation of {occupation}. {auth_clause}
2. THE ACCUSED:
   The Accused, {accused}, residing at {accused_addr}, entered into the underlying business transaction/relationship with the Complainant, as detailed hereinafter.
{liability_clause}
4. THE LEGALLY ENFORCEABLE DEBT:
   {debt_pleading}
5. ISSUANCE OF CHEQUE:
   In discharge of the aforesaid legal liability, the Accused issued a cheque bearing No. {cheque_no}, dated {cheque_date}, drawn on {bank_full}, for an amount of {amount_str} in favour of the Complainant.
6. PRESENTATION AND DISHONOUR:
   The Complainant duly presented the said cheque for encashment through its banker. However, the said cheque was returned/dishonoured on {dishonour_date} with the bank memo citing "{dishonour_reason}", thereby constituting an offence under Section 138 of the NI Act, 1881.
7. STATUTORY DEMAND NOTICE AND ACCUSED'S DEFAULT:
   As mandated under Section 138(b) of the NI Act, 1881, the Complainant sent a legal demand notice dated {notice_date} to the Accused at their correct and known address via Registered Post (AD)/Speed Post, demanding payment of the cheque amount of {amount_str} within 15 days of receipt of the notice. The notice was duly served/deemed to be served upon the Accused. Despite receipt/deemed receipt of the notice, the Accused failed to make the payment of the cheque amount within the statutory period of 15 days, which expired on ________. The Accused has thus committed an offence punishable under Section 138 of the Negotiable Instruments Act, 1881. {delay_para} {dynamic_rebuttal}
8. JURISDICTION:
   This Hon'ble Court has territorial jurisdiction to entertain and try this Complaint as the cheque in question was presented for encashment at {bank_full}, which is situated within the territorial limits of this Court, as per the law laid down by the Hon'ble Supreme Court in Dashrath Rupsingh Rathod vs. State of Maharashtra.
9. PRAYER:
   It is, therefore, most respectfully prayed that this Hon'ble Court may be pleased to:
   (a) Take cognizance of the offence committed by the Accused under Section 138 of the NI Act, 1881;
   (b) Issue summons/process to the Accused to face trial;
   (c) Direct the Accused to pay INTERIM COMPENSATION of 20% of the cheque amount to the Complainant as per Section 143A of the NI Act (as amended in 2018);
   (d) On conviction, sentence the Accused to imprisonment for the maximum term and/or impose a fine of twice the cheque amount to meet the ends of justice; and
   (e) Pass such other order(s) as this Hon'ble Court may deem fit in the interest of justice.
LIST OF ANNEXURES:
ANNEXURE-A: Original Board Resolution / Letter of Authority (If applicable)
ANNEXURE-B: Original Dishonoured Cheque No. {cheque_no}
ANNEXURE-C: Original Bank Dishonour Memo dated {dishonour_date}
ANNEXURE-D: Office Copy of Legal Demand Notice dated {notice_date}
ANNEXURE-E: Original Postal Receipt and A.D. Card / Tracking Report
ANNEXURE-F: Section 63(4) BSA Certificate for WhatsApp/Email records (Mandatory)
VERIFICATION:
I, {complainant}, do hereby solemnly verify that the contents of the above Complaint are true and correct to the best of my knowledge, information, and belief. Nothing material has been concealed therefrom, and all supporting documents are annexed herewith.
Place: {place_val}
Date: {today}
                                                        {complainant}
                                                        (Complainant)
"""
    return f"{index_section}\n\n{synopsis_section}\n\n{memo_section}\n\n{complaint_body}\n\n{affidavit_section}"
def generate_defence_strategy(case_data: Dict, concepts: List[Dict], score: int) -> str:
    today, amount_str = _case_meta(case_data)
    concept_names = {c.get("concept", "") for c in concepts if isinstance(c, dict)}
    defences_identified = []
    legal_arguments = []
    if "security_cheque" in concept_names:
        defences_identified.append("Cheque Given as Security — Not for Debt Discharge")
        legal_arguments.append(
            "The cheque in question was given purely as a security/collateral cheque and not in discharge of any legally enforceable debt. As per the Hon'ble Supreme Court in Indus Airways Pvt. Ltd. v. Magnum Aviation Pvt. Ltd. (2014), a security cheque falls outside the scope of Section 138 NI Act, as there is no legally enforceable debt against which the cheque was drawn."
        )
    if "signature_dispute" in concept_names:
        defences_identified.append("Signature on Cheque Not Genuine — Forgery Alleged")
        legal_arguments.append(
            "The Accused specifically denies that the signature on the dishonoured cheque is his/her genuine signature. It is submitted that the signature has been forged/fabricated. The Complainant bears the burden of proving the signature's authenticity. A handwriting expert's examination is essential. Refer: Modi Cements Ltd. v. Kuchil Kumar Nandi (2013) — mere presumption cannot override a bona fide denial of signature."
        )
    if "no_agreement" in concept_names:
        defences_identified.append("Absence of Written Agreement — Debt Not Established")
        legal_arguments.append(
            "There is no written agreement, contract of loan, or documentary evidence establishing the alleged debt. Without a legally documented basis, the Complainant cannot invoke the presumption under Section 139 NI Act. Kumar Exports v. Sharma Carpets (2009) — the presumption under S.139 can be rebutted by showing absence of consideration."
        )
    if "no_debt_proof" in concept_names:
        defences_identified.append("No Legally Enforceable Debt or Liability Exists")
        legal_arguments.append(
            "The Accused denies existence of any legally enforceable debt or liability. The Complainant has failed to produce any loan agreement, bank transfer records, invoice, or corroborating evidence. Section 138 NI Act requires the cheque to be drawn 'in discharge of any debt or other liability' — absence of underlying debt is a complete defence."
        )
    if "cheque_misuse" in concept_names:
        defences_identified.append("Cheque Was Misused / Misappropriated")
        legal_arguments.append(
            "The cheque was issued for a specific, limited purpose and has been misused/misappropriated by the Complainant. The Accused submits that the cheque was not issued in discharge of the liability alleged. The Complainant's act of presenting the cheque for encashment beyond its intended purpose constitutes dishonest misuse."
        )
    if len(defences_identified) > 1:
        synthesis = "COMPOSITE DEFENCE STRATEGY:\nThe Accused has a multi-tiered defence. We will primarily challenge the existence of the legally enforceable debt, whilst simultaneously disputing the mechanics of the cheque's execution. This dual-pronged attack forces the Complainant to prove both the financial transaction and the instrument's integrity beyond reasonable doubt."
        defences_identified.insert(0, synthesis)
    defences_text = "\n".join([f"   {i+1}. {d}" if not str(d).startswith("COMPOSITE") else f"   {d}" for i, d in enumerate(defences_identified)]) if defences_identified else "   (To be determined based on full case facts)"
    arguments_text = "\n\n".join([f"   {i+1}. {a}" for i, a in enumerate(legal_arguments)]) if legal_arguments else "   (Legal arguments to be elaborated based on specific case documents)"
    return f"""{_header("DEFENCE STRATEGY BRIEF — SECTION 138 NI ACT")}
Date: {today}
Case Strength Score: {score}/100
Classification: DEFENCE-SIDED (ACCUSED STRATEGY)
DEFENCES IDENTIFIED:
{defences_text}
DETAILED LEGAL ARGUMENTS:
{arguments_text}
EVIDENTIARY STRATEGY:
   1. Dispute the genuineness and purpose of the cheque through sworn affidavit.
   2. File application under Section 91 CrPC to call for original transaction documents.
   3. Commission handwriting expert if signature is disputed.
   4. Cross-examine Complainant on the nature, purpose, and quantum of alleged debt.
   5. Produce all communications (WhatsApp, email, letters) showing the true purpose of the cheque.
PROCEDURAL STEPS:
   1. Appear before Court on date of first hearing; do NOT ignore summons.
   2. File detailed reply to complaint on first or second date.
   3. Apply for bail (if required) and obtain anticipatory bail preemptively.
   4. File application under Section 145(2) NI Act to cross-examine the Complainant.
   5. Consider filing complaint under Section 500 IPC (defamation) if allegations are false.
SETTLEMENT ASSESSMENT:
   Given the case strength score of {score}/100, a negotiated settlement may be advisable to avoid
   prolonged litigation risk. The Accused should evaluate a commercial resolution.
DISCLAIMER: This is an AI-generated preliminary strategy document. Consult a qualified advocate before taking any legal action.
WARNING: Do NOT file raw AI output. You MUST 'humanize' the draft to avoid 'Cookie-Cutter' objections from the Magistrate, and verify ALL citations to prevent 'Phantom Precedent' penalties (Professional Misconduct/₹50k fine).
"""
def generate_discharge_application(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Accused Name)"
    return f"""{_header("DISCHARGE APPLICATION — SECTION 227/239 CrPC / 250/262 BNSS")}
IN THE COURT OF ________ (Sessions Judge / Magistrate), ________ (Location)
IN THE MATTER OF:
STATE                                                      ... PROSECUTION
VERSUS
{accused}                                                  ... ACCUSED
APPLICATION FOR DISCHARGE OF THE ACCUSED
MOST RESPECTFULLY SHOWETH:
1. That the police have filed a charge sheet against the Accused. However, a bare perusal of the charge sheet and accompanying documents under Section 207 CrPC reveals that no prima facie case is made out.
2. GRAVE SUSPICION LACKING:
   As per the Hon'ble Supreme Court in 'Union of India v. Prafulla Kumar Samal', the Court must evaluate if the materials create a 'grave suspicion'. Here, the evidence is entirely hearsay, legally inadmissible, and fundamentally flawed.
3. ABSENCE OF MENS REA:
   Even if the allegations are taken at face value (without admitting them), the essential ingredients of the offence, particularly the requisite mens rea, are completely absent.
PRAYER:
It is prayed that the charges against the Accused be dropped and the Accused be discharged to prevent the abuse of the process of the Court.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_quashing_petition(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Accused Name)"
    offense = case_data.get("offense_type", "General")
    fir_no = case_data.get("fir_no", "________")
    fir_date = case_data.get("fir_date", "________ (Date)")
    police_station = case_data.get("police_station", "________ (Police Station)")
    state_name = case_data.get("state_name", "________ (State Name)")
    return f"""{_header("QUASHING PETITION — SECTION 482 CrPC / 528 BNSS")}
IN THE HON'BLE HIGH COURT OF {state_name}
CRIMINAL MISC. PETITION NO. ______ OF {datetime.now().year}
IN THE MATTER OF:
{accused}                                                  ... PETITIONER
VERSUS
STATE OF {state_name} & ANR.                               ... RESPONDENTS
PETITION UNDER SECTION 482 OF THE CODE OF CRIMINAL PROCEDURE FOR QUASHING OF FIR NO. {fir_no} DATED {fir_date} U/S {offense} P.S. {police_station} AND ALL CONSEQUENTIAL PROCEEDINGS
MOST RESPECTFULLY SHOWETH:
1. That the present petition is being filed invoking the inherent jurisdiction of this Hon'ble Court to prevent the abuse of the process of law and to secure the ends of justice.
2. MALA FIDE IMPLICATION (BHAJAN LAL GUIDELINES):
   That the FIR has been instituted with an ulterior motive to wreak vengeance on the Petitioner due to a private and personal dispute. The allegations, even if taken on their face value and accepted in their entirety, do not prima facie constitute any offence or make out a case against the Petitioner, falling squarely within Parameters 1 and 7 laid down in 'State of Haryana v. Bhajan Lal'.
3. PURELY CIVIL DISPUTE GIVEN CRIMINAL COLOR:
   That the crux of the dispute between the parties is inherently civil/commercial in nature (e.g., breach of contract/partnership dispute). The Complainant is attempting to weaponize the criminal justice system to exert pressure for a civil recovery, which is strictly deprecated by the Hon'ble Supreme Court in 'Indian Oil Corp v. NEPC India'.
PRAYER:
It is prayed that this Hon'ble Court may be pleased to quash the impugned FIR No. ________ (FIR No.) and all consequential proceedings emanating therefrom.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_suspension_sentence(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Appellant Name)"
    return f"""{_header("APPLICATION FOR SUSPENSION OF SENTENCE — SECTION 389 CrPC / 430 BNSS")}
IN THE COURT OF ________ (Sessions Judge / High Court), ________ (Location)
CRIMINAL MISC. APPLICATION IN CRIMINAL APPEAL NO. ______ OF {datetime.now().year}
IN THE MATTER OF:
{accused}                                                  ... APPELLANT
VERSUS
STATE OF ________ (State Name)                                      ... RESPONDENT
APPLICATION UNDER SECTION 389 OF CrPC FOR SUSPENSION OF SENTENCE AND GRANT OF BAIL PENDING APPEAL
MOST RESPECTFULLY SHOWETH:
1. That the Appellant has preferred the accompanying Criminal Appeal challenging the judgment and order of conviction dated ________ (Date) passed by the Ld. Trial Court, whereby the Appellant has been sentenced to undergo rigorous imprisonment for ________ (X) years.
2. SHORT SENTENCE:
   That the sentence imposed is a short-term sentence (less than 3/5 years). As per the settled law, where the appeal is not likely to be heard in the near future and the sentence is short, the sentence ought to be suspended pending appeal to prevent the right of appeal from becoming illusory.
3. GOOD CONDUCT ON TRIAL BAIL:
   That the Appellant was on bail throughout the trial and never misused the liberty granted to him/her.
PRAYER:
It is prayed that the execution of the sentence be suspended and the Appellant be enlarged on bail pending the final disposal of the accompanying appeal.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_criminal_appeal(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Appellant Name)"
    offense = case_data.get("offense_type", "General")
    return f"""{_header("CRIMINAL APPEAL — SECTION 374 CrPC / 415 BNSS")}
IN THE COURT OF ________ (Sessions Judge / High Court), ________ (Location)
CRIMINAL APPEAL NO. ______ OF {datetime.now().year}
IN THE MATTER OF:
{accused}                                                  ... APPELLANT
VERSUS
STATE OF ________ (State Name)                                      ... RESPONDENT
CRIMINAL APPEAL UNDER SECTION 374 OF THE CrPC AGAINST THE JUDGMENT OF CONVICTION DATED ________ (Date) PASSED IN CASE NO. ________ (Case No.) U/S {offense}
MOST RESPECTFULLY SHOWETH:
1. That the present appeal is directed against the impugned judgment and order of sentence dated ________ (Date), whereby the Ld. Trial Court has erroneously convicted the Appellant based on conjectures and surmises.
GROUNDS OF APPEAL:
A. BECAUSE the Ld. Trial Court completely failed to appreciate the glaring material contradictions and improvements in the testimonies of the prosecution witnesses (PW-1 and PW-2).
B. BECAUSE the prosecution failed to prove the case beyond a reasonable doubt. The benefit of doubt, which is a constitutional right of the Accused, was unjustly denied.
C. BECAUSE the defence evidence (DW-1) was arbitrarily discarded without assigning cogent legal reasons.
PRAYER:
It is prayed that the impugned judgment of conviction and order of sentence be set aside and the Appellant be acquitted of all charges.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_recall_witness(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Applicant Name)"
    return f"""{_header("APPLICATION TO RECALL WITNESS — SECTION 311 CrPC / 348 BNSS")}
IN THE COURT OF ________ (Sessions Judge / Magistrate), ________ (Location)
IN THE MATTER OF:
STATE                                                      ... PROSECUTION
VERSUS
{accused}                                                  ... ACCUSED
APPLICATION UNDER SECTION 311 OF THE CrPC FOR RECALLING PROSECUTION WITNESS (PW-________ (X)) FOR FURTHER CROSS-EXAMINATION
MOST RESPECTFULLY SHOWETH:
1. That the present case is pending adjudication before this Hon'ble Court and is fixed for ________ (Next Stage) on ________ (Next Date).
2. ESSENTIAL FOR JUST DECISION:
   That subsequent to the cross-examination of PW-________ (X) (________ (Witness Name)), certain material documents/facts have surfaced which go to the root of the matter. Recalling the witness is essential for arriving at a just decision of the case as mandated by the second part of Section 311 CrPC.
3. NO DELAY TACTIC:
   That this application is bona fide and not filed to protract the trial. The defence will be severely prejudiced if the opportunity to confront the witness with these newly discovered facts is denied.
PRAYER:
It is prayed that PW-________ (X) be recalled for further cross-examination in the interest of justice and fair trial.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_add_accused(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    complainant = case_data.get("complainant_name") or case_data.get("complainantName") or "________ (Complainant Name)"
    return f"""{_header("APPLICATION TO SUMMON ADDITIONAL ACCUSED — SECTION 319 CrPC / 358 BNSS")}
IN THE COURT OF ________ (Sessions Judge / Magistrate), ________ (Location)
IN THE MATTER OF:
{complainant} / STATE                                      ... COMPLAINANT/PROSECUTION
VERSUS
________ (Current Accused) & ORS.                                   ... ACCUSED
APPLICATION UNDER SECTION 319 OF THE CrPC FOR SUMMONING ADDITIONAL ACCUSED PERSON
MOST RESPECTFULLY SHOWETH:
1. That the trial in the present matter is ongoing. During the recording of evidence of PW-________ (X), specific and overt acts have been attributed to one Mr./Ms. ________ (Name of Proposed Accused), who was not charge-sheeted by the police.
2. STRONG PRIMA FACIE EVIDENCE:
   That the testimony before this Hon'ble Court establishes a strong prima facie case against the proposed accused. As per the Constitution Bench ruling in 'Hardeep Singh v. State of Punjab', the evidence is more than a mere probability of complicity.
PRAYER:
It is prayed that Mr./Ms. ________ (Name) be summoned to stand trial alongside the current accused persons, to meet the ends of justice.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_exemption_appearance(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Accused Name)"
    return f"""{_header("EXEMPTION FROM PERSONAL APPEARANCE — SECTION 205/317 CrPC / 355 BNSS")}
IN THE COURT OF ________ (Sessions Judge / Magistrate), ________ (Location)
IN THE MATTER OF:
STATE                                                      ... PROSECUTION
VERSUS
{accused}                                                  ... ACCUSED
APPLICATION FOR EXEMPTION FROM PERSONAL APPEARANCE OF THE ACCUSED FOR TODAY
MOST RESPECTFULLY SHOWETH:
1. That the Accused is a law-abiding citizen and has been regularly appearing before this Hon'ble Court.
2. UNAVOIDABLE REASON:
   That today, the Accused is unable to attend the Court due to ________ (Reason for Absence). A medical certificate/proof is annexed herewith.
3. NO PREJUDICE TO TRIAL:
   That the absence of the Accused is neither intentional nor deliberate. The Accused's counsel is present and the identity of the Accused is not disputed. The trial will not be impeded by his/her absence today.
PRAYER:
It is prayed that the personal appearance of the Accused be exempted for today only.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_superdari_application(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    applicant = case_data.get("complainant_name") or case_data.get("accused_name") or "________ (Applicant Name)"
    return f"""{_header("SUPERDARI APPLICATION (RELEASE OF PROPERTY) — SECTION 451 CrPC / 497 BNSS")}
IN THE COURT OF ________ (Magistrate), ________ (Location)
IN THE MATTER OF:
{applicant}                                                ... APPLICANT
VERSUS
STATE                                                      ... PROSECUTION
APPLICATION UNDER SECTION 451 OF THE CrPC FOR RELEASE OF VEHICLE / PROPERTY ON SUPERDARI
MOST RESPECTFULLY SHOWETH:
1. That the Applicant is the registered owner of the vehicle ________ (Make/Model) bearing Registration No. ________ (Reg No.), which was seized by the police in connection with the present FIR.
2. DEPRECIATION OF ASSET:
   That the vehicle is currently parked at the police station, exposed to extreme weather, and is rapidly deteriorating in value and mechanical condition, as noted by the Hon'ble Supreme Court in 'Sunderbhai Ambalal Desai v. State of Gujarat'.
3. UNDERTAKING:
   That the Applicant undertakes to produce the vehicle before this Hon'ble Court as and when directed, and shall not alter its color or sell it without the prior permission of the Court.
PRAYER:
It is prayed that the seized vehicle be released to the Applicant on Superdari upon furnishing a suitable indemnity bond.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_protest_petition(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    complainant = case_data.get("complainant_name") or case_data.get("complainantName") or "________ (Complainant Name)"
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Accused Name)"
    return f"""{_header("PROTEST PETITION AGAINST CLOSURE REPORT")}
IN THE COURT OF ________ (Magistrate), ________ (Location)
IN THE MATTER OF:
{complainant}                                              ... COMPLAINANT
VERSUS
{accused}                                                  ... PROPOSED ACCUSED
PROTEST PETITION AGAINST THE FINAL REPORT (CLOSURE REPORT) FILED BY THE POLICE U/S 173 CrPC
MOST RESPECTFULLY SHOWETH:
1. That the police have filed a Closure Report / B-Summary in FIR No. ________ (FIR No.), erroneously concluding that no case is made out against the Accused.
2. TAINTED INVESTIGATION:
   That the Investigating Officer (IO) has acted in a highly partisan manner and deliberately ignored the direct evidence, medical reports, and independent eyewitness statements provided by the Complainant.
3. PRIMA FACIE CASE EXISTS:
   That despite the defective investigation, the materials on record clearly disclose the commission of cognizable offences. This Hon'ble Court has the power under Section 190(1)(b) CrPC to disagree with the police report, take cognizance, and summon the Accused.
PRAYER:
It is prayed that this Hon'ble Court reject the Closure Report, take cognizance of the offences, and summon the Accused to face trial.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
class DraftEngine:
    @staticmethod
    def generate_opinion(analysis_result: Dict[str, Any]) -> str:
        score = analysis_result.get("score", 0)
        concepts = analysis_result.get("concepts", [])
        case_data = analysis_result.get("case_data", {})
        draft_type = decide_draft_type(score, concepts, case_data)
        return DraftEngine.generate_draft(draft_type, score, concepts, case_data)
    @staticmethod
    def generate_draft(draft_type: str, score: int, concepts: List[Dict], case_data: Dict) -> str:
        offensive_drafts = ["LEGAL_NOTICE", "COMPLAINT", "FIR_DRAFT"]
        is_offensive = draft_type in offensive_drafts
        has_fatal_defect = case_data.get("fatal_defect")
        if is_offensive and (score < 40 or has_fatal_defect):
            reason = has_fatal_defect if has_fatal_defect else "Survivability score below 40."
            return f"DRAFT GENERATION BLOCKED.\n\nReason: {reason}\n\nJudiQ refuses to generate {draft_type} due to critical strategic or procedural defects that make the filing legally untenable or frivolous. Please review the Executive Summary."
        tone = case_data.get("draft_tone", "standard")
        if draft_type == "FIR_DRAFT":
            return generate_fir_draft(case_data, concepts)
        elif draft_type == "REGULAR_BAIL":
            return generate_regular_bail(case_data)
        elif draft_type == "ANTICIPATORY_BAIL":
            return generate_anticipatory_bail(case_data)
        elif draft_type == "DISCHARGE_APPLICATION":
            return generate_discharge_application(case_data)
        elif draft_type == "QUASHING_PETITION":
            return generate_quashing_petition(case_data)
        elif draft_type == "SUSPENSION_SENTENCE":
            return generate_suspension_sentence(case_data)
        elif draft_type == "CRIMINAL_APPEAL":
            return generate_criminal_appeal(case_data)
        elif draft_type == "RECALL_WITNESS":
            return generate_recall_witness(case_data)
        elif draft_type == "ADD_ACCUSED":
            return generate_add_accused(case_data)
        elif draft_type == "EXEMPTION_APPEARANCE":
            return generate_exemption_appearance(case_data)
        elif draft_type == "SUPERDARI_APPLICATION":
            return generate_superdari_application(case_data)
        elif draft_type == "PROTEST_PETITION":
            return generate_protest_petition(case_data)
        if draft_type == "LEGAL_NOTICE":
            return generate_legal_notice(case_data, tone=tone)
        elif draft_type == "COMPLAINT":
            return generate_complaint(case_data, concepts, tone=tone)
        elif draft_type in ("CERTIFICATE_BSA", "CERTIFICATE_65B"):
            return generate_certificate_63_bsa(case_data)
        elif draft_type in ("DEFENCE_STRATEGY", "DEFENCE_REPLY"):
            return generate_defence_strategy(case_data, concepts, score)
        elif draft_type == "SETTLEMENT":
            return generate_settlement_draft(case_data, score)
        elif draft_type == "DELAY_CONDONATION":
            return generate_delay_condonation(case_data)
        elif draft_type == "APPLICATION_143A":
            return generate_application_143a(case_data)
        else:
            return generate_legal_opinion(score, concepts, case_data)
def generate_settlement_draft(case_data: Dict, score: int) -> str:
    return "MEMORANDUM OF SETTLEMENT\n\nThis memorandum of settlement is generated based on the case facts. A formal mediator or counsel should review the terms."
def generate_fir_draft(case_data: Dict, concepts: List[Dict]) -> str:
    return "FIRST INFORMATION REPORT (FIR) DRAFT\n\nDrafted based on core criminal facts."
def generate_regular_bail(case_data: Dict) -> str:
    return "APPLICATION FOR REGULAR BAIL\n\nUnder Section 439 of the Code of Criminal Procedure."
def generate_anticipatory_bail(case_data: Dict) -> str:
    return "APPLICATION FOR ANTICIPATORY BAIL\n\nUnder Section 438 of the Code of Criminal Procedure."
def generate_delay_condonation(case_data: Dict) -> str:
    return "APPLICATION FOR CONDONATION OF DELAY\n\nUnder Section 5 of the Limitation Act, 1963 read with Section 142(b) of the Negotiable Instruments Act, 1881.\n\n[DRAFT DETAILS TO BE FILLED]"
def generate_application_143a(case_data: Dict) -> str:
    return "APPLICATION UNDER SECTION 143A OF THE NEGOTIABLE INSTRUMENTS ACT\n\nFor direction to the Accused to pay interim compensation.\n\n[DRAFT DETAILS TO BE FILLED]"
def generate_legal_opinion(score: int, concepts: List[Dict], case_data: Dict) -> str:
    today, amount_str = _case_meta(case_data)
    return f"""{_header("PROFESSIONAL LEGAL OPINION — ADVERSARIAL ASSESSMENT")}
Date: {today}
Case Viability Score: {score}/100
Subject: Strategic Assessment of Cheque Dishonour Case involving {amount_str}
1. EXECUTIVE SUMMARY:
   Based on the current evidentiary configuration, this case has a viability score of {score}%. 
   { "The case is structurally sound but requires procedural precision." if score > 70 else "The case exhibits significant structural vulnerabilities that may impede successful prosecution." }
2. KEY RISK VECTORS:
   The following legal concepts were detected which directly impact the litigation posture:
   { "\n".join([f"   - {c.get('concept', '').replace('_', ' ').upper()} (Impact: High)" for c in concepts if c.get('confidence', 0) > 0.7]) or "   - No high-confidence risks detected." }
3. STRATEGIC RECOMMENDATION:
   { "Proceed with the filing of a Criminal Complaint under Section 138 NI Act whilst ensuring all statutory timelines are strictly met." if score > 60 else "Immediate litigation is not recommended. Focus on evidentiary remediation or explore a mediated settlement (Section 147 NI Act) to mitigate costs." }
4. LITIGATION DIRECTIVE:
   { "1. Prepare and file the complaint within the 30-day limitation window from notice service.\\n   2. Confirm original documents are available for verification." if score > 60 else "1. Issue a remedial notice or seek compounding to avoid dismissal.\\n   2. Collect additional documentary evidence to verify transaction details." }
DISCLAIMER: This is an AI-generated preliminary strategy document. Consult a qualified advocate before taking any legal action.
WARNING: Do NOT file raw AI output. You MUST 'humanize' the draft to avoid 'Cookie-Cutter' objections from the Magistrate, and verify ALL citations to prevent 'Phantom Precedent' penalties (Professional Misconduct/₹50k fine).
"""
