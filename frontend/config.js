export const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? "http://127.0.0.1:8000"
    : "https://cheque-bounce-ragbased.onrender.com";

export const firebaseConfig = {
    apiKey: "AIzaSyBdqc1C8LPVj4zqvWJWJWMrXhPad20MZCw",
    authDomain: "idcourt-cb58f.firebaseapp.com",
    projectId: "idcourt-cb58f",
    storageBucket: "idcourt-cb58f.firebasestorage.app",
    messagingSenderId: "941086914513",
    appId: "1:941086914513:web:8edad96b7e9f0dd4be12f0",
    measurementId: "G-YQMJ6KXGBR"
};

export const wizardSteps = [
    {
        id: 'case_identity',
        title: 'Case Identity',
        subtitle: 'Basic case information and filing details',
        fields: [
            { name: 'case_id', label: 'Case ID', type: 'text', required: false, placeholder: 'e.g., CC/2024/123' },
            { name: 'case_title', label: 'Case Title', type: 'text', required: true, placeholder: 'Complainant vs Accused' },
            { name: 'complainant_type', label: 'Complainant Entity Type', type: 'select', options: ['Individual', 'Partnership Firm', 'Pvt Ltd/Ltd Company', 'HUF', 'Proprietorship'], required: true },
            { name: 'filing_date', label: 'Filing Date', type: 'date', required: true },
            { name: 'court_name', label: 'Court Name', type: 'text', required: false, placeholder: 'e.g., District Court, Mumbai' },
            { name: 'condonation_attached', label: 'Condonation of Delay App Attached? (S.142)', type: 'select', options: ['Yes', 'No', 'Not Applicable'], required: false },
            { name: 'case_type', label: 'Case Type', type: 'select', options: ['Cheque Bounce', 'SARFAESI'], required: true },
            { name: 'judicial_temperament', label: 'Judicial Temperament / Courtroom Mood', type: 'select', options: ['Balanced', 'Pro-Complainant', 'Pro-Accused'], required: false }
        ]
    },
    {
        id: 'parties',
        title: 'Parties Information',
        subtitle: 'Details of complainant and accused',
        fields: [
            { name: 'complainant_name', label: 'Complainant Name', type: 'text', required: true },
            { name: 'complainant_address', label: 'Complainant Address', type: 'textarea', required: true },
            { name: 'complainant_authorized', label: 'Board Resolution/Authorization Available? (If Entity)', type: 'select', options: ['Yes - Original', 'Yes - Copy', 'No', 'Not Applicable'], required: true },
            { name: 'accused_name', label: 'Accused Name', type: 'text', required: true },
            { name: 'accused_type', label: 'Accused Entity Type', type: 'select', options: ['Individual', 'Pvt Ltd/Ltd Company', 'Partnership Firm', 'Other'], required: true },
            { name: 'accused_address', label: 'Accused Address', type: 'textarea', required: true },
            { name: 'directors_named', label: 'Directors Named & Operational Role Pled? (S.141)', type: 'select', options: ['Yes - Actively Managed Operations', 'Yes - Partial', 'No', 'Not Applicable'], required: true },
            { name: 'accused_directors', label: 'Names of Directors/Partners Responsible', type: 'textarea', required: false, placeholder: 'e.g., Mr. A (Director), Mr. B (Managing Partner)' }
        ]
    },
    {
        id: 'transaction',
        title: 'Transaction Details',
        subtitle: 'Underlying debt and transaction information',
        fields: [
            { name: 'transaction_date', label: 'Transaction Date', type: 'date', required: true },
            { name: 'purpose', label: 'Purpose of Transaction', type: 'textarea', required: true, placeholder: 'Describe the reason for the debt/loan...' },
            { name: 'agreement_type', label: 'Agreement Type', type: 'select', options: ['Written Agreement', 'Verbal Agreement', 'Invoice/Bill', 'Promissory Note', 'No Formal Agreement'], required: true },
            { name: 'itr_available', label: 'Complainant ITR Available? (Financial Capacity)', type: 'select', options: ['Yes', 'No'], required: false },
            { name: 'loan_advanced_via', label: 'How was the loan/debt advanced?', type: 'select', options: ['Bank Transfer (NEFT/RTGS/IMPS)', 'Account Payee Cheque', 'Cash', 'Other (e.g., Invoices/Goods)'], required: true }
        ]
    },
    {
        id: 'cheque',
        title: 'Cheque Details',
        subtitle: 'Information about the dishonoured cheque',
        fields: [
            { name: 'cheque_number', label: 'Cheque Number', type: 'text', required: true, placeholder: '123456' },
            { name: 'cheque_date', label: 'Cheque Date', type: 'date', required: true },
            { name: 'cheque_amount', label: 'Cheque Amount (₹)', type: 'number', required: true },
            { name: 'bank_name', label: 'Bank Name', type: 'text', required: true },
            { name: 'branch_name', label: 'Branch Name', type: 'text', required: false },
            { name: 'account_number', label: 'Account Number', type: 'text', required: false },
            { name: 'cheque_type', label: 'Cheque Type', type: 'select', options: ['Bearer Cheque', 'Account Payee Cheque', 'Crossed Cheque'], required: true },
            { name: 'post_dated', label: 'Post-Dated Cheque?', type: 'select', options: ['Yes', 'No'], required: true }
        ]
    },
    {
        id: 'dishonour',
        title: 'Dishonour Information',
        subtitle: 'Details of cheque dishonour and bank memo',
        fields: [
            { name: 'dishonour_date', label: 'Dishonour Date', type: 'date', required: true },
            { name: 'dishonour_reason', label: 'Reason for Dishonour', type: 'select', options: ['Insufficient Funds', 'Funds Insufficient', 'Account Closed', 'Signature Mismatch', 'Signature Differs', 'Payment Stopped', 'Refer to Drawer', 'Other'], required: true },
            { name: 'bank_memo_received', label: 'Bank Dishonour Memo Received?', type: 'select', options: ['Yes', 'No'], required: true },
            { name: 'memo_date', label: 'Memo Received Date', type: 'date', required: false },
            { name: 'memo_signed', label: 'Is Bank Memo Signed & Stamped?', type: 'select', options: ['Yes - Signed & Stamped', 'No - Unsigned/Digital', 'Unsure'], required: false },
            { name: 'presentation_date', label: 'First Presentation Date', type: 'date', required: true },
            { name: 'second_presentation', label: 'Second Presentation Made?', type: 'select', options: ['Yes', 'No', 'Not Applicable'], required: false },
            { name: 'second_presentation_date', label: 'Second Presentation Date', type: 'date', required: false }
        ]
    },
    {
        id: 'notice',
        title: 'Legal Notice (Section 138)',
        subtitle: 'Statutory notice details under NI Act',
        fields: [
            { name: 'notice_sent', label: 'Legal Notice Sent?', type: 'select', options: ['Yes', 'Yes - Being Sent', 'No'], required: true },
            { name: 'notice_date', label: 'Notice Sent Date', type: 'date', required: false },
            { name: 'notice_mode', label: 'Mode of Sending Notice', type: 'select', options: ['Registered Post AD', 'Speed Post', 'Courier', 'Email (Not Recommended)', 'Hand Delivery', 'Multiple Modes'], required: false },
            { name: 'notice_received', label: 'Notice Received by Accused?', type: 'select', options: ['Yes - Acknowledged', 'Yes - Refused', 'Returned Unserved', 'Unknown'], required: false },
            { name: 'notice_received_date', label: 'Notice Received/Refused Date', type: 'date', required: false },
            { name: 'reply_received', label: 'Reply from Accused Received?', type: 'select', options: ['Yes - Full Payment', 'Yes - Denial', 'Yes - Partial Response', 'No Reply'], required: false }
        ]
    },
    {
        id: 'evidence',
        title: 'Evidence & Documentation',
        subtitle: 'Available evidence to support your case',
        fields: [
            { name: 'original_cheque', label: 'Original Cheque Available?', type: 'select', options: ['Yes - Original', 'No - Lost', 'No - With Bank'], required: true },
            { name: 'agreement_documents', label: 'Loan/Agreement Documents?', type: 'select', options: ['Yes - Signed Agreement', 'Yes - Unsigned Draft', 'Promissory Note', 'None'], required: false },
            { name: 'witness_available', label: 'Witnesses Available?', type: 'select', options: ['Yes - Multiple', 'Yes - One', 'No'], required: false },
            { name: 'communication_records', label: 'Email/SMS/WhatsApp Records?', type: 'select', options: ['Yes - Extensive', 'Yes - Limited', 'No'], required: false },
            { name: 'has_bsa_certificate', label: 'S.63(4) BSA Certificate Attached?', type: 'select', options: ['Yes - Signed Certificate', 'No', 'Not Applicable'], required: false },
            { name: 'bank_statements', label: 'Bank Statements Available?', type: 'select', options: ['Yes - Complete', 'Yes - Partial', 'No'], required: false },
            { name: 'receipts_invoices', label: 'Receipts/Invoices Available?', type: 'select', options: ['Yes', 'No'], required: false }
        ]
    },
    {
        id: 'defence_inputs',
        title: 'Known Defence Arguments',
        subtitle: 'Any defence claims made by the accused',
        fields: [
            { name: 'signature_dispute', label: 'Signature Disputed by Accused?', type: 'select', options: ['Yes - Claimed Forged', 'Yes - Claimed Unauthorized', 'No', 'Unknown'], required: false },
            { name: 'debt_denial', label: 'Debt Denied Completely?', type: 'select', options: ['Yes - Complete Denial', 'Partially Denied', 'No', 'Unknown'], required: false },
            { name: 'cheque_security_claim', label: 'Accused Claims Cheque Was Security?', type: 'select', options: ['Yes', 'No', 'Unknown'], required: false },
            { name: 'limitation_claim', label: 'Limitation Period Claimed Expired?', type: 'select', options: ['Yes', 'No', 'Unknown'], required: false },
            { name: 'already_paid_claim', label: 'Accused Claims Already Paid?', type: 'select', options: ['Yes - Full', 'Yes - Partial', 'No', 'Unknown'], required: false },
            { name: 'jurisdiction_challenge', label: 'Jurisdiction Challenged?', type: 'select', options: ['Yes', 'No', 'Unknown'], required: false },
            { name: 'other_defences', label: 'Other Known Defences', type: 'textarea', required: false, placeholder: 'Describe any other defence arguments...' }
        ]
    },
    {
        id: 'negotiations_conduct',
        title: 'Negotiations & Conduct',
        subtitle: 'Settlement attempts and accused behavior',
        fields: [
            { name: 'settlement_attempted', label: 'Out-of-Court Settlement Attempted?', type: 'select', options: ['Yes - Multiple Times', 'Yes - Once', 'No'], required: false },
            { name: 'settlement_amount', label: 'Settlement Amount Discussed (₹)', type: 'number', required: false },
            { name: 'evasive_conduct', label: 'Evasive/Avoiding Conduct?', type: 'select', options: ['Yes - Avoiding Calls', 'Yes - Changed Address', 'Yes - Absconding', 'No'], required: false },
            { name: 'court_attendance', label: 'Is Accused Attending Court Dates?', type: 'select', options: ['Yes - Appearing', 'No - Skipping Dates', 'Not Applicable (Pre-Filing)'], required: false },
            { name: 'counter_claim', label: 'Counter Claim Filed?', type: 'select', options: ['Yes', 'No', 'Threatened'], required: false },
            { name: 'urgency_level', label: 'Case Urgency Level', type: 'select', options: ['Very Urgent', 'Urgent', 'Normal'], required: false },
            { name: 'additional_notes', label: 'Additional Case Notes/Context', type: 'textarea', required: false, placeholder: 'Any other relevant information about the case...' }
        ]
    }
];

export const sarfaesiWizardSteps = [
    {
        id: 'sarfaesi_identity',
        title: 'Case Identity & Mode',
        subtitle: 'Basic case details and perspective selection',
        fields: [
            { name: 'case_id', label: 'Case ID / Loan Ref', type: 'text', required: false, placeholder: 'e.g., SARFAESI/2026/001' },
            { name: 'case_title', label: 'Case Title', type: 'text', required: true, placeholder: 'State Bank vs M/s XYZ Ltd' },
            // case_type is intentionally excluded here — it is auto-locked to 'SARFAESI' by wizard.js
            // when this flow is activated, preventing accidental cross-domain re-routing.
            { name: 'perspective', label: 'Client Perspective (Mode)', type: 'select', options: ['creditor', 'borrower'], required: true },
            { name: 'filing_date', label: 'Audit / Filing Date', type: 'date', required: true },
            { name: 'drt_bench', label: 'DRT Bench / Court Location', type: 'text', required: false, placeholder: 'e.g., DRT-I Mumbai' }
        ]
    },
    {
        id: 'sarfaesi_facility',
        title: 'Loan & Default Details',
        subtitle: 'Facility type, outstanding debt, and NPA classification',
        fields: [
            { name: 'bank_name', label: 'Secured Creditor (Bank/NBFC)', type: 'text', required: true, placeholder: 'e.g., State Bank of India' },
            { name: 'borrower_name', label: 'Borrower / Mortgagor Name', type: 'text', required: true, placeholder: 'e.g., M/s Zenith Enterprises' },
            { name: 'loan_account_number', label: 'Loan Account Number', type: 'text', required: true, placeholder: 'e.g., CC-99887711' },
            { name: 'facility_type', label: 'Facility Type', type: 'select', options: ['Term Loan', 'Cash Credit', 'Housing Loan', 'Commercial Overdraft'], required: true },
            { name: 'outstanding_amount', label: 'Total Outstanding Debt (₹)', type: 'number', required: true, placeholder: 'e.g., 25000000' },
            { name: 'npa_date', label: 'NPA Classification Date', type: 'date', required: true }
        ]
    },
    {
        id: 'sarfaesi_security',
        title: 'Mortgaged Asset & CERSAI',
        subtitle: 'Property description, CERSAI portal registration, and agricultural status',
        fields: [
            { name: 'property_description', label: 'Mortgaged Asset Description', type: 'textarea', required: true, placeholder: 'Describe property location, plot/survey number...' },
            { name: 'cersai_registered', label: 'Security Registered on CERSAI Portal? (S.26D)', type: 'select', options: ['Yes', 'No'], required: true },
            { name: 'is_agricultural_land', label: 'Is Property Agricultural Land? (S.31i)', type: 'select', options: ['No - Commercial/Residential', 'Yes - Agricultural Land'], required: true },
            { name: 'valuation_amount', label: 'Valuation / Reserve Price (₹)', type: 'number', required: false, placeholder: 'e.g., 30000000' }
        ]
    },
    {
        id: 'sarfaesi_enforcement',
        title: 'Enforcement Timeline',
        subtitle: 'Section 13(2), 13(3A) representation, and Section 13(4) measures',
        fields: [
            { name: 'notice_13_2_date', label: 'Section 13(2) Demand Notice Date', type: 'date', required: false },
            { name: 'borrower_representation_date', label: 'Borrower S.13(3A) Objection Date', type: 'date', required: false },
            { name: 'bank_reply_13_3a_date', label: 'Bank S.13(3A) Reasoned Reply Date', type: 'date', required: false },
            { name: 'possession_13_4_date', label: 'Section 13(4) Possession Notice Date', type: 'date', required: false },
            { name: 'newspaper_publication_done', label: 'Published in 2 Newspapers? (Rule 8-2)', type: 'select', options: ['Yes', 'No'], required: false }
        ]
    },
    {
        id: 'sarfaesi_litigation',
        title: 'Tribunal & Auction Details',
        subtitle: 'Section 14 DM order, auction date, and Section 17 DRT SA',
        fields: [
            { name: 'dm_order_date', label: 'Section 14 DM Physical Possession Order Date', type: 'date', required: false },
            { name: 'auction_notice_date', label: 'Rule 8(6)/9(1) Sale Auction Notice Date', type: 'date', required: false },
            { name: 'sa_filing_date', label: 'Section 17 DRT SA Filing Date', type: 'date', required: false },
            { name: 'additional_notes', label: 'Additional Case Notes / Defense Arguments', type: 'textarea', required: false, placeholder: 'Describe any specific legal objections or disputes...' }
        ]
    }
];

export function getActiveWizardSteps(caseType) {
    const type = (caseType || '').toLowerCase();
    if (type.includes('sarfaesi') || type.includes('drt')) {
        return sarfaesiWizardSteps;
    }
    return wizardSteps;
}


export const roleActions = {
    law_firm: [
        { title: 'Run Analysis', description: 'Scan for FATAL defects and map courtroom strategy', icon: 'fa-search', color: '#ef4444', action: 'startCaseAnalysis' },
        { title: 'Generate Draft', description: 'Generate court-ready legal drafts', icon: 'fa-file-contract', color: '#10b981', action: 'generateDraft' }
    ],
    in_house: [
        { title: 'Run Analysis', description: 'Scan for FATAL defects and map courtroom strategy', icon: 'fa-search', color: '#ef4444', action: 'startCaseAnalysis' },
        { title: 'Generate Draft', description: 'Generate court-ready legal drafts', icon: 'fa-file-contract', color: '#10b981', action: 'generateDraft' }
    ],
    corporate_legal: [
        { title: 'Run Analysis', description: 'Scan for FATAL defects and map courtroom strategy', icon: 'fa-search', color: '#ef4444', action: 'startCaseAnalysis' },
        { title: 'Generate Draft', description: 'Generate court-ready legal drafts', icon: 'fa-file-contract', color: '#10b981', action: 'generateDraft' }
    ],
    research: [
        { title: 'Run Analysis', description: 'Scan for FATAL defects and map courtroom strategy', icon: 'fa-search', color: '#ef4444', action: 'startCaseAnalysis' },
        { title: 'Generate Draft', description: 'Generate court-ready legal drafts', icon: 'fa-file-contract', color: '#10b981', action: 'generateDraft' }
    ],
    citizen: [
        { title: 'Run Analysis', description: 'Scan for FATAL defects and map courtroom strategy', icon: 'fa-search', color: '#ef4444', action: 'startCaseAnalysis' },
        { title: 'Generate Draft', description: 'Generate court-ready legal drafts', icon: 'fa-file-contract', color: '#10b981', action: 'generateDraft' }
    ],
    lawyer: [
        { title: 'Run Analysis', description: 'Scan for FATAL defects and map courtroom strategy', icon: 'fa-search', color: '#ef4444', action: 'startCaseAnalysis' },
        { title: 'Generate Draft', description: 'Generate court-ready legal drafts', icon: 'fa-file-contract', color: '#10b981', action: 'generateDraft' }
    ],
    student: [
        { title: 'Run Analysis', description: 'Scan for FATAL defects and map courtroom strategy', icon: 'fa-search', color: '#ef4444', action: 'startCaseAnalysis' },
        { title: 'Generate Draft', description: 'Generate court-ready legal drafts', icon: 'fa-file-contract', color: '#10b981', action: 'generateDraft' }
    ]
};
