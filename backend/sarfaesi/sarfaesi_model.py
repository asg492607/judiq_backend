from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class LoanFacility(BaseModel):
    loan_account_number: Optional[str] = Field(None, description="Loan Account Number / Facility ID")
    facility_type: Optional[str] = Field(default="Term Loan / Cash Credit", description="Category of credit facility")
    sanction_date: Optional[str] = None
    sanctioned_amount: Optional[float] = Field(default=0.0, ge=0.0)
    outstanding_amount: Optional[float] = Field(default=0.0, ge=0.0)
    npa_date: Optional[str] = None
    irac_classification: Optional[str] = Field(default="Sub-Standard", description="NPA classification under RBI IRAC norms")
    default_amount: Optional[float] = Field(default=0.0, ge=0.0)

class SecuredParties(BaseModel):
    secured_creditor_bank: str = Field(default="Secured Creditor Bank")
    bank_branch: Optional[str] = None
    authorized_officer_name: Optional[str] = None
    borrower_name: str = Field(default="Borrower")
    co_borrowers: List[str] = Field(default_factory=list)
    guarantors: List[str] = Field(default_factory=list)
    mortgagors: List[str] = Field(default_factory=list)

class MortgagedSecurity(BaseModel):
    asset_id: Optional[str] = Field(None, description="Property ID / CERSAI Asset ID")
    property_description: Optional[str] = None
    is_agricultural_land: bool = Field(default=False, description="Section 31(i) exemption check")
    cersai_registered: bool = Field(default=False, description="Section 26D mandatory portal registration")
    cersai_security_id: Optional[str] = None
    valuation_amount: Optional[float] = Field(default=0.0, ge=0.0)
    valuation_date: Optional[str] = None
    reserve_price: Optional[float] = Field(default=0.0, ge=0.0)

class EnforcementMeasures(BaseModel):
    notice_13_2_date: Optional[str] = None
    notice_13_2_served: bool = True
    borrower_representation_date: Optional[str] = None
    bank_reply_13_3a_date: Optional[str] = None
    possession_13_4_date: Optional[str] = None
    possession_type: Optional[str] = Field(default="Symbolic", description="Symbolic or Physical")
    newspaper_publication_done: bool = Field(default=False, description="Rule 8(2) 2-newspaper publication check")
    dm_application_date: Optional[str] = None
    dm_order_date: Optional[str] = None
    auction_notice_date: Optional[str] = None
    auction_publication_date: Optional[str] = None
    auction_date: Optional[str] = None

class TribunalProceedings(BaseModel):
    sa_number: Optional[str] = None
    sa_filing_date: Optional[str] = None
    drt_bench: Optional[str] = None
    interim_stay_prayed: bool = False
    interim_stay_granted: bool = False
    drat_appeal_filed: bool = False
    pre_deposit_percent: Optional[float] = Field(default=50.0, description="Section 18 pre-deposit (50% reducible to 25%)")

class SarfaesiCaseModel(BaseModel):
    case_id: str = Field(default="SARFAESI-ANON")
    perspective: str = Field(default="creditor", description="creditor or borrower")
    facility: LoanFacility = Field(default_factory=LoanFacility)
    parties: SecuredParties = Field(default_factory=SecuredParties)
    security: MortgagedSecurity = Field(default_factory=MortgagedSecurity)
    enforcement: EnforcementMeasures = Field(default_factory=EnforcementMeasures)
    tribunal: TribunalProceedings = Field(default_factory=TribunalProceedings)
