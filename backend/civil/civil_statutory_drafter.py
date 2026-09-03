"""
JudiQ AI — Civil & Commercial Statutory Drafter
Generates institutional-grade, court-ready plaints, interim applications,
Statements of Truth, and defense petitions under CPC and Commercial Courts Act.
"""

from typing import Dict, Any
from datetime import datetime

class CivilStatutoryDrafter:
    """
    Generates court pleadings adhering to Order VI, VII, VIII, XXXVII, and XXXIX CPC formats.
    """

    @classmethod
    def draft_commercial_plaint(cls, case_data: Dict[str, Any]) -> str:
        court = case_data.get("court_name", "IN THE COURT OF THE DISTRICT JUDGE (COMMERCIAL DIVISION)")
        plaintiff = case_data.get("plaintiff_name", "PLAINTIFF PVT LTD")
        defendant = case_data.get("defendant_name", "DEFENDANT CORP LTD")
        suit_val = float(case_data.get("suit_valuation_amount", 5000000.0))
        coa_date = case_data.get("cause_of_action_date", "2024-05-10")
        today = datetime.now().strftime("%d-%m-%Y")

        return f"""{court.upper()}
COMMERCIAL SUIT NO. ________ OF 2026

IN THE MATTER OF:
{plaintiff.upper()}
... PLAINTIFF

VERSUS

{defendant.upper()}
... DEFENDANT

SUIT FOR RECOVERY OF ₹{suit_val:,.2f} ALONG WITH PENDENTE LITE AND FUTURE INTEREST UNDER SECTION 34 CPC READ WITH COMMERCIAL COURTS ACT, 2015

MOST RESPECTFULLY SHOWETH:

1. THE PARTIES:
That the Plaintiff is a registered corporate entity having its principal place of business at the address mentioned in the memo of parties. The Defendant is a corporate commercial entity transacting business within the territorial jurisdiction of this Hon'ble Court.

2. COMMERCIAL DISPUTE & SPECIFIED VALUE:
That the present dispute arises out of a commercial contract and qualifies as a "Commercial Dispute" within the meaning of Section 2(1)(c) of the Commercial Courts Act, 2015. The Specified Value of the claim is ₹{suit_val:,.2f}, which exceeds the statutory threshold of ₹3,00,000 u/s 2(1)(i).

3. COMPLIANCE WITH SECTION 12A (PIMS):
That the Plaintiff has duly complied with Section 12A of the Commercial Courts Act, 2015, or is seeking urgent interim relief under Order XXXIX Rules 1 & 2 CPC concurrently herewith.

4. CAUSE OF ACTION & LIMITATION:
That the cause of action first arose on {coa_date} upon the Defendant's contractual breach and non-payment. The suit is instituted within the 3-year period of limitation under Article 55 of the Limitation Act, 1963.

5. PRAYER:
WHEREFORE, it is most respectfully prayed that this Hon'ble Court may be pleased to:
(a) Pass a Money Decree for a sum of ₹{suit_val:,.2f} in favour of the Plaintiff and against the Defendant;
(b) Award pendente lite and future commercial interest @ 18% per annum under Section 34 CPC from the date of default till actual realization;
(c) Award costs of the suit in favour of the Plaintiff;
(d) Pass such other and further relief(s) as this Hon'ble Court deems fit and proper.

DATED: {today}
PLACE: _______________
ADVOCATE FOR PLAINTIFF

----------------------------------------------------------------------
STATEMENT OF TRUTH UNDER ORDER VI RULE 15A CPC
(Commercial Courts Act, 2015)

I, the authorized representative of the Plaintiff, do hereby solemnly affirm and state as under:
1. I say that I am the Authorized Signatory of the Plaintiff in the above suit and am conversant with the facts of the case.
2. I say that the statements contained in paragraphs 1 to 5 of the plaint are true and correct to my personal knowledge derived from the commercial books and records of the Plaintiff.
3. I say that all documents in my power, possession, and control relating to the commercial dispute have been disclosed and produced herewith.

DEPONENT
VERIFICATION: Verified at _______________ on this {today} that the contents of the above affidavit are true and correct.
DEPONENT
"""

    @classmethod
    def draft_order39_application(cls, case_data: Dict[str, Any]) -> str:
        plaintiff = case_data.get("plaintiff_name", "PLAINTIFF PVT LTD")
        defendant = case_data.get("defendant_name", "DEFENDANT CORP LTD")
        today = datetime.now().strftime("%d-%m-%Y")

        return f"""APPLICATION UNDER ORDER XXXIX RULES 1 & 2 READ WITH SECTION 151 CPC FOR AD-INTERIM EX-PARTE TEMPORARY INJUNCTION

IN THE MATTER OF:
{plaintiff} ... APPLICANT/PLAINTIFF
VERSUS
{defendant} ... RESPONDENT/DEFENDANT

MOST RESPECTFULLY SHOWETH:

1. That the Applicant has instituted the accompanying Suit for Specific Performance / Declaration before this Hon'ble Court. The contents of the Plaint may be read as part and parcel of this Application.

2. PRIMA FACIE CASE:
That the Applicant has established an unimpeachable documentary title and registered agreement on record. The Applicant satisfies the first prong of the Golden Triad as laid down in Dalpat Kumar v. Prahlad Singh (1992) 1 SCC 719.

3. BALANCE OF CONVENIENCE:
That the balance of convenience lies overwhelmingly in favour of the Applicant. If the Respondent is permitted to alienate or create third-party encumbrance over the suit property pending adjudication, the subject matter of the suit will be permanently defeated (Wander Ltd v. Antox India).

4. IRREPARABLE INJURY:
That the Applicant will suffer grave, irreversible, and irreparable injury incapable of being compensated in monetary terms if ad-interim protection is not granted forthwith.

5. PRAYER:
It is therefore respectfully prayed that this Hon'ble Court may be pleased to:
(a) Pass an ad-interim ex-parte injunction restraining the Respondent, its directors, agents, and assigns from selling, transferring, leasing, mortgaging, or creating any third-party interest in the suit property till the disposal of the suit;
(b) Pass such other or further order(s) as this Hon'ble Court may deem fit.

APPLICANT THROUGH COUNSEL
DATED: {today}
"""

    @classmethod
    def draft_order7_rule11_application(cls, case_data: Dict[str, Any]) -> str:
        plaintiff = case_data.get("plaintiff_name", "PLAINTIFF")
        defendant = case_data.get("defendant_name", "DEFENDANT")
        ground = case_data.get("order7_rule11_ground", "Barred by Limitation / Section 12A PIMS Omission")
        today = datetime.now().strftime("%d-%m-%Y")

        return f"""APPLICATION UNDER ORDER VII RULE 11 READ WITH SECTION 151 CPC FOR REJECTION OF PLAINT

IN THE MATTER OF:
{plaintiff} ... PLAINTIFF
VERSUS
{defendant} ... DEFENDANT/APPLICANT

MOST RESPECTFULLY SHOWETH:

1. That the Plaintiff has filed the present suit which is an abuse of judicial process and is barred by law under Order VII Rule 11 CPC.

2. THRESHOLD STATUTORY BAR:
That on a demurrer reading of the plaint itself, the suit is fatally defective on the following ground:
GROUND: {ground}

3. JUDICIAL AUTHORITY:
That as laid down by the Hon'ble Supreme Court in Dahiben v. Arvindbhai Kalyanji Bhanusali (2020) 7 SCC 366 and Patil Automation Pvt Ltd v. Rakheja Engineers Pvt Ltd (2022) 10 SCC 1, it is the bounden duty of the Court to reject a plaint at the threshold when it is barred by limitation or statutory mandate.

4. PRAYER:
WHEREFORE, the Applicant respectfully prays that this Hon'ble Court may be pleased to reject the Plaint under Order VII Rule 11 CPC with exemplary costs.

APPLICANT/DEFENDANT THROUGH COUNSEL
DATED: {today}
"""
