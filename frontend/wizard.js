import { wizardSteps, sarfaesiWizardSteps, getActiveWizardSteps } from './config.js?v=12';
import { ui, switchScreen } from './ui.js?v=12';
import { api } from './api.js?v=12';
import { renderResults } from './renderer.js?v=12';

let isWizardInitialized = false;
let currentCaseType = null;

function getCurrentSteps() {
    const caseType = window.state?.caseData?.case_type || 'Cheque Bounce';
    return getActiveWizardSteps(caseType);
}

function loadAutosave() {
    try {
        const saved = localStorage.getItem('judiq_wizard_autosave');
        if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed && typeof parsed === 'object') {
                window.state = window.state || {};
                window.state.caseData = { ...(window.state.caseData || {}), ...parsed };
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


export function renderWizardStep() {
    const steps = getCurrentSteps();
    const caseType = window.state?.caseData?.case_type || 'Cheque Bounce';
    if (currentCaseType !== caseType) {
        isWizardInitialized = false;
        currentCaseType = caseType;
    }

    const stepIdx = Math.min(window.state.currentStep - 1, steps.length - 1);
    const step = steps[stepIdx];

    // Auto-lock case_type to 'SARFAESI' when the SARFAESI wizard is active.
    // This prevents stale autosave values or accidental resets from re-routing
    // the submission to the Section 138 / Cheque Bounce engine.
    if (caseType === 'SARFAESI' || steps === sarfaesiWizardSteps) {
        window.state.caseData['case_type'] = 'SARFAESI';
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
}

function renderField(field) {
    const value = window.state.caseData[field.name] || '';
    let inputHtml = '';
    
    if (field.type === 'select') {
        inputHtml = `
            <select id="${field.name}" name="${field.name}" ${field.required ? 'required' : ''} onchange="if(typeof updateConditionalFields === 'function') updateConditionalFields()">
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
        'within_30_days', 'reply_received', 'memo_signed', 'court_attendance'
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

export const SAMPLE_CASE_PRESET = {
    case_title: "Apex Global vs. Vanguard Tech",
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

window.loadSampleCaseData = () => {
    window.state.caseData = { ...window.state.caseData, ...SAMPLE_CASE_PRESET };
    persistAutosave();
    renderWizardStep();
    if (window.ui) {
        window.ui.toast('⚡ Sample Section 138 Case Data Loaded!', 'success');
    }
};



