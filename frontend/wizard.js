import { wizardSteps, sarfaesiWizardSteps, criminalWizardSteps, civilWizardSteps, compositeWizardSteps, getActiveWizardSteps } from './config.js?v=14';
import { ui, switchScreen } from './ui.js?v=14';
import { api } from './api.js?v=14';
import { renderResults } from './renderer.js?v=14';

let isWizardInitialized = false;
let currentCaseType = null;

function getCurrentSteps() {
    const domain = (window.state?.userDomain || 'ni_act').toLowerCase();
    let caseType = window.state?.caseData?.case_type;
    if (!caseType) {
        if (domain === 'composite' || domain === 'multi_track') caseType = 'Multi-Track (SARFAESI + 138 + Criminal)';
        else if (domain === 'criminal') caseType = 'Criminal';
        else if (domain === 'sarfaesi') caseType = 'SARFAESI';
        else if (domain === 'civil') caseType = 'Civil';
        else caseType = 'Cheque Bounce';
        window.state = window.state || {};
        window.state.caseData = window.state.caseData || {};
        window.state.caseData.case_type = caseType;
    }
    return getActiveWizardSteps(caseType);
}

function loadAutosave() {
    try {
        const saved = localStorage.getItem('judiq_wizard_autosave');
        if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed && typeof parsed === 'object') {
                window.state = window.state || {};
                window.state.caseData = { ...parsed, ...(window.state.caseData || {}) };
            }
        }
    } catch (e) {
        console.warn('Failed to load autosave state:', e);
    }
}

function persistAutosave() {
    try {
        saveCurrentStepValues();
        localStorage.setItem('judiq_wizard_autosave', JSON.stringify(window.state?.caseData || {}));
    } catch (e) {
        console.warn('Failed to persist autosave state:', e);
    }
}

window.loadAutosave = loadAutosave;
window.persistAutosave = persistAutosave;

window.setCaseType = (type) => {
    window.state = window.state || {};
    window.state.caseData = window.state.caseData || {};
    window.state.caseData.case_type = type;
    window.state.currentStep = 1;
    isWizardInitialized = false;
    currentCaseType = null;
    renderWizardStep();
};

export function renderWizardStep() {
    const steps = getCurrentSteps();
    const caseType = window.state?.caseData?.case_type || 'Cheque Bounce';
    
    if (currentCaseType !== caseType) {
        isWizardInitialized = false;
        currentCaseType = caseType;
    }

    const currentStep = window.state.currentStep || 1;
    const stepIdx = Math.min(Math.max(0, currentStep - 1), steps.length - 1);
    const step = steps[stepIdx];

    // Auto-lock case_type based on active steps
    if (steps === compositeWizardSteps || (caseType && (caseType.toLowerCase().includes('composite') || caseType.toLowerCase().includes('multi_track') || caseType.toLowerCase().includes('all-in-one')))) {
        window.state.caseData['case_type'] = 'Multi-Track (SARFAESI + 138 + Criminal)';
    } else if (steps === criminalWizardSteps || (caseType && caseType.toLowerCase().includes('criminal'))) {
        window.state.caseData['case_type'] = 'Criminal';
    } else if (steps === sarfaesiWizardSteps || (caseType && caseType.toLowerCase().includes('sarfaesi'))) {
        window.state.caseData['case_type'] = 'SARFAESI';
    } else if (steps === civilWizardSteps || (caseType && caseType.toLowerCase().includes('civil'))) {
        window.state.caseData['case_type'] = 'Civil';
    } else {
        window.state.caseData['case_type'] = 'Cheque Bounce';
    }

    
    ui.setText('wizardTitle', step.title);
    ui.setText('wizardSubtitle', step.subtitle);
    ui.setText('stepBadgeNumber', stepIdx + 1);
    ui.setText('totalBadgeNumber', steps.length);
    ui.setText('currentStepDisplay', stepIdx + 1);
    ui.setText('totalStepsDisplay', steps.length);
    
    const container = document.getElementById('wizardStepsContainer');
    if (!container) return;
    
    if (!isWizardInitialized) {
        loadAutosave();
        window.wizardStepsLength = steps.length;
        container.innerHTML = steps.map((s, idx) => `
            <form id="stepForm_${idx}" class="step-form fade-in ${idx === stepIdx ? '' : 'hidden'}" onsubmit="event.preventDefault(); nextStep();">
                ${s.fields.map(field => renderField(field)).join('')}
            </form>
        `).join('');
        isWizardInitialized = true;
    } else {
        steps.forEach((s, idx) => {
            const form = document.getElementById(`stepForm_${idx}`);
            if (form) {
                if (idx === stepIdx) {
                    form.classList.remove('hidden');
                } else {
                    form.classList.add('hidden');
                }
            }
            s.fields.forEach(field => {
                const el = document.getElementById(field.name);
                if (el) {
                    el.value = window.state.caseData[field.name] || '';
                }
            });
        });
    }
    
    updateProgress();
    updateNavigationButtons();
    updateConditionalFields();
}

function updateConditionalFields() {
    // Helper to toggle visibility and required attribute
    const toggleField = (fieldId, isVisible) => {
        const el = document.getElementById(fieldId);
        if (!el) return;
        const group = el.closest('.form-group');
        if (group) {
            group.style.display = isVisible ? 'block' : 'none';
        }
        if (isVisible) {
            el.setAttribute('required', 'required');
            el.required = true;
            el.disabled = false;
        } else {
            el.removeAttribute('required');
            el.required = false;
            el.disabled = true;
        }
    };

    // Complainant Type -> Authorized Representative
    const compTypeEl = document.getElementById('complainant_type');
    if (compTypeEl) {
        const isEntity = compTypeEl.value !== 'Individual' && compTypeEl.value !== '';
        toggleField('complainant_authorized', isEntity);
    }

    // Accused Type -> Directors Named
    const accTypeEl = document.getElementById('accused_type');
    if (accTypeEl) {
        const isEntity = accTypeEl.value !== 'Individual' && accTypeEl.value !== '';
        toggleField('directors_named', isEntity);
    }

    // Criminal Offense Type -> Intelligent Presets for Sections & Maximum Punishment
    const offenseTypeEl = document.getElementById('offense_type');
    const ipcSectionEl = document.getElementById('ipc_section');
    const maxPunishmentEl = document.getElementById('max_punishment_years');
    if (offenseTypeEl && offenseTypeEl.value) {
        const val = offenseTypeEl.value;
        if (ipcSectionEl && !ipcSectionEl.value) {
            if (val.includes('420') || val.includes('318')) ipcSectionEl.value = 'S. 420, 406, 120B IPC / S. 318, 316, 61 BNS';
            else if (val.includes('498A') || val.includes('85')) ipcSectionEl.value = 'S. 498A, 304B, 34 IPC / S. 85, 80, 3(5) BNS';
            else if (val.includes('302') || val.includes('103')) ipcSectionEl.value = 'S. 302, 304 Part II, 34 IPC / S. 103, 105, 3(5) BNS';
            else if (val.includes('307') || val.includes('109')) ipcSectionEl.value = 'S. 307, 324, 34 IPC / S. 109, 117, 3(5) BNS';
            else if (val.includes('376') || val.includes('64')) ipcSectionEl.value = 'S. 376(2)(n), 506 IPC / S. 64(2)(m), 351 BNS';
            else if (val.includes('POCSO')) ipcSectionEl.value = 'POCSO Act 2012 S. 3, 4, 5, 6, 29 / S. 376 IPC';
            else if (val.includes('NDPS')) ipcSectionEl.value = 'NDPS Act S. 8(c), 20(b)(ii)(C), 29, 37';
            else if (val.includes('Corruption') || val.includes('17A')) ipcSectionEl.value = 'Prevention of Corruption Act S. 7, 13(1)(b), 13(2), 17A';
            else if (val.includes('PMLA') || val.includes('Laundering')) ipcSectionEl.value = 'PMLA 2002 S. 3, 4, 45';
            else if (val.includes('Cyber')) ipcSectionEl.value = 'IT Act 2000 S. 66C, 66D, 67 / S. 420 IPC';
            else if (val.includes('Hit & Run') || val.includes('279')) ipcSectionEl.value = 'S. 279, 304A IPC / S. 281, 106 BNS';
        }
        if (maxPunishmentEl && (!maxPunishmentEl.value || maxPunishmentEl.value === '0')) {
            if (val.includes('420') || val.includes('318') || val.includes('Corruption') || val.includes('PMLA')) maxPunishmentEl.value = 7;
            else if (val.includes('498A') || val.includes('85') || val.includes('Cyber') || val.includes('Hit & Run')) maxPunishmentEl.value = 3;
            else if (val.includes('302') || val.includes('103') || val.includes('NDPS') || val.includes('POCSO') || val.includes('376') || val.includes('307')) maxPunishmentEl.value = 20;
        }
    }
}

function renderField(field) {
    const value = window.state.caseData[field.name] || '';
    let inputHtml = '';
    
    if (field.type === 'select') {
        const changeHandler = field.name === 'case_type'
            ? "window.setCaseType(this.value); if(typeof updateConditionalFields === 'function') updateConditionalFields();"
            : "if(typeof updateConditionalFields === 'function') updateConditionalFields();";
        inputHtml = `
            <select id="${field.name}" name="${field.name}" ${field.required ? 'required' : ''} onchange="${changeHandler}">
                <option value="">Select Option</option>
                ${field.options.map(opt => `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`).join('')}
            </select>
        `;
    } else if (field.type === 'textarea') {
        inputHtml = `<textarea id="${field.name}" name="${field.name}" ${field.required ? 'required' : ''} placeholder="${field.placeholder || ''}" onchange="if(typeof updateConditionalFields === 'function') updateConditionalFields()">${value}</textarea>`;
    } else {
        inputHtml = `<input type="${field.type}" id="${field.name}" name="${field.name}" value="${value}" ${field.required ? 'required' : ''} placeholder="${field.placeholder || ''}" onchange="if(typeof updateConditionalFields === 'function') updateConditionalFields()">`;
    }
    
    return `
        <div class="form-group">
            <label for="${field.name}">${field.label} ${field.required ? '<span class="required">*</span>' : ''}</label>
            ${inputHtml}
        </div>
    `;
}

function updateProgress() {
    const steps = getCurrentSteps();
    const current = window.state.currentStep || 1;
    const progress = (current / steps.length) * 100;
    const fill = document.getElementById('progressFill');
    if (fill) fill.style.width = `${progress}%`;
    ui.setText('progressPercentage', `${Math.round(progress)}%`);

    const stepsContainer = document.getElementById('progressSteps');
    if (stepsContainer) {
        stepsContainer.innerHTML = steps.map((s, idx) => {
            const num = idx + 1;
            const isCurrent = num === current;
            const isCompleted = num < current;
            const stateClass = isCurrent ? 'step-active' : (isCompleted ? 'step-completed' : 'step-upcoming');
            return `
                <div class="progress-step-pill ${stateClass}" onclick="if(${num} <= ${current} + 1) { saveCurrentStepValues(); window.state.currentStep = ${num}; persistAutosave(); renderWizardStep(); }">
                    <span class="step-num">${isCompleted ? '<i class="fas fa-check"></i>' : num}</span>
                    <span class="step-label">${s.title || `Step ${num}`}</span>
                </div>
            `;
        }).join('');
    }
}

// Update wizard navigation buttons state
function updateNavigationButtons() {
    const steps = getCurrentSteps();
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    if (prevBtn) prevBtn.disabled = window.state.currentStep === 1;
    
    if (window.state.currentStep >= steps.length) {
        if (nextBtn) nextBtn.classList.add('hidden');
        if (submitBtn) submitBtn.classList.remove('hidden');
    } else {
        if (nextBtn) nextBtn.classList.remove('hidden');
        if (submitBtn) submitBtn.classList.add('hidden');
    }
}

window.nextStep = () => {
    const steps = getCurrentSteps();
    const stepIdx = Math.min(window.state.currentStep - 1, steps.length - 1);
    const form = document.getElementById(`stepForm_${stepIdx}`);
    if (form && !form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Save data
    const step = steps[stepIdx];
    step.fields.forEach(field => {
        const el = document.getElementById(field.name);
        if (el) window.state.caseData[field.name] = el.value;
    });

    // Auto-selection logic: if Agreement Type is "Invoice/Bill", select "receipts_invoices"
    if (step.id === 'transaction') {
        if (window.state.caseData['agreement_type'] === 'Invoice/Bill') {
            window.state.caseData['receipts_invoices'] = 'Yes';
        }
    }
    
    if (window.state.currentStep < steps.length) {
        window.state.currentStep++;
        persistAutosave();
        renderWizardStep();
    }
};

window.previousStep = () => {
    if (window.state.currentStep > 1) {
        window.state.currentStep--;
        persistAutosave();
        renderWizardStep();
    }
};

/**
 * Sanitizes wizard payload before sending to API.
 * Converts string Yes/No fields to actual booleans for boolean-typed fields
 * so the backend normalizer receives clean data.
 */
function sanitizePayload(rawData) {
    const BOOLEAN_FIELDS = [
        'notice_sent', 'cheque_present', 'dishonour_memo', 'debt_proven',
        'directors_named', 'complainant_authorized', 'itr_available',
        'bank_memo_received', 'second_presentation', 'post_dated',
        'signature_dispute', 'debt_denial', 'cheque_security_claim',
        'within_30_days', 'reply_received', 'memo_signed', 'court_attendance',
        // Criminal fields
        'electronic_evidence', 's65b_certificate', 'medical_contradicts_ocular',
        's161_s164_contradiction', 'contract_exists', 'relative_impleaded',
        'flight_risk', 'is_public_servant', 'sanction_obtained', 'no_s41a_notice',
        // SARFAESI fields
        'cersai_registered', 'is_agricultural_land', 'newspaper_publication_done',
        // Civil fields
        's12a_mediation', 'agreement_registered', 'order_39_injunction'
    ];
    const TRUTHY_VALUES = ['yes', 'true', '1', 'yes - all', 'yes - partial',
        'yes - original', 'yes - copy', 'yes - written', 'yes - verbal',
        'yes - acknowledged', 'yes - denied', 'yes - full payment',
        'yes - denial', 'yes - partial response', 'yes - being sent', 'in progress', 'yes - signed', 'yes - regular'];

    const cleaned = { ...rawData };
    for (const field of BOOLEAN_FIELDS) {
        if (field in cleaned) {
            const val = String(cleaned[field] || '').trim().toLowerCase();
            cleaned[field] = TRUTHY_VALUES.some(t => val.startsWith(t) || val === t);
        }
    }
    return cleaned;
}

function saveCurrentStepValues() {
    const steps = getCurrentSteps();
    const stepIdx = (window.state?.currentStep || 1) - 1;
    const step = steps[stepIdx];
    if (!step) return;
    step.fields.forEach(field => {
        const el = document.getElementById(field.name);
        if (el && window.state?.caseData) window.state.caseData[field.name] = el.value;
    });
}

window.submitCase = async () => {
    const stepIdx = window.state.currentStep - 1;
    const form = document.getElementById(`stepForm_${stepIdx}`);
    if (form && !form.checkValidity()) {
        form.reportValidity();
        return;
    }
    saveCurrentStepValues();
    ui.show('analysisLoading');
    try {
        const userId = window.state.currentUser ? window.state.currentUser.uid : 'ANONYMOUS';
        const rawPayload = { ...window.state.caseData, user_id: userId };
        const payload = sanitizePayload(rawPayload);
        const result = await api.analyze(payload);
        window.state.analysisResult = result;
        if (window.saveCaseToHistory) {
            window.saveCaseToHistory(payload, result);
        }
        // Clear autosave after successful submission
        localStorage.removeItem('judiq_wizard_autosave');
        ui.hide('analysisLoading');
        switchScreen('resultsScreen');
        renderResults(result);
    } catch (err) {
        ui.hide('analysisLoading');
        ui.toast(err.message, 'error');
    }
};

export const SAMPLE_NI_ACT_PRESET = {
    case_title: "Apex Global vs. Vanguard Tech",
    case_type: "Cheque Bounce",
    complainant_name: "Apex Global Traders Pvt Ltd",
    complainant_type: "Pvt Ltd/Ltd Company",
    complainant_authorized: "Yes - Original",
    authorized_person_name: "Mr. Vikram Joshi",
    board_resolution_date: "2026-04-01",
    accused_name: "Vanguard Tech Solutions Pvt Ltd",
    accused_type: "Pvt Ltd/Ltd Company",
    directors_named: "Yes - Actively Managed Operations",
    accused_directors: "Mr. Rahul Verma (Managing Director)",
    director_roles: "Managing Director in charge of financial operations and cheque issuance",
    cheque_number: "482019",
    bank_name: "HDFC Bank Ltd",
    branch_name: "Hinjewadi Branch, Pune",
    cheque_amount: 1550000,
    cheque_date: "2026-04-10",
    dishonour_date: "2026-05-02",
    dishonour_reason: "Funds Insufficient",
    notice_date: "2026-05-18",
    notice_delivery_date: "2026-05-22",
    complaint_date: "2026-07-01",
    court_name: "JMFC Court, Pune",
    jurisdiction_city: "Pune",
    agreement_type: "Written Contract / Invoice",
    purpose: "Supply of IT Hardware Equipment and Enterprise Servers",
    debt_amount: 1550000,
    debt_proven: "Yes - Documented",
    itr_available: "Yes",
    signature_dispute: "No",
    cheque_security_claim: "No",
    reply_received: "Yes - Denied Liability",
    within_30_days: "Yes",
    condonation_attached: "No"
};

export const SAMPLE_SARFAESI_PRESET = {
    case_id: "SARFAESI-DEMO-001",
    case_title: "Axis Bank Ltd vs. Zenith Fabricators Pvt Ltd",
    case_type: "SARFAESI",
    perspective: "Creditor (Bank / Financial Institution / Complainant)",
    bank_name: "Axis Bank Ltd (Stressed Assets Management Branch)",
    borrower_name: "Zenith Fabricators Pvt Ltd & Rajiv Mehta",
    outstanding_amount: 45000000.0,
    amount: 45000000.0,
    npa_date: "2025-09-30",
    notice_13_2_date: "2025-10-15",
    cersai_registered: true,
    property_description: "Industrial Shed No. 12, Phase II, GIDC Industrial Estate, Vatva, Ahmedabad",
    is_agricultural_land: false,
    possession_13_4_date: "2026-01-20",
    description: "Borrower defaulted on working capital credit facility of Rs. 4.50 Crore. Demand notice under Section 13(2) served and symbolical possession taken u/s 13(4)."
};

export const SAMPLE_CRIMINAL_PRESET = {
    case_id: "CR-FIR-2026-882",
    case_title: "State of Maharashtra vs Vikram Sharma & Ors",
    case_type: "Criminal",
    police_station: "Cyber & Financial Crime PS, BKC, Mumbai",
    client_role: "Accused",
    statutory_regime: "Indian Penal Code (IPC 1860 / CrPC 1973)",
    filing_date: "2026-05-10",
    court_name: "Additional Sessions Court, Greater Mumbai",
    offense_type: "S.420 IPC / S.318 BNS (Cheating & Financial Fraud)",
    ipc_section: "S. 420, 406, 120B IPC",
    incident_date: "2024-03-15",
    fir_date: "2026-05-10",
    delay_explanation: "FIR registered with an unexplained inordinate delay of 2 years after commercial payment dispute arose.",
    max_punishment_years: 7,
    arrested_during_investigation: "No - Anticipating Arrest / Not Arrested",
    no_s41a_notice: "Arrested Directly Without S.41A Notice (Arnesh Kumar Violation)",
    chargesheet_filed: "No - Investigation Pending (Default Bail S.167 Check)",
    is_public_servant: "No",
    sanction_obtained: "Not Applicable",
    electronic_evidence: "Yes",
    s65b_certificate: "No - Uncertified / Missing (Inadmissible)",
    recovery_memo_s27: "No Recovery Made",
    contract_exists: "Yes - Commercial Contract / Debt Recovery in Criminal Garb",
    primary_relief_sought: "High Court Quashing u/s 482 CrPC / S.528 BNSS (Bhajan Lal)",
    additional_notes: "Pure civil contractual dispute converted into criminal prosecution (Bhajan Lal precedent)."
};

export const SAMPLE_CIVIL_PRESET = {
    case_id: "COMM-SUIT-2026-104",
    case_title: "Apex Real Estate Infra Pvt Ltd vs Metro Skyline Projects Ltd",
    case_type: "Civil",
    court_name: "City Civil Court (Commercial Division), Mumbai",
    suit_valuation: 50000000.0,
    s12a_mediation: "Yes - Mediation Attempted / Failed",
    filing_date: "2026-06-15",
    agreement_date: "2024-04-10",
    breach_date: "2025-08-20",
    agreement_registered: "Yes - Duly Stamped & Registered",
    limitation_article: "Article 54 - Specific Performance (3 Years)",
    primary_prayer: "Specific Performance of Contract",
    order_39_injunction: "Yes - Prima Facie Case & Balance of Convenience Pled",
    additional_notes: "Suit for Specific Performance of registered Development Agreement with Order 39 interim relief."
};

export const SAMPLE_COMPOSITE_PRESET = {
    case_id: "SBI-NPA-MULTITRACK-2026",
    case_title: "State Bank of India vs. Zenith Infrastructure & Allied Projects Ltd",
    case_type: "Multi-Track (SARFAESI + 138 + Criminal)",
    perspective: "Creditor (Bank / Financial Institution / Complainant)",
    bank_name: "State Bank of India (SAMB Branch, Mumbai)",
    borrower_name: "Zenith Infrastructure & Allied Projects Ltd & Rajesh Singhania",
    outstanding_amount: 75000000.0,
    amount: 75000000.0,
    filing_date: "2026-06-15",
    npa_date: "2025-11-01",
    notice_13_2_date: "2025-11-15",
    cersai_registered: true,
    property_description: "Commercial Plot No. 45, Industrial Park, Sector 18, MIDC Pune",
    is_agricultural_land: false,
    possession_13_4_date: "2026-02-10",
    cheque_present: true,
    cheque_number: "981240",
    cheque_amount: 25000000.0,
    date_of_dishonour: "2025-12-05",
    dishonour_memo: true,
    notice_sent: true,
    date_of_notice: "2025-12-20",
    contract_exists: true,
    entrustment_proven: true,
    alienation_of_hypothecated_assets: true,
    offense_type: "Cheating & Alienation of Hypothecated Stocks (BNS 318/316 ↔ IPC 420/406)",
    s143a_interim_sought: true,
    sec14_dm_application_filed: true,
    description: "Defaulted commercial loan facility of Rs. 7.5 Crore with bounced cheque of Rs. 2.5 Crore and hypothecated asset alienation."
};

export const SAMPLE_CASE_PRESET = SAMPLE_NI_ACT_PRESET;

window.loadSampleCaseData = () => {
    const domain = (window.state?.userDomain || 'all').toLowerCase();
    const currentCaseType = (window.state?.caseData?.case_type || '').toLowerCase();
    
    let preset = SAMPLE_NI_ACT_PRESET;
    let label = 'Section 138';

    if (domain === 'composite' || currentCaseType.includes('composite') || currentCaseType.includes('multi')) {
        preset = SAMPLE_COMPOSITE_PRESET;
        label = 'Multi-Track Composite';
    } else if (domain === 'sarfaesi' || currentCaseType.includes('sarfaesi')) {
        preset = SAMPLE_SARFAESI_PRESET;
        label = 'SARFAESI & DRT';
    } else if (domain === 'criminal' || currentCaseType.includes('criminal')) {
        preset = SAMPLE_CRIMINAL_PRESET;
        label = 'Criminal Law';
    } else if (domain === 'civil' || currentCaseType.includes('civil')) {
        preset = SAMPLE_CIVIL_PRESET;
        label = 'Civil Litigation';
    }

    window.state.caseData = { ...(window.state.caseData || {}), ...preset };
    persistAutosave();
    renderWizardStep();
    if (window.ui && typeof window.ui.toast === 'function') {
        window.ui.toast(`⚡ Sample ${label} Case Data Loaded!`, 'success');
    }
};

window.autoAlignCourtJurisdiction = (suggestedCourt) => {
    if (!suggestedCourt) {
        const branch = window.state?.caseData?.branch_name || window.state?.caseData?.payee_branch || '';
        const cityMatch = branch.match(/(?:,\s*)([A-Za-z\s]+)$/);
        const city = cityMatch ? cityMatch[1].trim() : 'Jurisdictional';
        suggestedCourt = `Metropolitan Magistrate Court, ${city}`;
    }
    window.state.caseData = window.state.caseData || {};
    window.state.caseData.court_name = suggestedCourt;
    const courtInput = document.getElementById('court_name');
    if (courtInput) courtInput.value = suggestedCourt;
    persistAutosave();
    if (window.ui && typeof window.ui.toast === 'function') {
        window.ui.toast(`⚡ Filing Court Auto-Aligned to: ${suggestedCourt} (S.142(2) NI Act)`, 'success');
    }
};




