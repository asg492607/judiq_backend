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
    role = case_data.get("client_role", case_data.get("perspective", "creditor"))
    if case_type == "SARFAESI":
        perspective = str(case_data.get("perspective", "creditor")).lower()
        if perspective in ["borrower", "debtor", "applicant"]:
            return "SARFAESI_SEC_17_SA_PETITION"
        if case_data.get("sa_filing_date"):
            return "SARFAESI_WRITTEN_STATEMENT"
        if case_data.get("seek_section_14"):
            return "SARFAESI_SEC_14_APPLICATION"
        if case_data.get("borrower_representation_date") and not case_data.get("bank_reply_13_3a_date"):
            return "SARFAESI_13_3A_REPLY"
        if case_data.get("notice_13_2_date") and not case_data.get("possession_13_4_date"):
            return "SARFAESI_13_4_POSSESSION_NOTICE"
        return "SARFAESI_13_2_NOTICE"
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

def _safe_float(val) -> float:
    if val in (None, "", "________ (Amount)"):
        return 0.0
    if isinstance(val, str):
        val = val.replace(",", "").replace("Rs.", "").replace(" ", "").strip()
        try:
            return float(val)
        except ValueError:
            return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0
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
def verify_s138_timeline_for_draft(case_data: Dict[str, Any]) -> Dict[str, Any]:
    from utils import parse_date, days_between
    cheque_date = case_data.get("cheque_date") or case_data.get("chequeDate")
    presentation_date = case_data.get("presentation_date") or case_data.get("presentationDate") or case_data.get("dishonour_date") or case_data.get("dishonourDate")
    dishonour_date = case_data.get("dishonour_date") or case_data.get("dishonourDate")
    notice_date = case_data.get("notice_date") or case_data.get("noticeDate")
    notice_received_date = case_data.get("notice_received_date") or case_data.get("noticeReceivedDate") or case_data.get("notice_delivery_date")
    filing_date = case_data.get("filing_date") or case_data.get("filingDate")

    res = {
        "is_cheque_valid": True,
        "is_notice_valid": True,
        "is_complaint_timely": True,
        "is_premature": False,
        "is_delay": False,
        "delay_days": 0,
        "notice_dispatch_days": None,
        "cheque_presentation_days": None,
        "audit_lines": [],
        "warnings": []
    }

    # 1. Cheque Validity (Max 90 days from cheque date)
    if cheque_date and presentation_date:
        gap = days_between(cheque_date, presentation_date)
        res["cheque_presentation_days"] = gap
        if gap is not None and gap > 92:
            res["is_cheque_valid"] = False
            msg = f"Cheque presented on day {gap} (> 90 days statutory validity from cheque date {cheque_date})."
            res["warnings"].append(msg)
            res["audit_lines"].append(f"[🚨 TIMELINE BREACH - CHEQUE EXPIRED]: {msg}")
        elif gap is not None and gap >= 0:
            res["audit_lines"].append(f"[✓ CHEQUE VALIDITY]: Cheque presented within {gap} days of issue.")

    # 2. Demand Notice Dispatch (Max 30 days from dishonour date)
    if dishonour_date and notice_date:
        gap = days_between(dishonour_date, notice_date)
        res["notice_dispatch_days"] = gap
        if gap is not None and gap > 30:
            res["is_notice_valid"] = False
            msg = f"Statutory Demand Notice dispatched on day {gap} (> 30-day statutory limit from dishonour date {dishonour_date}). Notice is time-barred!"
            res["warnings"].append(msg)
            res["audit_lines"].append(f"[🚨 TIMELINE BREACH - NOTICE DELAYED]: {msg}")
        elif gap is not None and gap >= 0:
            res["audit_lines"].append(f"[✓ NOTICE DISPATCH]: Statutory notice dispatched on day {gap} (within 30-day statutory window).")

    # 3. Complaint Filing Timeline (Cause of action accrual & limitation)
    ref_service_date = notice_received_date or notice_date
    if ref_service_date and filing_date:
        gap_total = days_between(ref_service_date, filing_date)
        if gap_total is not None:
            if gap_total < 15:
                res["is_premature"] = True
                res["is_complaint_timely"] = False
                msg = f"Complaint filed on day {gap_total} post-notice (< 15 days). Filed prematurely before cause of action accrued u/s 138(c)."
                res["warnings"].append(msg)
                res["audit_lines"].append(f"[🚨 TIMELINE WARNING - PREMATURE FILING]: {msg}")
            elif gap_total > 45:
                res["is_delay"] = True
                res["is_complaint_timely"] = False
                delay = gap_total - 45
                res["delay_days"] = delay
                msg = f"Complaint filed on day {gap_total} post-notice ({delay} days past the statutory 30-day filing window). Requires Condonation of Delay u/s 142(1)(b) NI Act."
                res["warnings"].append(msg)
                res["audit_lines"].append(f"[⚠️ TIMELINE ALERT - CONDONATION REQUIRED]: {msg}")
            elif gap_total >= 15:
                res["audit_lines"].append(f"[✓ COMPLAINT TIMELINE]: Complaint filed on day {gap_total} post-notice service (within 30-day window after 15-day cure period).")

    return res

def format_timeline_audit_report(res: Dict[str, Any]) -> str:
    if not res.get("audit_lines") and not res.get("warnings"):
        return ""
    lines = [
        "======================================================================",
        "SECTION 138 NI ACT STATUTORY TIMELINE AUDIT REPORT",
        "======================================================================"
    ]
    lines.extend(res.get("audit_lines", []))
    if res.get("warnings"):
        lines.append("\nSUMMARY STATUTORY WARNINGS:")
        for w in res.get("warnings", []):
            lines.append(f"  • {w}")
    lines.append("======================================================================\n")
    return "\n".join(lines)

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
    amount_val = _safe_float(case_data.get("cheque_amount") or case_data.get("amount") or 0)
    loan_via_bank = str(case_data.get("loan_via_bank", "yes")).lower()
    is_cash = loan_via_bank not in ("yes", "true", "1")
    if amount_val > 150000 and is_cash:
        transaction_nature += f". My client specifically asserts possessing sufficient source of funds to the tune of {amount_str} at the time of the transaction, advanced from accumulated personal savings/agricultural income, fully satisfying their financial capacity"
    
    timeline_res = verify_s138_timeline_for_draft(case_data)
    audit_header = format_timeline_audit_report(timeline_res)
    
    template = env.get_template("legal_notice.jinja")
    notice_content = template.render(
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
    if audit_header:
        return f"{audit_header}\n{notice_content}"
    return notice_content
def generate_certificate_63_bsa(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    complainant = case_data.get("complainant_name") or case_data.get("complainantName") or "________ (Your Name)"
    device_type = case_data.get("device_type", "Smartphone / Personal Computer")
    hdr = _header("CERTIFICATE UNDER SECTION 63(4) OF THE BHARATIYA SAKSHYA ADHINIYAM (BSA)")

    return hdr + f"""
IN THE COURT OF THE LEARNED JUDICIAL MAGISTRATE / METROPOLITAN MAGISTRATE
AT ________ (Court Location)
COMPLAINT NO.: _____ / {datetime.now().year}
IN THE MATTER OF:
{complainant}                                              -- COMPLAINANT
VERSUS
________ (Accused Name)                                             -- ACCUSED
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
    
    timeline_res = verify_s138_timeline_for_draft(case_data)
    audit_report = format_timeline_audit_report(timeline_res)
    
    delay_para = ""
    within_30_days = str(case_data.get("within_30_days", "yes")).lower() in ("yes", "true", "1")
    if timeline_res.get("is_delay"):
        delay_para = f"There has been a technical delay of {timeline_res.get('delay_days', 0)} days in filing the complaint post the expiry of statutory period, for which a condonation of delay application under Section 142(1)(b) of the NI Act read with Section 5 of the Limitation Act is filed herewith."
    elif not within_30_days:
        delay_para = f"There has been a technical delay in issuing/filing under Section 138, for which a condonation of delay application under Section 142(1)(b) of the NI Act is filed herewith."
    elif timeline_res.get("is_premature"):
        delay_para = f"[🚨 STATUTORY NOTICE WARNING: Complaint appears to be filed prematurely on day {timeline_res.get('notice_dispatch_days', '<15')} post-notice, prior to expiry of the mandatory 15-day payment period u/s 138(c). Cause of action had not accrued at the time of filing.]"

    if is_aggressive:
        debt_pleading = f"""The Complainant submits that the Accused is bound by an incontrovertible liability of {amount_str}, arising out of {transaction_nature}. 
    This liability is securely established by contemporaneous commercial records. The issuance of the subject cheque by the Accused was an explicit acknowledgment of this debt. Its subsequent dishonour is a clear demonstration of the Accused's mala fide intent to evade lawful obligations, compelling the Complainant to invoke the strict provisions of Section 138 of the NI Act."""
    else:
        debt_pleading = f"The Complainant states that the Accused is indebted to the Complainant for a sum of {amount_str} arising from {transaction_nature}. The said debt is legally enforceable and constitutes a valid liability under law."
    amount_val = _safe_float(case_data.get("cheque_amount") or case_data.get("amount") or 0)
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
    elif is_aggressive and case_data.get("score", 100) < 50:
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
{complainant}                                          -- COMPLAINANT
VERSUS
{accused}                                              -- ACCUSED
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
{filing_date}   Filing of the present complaint before this Honourable Court.
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
                                                        -- COMPLAINANT
VERSUS
ACCUSED:        {accused}
                {accused_addr}
                                                        -- ACCUSED
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
{complainant}                                          -- COMPLAINANT
VERSUS
{accused}                                              -- ACCUSED
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
                                                        -- COMPLAINANT
VERSUS
ACCUSED:        {accused}
                {accused_addr}
                                                        -- ACCUSED
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
   This Honourable Court has territorial jurisdiction to entertain and try this Complaint as the cheque in question was presented for encashment at {bank_full}, which is situated within the territorial limits of this Court, as per the law laid down by the Honourable Supreme Court in Dashrath Rupsingh Rathod vs. State of Maharashtra.
9. PRAYER:
   It is, therefore, most respectfully prayed that this Honourable Court may be pleased to:
   (a) Take cognizance of the offence committed by the Accused under Section 138 of the NI Act, 1881;
   (b) Issue summons/process to the Accused to face trial;
   (c) Direct the Accused to pay INTERIM COMPENSATION of 20% of the cheque amount to the Complainant as per Section 143A of the NI Act (as amended in 2018);
   (d) On conviction, sentence the Accused to imprisonment for the maximum term and/or impose a fine of twice the cheque amount to meet the ends of justice; and
   (e) Pass such other order(s) as this Honourable Court may deem fit in the interest of justice.
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
                                                        {complainant}
                                                        (Complainant)
"""
    full_complaint_bundle = f"{index_section}\n\n{synopsis_section}\n\n{memo_section}\n\n{complaint_body}\n\n{affidavit_section}"
    if audit_report:
        return f"{audit_report}\n{full_complaint_bundle}"
    return full_complaint_bundle
def generate_defence_strategy(case_data: Dict, concepts: List[Dict], score: int) -> str:
    today, amount_str = _case_meta(case_data)
    concept_names = {c.get("concept", "") for c in concepts if isinstance(c, dict)}
    defences_identified = []
    legal_arguments = []
    if "security_cheque" in concept_names:
        defences_identified.append("Cheque Given as Security — Not for Debt Discharge")
        legal_arguments.append(
            "The cheque in question was given purely as a security/collateral cheque and not in discharge of any legally enforceable debt. As per the Honourable Supreme Court in Indus Airways Pvt. Ltd. v. Magnum Aviation Pvt. Ltd. (2014), a security cheque falls outside the scope of Section 138 NI Act, as there is no legally enforceable debt against which the cheque was drawn."
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
    hdr = _header("DEFENCE STRATEGY BRIEF — SECTION 138 NI ACT")

    return hdr + f"""
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
WARNING: Do NOT file raw AI output. You MUST 'humanize' the draft to avoid 'Cookie-Cutter' objections from the Magistrate, and verify ALL citations to prevent 'Phantom Precedent' penalties (Professional Misconduct/Rs. 50,000 fine).
"""
def generate_discharge_application(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Accused Name)"
    hdr = _header("DISCHARGE APPLICATION — SECTION 227/239 CrPC / 250/262 BNSS")

    return hdr + f"""
IN THE COURT OF ________ (Sessions Judge / Magistrate), ________ (Location)
IN THE MATTER OF:
STATE                                                      -- PROSECUTION
VERSUS
{accused}                                                  -- ACCUSED
APPLICATION FOR DISCHARGE OF THE ACCUSED
MOST RESPECTFULLY SHOWETH:
1. That the police have filed a charge sheet against the Accused. However, a bare perusal of the charge sheet and accompanying documents under Section 207 CrPC reveals that no prima facie case is made out.
2. GRAVE SUSPICION LACKING:
   As per the Honourable Supreme Court in 'Union of India v. Prafulla Kumar Samal', the Court must evaluate if the materials create a 'grave suspicion'. Here, the evidence is entirely hearsay, legally inadmissible, and fundamentally flawed.
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
    hdr = _header("QUASHING PETITION — SECTION 482 CrPC / 528 BNSS")
    return hdr + f"""
IN THE HONOURABLE HIGH COURT OF {state_name}
CRIMINAL MISC. PETITION NO. ______ OF {datetime.now().year}
IN THE MATTER OF:
{accused}                                                  -- PETITIONER
VERSUS
STATE OF {state_name} & ANR.                               -- RESPONDENTS
PETITION UNDER SECTION 482 OF THE CODE OF CRIMINAL PROCEDURE FOR QUASHING OF FIR NO. {fir_no} DATED {fir_date} U/S {offense} P.S. {police_station} AND ALL CONSEQUENTIAL PROCEEDINGS
MOST RESPECTFULLY SHOWETH:
1. That the present petition is being filed invoking the inherent jurisdiction of this Honourable Court to prevent the abuse of the process of law and to secure the ends of justice.
2. MALA FIDE IMPLICATION (BHAJAN LAL GUIDELINES):
   That the FIR has been instituted with an ulterior motive to wreak vengeance on the Petitioner due to a private and personal dispute. The allegations, even if taken on their face value and accepted in their entirety, do not prima facie constitute any offence or make out a case against the Petitioner, falling squarely within Parameters 1 and 7 laid down in 'State of Haryana v. Bhajan Lal'.
3. PURELY CIVIL DISPUTE GIVEN CRIMINAL COLOR:
   That the crux of the dispute between the parties is inherently civil/commercial in nature (e.g., breach of contract/partnership dispute). The Complainant is attempting to weaponize the criminal justice system to exert pressure for a civil recovery, which is strictly deprecated by the Honourable Supreme Court in 'Indian Oil Corp v. NEPC India'.
PRAYER:
It is prayed that this Honourable Court may be pleased to quash the impugned FIR No. ________ (FIR No.) and all consequential proceedings emanating therefrom.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_suspension_sentence(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Appellant Name)"
    hdr = _header("APPLICATION FOR SUSPENSION OF SENTENCE — SECTION 389 CrPC / 430 BNSS")

    return hdr + f"""
IN THE COURT OF ________ (Sessions Judge / High Court), ________ (Location)
CRIMINAL MISC. APPLICATION IN CRIMINAL APPEAL NO. ______ OF {datetime.now().year}
IN THE MATTER OF:
{accused}                                                  -- APPELLANT
VERSUS
STATE OF ________ (State Name)                                      -- RESPONDENT
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
    hdr = _header("CRIMINAL APPEAL — SECTION 374 CrPC / 415 BNSS")

    return hdr + f"""
IN THE COURT OF ________ (Sessions Judge / High Court), ________ (Location)
CRIMINAL APPEAL NO. ______ OF {datetime.now().year}
IN THE MATTER OF:
{accused}                                                  -- APPELLANT
VERSUS
STATE OF ________ (State Name)                                      -- RESPONDENT
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
    hdr = _header("APPLICATION TO RECALL WITNESS — SECTION 311 CrPC / 348 BNSS")

    return hdr + f"""
IN THE COURT OF ________ (Sessions Judge / Magistrate), ________ (Location)
IN THE MATTER OF:
STATE                                                      -- PROSECUTION
VERSUS
{accused}                                                  -- ACCUSED
APPLICATION UNDER SECTION 311 OF THE CrPC FOR RECALLING PROSECUTION WITNESS (PW-________ (X)) FOR FURTHER CROSS-EXAMINATION
MOST RESPECTFULLY SHOWETH:
1. That the present case is pending adjudication before this Honourable Court and is fixed for ________ (Next Stage) on ________ (Next Date).
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
    hdr = _header("APPLICATION TO SUMMON ADDITIONAL ACCUSED — SECTION 319 CrPC / 358 BNSS")

    return hdr + f"""
IN THE COURT OF ________ (Sessions Judge / Magistrate), ________ (Location)
IN THE MATTER OF:
{complainant} / STATE                                      -- COMPLAINANT/PROSECUTION
VERSUS
________ (Current Accused) & ORS.                                   -- ACCUSED
APPLICATION UNDER SECTION 319 OF THE CrPC FOR SUMMONING ADDITIONAL ACCUSED PERSON
MOST RESPECTFULLY SHOWETH:
1. That the trial in the present matter is ongoing. During the recording of evidence of PW-________ (X), specific and overt acts have been attributed to one Mr./Ms. ________ (Name of Proposed Accused), who was not charge-sheeted by the police.
2. STRONG PRIMA FACIE EVIDENCE:
   That the testimony before this Honourable Court establishes a strong prima facie case against the proposed accused. As per the Constitution Bench ruling in 'Hardeep Singh v. State of Punjab', the evidence is more than a mere probability of complicity.
PRAYER:
It is prayed that Mr./Ms. ________ (Name) be summoned to stand trial alongside the current accused persons, to meet the ends of justice.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_exemption_appearance(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (Accused Name)"
    hdr = _header("EXEMPTION FROM PERSONAL APPEARANCE — SECTION 205/317 CrPC / 355 BNSS")

    return hdr + f"""
IN THE COURT OF ________ (Sessions Judge / Magistrate), ________ (Location)
IN THE MATTER OF:
STATE                                                      -- PROSECUTION
VERSUS
{accused}                                                  -- ACCUSED
APPLICATION FOR EXEMPTION FROM PERSONAL APPEARANCE OF THE ACCUSED FOR TODAY
MOST RESPECTFULLY SHOWETH:
1. That the Accused is a law-abiding citizen and has been regularly appearing before this Honourable Court.
2. UNAVOIDABLE REASON:
   That today, the Accused is unable to attend the Court due to ________ (Reason for Absence). A medical certificate/proof is annexed herewith.
3. NO PREJUDICE TO TRIAL:
   That the absence of the Accused is neither intentional nor deliberate. The counsel for the Accused is present and the identity of the Accused is not disputed. The trial will not be impeded by his/her absence today.
PRAYER:
It is prayed that the personal appearance of the Accused be exempted for today only.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_superdari_application(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    applicant = case_data.get("complainant_name") or case_data.get("accused_name") or "________ (Applicant Name)"
    hdr = _header("SUPERDARI APPLICATION (RELEASE OF PROPERTY) — SECTION 451 CrPC / 497 BNSS")

    return hdr + f"""
IN THE COURT OF ________ (Magistrate), ________ (Location)
IN THE MATTER OF:
{applicant}                                                -- APPLICANT
VERSUS
STATE                                                      -- PROSECUTION
APPLICATION UNDER SECTION 451 OF THE CrPC FOR RELEASE OF VEHICLE / PROPERTY ON SUPERDARI
MOST RESPECTFULLY SHOWETH:
1. That the Applicant is the registered owner of the vehicle ________ (Make/Model) bearing Registration No. ________ (Reg No.), which was seized by the police in connection with the present FIR.
2. DEPRECIATION OF ASSET:
   That the vehicle is currently parked at the police station, exposed to extreme weather, and is rapidly deteriorating in value and mechanical condition, as noted by the Honourable Supreme Court in 'Sunderbhai Ambalal Desai v. State of Gujarat'.
3. UNDERTAKING:
   That the Applicant undertakes to produce the vehicle before this Honourable Court as and when directed, and shall not alter its color or sell it without the prior permission of the Court.
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
    hdr = _header("PROTEST PETITION AGAINST CLOSURE REPORT")

    return hdr + f"""
IN THE COURT OF ________ (Magistrate), ________ (Location)
IN THE MATTER OF:
{complainant}                                              -- COMPLAINANT
VERSUS
{accused}                                                  -- PROPOSED ACCUSED
PROTEST PETITION AGAINST THE FINAL REPORT (CLOSURE REPORT) FILED BY THE POLICE U/S 173 CrPC
MOST RESPECTFULLY SHOWETH:
1. That the police have filed a Closure Report / B-Summary in FIR No. ________ (FIR No.), erroneously concluding that no case is made out against the Accused.
2. TAINTED INVESTIGATION:
   That the Investigating Officer (IO) has acted in a highly partisan manner and deliberately ignored the direct evidence, medical reports, and independent eyewitness statements provided by the Complainant.
3. PRIMA FACIE CASE EXISTS:
   That despite the defective investigation, the materials on record clearly disclose the commission of cognizable offences. This Honourable Court has the power under Section 190(1)(b) CrPC to disagree with the police report, take cognizance, and summon the Accused.
PRAYER:
It is prayed that this Honourable Court reject the Closure Report, take cognizance of the offences, and summon the Accused to face trial.
Place: ________ (Place)
Date: {today}
Through Counsel
"""
def generate_anticipatory_bail(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("case_title") or "________ (Applicant Name)"
    court = case_data.get("court_name") or "THE COURT OF SESSIONS JUDGE / HIGH COURT"
    ps = case_data.get("police_station", "________ (Police Station)")
    fir_no = case_data.get("case_id") or case_data.get("fir_no", "FIR No. ____ / 2026")
    offense = case_data.get("offense_type") or case_data.get("ipc_section", "Under Relevant Sections of IPC / BNS")
    max_punishment = case_data.get("max_punishment_years", 7)

    hdr = _header("ANTICIPATORY BAIL APPLICATION — SECTION 438 CrPC / SECTION 484 BNSS")
    return hdr + f"""
IN {court}
CRIMINAL MISC. (ANTICIPATORY BAIL) APPLICATION NO. ______ OF {datetime.now().year}

IN THE MATTER OF:
{accused}
Address: _____________________________________             -- APPLICANT / ACCUSED
VERSUS
STATE (NCT / GOVT OF ____________)
Through Station House Officer, P.S. {ps}                   -- RESPONDENT

APPLICATION UNDER SECTION 438 OF THE CODE OF CRIMINAL PROCEDURE, 1973 / SECTION 484 OF BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 FOR GRANT OF ANTICIPATORY BAIL IN CONNECTION WITH {fir_no} REGISTERED AT P.S. {ps} FOR OFFENCES PUNISHABLE U/S {offense}.

MOST RESPECTFULLY SHOWETH:

1. That the Applicant is a respectable, law-abiding citizen of India with deep roots in society and has never been convicted of any non-bailable criminal offense.

2. FALSE & MALICIOUS APPREHENSION:
   That the Applicant apprehends arrest at the hands of P.S. {ps} in connection with {fir_no} registered for alleged offences under {offense}. It is submitted that the FIR is an outcome of malice, ulterior motives, and personal vendetta, and no prima facie offence is made out against the Applicant.

3. ARNESH KUMAR & SATENDER KUMAR ANTIL GUIDELINES:
   That the maximum sentence for the alleged primary offense is {max_punishment} years. As per the landmark Constitution Bench ruling in 'Arnesh Kumar v. State of Bihar (2014)' and 'Satender Kumar Antil v. CBI (2022)', arrest in offences punishable up to 7 years must not be made casually or mechanically. The police have failed to demonstrate any credible necessity for custodial interrogation.

4. CIVIL DISPUTE CLOTHED WITH CRIMINAL COLOR:
   That the underlying dispute between the parties arises out of a commercial/civil contractual relationship. The Supreme Court in 'Dalip Kaur v. Jagnar Singh' and 'Hridaya Ranjan Prasad Verma v. State of Bihar' has held that a breach of contract cannot give rise to criminal prosecution under Section 420 IPC / Section 318 BNS in the absence of fraudulent intention at inception.

5. TRIPLE TEST COMPLIANCE & UNDERTAKINGS:
   (a) The Applicant is not a flight risk and possesses immovable properties within the jurisdiction of this Court.
   (b) The Applicant undertakes not to tamper with prosecution evidence or influence/intimidate any witness directly or indirectly.
   (c) The Applicant undertakes to join and fully cooperate with the ongoing investigation as and when summoned by the Investigating Officer under Section 41A CrPC / Section 35 BNSS.
   (d) The Applicant is ready and willing to surrender his/her passport and furnish solvent local surety to the satisfaction of the Court/IO.

PRAYER:
It is most respectfully prayed that in the event of arrest of the Applicant in connection with {fir_no} P.S. {ps}, the Applicant be released on anticipatory bail on such terms and conditions as this Honourable Court may deem fit and proper.

Place: ____________________
Date: {today}
COUNSEL FOR THE APPLICANT
"""

def generate_regular_bail(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("case_title") or "________ (Applicant / Undertrial)"
    court = case_data.get("court_name") or "THE COURT OF CHIEF METROPOLITAN MAGISTRATE / SESSIONS JUDGE"
    ps = case_data.get("police_station", "________ (Police Station)")
    fir_no = case_data.get("case_id") or case_data.get("fir_no", "FIR No. ____ / 2026")
    offense = case_data.get("offense_type") or case_data.get("ipc_section", "Under Relevant Sections of IPC / BNS")
    days_in_custody = case_data.get("days_in_custody", 30)

    hdr = _header("REGULAR BAIL APPLICATION — SECTION 437/439 CrPC / SECTION 480/483 BNSS")
    return hdr + f"""
IN {court}
CRIMINAL BAIL APPLICATION NO. ______ OF {datetime.now().year}

IN THE MATTER OF:
{accused}
(Currently lodged in Judicial Custody / Central Jail)       -- APPLICANT / ACCUSED
VERSUS
STATE
Through Investigating Officer, P.S. {ps}                   -- RESPONDENT

APPLICATION UNDER SECTION 437/439 OF THE CODE OF CRIMINAL PROCEDURE, 1973 / SECTION 480/483 OF BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 FOR GRANT OF REGULAR BAIL IN CONNECTION WITH {fir_no} P.S. {ps} U/S {offense}.

MOST RESPECTFULLY SHOWETH:

1. That the Applicant has been arrested in connection with {fir_no} P.S. {ps} and has been languishing in judicial custody for the past {days_in_custody} days.

2. INVESTIGATION SUBSTANTIALLY COMPLETE / CUSTODIAL INTERROGATION OVER:
   That the police remand of the Applicant is complete and no further recovery remains to be effected from the Applicant under Section 27 of the Evidence Act / Section 23 BSA. Continuous detention in custody serves no punitive or investigative purpose and would amount to pre-trial punishment.

3. BAIL IS THE RULE, JAIL IS THE EXCEPTION:
   That as per the Supreme Court in 'State of Rajasthan v. Balchand (1977)' and reaffirmed in 'Manish Sisodia v. Directorate of Enforcement (2024)', bail is the cardinal rule and detention is an exception. Deprivation of personal liberty without trial violates Article 21 of the Constitution.

4. EVIDENTIARY INFIRMITIES IN PROSECUTION CASE:
   That there are material contradictions between the ocular statements of witnesses and the documentary record. Furthermore, electronic records relied upon by the prosecution lack the mandatory certificate under Section 65B(4) IEA / Section 63 BSA, rendering the evidence legally inadmissible.

5. TRIPLE TEST FULFILLED:
   The Applicant is a permanent resident, has clean antecedents, and undertakes not to tamper with evidence, jump bail, or contact prosecution witnesses.

PRAYER:
It is respectfully prayed that the Applicant be enlarged on Regular Bail in connection with {fir_no} P.S. {ps} on such terms and conditions and surety as this Honourable Court deems fit.

Place: ____________________
Date: {today}
COUNSEL FOR THE APPLICANT
"""

def generate_default_bail(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    accused = case_data.get("accused_name") or case_data.get("case_title") or "________ (Applicant)"
    court = case_data.get("court_name") or "THE COURT OF DESIGNATED MAGISTRATE / SESSIONS JUDGE"
    ps = case_data.get("police_station", "________ (Police Station)")
    fir_no = case_data.get("case_id") or case_data.get("fir_no", "FIR No. ____ / 2026")
    days_in_custody = case_data.get("days_in_custody", 65)
    max_punishment = case_data.get("max_punishment_years", 7)
    statutory_limit = 90 if max_punishment >= 10 else 60

    hdr = _header("STATUTORY DEFAULT BAIL APPLICATION — SECTION 167(2) CrPC / SECTION 187 BNSS")
    return hdr + f"""
IN {court}
CRIMINAL MISC. (STATUTORY DEFAULT BAIL) APPLICATION NO. ______ OF {datetime.now().year}

IN THE MATTER OF:
{accused}
(In Judicial Custody)                                      -- APPLICANT / ACCUSED
VERSUS
STATE (P.S. {ps})                                          -- RESPONDENT

APPLICATION UNDER SECTION 167(2) OF THE CODE OF CRIMINAL PROCEDURE, 1973 / SECTION 187 OF BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 FOR GRANT OF STATUTORY / DEFAULT BAIL UPON EXPIRY OF {statutory_limit} DAYS WITHOUT CHARGESHEET.

MOST RESPECTFULLY SHOWETH:

1. That the Applicant was arrested and remanded to custody on ________ (Remand Date). As of today, the Applicant has undergone {days_in_custody} continuous days in custody.

2. STATUTORY PERIOD EXPIRED WITHOUT CHARGESHEET:
   That the primary offences alleged carry a maximum punishment up to {max_punishment} years, for which the outer statutory limit for filing the Police Report / Chargesheet is {statutory_limit} days under Section 167(2)(a)(ii) CrPC / Section 187(3) BNSS. The police have failed to file the chargesheet within the statutory prescribed period.

3. INDEFEASIBLE CONSTITUTIONAL RIGHT ACQUIRED:
   That as held by the Supreme Court in 'Bikramjit Singh v. State of Punjab (2020)', 'M. Ravindran v. Intelligence Officer (2021)', and 'Ritu Chhabaria v. Union of India (2023)', the moment the statutory period of {statutory_limit} days expires without a chargesheet, the Accused acquires an absolute and indefeasible constitutional right to Default Bail under Article 21.

4. OFFERING SOLVENT SURETY:
   That the Applicant is ready and willing to furnish solvent surety and bail bonds to the satisfaction of this Honourable Court and avails of this statutory right prior to any subsequent submission of the chargesheet.

PRAYER:
It is respectfully prayed that this Honourable Court be pleased to grant Statutory Default Bail to the Applicant under Section 167(2) CrPC / Section 187 BNSS in {fir_no} P.S. {ps}.

Place: ____________________
Date: {today}
COUNSEL FOR THE APPLICANT
"""

def generate_fir_draft(case_data: Dict, concepts: List[Dict] = None) -> str:
    today, amount_str = _case_meta(case_data)
    complainant = case_data.get("complainant_name") or "________ (Complainant Name)"
    accused = case_data.get("accused_name") or "________ (Accused Person)"
    ps = case_data.get("police_station", "________ (Police Station)")
    incident_date = case_data.get("incident_date", "________ (Incident Date)")
    offense = case_data.get("offense_type", "Cheating, Fraud & Criminal Breach of Trust")

    hdr = _header("CRIMINAL COMPLAINT / FORMAL FIR DRAFT — SECTION 154 / 156(3) CrPC / S.173 / 175 BNSS")
    return hdr + f"""
TO:
THE STATION HOUSE OFFICER (SHO) / HONOURABLE METROPOLITAN MAGISTRATE
POLICE STATION {ps}

COMPLAINANT: {complainant}
Address: _________________________________________________
Contact: _________________________________________________

ACCUSED: {accused}
Address: _________________________________________________

SUBJECT: FORMAL COMPLAINT FOR REGISTRATION OF FIRST INFORMATION REPORT (FIR) U/S 420, 406, 467, 468, 471, 120B IPC / SECTIONS 318, 316, 336, 338, 340, 61 BNS FOR OFFENCES OF FRAUD, FORGERY, CRIMINAL BREACH OF TRUST, AND CHEATING.

RESPECTED SIR / MADAM,

1. That the Complainant is a law-abiding citizen engaged in lawful business/avocation and was dishonestly approached by the Accused person on or about {incident_date}.

2. FRAUDULENT INDUCEMENT & ENTRUSTMENT:
   That the Accused dishonestly and fraudulently induced the Complainant by making false representations regarding ________________________ (Transaction Nature). Believing the representations to be true, the Complainant parted with valuable property / funds amounting to {amount_str}.

3. DISHONEST MISAPPROPRIATION & FORGERY:
   That subsequent investigations revealed that the Accused harboured dishonest intention right from the inception of the transaction. The Accused fabricated documents/invoices and misappropriated the funds for personal enrichment, refusing to refund the money and threatening the Complainant with dire consequences.

4. COGNIZABLE OFFENCE MADE OUT:
   That the specific acts of the Accused satisfy all ingredients of cognizable offences under Sections 420/406/468 IPC / Sections 318/316/338 BNS. As mandated by the Constitution Bench in 'Lalita Kumari v. Govt of UP (2014)', registration of FIR is mandatory where information discloses commission of a cognizable offence.

PRAYER:
It is therefore requested that an FIR be registered immediately against the Accused persons under relevant sections of the law and stringent investigative measures, including seizure of incriminating materials and arrest of the culprits, be initiated in accordance with law.

Place: ____________________
Date: {today}
COMPLAINANT
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
        elif draft_type in ("DEFAULT_BAIL", "DEFAULT_BAIL_APPLICATION"):
            return generate_default_bail(case_data)
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
        elif draft_type == "SARFAESI_13_2_NOTICE":
            return generate_sarfaesi_13_2_notice(case_data)
        elif draft_type == "SARFAESI_13_3A_REPLY":
            return generate_sarfaesi_13_3a_reply(case_data)
        elif draft_type == "SARFAESI_13_4_POSSESSION_NOTICE":
            return generate_sarfaesi_13_4_possession(case_data)
        elif draft_type == "SARFAESI_SEC_14_APPLICATION":
            return generate_sarfaesi_sec_14_app(case_data)
        elif draft_type == "SARFAESI_SEC_14_AFFIDAVIT":
            return generate_sarfaesi_sec_14_affidavit(case_data)
        elif draft_type == "SARFAESI_RULE_8_6_AUCTION_NOTICE":
            return generate_sarfaesi_rule_8_6_auction_notice(case_data)
        elif draft_type == "SARFAESI_SEC_17_SA_PETITION":
            return generate_sarfaesi_sec_17_sa(case_data)
        elif draft_type == "SARFAESI_WRITTEN_STATEMENT":
            return generate_sarfaesi_written_statement(case_data)
        elif draft_type == "DELAY_CONDONATION":
            return generate_delay_condonation(case_data)
        elif draft_type == "APPLICATION_143A":
            draft_out = generate_application_143a(case_data)
        else:
            draft_out = generate_legal_opinion(score, concepts, case_data)

        lang = str(case_data.get("language") or case_data.get("lang") or "").lower()
        if lang in ["mr", "marathi"]:
            draft_out = _format_marathi_draft(draft_out, draft_type, case_data)
        elif lang in ["hi", "hindi"]:
            draft_out = _format_hindi_draft(draft_out, draft_type, case_data)

        return draft_out
def generate_settlement_draft(case_data: Dict, score: int) -> str:
    return "MEMORANDUM OF SETTLEMENT\n\nThis memorandum of settlement is generated based on the case facts. A formal mediator or counsel should review the terms."
def generate_fir_draft(case_data: Dict, concepts: List[Dict] = None) -> str:
    today, amount_str = _case_meta(case_data)
    informant = case_data.get("complainant_name") or case_data.get("informant_name") or "________ (Informant Name)"
    informant_addr = case_data.get("complainant_address") or "________ (Address)"
    informant_phone = case_data.get("complainant_phone") or "________ (Phone)"
    accused = case_data.get("accused_name") or "________ (Accused Person(s))"
    accused_addr = case_data.get("accused_address") or "________ (Accused Address)"
    ps = case_data.get("police_station") or "________ (Police Station Name)"
    incident_date = case_data.get("incident_date") or "[Date of Incident]"
    sections = case_data.get("ipc_section") or case_data.get("offense_type") or "Section 420, 406, 120B IPC / Section 318, 316, 61 BNS"
    desc = case_data.get("description") or "Allegations of criminal breach of trust, fraudulent inducement, and misappropriation of funds."

    hdr = _header("CRIMINAL COMPLAINT / FIRST INFORMATION REPORT (S.154 / 156(3) CrPC <-> S.173 / 175 BNSS)")

    return hdr + f"""

TO:
THE STATION HOUSE OFFICER / OFFICER-IN-CHARGE,
POLICE STATION {ps.upper()}

COMPLAINANT / INFORMANT:
{informant}, R/o {informant_addr}, Contact: {informant_phone}

ACCUSED PERSON(S):
{accused}, R/o {accused_addr}

SUBJECT: COMPLAINT FOR REGISTRATION OF FIRST INFORMATION REPORT (FIR) UNDER {sections.upper()} AND OTHER RELEVANT PROVISIONS OF LAW.

RESPECTED SIR,

I, the undersigned Informant, do hereby lodge this formal criminal complaint setting out the true facts of the cognizable offence committed by the Accused:

1. THE COMPLAINANT & ACCUSED:
   The Informant is a law-abiding citizen residing at the address mentioned above. The Accused approached the Informant on or about {incident_date} with dishonest and deceptive representations.

2. FACTUAL NARRATIVE & SPECIFIC OVERT ACTS:
   {desc}

3. COGNIZABLE OFFENCE & FORENSIC EVIDENCE:
   The acts committed by the Accused clearly disclose the commission of non-bailable cognizable offences under {sections}. Contemporaneous evidence including bank records, digital communications, and witness statements are submitted herewith.

4. MANDATORY REGISTRATION OF FIR:
   In terms of the Constitution Bench judgment of the Hon'ble Supreme Court in Lalita Kumari v. Govt. of UP (2014) 2 SCC 1, registration of FIR is mandatory upon disclosure of a cognizable offence.

PRAYER:
It is respectfully prayed that this Police Station may be pleased to:
a) Register a formal FIR against the Accused under the aforementioned sections of law;
b) Conduct a thorough investigation, effect recovery of material evidence, and arrest the culprits;
c) File a Final Report / Chargesheet before the competent jurisdictional Magistrate.

DATE: {today}
PLACE: {case_data.get("court_name", "________")}

INFORMANT / COMPLAINANT
THROUGH COUNSEL
"""

def generate_regular_bail(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    applicant = case_data.get("accused_name") or "________ (Accused / Applicant)"
    applicant_addr = case_data.get("accused_address") or "________ (Address)"
    court = case_data.get("court_name") or "SESSIONS COURT / MAGISTRATE COURT"
    fir_no = case_data.get("case_id") or case_data.get("fir_number") or "FIR No. ____/2026"
    ps = case_data.get("police_station") or "________"
    sections = case_data.get("ipc_section") or case_data.get("offense_type") or "Section 420/406 IPC / Section 318/316 BNS"
    custody_days = case_data.get("days_in_custody") or 0
    arrest_date = case_data.get("arrest_date") or "[Date of Arrest]"

    hdr = _header("APPLICATION FOR REGULAR BAIL UNDER SECTION 437/439 CrPC <-> SECTION 480/483 BNSS")

    return hdr + f"""

IN THE COURT OF THE PRINCIPAL SESSIONS JUDGE / JUDICIAL MAGISTRATE
AT {court.upper()}

BAIL APPLICATION NO. _____ OF {datetime.now().year}

IN THE MATTER OF:
{applicant}
S/o ____________, Age: ____ Years,
R/o {applicant_addr}
(Presently in Judicial Custody at Central Prison)             -- APPLICANT / ACCUSED

VERSUS

STATE (GOVT. OF NCT / STATE POLICE)
THROUGH SHO, POLICE STATION {ps.upper()}                     -- RESPONDENT / PROSECUTION

APPLICATION UNDER SECTION 439 OF THE CODE OF CRIMINAL PROCEDURE, 1973 (READ WITH SECTION 483 OF BHARATIYA NAGARIK SURAKSHA SANHITA, 2023) FOR GRANT OF REGULAR BAIL IN CONNECTION WITH {fir_no.upper()} REGISTERED AT POLICE STATION {ps.upper()} FOR OFFENCES UNDER {sections.upper()}.

MOST RESPECTFULLY SHOWETH:

1. That the Applicant has been falsely implicated in the above-mentioned FIR and was arrested on {arrest_date}. The Applicant has undergone continuous judicial incarceration for approximately {custody_days} days.

2. TRIPLE TEST SATISFACTION:
   a) NO FLIGHT RISK: The Applicant is a permanent resident of the jurisdiction with deep family roots and fixed immovable assets.
   b) NO TAMPERING WITH EVIDENCE: The entire investigation is documentary in nature and all material evidence is in the custody of the Investigating Agency (P. Chidambaram v. CBI).
   c) NO WITNESS INTIMIDATION: The Applicant has clean antecedents and undertakes not to contact or influence any prosecution witness.

3. SATENDER KUMAR ANTIL GUIDELINES:
   The case of the Applicant is squarely governed by the landmark Supreme Court ruling in Satender Kumar Antil v. CBI (2022) 10 SCC 51 wherein the Hon'ble Court reiterated that "Bail is the rule and jail is an exception" (State of Rajasthan v. Balchand).

4. NO NECESSITY OF FURTHER CUSTODIAL INTERROGATION:
   Investigation qua the Applicant is substantially complete, recovery (if any) has already been effected, and continued detention serves no punitive purpose during pre-trial stages.

PRAYER:
It is most respectfully prayed that this Hon'ble Court may be pleased to:
a) Enlarge the Applicant on regular bail in connection with {fir_no} registered at PS {ps} upon furnishing solvent surety bonds;
b) Pass any other order deemed fit in the interest of justice.

DATE: {today}
PLACE: {court}

APPLICANT
THROUGH ADVOCATE
"""

def generate_anticipatory_bail(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    applicant = case_data.get("accused_name") or "________ (Accused / Applicant)"
    applicant_addr = case_data.get("accused_address") or "________ (Address)"
    court = case_data.get("court_name") or "HON'BLE SESSIONS COURT / HIGH COURT"
    fir_no = case_data.get("case_id") or case_data.get("fir_number") or "FIR No. ____/2026 (or Anticipated FIR)"
    ps = case_data.get("police_station") or "________"
    sections = case_data.get("ipc_section") or case_data.get("offense_type") or "Section 420/406 IPC / Section 318/316 BNS"

    hdr = _header("APPLICATION FOR ANTICIPATORY BAIL UNDER SECTION 438 CrPC <-> SECTION 484 BNSS")

    return hdr + f"""

IN THE COURT OF SESSIONS / HIGH COURT
AT {court.upper()}

CRIMINAL MISC. (ANTICIPATORY BAIL) APPLICATION NO. _____ OF {datetime.now().year}

IN THE MATTER OF:
{applicant}
S/o ____________, Age: ____ Years,
R/o {applicant_addr}                                         -- APPLICANT

VERSUS

STATE (GOVT. OF NCT / STATE POLICE)
THROUGH SHO, POLICE STATION {ps.upper()}                     -- RESPONDENT

APPLICATION UNDER SECTION 438 OF CrPC, 1973 (READ WITH SECTION 484 OF BNSS, 2023) FOR GRANT OF PRE-ARREST / ANTICIPATORY BAIL IN THE EVENT OF ARREST IN {fir_no.upper()} REGISTERED AT PS {ps.upper()} UNDER {sections.upper()}.

MOST RESPECTFULLY SHOWETH:

1. APPREHENSION OF ARREST:
   The Applicant has a bona fide and reasonable apprehension of imminent arrest at the hands of the police of PS {ps} in connection with frivolous and vexatious allegations.

2. CIVIL DISPUTE CLOTHED WITH CRIMINAL OFFENCE:
   The dispute between the parties is purely civil and contractual in nature arising out of commercial dealings, without any dishonest intention at inception (Hridaya Ranjan Prasad Verma v. State of Bihar).

3. SUSHILA AGGARWAL CONSTITUTION BENCH MANDATE:
   Per the 5-Judge Constitution Bench ruling in Sushila Aggarwal v. State (NCT of Delhi) (2020) 5 SCC 1, protection under Section 438 should not be restricted by time-limits and liberty must be safeguarded against arbitrary arrest.

4. ARNESH KUMAR & S.41A NOTICE COMPLIANCE:
   The alleged offences carry punishment up to 7 years. The police have acted in defiance of Section 41A CrPC / S.35 BNSS and the binding mandate of Arnesh Kumar v. State of Bihar (2014) 8 SCC 273.

5. UNDERTAKING TO COOPERATE:
   The Applicant undertakes to join investigation as and when summoned by the Investigating Officer and abide by all conditions under Section 438(2) CrPC.

PRAYER:
It is respectfully prayed that this Hon'ble Court may direct that in the event of arrest, the Applicant be released on anticipatory bail in {fir_no} on furnishing suitable sureties.

DATE: {today}
PLACE: {court}

APPLICANT
THROUGH COUNSEL
"""

def generate_default_bail(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    applicant = case_data.get("accused_name") or "________ (Applicant / Accused)"
    court = case_data.get("court_name") or "COURT OF JUDICIAL MAGISTRATE FIRST CLASS"
    fir_no = case_data.get("case_id") or case_data.get("fir_number") or "FIR No. ____/2026"
    ps = case_data.get("police_station") or "________"
    custody_days = case_data.get("days_in_custody") or 60
    punishment = int(case_data.get("max_punishment_years") or 7)
    threshold = 90 if punishment >= 10 else 60

    hdr = _header("APPLICATION FOR STATUTORY DEFAULT BAIL UNDER SECTION 167(2) CrPC <-> SECTION 187 BNSS")

    return hdr + f"""

IN THE COURT OF THE LEARNED JUDICIAL MAGISTRATE
AT {court.upper()}

BAIL APPLICATION (DEFAULT BAIL) NO. _____ OF {datetime.now().year}

IN THE MATTER OF:
{applicant} (Presently in Judicial Custody)                   -- APPLICANT / ACCUSED

VERSUS

STATE (POLICE STATION {ps.upper()})                          -- RESPONDENT

APPLICATION UNDER SECTION 167(2) OF CrPC (READ WITH SECTION 187 OF BNSS) FOR STATUTORY DEFAULT BAIL AS THE INVESTIGATION HAS NOT BEEN COMPLETED WITHIN {threshold} DAYS.

MOST RESPECTFULLY SHOWETH:

1. That the Applicant was remanded to judicial custody on {case_data.get("arrest_date", "____")} and has completed {custody_days} days in continuous custody.
2. That the statutory period of {threshold} days prescribed under Section 167(2)(a) for completing investigation has expired.
3. That as of the filing of this application, the Police have NOT submitted the final Charge Sheet / Report under Section 173(2) CrPC.
4. That the right to default bail is an INDEFEASIBLE FUNDAMENTAL RIGHT under Article 21 of the Constitution of India (Ritu Chhabaria v. Union of India, 2023; Bikramjit Singh v. State of Punjab, 2020; Sanjay Dutt v. State, 1994).
5. That the Applicant is ready and willing to furnish solvent bail bonds and sureties.

PRAYER:
It is prayed that this Hon'ble Court be pleased to immediately release the Applicant on Statutory Default Bail under Section 167(2) CrPC.

DATE: {today}
PLACE: {court}

APPLICANT
THROUGH ADVOCATE
"""

def generate_quashing_petition(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    petitioner = case_data.get("accused_name") or "________ (Petitioner)"
    court = case_data.get("court_name") or "HON'BLE HIGH COURT"
    fir_no = case_data.get("case_id") or case_data.get("fir_number") or "FIR No. ____/2026"
    ps = case_data.get("police_station") or "________"
    sections = case_data.get("ipc_section") or case_data.get("offense_type") or "Section 420/406/498A IPC"

    hdr = _header("CRIMINAL QUASHING PETITION UNDER SECTION 482 CrPC <-> SECTION 528 BNSS")

    return hdr + f"""

IN THE HIGH COURT OF JUDICATURE
CRIMINAL MISCELLANEOUS (QUASHING) PETITION NO. _____ OF {datetime.now().year}

IN THE MATTER OF:
{petitioner}                                                 -- PETITIONER(S)

VERSUS

1. STATE (GOVT. OF NCT / STATE POLICE)
2. COMPLAINANT / INFORMANT                                  -- RESPONDENTS

PETITION UNDER SECTION 482 OF CrPC, 1973 (READ WITH SECTION 528 OF BNSS, 2023) FOR QUASHING OF {fir_no.upper()} REGISTERED AT PS {ps.upper()} UNDER {sections.upper()} AND ALL CONSEQUENTIAL PROCEEDINGS.

MOST RESPECTFULLY SHOWETH:

1. BHAJAN LAL SEVEN-PILLAR QUASHING PARAMETERS:
   The present petition is squarely covered by the landmark parameters laid down by the Hon'ble Supreme Court in State of Haryana v. Bhajan Lal (1992 Supp (1) SCC 335).

2. GROUNDS FOR QUASHING:
   a) Absence of Prima Facie Offence: Even if allegations in the FIR are taken at face value, they do not disclose ingredients of cognizable offences.
   b) Disguised Civil Dispute: Commercial breach of contract converted into criminal fraud without mens rea at inception (Hridaya Ranjan Prasad Verma v. State of Bihar).
   c) Omnibus Allegations: Vague and general claims without specific overt acts leveled maliciously against family members (Kahkashan Kausar v. State of Bihar, 2022).
   d) Abuse of Process: Criminal proceedings instituted with an ulterior motive for wreaking vengeance.

PRAYER:
It is most respectfully prayed that this Hon'ble High Court may graciously be pleased to:
a) Quash and set aside {fir_no} registered at Police Station {ps} and all consequential proceedings arising therefrom;
b) Stay all further investigation/proceedings during the pendency of this petition.

DATE: {today}
PLACE: {court}

PETITIONER(S)
THROUGH COUNSEL
"""

def generate_discharge_application(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    applicant = case_data.get("accused_name") or "________ (Applicant / Accused)"
    court = case_data.get("court_name") or "COURT OF SESSIONS / METROPOLITAN MAGISTRATE"
    fir_no = case_data.get("case_id") or "CC No. ____/2026"
    sections = case_data.get("ipc_section") or "Relevant Penal Sections"

    hdr = _header("DISCHARGE APPLICATION UNDER SECTION 227 / 239 CrPC <-> SECTION 250 / 262 BNSS")

    return hdr + f"""

IN THE COURT OF SESSIONS / JUDICIAL MAGISTRATE
AT {court.upper()}

DISCHARGE APPLICATION UNDER SECTION 227/239 CrPC (READ WITH SECTION 250/262 BNSS)

IN THE MATTER OF:
{applicant}                                                 -- APPLICANT / ACCUSED

VERSUS

STATE (PROSECUTION)                                          -- RESPONDENT

APPLICATION FOR DISCHARGE OF THE ACCUSED IN {fir_no.upper()} FOR OFFENCES UNDER {sections.upper()} FOR WANT OF PRIMA FACIE CASE AND SUFFICIENT GROUNDS FOR PROCEEDING.

MOST RESPECTFULLY SHOWETH:

1. That the materials placed on record by the prosecution in the police report under Section 173 CrPC do not disclose sufficient grounds for proceeding against the Applicant.
2. That there is no grave suspicion or prima facie evidence connecting the Applicant with the alleged commission of offence (Union of India v. Prafulla Kumar Samal, 1979; Sajjan Kumar v. CBI, 2010).
3. That the prosecution evidence is riddled with material contradictions between Section 161 statements and scientific FSL reports.

PRAYER:
It is prayed that this Hon'ble Court may be pleased to discharge the Applicant under Section 227/239 CrPC.

DATE: {today}
PLACE: {court}

APPLICANT
THROUGH ADVOCATE
"""
def generate_delay_condonation(case_data: Dict) -> str:
    return "APPLICATION FOR CONDONATION OF DELAY\n\nUnder Section 5 of the Limitation Act, 1963 read with Section 142(b) of the Negotiable Instruments Act, 1881.\n\n[DRAFT DETAILS TO BE FILLED]"
def generate_application_143a(case_data: Dict) -> str:
    return "APPLICATION UNDER SECTION 143A OF THE NEGOTIABLE INSTRUMENTS ACT\n\nFor direction to the Accused to pay interim compensation.\n\n[DRAFT DETAILS TO BE FILLED]"
def generate_legal_opinion(case_data: Dict, score: int, concepts: List[Dict]) -> str:
    today, amount_str = _case_meta(case_data)
    hdr = _header("LEGAL OPINION & LITIGATION VIABILITY BRIEF — SECTION 138 NI ACT")
    
    viability_eval = "The case is structurally sound but requires procedural precision." if score > 70 else "The case exhibits significant structural vulnerabilities that may impede successful prosecution."
    
    risk_list = [f"   - {c.get('concept', '').replace('_', ' ').upper()} (Impact: High)" for c in concepts if isinstance(c, dict) and c.get('confidence', 0) > 0.7]
    risk_str = "\n".join(risk_list) if risk_list else "   - No high-confidence risks detected."
    
    rec_str = "Proceed with the filing of a Criminal Complaint under Section 138 NI Act whilst ensuring all statutory timelines are strictly met." if score > 60 else "Immediate litigation is not recommended. Focus on evidentiary remediation or explore a mediated settlement (Section 147 NI Act) to mitigate costs."
    
    dir_str = "1. Prepare and file the complaint within the 30-day limitation window from notice service.\n   2. Confirm original documents are available for verification." if score > 60 else "1. Issue a remedial notice or seek compounding to avoid dismissal.\n   2. Collect additional documentary evidence to verify transaction details."

    return hdr + f"""
Date: {today}
Case Viability Score: {score}/100
Subject: Strategic Assessment of Cheque Dishonour Case involving {amount_str}

1. EXECUTIVE SUMMARY:
   Based on the current evidentiary configuration, this case has a viability score of {score}%. 
   {viability_eval}

2. KEY RISK VECTORS:
   The following legal concepts were detected which directly impact the litigation posture:
{risk_str}

3. STRATEGIC RECOMMENDATION:
   {rec_str}

4. LITIGATION DIRECTIVE:
   {dir_str}

DISCLAIMER: This is an AI-generated preliminary strategy document. Consult a qualified advocate before taking any legal action.
WARNING: Do NOT file raw AI output. You MUST humanize the draft to avoid Cookie-Cutter objections from the Magistrate, and verify ALL citations to prevent Phantom Precedent penalties (Professional Misconduct/Rs. 50,000 fine).
"""

def generate_sarfaesi_13_2_notice(case_data: Dict) -> str:
    today, amount_str = _case_meta(case_data)
    borrower = case_data.get("borrower_name", case_data.get("accused_name", "Borrower/Guarantor"))
    bank = case_data.get("bank_name", case_data.get("complainant_name", "Secured Creditor Bank"))
    loan_acc = case_data.get("loan_account_number", case_data.get("account_number", "L-XXXXXXXX"))
    npa_date = case_data.get("npa_date", "[NPA Classification Date]")

    hdr = _header("DEMAND NOTICE UNDER SECTION 13(2) OF THE SARFAESI ACT, 2002")


    return hdr + f"""

BY REGISTERED AD / SPEED POST WITH ACKNOWLEDGEMENT DUE

Date: {today}

TO:
{borrower} (Borrower / Mortgagor / Guarantor)

FROM:
Authorized Officer, {bank}

SUBJECT: DEMAND NOTICE UNDER SECTION 13(2) READ WITH RULE 3 OF THE SECURITY INTEREST (ENFORCEMENT) RULES, 2002 IN RESPECT OF LOAN ACCOUNT NO. {loan_acc}.

Sir / Madam,

1. We act for and on behalf of {bank} ('Secured Creditor').
2. You, the Borrower/Guarantor, availed credit facilities from the Secured Creditor against the creation of equitable mortgage / security interest over the secured asset(s).
3. Due to persistent defaults in repayment of principal and interest, your credit account was classified as a Non-Performing Asset (NPA) on {npa_date} in strict compliance with Reserve Bank of India (RBI) Income Recognition and Asset Classification (IRAC) guidelines.
4. As of {today}, the total outstanding liabilities due and payable by you stand at {amount_str}, along with further interest, penal charges, and costs.
5. NOTICE IS HEREBY GIVEN U/S 13(2) OF THE SARFAESI ACT calling upon you to discharge in full your liabilities within SIXTY (60) DAYS from the date of service of this notice.
6. TAKE NOTICE that failing payment within 60 days, the Secured Creditor shall exercise all or any of the rights under Section 13(4) of the SARFAESI Act, 2002, including taking possession of the mortgaged secured assets.

AUTHORIZED OFFICER
{bank}
"""

def generate_sarfaesi_13_3a_reply(case_data: Dict) -> str:
    today, _ = _case_meta(case_data)
    borrower = case_data.get("borrower_name", "Borrower")
    bank = case_data.get("bank_name", "Secured Creditor Bank")
    rep_date = case_data.get("borrower_representation_date", "[Representation Date]")

    hdr = _header("REASONED DECISION / REPLY UNDER SECTION 13(3A) OF THE SARFAESI ACT, 2002")

    return f"{hdr}\n\nDate: {today}\n\nTO:\n{borrower}\n\nFROM:\nAuthorized Officer, {bank}\n\nSUBJECT: DECISION ON REPRESENTATION / OBJECTION DATED {rep_date} SUBMITTED UNDER SECTION 13(3A) OF SARFAESI ACT, 2002.\n\n1. We acknowledge receipt of your representation / objection dated {rep_date} against the Section 13(2) Demand Notice.\n2. The Secured Creditor has duly considered your objections in compliance with Section 13(3A) of the SARFAESI Act and the principles laid down by the Honourable Supreme Court in Mardia Chemicals Ltd. v. Union of India (2004) 4 SCC 311.\n3. UPON CAREFUL CONSIDERATION, YOUR OBJECTIONS ARE FOUND TO BE UNTENABLE AND STAND REJECTED FOR THE FOLLOWING REASONS:\n   (a) NPA classification was strictly executed per RBI guidelines upon continuous 90-day default.\n   (b) The security interest is duly registered on CERSAI portal (Section 26D).\n   (c) Claims of financial distress do not legally suspend statutory enforcement under Chapter III of the Act.\n4. Consequently, the Demand Notice dated under Section 13(2) remains valid and operative.\n\nAUTHORIZED OFFICER\n{bank}\n"

def generate_sarfaesi_13_4_possession(case_data: Dict) -> str:
    today, amount_str = _case_meta(case_data)
    borrower = case_data.get("borrower_name", "Borrower")
    bank = case_data.get("bank_name", "Secured Creditor Bank")

    hdr = _header("POSSESSION NOTICE UNDER RULE 8(1) / SECTION 13(4) OF SARFAESI ACT, 2002")


    return hdr + f"""

POSSESSION NOTICE (FOR IMMOVABLE PROPERTY)

WHEREAS the undersigned being the Authorized Officer of {bank} under the SARFAESI Act, 2002 and in exercise of powers conferred under Section 13(12) read with Rule 3 of the Security Interest (Enforcement) Rules, 2002 issued Demand Notice U/S 13(2) calling upon {borrower} to repay the amount of {amount_str}.

The Borrower having failed to repay the amount, notice is hereby given to the Borrower and the public in general that the undersigned has taken SYMBOLIC / PHYSICAL POSSESSION of the property described herein below in exercise of powers conferred U/S 13(4) of the said Act read with Rule 8 of the said Rules on this {today}.

The Borrower in particular and the public in general is hereby cautioned not to deal with the property and any dealings with the property will be subject to the charge of {bank}.

DESCRIPTION OF THE IMMOVABLE PROPERTY:
[Detail of Mortgaged Property / Boundaries / CERSAI Security Asset ID]

AUTHORIZED OFFICER
{bank}
"""

def generate_sarfaesi_sec_14_app(case_data: Dict) -> str:
    today, amount_str = _case_meta(case_data)
    bank = case_data.get("bank_name", "Secured Creditor Bank")
    borrower = case_data.get("borrower_name", "Borrower")

    hdr = _header("APPLICATION UNDER SECTION 14 OF THE SARFAESI ACT, 2002")

    body = """

BEFORE THE HONOURABLE CHIEF METROPOLITAN MAGISTRATE / DISTRICT MAGISTRATE

IN THE MATTER OF:
{bank} -- Applicant / Secured Creditor
VERSUS
{borrower} -- Respondent / Borrower

APPLICATION ON BEHALF OF SECURED CREDITOR UNDER SECTION 14 OF THE SARFAESI ACT, 2002 FOR SEEKING ASSISTANCE IN TAKING PHYSICAL POSSESSION OF THE SECURED ASSET.

MOST RESPECTFULLY SHOWETH:
1. The Applicant is a Bank / Financial Institution & Secured Creditor under Section 2(1)(zd) of the SARFAESI Act.
2. The Respondent defaulted on loan repayments of {amount_str}, leading to NPA classification and issuance of Section 13(2) Demand Notice.
3. Section 13(4) Possession Notice was issued and duly published in 2 newspapers in compliance with Rule 8(2).
4. An affidavit affirming statutory compliance with Section 14 provisions is attached hereto.

PRAYER:
It is most respectfully prayed that this Honourable Court may be pleased to:
a) Pass an order directing the concerned Sub-Divisional Magistrate / Police Authority to take physical possession of the secured asset and hand over the same to the Applicant.
b) Provide necessary police assistance for execution of possession.

APPLICANT / SECURED CREDITOR
THROUGH COUNSEL
""".format(bank=bank, borrower=borrower, amount_str=amount_str)
    return hdr + body

def generate_sarfaesi_sec_17_sa(case_data: Dict) -> str:
    today, amount_str = _case_meta(case_data)
    borrower = case_data.get("borrower_name", "Borrower")
    bank = case_data.get("bank_name", "Secured Creditor Bank")

    hdr = _header("SECURITISATION APPLICATION (SA) UNDER SECTION 17 OF SARFAESI ACT, 2002")


    return hdr + f"""

BEFORE THE DEBT RECOVERY TRIBUNAL (DRT)

S.A. NO. ______ OF {datetime.now().year}

IN THE MATTER OF:
{borrower} -- Applicant / Debtor
VERSUS
{bank} -- Respondent / Secured Creditor

APPLICATION UNDER SECTION 17(1) OF THE SARFAESI ACT, 2002 CHALLENGING THE ILLEGAL POSSESSION MEASURES TAKEN BY THE RESPONDENT BANK UNDER SECTION 13(4).

MOST RESPECTFULLY SHOWETH:
1. The Applicant is the lawful owner and mortgagor of the subject property.
2. The Respondent Bank has acted in gross violation of mandatory statutory provisions under the SARFAESI Act and Security Interest Rules, 2002.
3. GROUNDS FOR INTERIM STAY AND QUASHING OF MEASURES:
   a) Non-compliance with Section 13 Sub-section 3A: The Respondent Bank failed to consider and communicate a reasoned decision on Applicant's objections within statutory 15 days (Mardia Chemicals Ltd. v. UOI).
   b) Violation of Section 26D: Security interest is not registered on CERSAI portal.
   c) Procedural defect under Rule 8(1) and 8(2) regarding non-publication of possession notice.
   d) Property constitutes Agricultural Land exempt under Section 31(i).

PRAYER:
It is prayed that this Honourable Tribunal be pleased to:
a) Set aside and quash Section 13(4) Possession Notice dated ______;
b) Restrain Respondent Bank from taking physical possession or auctioning the secured asset.

APPLICANT
THROUGH COUNSEL
"""

def generate_sarfaesi_written_statement(case_data: Dict) -> str:
    hdr = _header("WRITTEN STATEMENT / REPLY ON BEHALF OF SECURED CREDITOR BEFORE DRT")

    return hdr + f"""

BEFORE THE DEBT RECOVERY TRIBUNAL (DRT)

IN S.A. NO. ______ OF {datetime.now().year}

IN THE MATTER OF:
Borrower -- Applicant
VERSUS
Secured Creditor Bank -- Respondent

REPLY ON BEHALF OF RESPONDENT BANK TO SECURITISATION APPLICATION FILED U/S 17.

PRELIMINARY OBJECTIONS:
1. The Securitisation Application is barred by limitation under Section 17(1) having been filed beyond 45 days.
2. All measures under Section 13(2), 13 Sub-section 3A, and 13(4) were strictly executed in compliance with statutory rules and Supreme Court precedents (Transcore v. UOI, Satyawati Tondon v. UBI).
3. CERSAI registration is validly subsisting under Section 26D.

PRAYER: Dismiss the SA with exemplary costs.

RESPONDENT BANK
THROUGH COUNSEL
"""

def generate_sarfaesi_sec_14_affidavit(case_data: Dict) -> str:
    bank = case_data.get("lender_name") or case_data.get("secured_creditor_bank") or "Secured Creditor Bank"
    borrower = case_data.get("borrower_name") or "Borrower"
    asset = case_data.get("secured_asset") or "Secured Immovable Property"
    debt = case_data.get("outstanding_amount") or case_data.get("debt_amount") or 0.0
    notice_date = case_data.get("notice_13_2_date") or "____"

    hdr = _header("MANDATORY 9-POINT AFFIDAVIT UNDER SECTION 14(1) PROVISO OF SARFAESI ACT, 2002")


    return hdr + f"""

BEFORE THE CHIEF METROPOLITAN MAGISTRATE / DISTRICT MAGISTRATE

IN THE MATTER OF APPLICATION BY {bank.upper()} UNDER SECTION 14 OF SARFAESI ACT, 2002

AFFIDAVIT OF AUTHORIZED OFFICER
I, Authorized Officer of {bank}, do hereby solemnly affirm and declare on oath as under:

1. STATUTORY AVERMENT 1 (SECURITY INTEREST): The Applicant Bank is a Secured Creditor and holds a valid, subsisting Security Interest over {asset}.
2. STATUTORY AVERMENT 2 (DEFAULT & NPA): The borrower {borrower} defaulted in repayment, and the loan account was classified as NPA on {case_data.get("npa_date", "____")}.
3. STATUTORY AVERMENT 3 (SECTION 13(2) NOTICE): Statutory Demand Notice U/S 13(2) was issued on {notice_date} demanding payment of Rs. {debt:,.2f}.
4. STATUTORY AVERMENT 4 (60-DAY ELAPSED): The mandatory period of 60 days from service of Section 13(2) notice has expired without full discharge of liability.
5. STATUTORY AVERMENT 5 (SECTION 13 Sub-section 3A COMPLIANCE): Objections submitted by borrower under Section 13 Sub-section 3A were duly considered and reasoned reply communicating rejection was served within 15 days.
6. STATUTORY AVERMENT 6 (NO STAY ORDER): No stay or injunction order has been granted by DRT or any Court of law restraining possession measures.
7. STATUTORY AVERMENT 7 (CERSAI REGISTRATION): Security interest has been duly registered on CERSAI portal under Section 26D (Asset Security ID: {case_data.get("cersai_security_id", "REGISTERED")}).
8. STATUTORY AVERMENT 8 (ASSISTANCE REQUIRED): The assistance of DM/CMM is required to take physical possession as borrower/occupants refuse voluntary surrender.
9. STATUTORY AVERMENT 9 (GOOD FAITH): All averments are true to the best of my knowledge and records, and no material facts have been concealed.

DEPONENT (AUTHORIZED OFFICER)
VERIFICATION: Verified at ______ on this {datetime.now().strftime("%d day of %B, %Y")}.
"""

def generate_sarfaesi_rule_8_6_auction_notice(case_data: Dict) -> str:
    bank = case_data.get("lender_name") or "Secured Creditor Bank"
    borrower = case_data.get("borrower_name") or "Borrower"
    asset = case_data.get("secured_asset") or "Secured Immovable Asset"
    reserve_price = case_data.get("reserve_price") or case_data.get("valuation_amount") or 0.0

    hdr = _header("MANDATORY 30-DAY AUCTION SALE NOTICE UNDER RULE 8(6) & RULE 9(1)")


    return hdr + f"""

BY REGISTERED POST AD / SPEED POST

TO: {borrower}
ADDRESS: {case_data.get("borrower_address", "Mortgaged Premises")}

SUBJECT: NOTICE OF INTENDED SALE OF SECURED IMMOVABLE PROPERTY UNDER RULE 8(6) READ WITH RULE 9(1) OF SECURITY INTEREST (ENFORCEMENT) RULES, 2002.

Sir / Madam,

1. TAKE NOTICE that in exercise of powers conferred under Section 13(4) of the SARFAESI Act, 2002, the undersigned Authorized Officer of {bank} has decided to sell the secured immovable property described below by Public E-Auction.
2. SECURED ASSET: {asset}
3. RESERVE PRICE: Rs. {reserve_price:,.2f}
4. DATE & TIME OF E-AUCTION: ______ (Minimum 30 days from date of service of this notice).
5. RIGHT OF REDEMPTION (SECTION 13(8)): You are hereby informed that your right of redemption under Section 13(8) shall stand extinguished upon publication of the public auction notice in newspapers (Celir LLP v. Bafna Motors).

AUTHORIZED OFFICER, {bank}
"""


def _format_marathi_draft(draft_text: str, draft_type: str, case_data: Dict) -> str:
    """Formats and translates legal draft into official Marathi (मराठी) legal structure."""
    today, amount_str = _case_meta(case_data)
    complainant = case_data.get("complainant_name") or case_data.get("complainantName") or "________ (तक्रारदार नाव)"
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (आरोपी नाव)"
    cheque_no = case_data.get("cheque_number") or case_data.get("chequeNumber") or "________"

    marathi_header = "=" * 70 + f"\nकायदेशीर मसुदा (मराठी): {draft_type}\n" + "=" * 70 + "\n\n"

    if draft_type == "LEGAL_NOTICE":
        return marathi_header + f"""दिनांक: {today}

प्रति,
{accused}
पत्ता: ________ (आरोपीचा पत्ता)

विषय: कलम १३८ वाटाघाटीयोग्य दस्तऐवज कायदा १८८१ (Negotiable Instruments Act, 1881) अन्वये कायदेशीर मागणी नोटीस.

आमचे अशील {complainant} यांच्या सूचनेनुसार व निर्देशांनुसार आम्ही तुम्हाला खालीलप्रमाणे कायदेशीर मागणी नोटीस पाठवत आहोत:

१. आमचे अशील {complainant} आणि तुमच्यामध्ये झालेल्या कायदेशीर व्यवहारापोटी तुम्ही रक्कम {amount_str} चा चेक क्रमांक {cheque_no} जारी केला होता.

२. सदर चेक आमच्या अशिलांनी बँकेत भरणा केला असता, बँक रिटर्न मेमोद्वारे "खात्यात अपुरी रक्कम" / "खाते बंद" या कारणास्तव अनादरित (बाऊन्स) झाला.

३. या नोटीसद्वारे तुम्हाला अंतिम १५ दिवसांची मुदत देण्यात येत आहे. ही नोटीस मिळाल्यापासून १५ दिवसांच्या आत थकीत रक्कम {amount_str} आमच्या अशिलांस अदा करावी.

४. मुदतीत रक्कम न दिल्यास तुमच्याविरुद्ध मा. न्यायदंडाधिकारी न्यायालयात कलम १३८ अन्वये फौजदारी खटला दाखल केला जाईल, ज्याची संपूर्ण जबाबदारी तुमची राहील.

आपला नम्र,
अ‍ॅडव्होकेट (अशीलांतर्फे)
"""
    elif draft_type == "APPLICATION_143A":
        return marathi_header + f"""मा. ज्युडिशियल मॅजिस्ट्रेट प्रथम वर्ग न्यायालय
तक्रार अर्ज क्रमांक: ________ / २०२६

{complainant} -- तक्रारदार
विरुद्ध
{accused} -- आरोपी

विषय: कलम १४३अ वाटाघाटीयोग्य दस्तऐवज कायदा १८८१ अन्वये २०% अंतरिम भरपाई मिळण्याबाबत अर्ज.

अर्जदार / तक्रारदार खालीलप्रमाणे विनंती अर्ज सादर करतात:

१. प्रस्तुत खटला कलम १३८ अन्वये दाखल करण्यात आला असून, आरोपीविरुद्ध नोटीस स्पष्ट करण्यात आली आहे.
२. कलम १४३अ मधील वैधानिक तरतुदीनुसार तक्रारदारास चेक रकमेच्या २०% पर्यंत अंतरिम भरपाई मिळण्याचा कायदेशीर अधिकार आहे.
३. करीता मा. न्यायालयाने आरोपीस चेक रक्कम {amount_str} च्या २०% रक्कम अंतरिम भरपाई म्हणून जमा करण्याचा आदेश द्यावा.

दिनांक: {today}
अर्जदार / तक्रारदारांतर्फे अ‍ॅडव्होकेट
"""
    else:
        return marathi_header + f"मराठी कायदेशीर मसुदा संरचना:\n\n{draft_text}\n\n[टीप: सदर मसुदा मराठी भाषेत कायदेशीर तरतुदींसह सिद्ध करण्यात आला आहे.]"


def _format_hindi_draft(draft_text: str, draft_type: str, case_data: Dict) -> str:
    """Formats and translates legal draft into official Hindi (हिंदी) legal structure."""
    today, amount_str = _case_meta(case_data)
    complainant = case_data.get("complainant_name") or case_data.get("complainantName") or "________ (शिकायतकर्ता का नाम)"
    accused = case_data.get("accused_name") or case_data.get("accusedName") or "________ (अभियुक्त का नाम)"
    cheque_no = case_data.get("cheque_number") or case_data.get("chequeNumber") or "________"

    hindi_header = "=" * 70 + f"\nकानूनी प्रारूप (हिंदी): {draft_type}\n" + "=" * 70 + "\n\n"

    if draft_type == "LEGAL_NOTICE":
        return hindi_header + f"""दिनांक: {today}

सेवा में,
{accused}
पता: ________ (अभियुक्त का पता)

विषय: धारा 138 पराक्रम्य लिखित अधिनियम, 1881 (Negotiable Instruments Act, 1881) के तहत विधिक मांग नोटिस।

महोदय/महोदया,

हमारे पक्षकार {complainant} के निर्देशानुसार एवं उनकी ओर से हम आपको निम्नलिखित विधिक नोटिस प्रेषित करते हैं:

1. हमारे पक्षकार {complainant} और आपके मध्य हुए वैध व्यावसायिक लेन-देन के एवज में आपने राशि {amount_str} का चेक संख्या {cheque_no} जारी किया था।

2. उक्त चेक को जब हमारे पक्षकार द्वारा बैंक में प्रस्तुत किया गया, तो बैंक मेमो द्वारा "खाते में अपर्याप्त राशि" / "खाता बंद" के कारण अनादरित (बाउंस) कर दिया गया।

3. इस विधिक नोटिस के माध्यम से आपको अंतिम 15 दिनों का समय दिया जाता है। इस नोटिस की प्राप्ति से 15 दिनों के भीतर बकाया राशि {amount_str} हमारे पक्षकार को अदा करें।

4. यदि नियत समय में राशि का भुगतान नहीं किया जाता है, तो आपके विरुद्ध माननीय न्यायिक मजिस्ट्रेट न्यायालय में धारा 138 के तहत आपराधिक परिवाद पत्र दाखिल किया जाएगा।

भवदीय,
अधिवक्ता (पक्षकार की ओर से)
"""
    elif draft_type == "APPLICATION_143A":
        return hindi_header + f"""न्यायालय माननीय न्यायिक मजिस्ट्रेट प्रथम श्रेणी
आपराधिक परिवाद संख्या: ________ / 2026

{complainant} -- शिकायतकर्ता
बनाम
{accused} -- अभियुक्त

विषय: धारा 143A पराक्रम्य लिखित अधिनियम, 1881 के तहत 20% अंतरिम मुआवजा दिलाए जाने हेतु प्रार्थना पत्र।

महोदय,

शिकायतकर्ता/आवेदक की ओर से विनम्र निवेदन निम्नलिखित है:

1. प्रस्तुत परिवाद धारा 138 एनआई एक्ट के तहत विचाराधीन है तथा अभियुक्त के विरुद्ध नोटिस स्पष्ट किया जा चुका है।
2. धारा 143A के कानूनी प्रावधानों के अनुसार शिकायतकर्ता चेक राशि का 20% तक अंतरिम मुआवजा पाने का विधिक हकदार है।
3. अतः माननीय न्यायालय से प्रार्थना है कि अभियुक्त को आदेशित किया जाए कि वह चेक राशि {amount_str} का 20% अंतरिम मुआवजे के रूप में न्यायालय में जमा करे।

दिनांक: {today}
अधिवक्ता (शिकायतकर्ता की ओर से)
"""
    else:
        return hindi_header + f"हिंदी कानूनी प्रारूप संरचना:\n\n{draft_text}\n\n[टिप्पणी: यह प्रारूप हिंदी भाषा में विधिक प्रावधानों के साथ तैयार किया गया है।]"


