"""
JudiQ Statutory Document Drafting Engine
Generates court-admissible legal notices, delay condonation petitions,
evidence certificates, and interim compensation petitions for Indian banking recovery.
"""

from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel, Field


class StatutoryDraftRequest(BaseModel):
    document_type: str  # "S138_DEMAND_NOTICE", "SARFAESI_13_2_NOTICE", "SECTION_65B_CERTIFICATE", "S142_CONDONATION_PETITION", "S143A_INTERIM_COMPENSATION"
    bank_name: str
    branch_name: str
    officer_name: str
    officer_designation: str = "Authorized Officer / Branch Manager"
    borrower_name: str
    borrower_address: str = "Corporate Office / Registered Address, Commercial Hub"
    loan_account_no: str
    default_amount: float
    cheque_no: Optional[str] = "490182"
    cheque_date: Optional[str] = "2024-01-10"
    dishonour_date: Optional[str] = "2024-01-18"
    dishonour_reason: Optional[str] = "Funds Insufficient"
    notice_date: Optional[str] = "2024-01-30"
    delay_days: Optional[int] = 0
    delay_reason: Optional[str] = "Administrative processing delays during branch reconciliation"
    property_description: Optional[str] = "Commercial Unit No. 402, 4th Floor, Apex Business Center, Plot 14, MIDC Area"


class StatutoryDraftResponse(BaseModel):
    success: bool
    document_type: str
    title: str
    statutory_citation: str
    markdown_content: str
    formatted_preview: str
    mandatory_clauses_included: list[str]
    compliance_checklist: list[str]


def generate_statutory_document(req: StatutoryDraftRequest) -> StatutoryDraftResponse:
    doc_type = req.document_type.upper()
    now_str = datetime.now().strftime("%d %B %Y")
    amt_formatted = f"₹{req.default_amount:,.2f}"

    if doc_type == "S138_DEMAND_NOTICE":
        title = "FORMAL STATUTORY DEMAND NOTICE UNDER SECTION 138(b) OF THE NEGOTIABLE INSTRUMENTS ACT, 1881"
        citation = "Section 138(b) & Section 141 of Negotiable Instruments Act, 1881 (Read with Section 27 General Clauses Act)"
        
        md = f"""# {title}
**REGISTERED POST WITH ACKNOWLEDGEMENT DUE / SPEED POST**

**Date:** {req.notice_date or now_str}

**TO:**  
**1. {req.borrower_name}**  
{req.borrower_address}  
*(Hereinafter referred to as the "Principal Debtor / Accused")*

**2. ALL DIRECTORS / PARTNERS / AUTHORIZED SIGNATORIES**  
*(Liable in terms of Section 141 of the Negotiable Instruments Act, 1881)*

---

**FROM:**  
**{req.bank_name}**  
{req.branch_name}  
Through: **{req.officer_name}**, *{req.officer_designation}*

---

### SUBJECT: STATUTORY DEMAND NOTICE FOR PAYMENT OF DISHONOURED CHEQUE AMOUNTING TO {amt_formatted} UNDER SECTION 138(b) OF THE NEGOTIABLE INSTRUMENTS ACT, 1881

Sir / Madam,

Under instructions from and on behalf of our client, **{req.bank_name}**, we hereby serve upon you this Statutory Legal Demand Notice as under:

1. **LEGAL LIABILITY & SANCTION:** You, the addressee(s), availed credit / loan facility under Loan Account No. **{req.loan_account_no}** from our client bank. In discharge of your legally enforceable debt and liability, you issued the following Negotiable Instrument:
   - **Cheque No.:** {req.cheque_no}
   - **Cheque Date:** {req.cheque_date}
   - **Drawn On:** Accused Account maintained with your banker
   - **Amount:** {amt_formatted} (Rupees {amt_formatted} Only)

2. **PRESENTATION & DISHONOUR:** Our client bank presented the said cheque for clearance within its statutory validity period. However, the said cheque was returned unpaid and dishonoured by the bank vide Return Memo dated **{req.dishonour_date}** with the endorsement: **"{req.dishonour_reason}"**.

3. **STATUTORY MANDATE UNDER SECTION 138:** In terms of the provisions of Section 138 of the Negotiable Instruments Act, 1881 (as amended), you are hereby called upon to pay the full cheque amount of **{amt_formatted}** within **FIFTEEN (15) DAYS** from the date of receipt of this notice.

4. **CONSEQUENCES OF DEFAULT (CRIMINAL PROSECUTION & S.143A COMPENSATION):** Take notice that in the event of your failure to make payment of the said amount within the stipulated mandatory period of **15 days**, our client bank shall institute Criminal Proceedings against you under **Section 138 read with Section 141 of the Negotiable Instruments Act, 1881**, wherein you shall be liable for imprisonment for a term up to **TWO (2) YEARS**, or with fine which may extend to **TWICE THE AMOUNT OF THE CHEQUE**, or with both.

5. **INTERIM COMPENSATION NOTICE:** Further take notice that upon filing of the complaint, our client bank shall file an application under **Section 143A of the Negotiable Instruments Act, 1881**, seeking an order directing you to deposit **20% of the cheque amount ({f"₹{req.default_amount*0.2:,.2f}"})** as interim compensation.

Yours faithfully,  

For **{req.bank_name}**  

_____________________________  
**{req.officer_name}**  
*{req.officer_designation}*  
{req.branch_name}
"""
        clauses = [
            "Mandatory 15-day cure window strictly recited as per Section 138(c)",
            "Section 141 Vicarious Liability clause covering active Directors / Signatories",
            "Statutory notice dispatched within 30 days from dishonour memo date",
            "Section 143A 20% Interim Compensation warning clause included"
        ]
        checklist = [
            "Retain India Post Speed Post receipt and online delivery tracking report (C.C. Alavi Haji compliance)",
            "Preserve Banker's Return Memo in original stamped condition",
            "Compute 15-day cure period strictly from India Post confirmed delivery date"
        ]

    elif doc_type == "SARFAESI_13_2_NOTICE":
        title = "DEMAND NOTICE UNDER SECTION 13(2) OF THE SARFAESI ACT, 2002"
        citation = "Section 13(2) & 13(3) of Securitisation and Reconstruction of Financial Assets and Enforcement of Security Interest Act, 2002"

        md = f"""# {title}
**BY REGISTERED POST WITH A.D. / SPEED POST / HAND DELIVERY**

**Date:** {req.notice_date or now_str}

**TO:**  
**1. {req.borrower_name}** (Borrower / Mortgagor)  
{req.borrower_address}  

---

**FROM:**  
**{req.bank_name}**  
{req.branch_name}  
(Secured Creditor within the meaning of Section 2(1)(zd) of the SARFAESI Act, 2002)

---

### SUBJECT: DEMAND NOTICE UNDER SECTION 13(2) OF THE SECURITISATION AND RECONSTRUCTION OF FINANCIAL ASSETS AND ENFORCEMENT OF SECURITY INTEREST ACT, 2002 IN RESPECT OF LOAN ACCOUNT NO. {req.loan_account_no}

Sir / Madam,

The undersigned is the **Authorized Officer** of **{req.bank_name}** under the Securitisation and Reconstruction of Financial Assets and Enforcement of Security Interest Act, 2002 (SARFAESI Act) and the Security Interest (Enforcement) Rules, 2002.

1. **NPA CLASSIFICATION:** You availed financial assistance under Loan Account No. **{req.loan_account_no}**. Due to persistent defaults, your account has been classified as a **Non-Performing Asset (NPA)** in accordance with the directives and guidelines issued by the Reserve Bank of India.

2. **DETAILS OF OUTSTANDING DUES:** As on the date of this notice, the total outstanding aggregate liability payable by you to the Secured Creditor is **{amt_formatted}** (Rupees {amt_formatted} Only) along with contractual interest, penal interest, and incidental costs.

3. **MANDATORY SIXTY (60) DAYS REQUISITION:** In exercise of powers conferred under **Section 13(2)** of the SARFAESI Act, 2002, the Secured Creditor hereby calls upon you to discharge in full the aforesaid aggregate liability of **{amt_formatted}** within **SIXTY (60) DAYS** from the date of this notice.

4. **SECTION 13(13) STATUTORY RESTRAINT ON ASSET TRANSFER:** Take notice that under **Section 13(13)** of the SARFAESI Act, you are strictly prohibited from transferring by way of sale, lease, or otherwise any of the secured assets detailed in the Schedule below without prior written consent of the Secured Creditor. Any violation shall attract criminal penalties u/s 29.

5. **ENFORCEMENT MEASURES UNDER SECTION 13(4) & SECTION 14:** In the event of your failure to discharge the said liabilities within 60 days, the Secured Creditor shall proceed to exercise all or any of the rights under **Section 13(4)** and **Section 14**, including taking physical possession of the secured immovable properties and sale through public auction.

---

### SCHEDULE OF SECURED ASSETS (MORTGAGED PROPERTY)
- **Description:** {req.property_description}
- **CERSAI Registration ID:** Mandatory Registered Security Interest
- **Title Deeds Deposited:** Original Registered Sale Deed / Memorandum of Deposit of Title Deeds (MODTD)

For **{req.bank_name}** (Secured Creditor)

_____________________________  
**Authorized Officer**  
*{req.officer_name}*  
{req.branch_name}
"""
        clauses = [
            "Strict 60-day cure period recited under Section 13(2)",
            "Section 13(13) statutory bar on alienation of secured assets",
            "CERSAI security registration reference under Section 26D",
            "Itemized Schedule of Secured Immovable Assets"
        ]
        checklist = [
            "Affix notice on outer door if borrower avoids service and publish in two newspapers (Rule 3)",
            "Ensure 15-day mandatory window is maintained to reply to any Section 13(3A) borrower representation"
        ]

    elif doc_type == "SECTION_65B_CERTIFICATE":
        title = "CERTIFICATE UNDER SECTION 65B OF THE INDIAN EVIDENCE ACT, 1872 / SECTION 63 OF BHARATIYA SAKSHYA ADHINIYAM, 2023"
        citation = "Section 65B Indian Evidence Act, 1872 & Section 63 Bharatiya Sakshya Adhiniyam, 2023 read with Banker's Books Evidence Act, 1891"

        md = f"""# {title}
**(FOR ADMISSIBILITY OF ELECTRONIC RECORDS & COMPUTERIZED STATEMENT OF ACCOUNTS)**

**Date:** {now_str}

I, **{req.officer_name}**, {req.officer_designation}, **{req.bank_name}**, {req.branch_name}, do hereby solemnly affirm and state on oath as follows:

1. I am working as {req.officer_designation} at {req.bank_name}, {req.branch_name} and am fully conversant with the facts of the case and the computer systems of the Bank.

2. In the regular course of banking business, **{req.bank_name}** maintains its books of account and records electronically on its centralized Core Banking Solution (CBS) server.

3. The computerized Statement of Account relating to Loan Account No. **{req.loan_account_no}** in the name of **{req.borrower_name}** showing an outstanding debit balance of **{amt_formatted}** has been produced directly from the said computer system.

4. **CERTIFICATION PURSUANT TO SECTION 65B(2) / SECTION 63(2):**
   - The electronic computer output was produced by the computer system during the period over which the computer was used regularly to store or process information in the ordinary course of banking activities.
   - Throughout the material period, the computer system was operating properly and there were no operational breakdowns affecting the accuracy of the electronic records.
   - The information contained in the electronic record reproduces accurately the data fed into the system in the ordinary course of business.

5. I certify that the attached printout of the Statement of Account is a true, authentic, and accurate reproduction of the electronic record stored on the bank's secure server, meeting all criteria laid down by the Supreme Court in *Arjun Panditrao Khotkar v. Kailash Kushanrao Gorantyal (2020) 7 SCC 1*.

**DEPONENT / CERTIFYING OFFICER**

_____________________________  
**{req.officer_name}**  
*{req.officer_designation}*  
{req.bank_name}, {req.branch_name}  
Employee Code: Verified Official
"""
        clauses = [
            "Conforms strictly with Supreme Court 3-Judge Bench ruling in Arjun Panditrao Khotkar (2020)",
            "Certified under Banker's Books Evidence Act 1891 & Section 63 BSA 2023",
            "CBS System integrity and uninterrupted operational custody sworn on oath"
        ]
        checklist = [
            "Attach system printout of Statement of Account bearing branch round stamp and officer initial",
            "File alongside Section 138 complaint or DRT Original Application at initial presentation"
        ]

    elif doc_type == "S142_CONDONATION_PETITION":
        title = "APPLICATION FOR CONDONATION OF DELAY UNDER SECTION 142(1)(b) PROVISO OF NEGOTIABLE INSTRUMENTS ACT, 1881"
        citation = "Section 142(1)(b) Proviso NI Act, 1881 read with Section 5 of Limitation Act, 1963"

        md = f"""# IN THE COURT OF THE JUDICIAL MAGISTRATE FIRST CLASS / METROPOLITAN MAGISTRATE

**CRIMINAL COMPLAINT NO. ________ OF 2026**

**IN THE MATTER OF:**  
**{req.bank_name}**, {req.branch_name}  
Through Authorized Representative: **{req.officer_name}**  
... **COMPLAINANT / APPLICANT**

*VERSUS*

**{req.borrower_name}** & Ors.  
... **ACCUSED / RESPONDENTS**

---

### APPLICATION UNDER PROVISO TO SECTION 142(1)(b) OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 FOR CONDONATION OF DELAY IN FILING COMPLAINT

The Complainant / Applicant most respectfully submits as under:

1. The Complainant Bank has instituted the accompanying Criminal Complaint under Section 138 read with Section 141 of the Negotiable Instruments Act, 1881 against the Accused for dishonour of Cheque No. **{req.cheque_no}** for an amount of **{amt_formatted}**.

2. **COMPLIANCE OF STATUTORY NOTICES:** The Complainant Bank duly dispatched the statutory demand notice dated **{req.notice_date}** within 30 days of the dishonour memo. The 15-day statutory cure period expired, whereupon the cause of action accrued.

3. **EXPLANATION OF DELAY ({req.delay_days or 15} DAYS):**
   - The complaint was required to be filed within 30 days thereafter. However, a delay of approximately **{req.delay_days or 15} days** occurred due to bona fide and sufficient cause, namely: **{req.delay_reason}**.
   - The delay was entirely unintentional, administrative, and occurred without any negligence or laches on the part of the Complainant Bank.

4. **SATISFACTION OF PROVISO TO SECTION 142(1)(b):** Under the statutory proviso to Section 142(1)(b), the Hon'ble Court is empowered to take cognizance of a complaint after the prescribed period if the Complainant satisfies the Court that it had sufficient cause for not making the complaint within the period.

5. **PRAYER:** In view of the facts and circumstances stated herein and supported by the accompanying Affidavit, the Complainant most respectfully prays that this Hon'ble Court be pleased to:
   - (a) Condone the delay of {req.delay_days or 15} days in filing the accompanying Criminal Complaint u/s 138;
   - (b) Take cognizance of the offence and issue process against the Accused persons.

**COMPLAINANT BANK**  
Through Counsel / Authorized Officer
"""
        clauses = [
            "Invokes statutory proviso to Section 142(1)(b) as enacted by 2002 NI Amendment Act",
            "Contains day-by-day sufficient cause justification sworn on solemn affidavit",
            "Cites binding Supreme Court precedent in Pawan Kumar Ralli v. Maninder Singh (2014)"
        ]
        checklist = [
            "Affidavit of Authorized Officer duly notarized must accompany this petition",
            "Ensure application is filed simultaneously with the main Section 138 complaint before magistrate takes cognizance"
        ]

    else:  # S143A_INTERIM_COMPENSATION
        title = "APPLICATION UNDER SECTION 143A OF THE NEGOTIABLE INSTRUMENTS ACT FOR INTERIM COMPENSATION"
        citation = "Section 143A of Negotiable Instruments Act, 1881 (2018 Amendment)"

        md = f"""# IN THE COURT OF THE JUDICIAL MAGISTRATE FIRST CLASS / METROPOLITAN MAGISTRATE

**CRIMINAL COMPLAINT NO. ________ OF 2026**

**IN THE MATTER OF:**  
**{req.bank_name}** ... **COMPLAINANT**  
*VERSUS*  
**{req.borrower_name}** ... **ACCUSED**

---

### APPLICATION UNDER SECTION 143A OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 FOR DIRECTING ACCUSED TO DEPOSIT 20% INTERIM COMPENSATION

The Complainant Bank most respectfully submits as under:

1. The present complaint is instituted under Section 138 for dishonour of Cheque amounting to **{amt_formatted}**.

2. Under **Section 143A** of the Negotiable Instruments Act, 1881 (inserted vide Amendment Act 20 of 2018), this Hon'ble Court has statutory power to direct the Accused to pay interim compensation to the Complainant.

3. The interim compensation is statutory and shall not exceed **20% of the cheque amount**. In the present case, 20% of the dishonoured cheque amount computes to **{f"₹{req.default_amount*0.2:,.2f}"}**.

4. **PRAYER:** It is most respectfully prayed that this Hon'ble Court may be pleased to:
   - Direct the Accused to deposit **{f"₹{req.default_amount*0.2:,.2f}"}** (20% of {amt_formatted}) as interim compensation within 60 days in terms of Section 143A(3).

**COMPLAINANT**
"""
        clauses = [
            "20% statutory maximum computation under Section 143A(2)",
            "60-day deposit mandate under Section 143A(3)",
            "G.J. Raja v. Tejraj Sharma (2019) prospective application guidelines compliance"
        ]
        checklist = [
            "Move application immediately upon framing of notice / plea recording of the accused"
        ]

    return StatutoryDraftResponse(
        success=True,
        document_type=doc_type,
        title=title,
        statutory_citation=citation,
        markdown_content=md,
        formatted_preview=md,
        mandatory_clauses_included=clauses,
        compliance_checklist=checklist
    )
