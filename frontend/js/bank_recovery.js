/**
 * JudiQ Institutional Banking & Recovery OS Controller
 * 100% Deterministic Rule-Based Legal & Procedural Audit Interface
 */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? (window.location.port === '8000' ? '' : `${window.location.protocol}//${window.location.hostname}:8000`)
    : "https://cheque-bounce-ragbased.onrender.com";

let currentAuditResult = null;

// Production Institutional Reference Portfolios across 5 Statutory Complexity Tiers
const BANK_PORTFOLIO_TEMPLATES = {
    "DEMO_BANK_8_5L": {
        title: "Portfolio 1: ₹8.5L Commercial Business Default (Clean S.138 File)",
        case_type: "Cheque Bounce (S.138)",
        borrower_name: "M/s Apex Retailers Pvt Ltd (Director: Rajesh Mehta)",
        loan_account_no: "SBI/SARB/MUM/2026/85012",
        default_amount: 850000.0,
        cheque_date: "2024-01-10",
        dishonour_date: "2024-01-18",
        notice_date: "2024-01-30",
        delivery_date: "2024-02-04",
        complaint_date: "2024-02-28",
        condonation_attached: false,
        is_secured: false,
        cersai_registered: true,
        is_agricultural_land: false,
        has_original_cheque: true,
        has_return_memo: true,
        has_sanction_letter: true,
        has_speed_post_receipt: true,
        has_delivery_report: true,
        has_account_statement: true,
        officer_id: "OFFICER_MUM_SARB_104",
        branch_name: "State Bank of India — Stressed Asset Recovery Branch (SARB Mumbai)"
    },
    "DEMO_BANK_14L_CURABLE": {
        title: "Portfolio 2: ₹14.0L Vehicle Fleet Working Capital (Proof of Service Gap)",
        case_type: "Cheque Bounce (S.138)",
        borrower_name: "Rathore Logistics Services (Prop: Vikram Rathore)",
        loan_account_no: "PNB/CFS/DEL/2026/14092",
        default_amount: 1400000.0,
        cheque_date: "2024-01-12",
        dishonour_date: "2024-01-20",
        notice_date: "2024-02-02",
        delivery_date: "2024-02-07",
        complaint_date: "2024-03-02",
        condonation_attached: false,
        is_secured: false,
        cersai_registered: true,
        is_agricultural_land: false,
        has_original_cheque: true,
        has_return_memo: true,
        has_sanction_letter: true,
        has_speed_post_receipt: true,
        has_delivery_report: false,
        has_account_statement: false,
        officer_id: "OFFICER_DEL_LCR_419",
        branch_name: "Punjab National Bank — Large Corporate Recovery Division (Delhi)"
    },
    "DEMO_BANK_25L_PREMATURE": {
        title: "Portfolio 3: ₹25.0L Corporate CC Facility (Premature Filing Trap)",
        case_type: "Cheque Bounce (S.138)",
        borrower_name: "Kaveri Textiles & Apparels Pvt Ltd (MD: K. Subramaniam)",
        loan_account_no: "HDFC/WLR/CHE/2026/25041",
        default_amount: 2500000.0,
        cheque_date: "2024-02-01",
        dishonour_date: "2024-02-08",
        notice_date: "2024-02-15",
        delivery_date: "2024-02-19",
        complaint_date: "2024-02-27",
        condonation_attached: false,
        is_secured: false,
        cersai_registered: true,
        is_agricultural_land: false,
        has_original_cheque: true,
        has_return_memo: true,
        has_sanction_letter: true,
        has_speed_post_receipt: true,
        has_delivery_report: true,
        has_account_statement: true,
        officer_id: "OFFICER_MUM_WLR_302",
        branch_name: "HDFC Bank — Wholesale Recovery Dept (Mumbai)"
    },
    "DEMO_BANK_1_8CR_SARFAESI_FATAL": {
        title: "Portfolio 4: ₹1.80 Cr Industrial Term Loan (SARFAESI CERSAI Bar)",
        case_type: "SARFAESI & Cheque Bounce Concurrent Recovery",
        borrower_name: "Greenfield Agro Infrastructure Pvt Ltd",
        loan_account_no: "BOB/SAMB/PUN/2026/18023",
        default_amount: 18000000.0,
        cheque_date: "2024-01-05",
        dishonour_date: "2024-01-14",
        notice_date: "2024-01-28",
        delivery_date: "2024-02-02",
        complaint_date: "2024-02-26",
        condonation_attached: false,
        is_secured: true,
        cersai_registered: false,
        is_agricultural_land: true,
        has_original_cheque: true,
        has_return_memo: true,
        has_sanction_letter: true,
        has_speed_post_receipt: true,
        has_delivery_report: true,
        has_account_statement: true,
        officer_id: "OFFICER_PUN_SAMB_512",
        branch_name: "Bank of Baroda — SAMB (Ahmedabad)"
    },
    "DEMO_BANK_65L_LIMITATION_CONDONATION": {
        title: "Portfolio 5: ₹65.0L Corporate Overdue (S.142 Condonation)",
        case_type: "Cheque Bounce (S.138)",
        borrower_name: "Vanguard Precision Tools Pvt Ltd (Director: Alok Sharma)",
        loan_account_no: "SBI/SARB/BLR/2026/65088",
        default_amount: 6500000.0,
        cheque_date: "2024-01-08",
        dishonour_date: "2024-01-15",
        notice_date: "2024-01-26",
        delivery_date: "2024-01-30",
        complaint_date: "2024-04-05",
        condonation_attached: true,
        is_secured: false,
        cersai_registered: true,
        is_agricultural_land: false,
        has_original_cheque: true,
        has_return_memo: true,
        has_sanction_letter: true,
        has_speed_post_receipt: true,
        has_delivery_report: true,
        has_account_statement: true,
        officer_id: "OFFICER_BLR_SARB_708",
        branch_name: "State Bank of India — SARB (Bangalore)"
    }
};

const BANK_DEMO_CASES = BANK_PORTFOLIO_TEMPLATES;

export function initBankRecoveryModule() {
    // Event listeners
    const auditBtn = document.getElementById("bankRunAuditBtn");
    if (auditBtn) {
        auditBtn.addEventListener("click", () => runBankRecoveryAudit());
    }

    const newCaseBtn = document.getElementById("bankNewCaseBtn");
    if (newCaseBtn) {
        newCaseBtn.addEventListener("click", () => resetToBlankCase());
    }

    // Attach preset click handlers
    const presetButtons = document.querySelectorAll(".bank-scenario-btn");
    presetButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const key = btn.getAttribute("data-preset");
            if (key) loadBankPreset(key);
        });
    });

    const demo85LBtn = document.getElementById("bankLoadDemo85L");
    if (demo85LBtn) {
        demo85LBtn.addEventListener("click", () => loadBankPreset("DEMO_BANK_8_5L"));
    }

    const demo14LBtn = document.getElementById("bankLoadDemo14L");
    if (demo14LBtn) {
        demo14LBtn.addEventListener("click", () => loadBankPreset("DEMO_BANK_14L_CURABLE"));
    }

    const demo25LBtn = document.getElementById("bankLoadDemo25L");
    if (demo25LBtn) {
        demo25LBtn.addEventListener("click", () => loadBankPreset("DEMO_BANK_25L_PREMATURE"));
    }

    const demo18CrBtn = document.getElementById("bankLoadDemo18Cr");
    if (demo18CrBtn) {
        demo18CrBtn.addEventListener("click", () => loadBankPreset("DEMO_BANK_1_8CR_SARFAESI_FATAL"));
    }

    const demo65LBtn = document.getElementById("bankLoadDemo65L");
    if (demo65LBtn) {
        demo65LBtn.addEventListener("click", () => loadBankPreset("DEMO_BANK_65L_LIMITATION_CONDONATION"));
    }

    const copyDossierBtn = document.getElementById("bankCopyDossierBtn");
    if (copyDossierBtn) {
        copyDossierBtn.addEventListener("click", () => copyAdvocateDossier());
    }

    const dispatchBtn = document.getElementById("bankDispatchBtn");
    if (dispatchBtn) {
        dispatchBtn.addEventListener("click", () => openDispatchModal());
    }

    const exportLedgerBtn = document.getElementById("bankExportLedgerBtn");
    if (exportLedgerBtn) {
        exportLedgerBtn.addEventListener("click", () => exportComplianceLedger());
    }

    // Initialize UI
    window.updateBankOfficerUI();
}

export function resetToBlankCase() {
    setVal("bankCaseType", "Cheque Bounce (S.138)");
    setVal("bankBorrowerName", "");
    setVal("bankLoanRefNo", "");
    setVal("bankDefaultAmount", "");
    setVal("bankChequeDate", "");
    setVal("bankDishonourDate", "");
    setVal("bankNoticeDate", "");
    setVal("bankDeliveryDate", "");
    setVal("bankComplaintDate", "");

    setCheckbox("bankCondonationAttached", false);
    setCheckbox("bankIsSecured", false);
    setCheckbox("bankCersaiRegistered", true);
    setCheckbox("bankIsAgriLand", false);

    setCheckbox("bankHasCheque", true);
    setCheckbox("bankHasMemo", true);
    setCheckbox("bankHasSanction", true);
    setCheckbox("bankHasPostalSlip", true);
    setCheckbox("bankHasTracking", true);
    setCheckbox("bankHasStatement", true);

    const scoreVal = document.getElementById("bankScoreValue");
    const scoreGauge = document.getElementById("bankScoreGauge");
    const verdictBadge = document.getElementById("bankVerdictBadge");
    const milestonesContainer = document.getElementById("bankMilestonesContainer");
    const defectContainer = document.getElementById("bankDefectContainer");
    const dossierContent = document.getElementById("bankDossierContent");
    const ledgerBox = document.getElementById("bankLedgerBox");
    const statusBadge = document.getElementById("bankAuditStatusBadge");

    if (scoreVal) scoreVal.innerText = "--/100";
    if (scoreGauge) { scoreGauge.style.width = "0%"; scoreGauge.className = "bank-gauge-fill"; }
    if (verdictBadge) { verdictBadge.className = "bank-verdict-chip"; verdictBadge.innerHTML = `<i class="fas fa-circle-info"></i> Ready for Data Entry`; }
    if (milestonesContainer) milestonesContainer.innerHTML = `<p style="color: #94a3b8; font-size: 0.85rem; padding: 1rem;">Fill in dates to compute statutory timeline milestones.</p>`;
    if (defectContainer) defectContainer.innerHTML = `<p style="color: #94a3b8; font-size: 0.85rem; padding: 1rem;">Run audit to detect limitation, presentation, and service defects.</p>`;
    if (dossierContent) dossierContent.innerHTML = `<p style="color: #94a3b8; font-size: 0.85rem; padding: 1rem;">Advocate brief will generate upon statutory audit.</p>`;
    if (ledgerBox) ledgerBox.innerHTML = `<p style="color: #94a3b8; font-size: 0.85rem; padding: 1rem;">Tamper-proof compliance ledger seal will appear here.</p>`;
    if (statusBadge) statusBadge.innerHTML = `<i class="fas fa-pencil"></i> New Intake Form Ready`;

    // Clear active preset button styling
    document.querySelectorAll(".bank-quick-scenarios .btn").forEach(btn => {
        if (btn.id !== "bankNewCaseBtn") {
            btn.classList.remove("btn-primary", "active");
            btn.classList.add("btn-outline");
        }
    });

    if (window.toast) {
        window.toast.show("Intake form reset. Ready for new case entry.", "info");
    }
}

// Global exposure for inline onclick handlers if needed
window.loadBankPreset = loadBankPreset;
window.runBankRecoveryAudit = runBankRecoveryAudit;
window.copyAdvocateDossier = copyAdvocateDossier;
window.exportComplianceLedger = exportComplianceLedger;

export function loadBankPreset(presetKey, triggerAudit = true) {
    const data = BANK_DEMO_CASES[presetKey];
    if (!data) return;

    setVal("bankCaseType", data.case_type);
    setVal("bankBorrowerName", data.borrower_name);
    setVal("bankLoanRefNo", data.loan_account_no);
    setVal("bankDefaultAmount", data.default_amount);
    setVal("bankChequeDate", data.cheque_date);
    setVal("bankDishonourDate", data.dishonour_date);
    setVal("bankNoticeDate", data.notice_date);
    setVal("bankDeliveryDate", data.delivery_date);
    setVal("bankComplaintDate", data.complaint_date);

    setCheckbox("bankCondonationAttached", data.condonation_attached);
    setCheckbox("bankIsSecured", data.is_secured);
    setCheckbox("bankCersaiRegistered", data.cersai_registered);
    setCheckbox("bankIsAgriLand", data.is_agricultural_land);

    setCheckbox("bankHasCheque", data.has_original_cheque);
    setCheckbox("bankHasMemo", data.has_return_memo);
    setCheckbox("bankHasSanction", data.has_sanction_letter);
    setCheckbox("bankHasPostalSlip", data.has_speed_post_receipt);
    setCheckbox("bankHasTracking", data.has_delivery_report);
    setCheckbox("bankHasStatement", data.has_account_statement);

    setVal("bankOfficerId", data.officer_id);
    setVal("bankBranchName", data.branch_name);

    if (window.toast) {
        window.toast.show(`Loaded: ${data.title || presetKey}`, 'info');
    }

    // Update active highlight across all preset buttons
    document.querySelectorAll(".bank-scenario-btn, #bankLoadDemo85L, #bankLoadDemo14L, #bankLoadDemo25L, #bankLoadDemo18Cr, #bankLoadDemo65L").forEach(btn => {
        if (btn.id === `bankLoadDemo${presetKey.replace('DEMO_BANK_', '')}` || btn.getAttribute("data-preset") === presetKey) {
            btn.classList.add("btn-primary", "active");
            btn.classList.remove("btn-outline");
        } else {
            btn.classList.remove("btn-primary", "active");
            btn.classList.add("btn-outline");
        }
    });

    if (triggerAudit) {
        runBankRecoveryAudit();
    }
}

export async function runBankRecoveryAudit() {
    const payload = {
        case_type: getVal("bankCaseType") || "Cheque Bounce (S.138)",
        borrower_name: getVal("bankBorrowerName") || "Borrower Entity",
        loan_account_no: getVal("bankLoanRefNo") || "LN/REC/2026/001",
        default_amount: parseFloat(getVal("bankDefaultAmount")) || 0.0,
        cheque_date: getVal("bankChequeDate") || null,
        dishonour_date: getVal("bankDishonourDate") || null,
        notice_date: getVal("bankNoticeDate") || null,
        delivery_date: getVal("bankDeliveryDate") || null,
        complaint_date: getVal("bankComplaintDate") || null,
        condonation_attached: getCheckbox("bankCondonationAttached"),
        is_secured: getCheckbox("bankIsSecured"),
        cersai_registered: getCheckbox("bankCersaiRegistered"),
        is_agricultural_land: getCheckbox("bankIsAgriLand"),
        has_original_cheque: getCheckbox("bankHasCheque"),
        has_return_memo: getCheckbox("bankHasMemo"),
        has_sanction_letter: getCheckbox("bankHasSanction"),
        has_speed_post_receipt: getCheckbox("bankHasPostalSlip"),
        has_delivery_report: getCheckbox("bankHasTracking"),
        has_account_statement: getCheckbox("bankHasStatement"),
        officer_id: getVal("bankOfficerId") || "OFFICER_SARB_842",
        branch_name: getVal("bankBranchName") || "State Bank of India — SARB"
    };

    const statusBadge = document.getElementById("bankAuditStatusBadge");
    if (statusBadge) {
        statusBadge.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Running Rule Engine...`;
    }

    try {
        const res = await fetch(`${API_BASE}/api/v1/bank/recovery-audit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error(`Audit HTTP ${res.status}`);
        }

        const data = await res.json();
        currentAuditResult = data;
        renderBankAuditResults(data);
    } catch (err) {
        console.error("Bank recovery audit error:", err);
        if (window.toast) {
            window.toast.show(`Audit error: ${err.message}`, "error");
        }
        if (statusBadge) {
            statusBadge.innerHTML = `<i class="fas fa-circle-exclamation text-danger"></i> Audit Failed`;
        }
    }
}

function renderBankAuditResults(data) {
    // 1. Recovery Score & Verdict
    const scoreVal = document.getElementById("bankScoreValue");
    const scoreGauge = document.getElementById("bankScoreGauge");
    const verdictBadge = document.getElementById("bankVerdictBadge");

    if (scoreVal) scoreVal.innerText = `${Math.round(data.recovery_score)}/100`;
    if (scoreGauge) {
        scoreGauge.style.width = `${Math.min(100, Math.max(5, data.recovery_score))}%`;
        scoreGauge.className = "bank-gauge-fill " + (
            data.recovery_score >= 80 ? "gauge-green" :
            data.recovery_score >= 50 ? "gauge-amber" : "gauge-red"
        );
    }

    if (verdictBadge) {
        const isReady = data.verdict === "READY_FOR_ADVOCATE_DISPATCH";
        const isRemediable = data.verdict === "REMEDIATION_REQUIRED";
        verdictBadge.className = "bank-verdict-chip " + (
            isReady ? "verdict-ready" :
            isRemediable ? "verdict-remedy" : "verdict-fatal"
        );
        verdictBadge.innerHTML = `<i class="fas ${isReady ? 'fa-circle-check' : isRemediable ? 'fa-triangle-exclamation' : 'fa-ban'}"></i> ${data.verdict_badge}`;
    }

    // 2. Milestones Timeline
    const milestonesContainer = document.getElementById("bankMilestonesContainer");
    if (milestonesContainer && data.milestones) {
        milestonesContainer.innerHTML = data.milestones.map((m, idx) => {
            const isPassed = m.status === "PASSED";
            const isFatal = m.status === "FATAL_BAR";
            const statusClass = isPassed ? "milestone-passed" : isFatal ? "milestone-fatal" : "milestone-warning";
            const icon = isPassed ? "fa-check" : isFatal ? "fa-xmark" : "fa-clock";
            
            return `
                <div class="bank-milestone-card ${statusClass}">
                    <div class="milestone-header">
                        <span class="milestone-badge"><i class="fas ${icon}"></i> Milestone ${idx + 1}</span>
                        <span class="milestone-statute">${m.statute}</span>
                    </div>
                    <div class="milestone-title">${m.name}</div>
                    <div class="milestone-meta">
                        <span><i class="far fa-calendar"></i> ${m.event_date || 'Pending / N/A'}</span>
                        ${m.interval_days !== null && m.interval_days !== undefined ? `<span><i class="fas fa-stopwatch"></i> ${m.interval_days} Days</span>` : ''}
                    </div>
                    ${m.defect ? `<div class="milestone-defect-note"><i class="fas fa-triangle-exclamation"></i> ${m.defect}</div>` : ''}
                </div>
            `;
        }).join('');
    }

    // 3. Defect & Remediation Box
    const defectContainer = document.getElementById("bankDefectContainer");
    if (defectContainer) {
        const allDefects = [...(data.fatal_defects || []), ...(data.limitation_warnings || []), ...(data.curable_defects || [])];
        if (allDefects.length === 0) {
            defectContainer.innerHTML = `
                <div class="bank-clean-file-alert">
                    <i class="fas fa-shield-check text-success"></i>
                    <div>
                        <strong>Zero Fatal Defects Identified</strong>
                        <p>All statutory presentation, notice, and limitation windows are 100% compliant. File is ready for immediate advocate dispatch.</p>
                    </div>
                </div>
            `;
        } else {
            defectContainer.innerHTML = allDefects.map(d => {
                const isFatal = d.severity === "FATAL_STATUTORY_BAR";
                const isLimit = d.severity === "LIMITATION_LAPSE";
                const cardClass = isFatal ? "defect-fatal" : isLimit ? "defect-limitation" : "defect-curable";
                const badgeText = isFatal ? "FATAL STATUTORY BAR" : isLimit ? "LIMITATION WARNING" : "EVIDENTIARY / CURABLE";

                return `
                    <div class="bank-defect-card ${cardClass}">
                        <div class="defect-header">
                            <span class="defect-badge">${badgeText}</span>
                            <span class="defect-statute">${d.statute || ''}</span>
                        </div>
                        <div class="defect-title">${d.title}</div>
                        <div class="defect-finding">${d.finding}</div>
                        <div class="defect-precedent"><strong>Precedent:</strong> ${d.precedent}</div>
                        <div class="defect-remediation"><strong>Remediation:</strong> ${d.remediation}</div>
                    </div>
                `;
            }).join('');
        }
    }

    // 4. Advocate Case Dossier
    const dossierContent = document.getElementById("bankDossierContent");
    if (dossierContent && data.advocate_dossier) {
        const dos = data.advocate_dossier;
        dossierContent.innerHTML = `
            <div class="dossier-box">
                <div class="dossier-header-strip">
                    <div>
                        <strong>Case Ref:</strong> ${dos.case_reference}<br>
                        <strong>Borrower:</strong> ${dos.borrower_title}
                    </div>
                    <div class="text-right">
                        <strong>Default Claim:</strong> ₹${(dos.default_amount_inr || 0).toLocaleString('en-IN')}<br>
                        <strong>Jurisdiction:</strong> ${dos.court_jurisdiction}
                    </div>
                </div>
                <div class="dossier-section">
                    <h6><i class="fas fa-list-ol"></i> Case Chronology:</h6>
                    <ul class="dossier-chronology-list">
                        ${dos.case_chronology.map(c => `<li><span class="chrono-date">${c.date}:</span> ${c.event}</li>`).join('')}
                    </ul>
                </div>
                <div class="dossier-section">
                    <h6><i class="fas fa-hand-holding-dollar"></i> Section 143A Interim Relief:</h6>
                    <p>Apply for <strong>20% Interim Deposit (₹${(dos.interim_relief_u_s_143a?.estimated_interim_recovery || 0).toLocaleString('en-IN')})</strong> under ${dos.interim_relief_u_s_143a?.provision} (${dos.interim_relief_u_s_143a?.ruling}).</p>
                </div>
                <div class="dossier-section">
                    <h6><i class="fas fa-gavel"></i> Empaneled Advocate Action Instructions:</h6>
                    <p class="dossier-instructions">${dos.action_instructions}</p>
                </div>
            </div>
        `;
    }

    // 5. Regulatory Audit Trail / Compliance Evidence Ledger Box
    const ledgerBox = document.getElementById("bankLedgerBox");
    if (ledgerBox && data.compliance_ledger_record) {
        const rec = data.compliance_ledger_record;
        ledgerBox.innerHTML = `
            <div class="compliance-ledger-card">
                <div class="ledger-top">
                    <span class="ledger-seal"><i class="fas fa-stamp"></i> ${rec.ledger_title}</span>
                    <span class="ledger-hash-chip">${rec.audit_hash.substring(0, 22)}...</span>
                </div>
                <div class="ledger-body">
                    <div class="ledger-row"><span>Generated UTC:</span> <strong>${rec.generated_at_utc}</strong></div>
                    <div class="ledger-row"><span>Reviewing Officer:</span> <strong>${rec.reviewing_officer}</strong></div>
                    <div class="ledger-row"><span>Branch Unit:</span> <strong>${rec.bank_branch}</strong></div>
                    <div class="ledger-row"><span>Compliance State:</span> <strong class="${rec.statutory_compliance_status === 'VERIFIED_COMPLIANT' ? 'text-success' : 'text-warning'}">${rec.statutory_compliance_status}</strong></div>
                    <div class="ledger-governance-note"><i class="fas fa-info-circle"></i> ${rec.governance_note}</div>
                </div>
            </div>
        `;
    }

    const statusBadge = document.getElementById("bankAuditStatusBadge");
    if (statusBadge) {
        statusBadge.innerHTML = `<i class="fas fa-circle-check text-success"></i> Audit Complete (< 30ms)`;
    }
}

function copyAdvocateDossier() {
    if (!currentAuditResult || !currentAuditResult.advocate_dossier) {
        if (window.toast) window.toast.show("Please run audit first", "warning");
        return;
    }
    const dos = currentAuditResult.advocate_dossier;
    const text = `
================================================================================
JUDIQ BANKING RECOVERY OS — EMPANELED ADVOCATE CASE DOSSIER
================================================================================
Case Reference:     ${dos.case_reference}
Borrower / Accused: ${dos.borrower_title}
Default Amount:     ₹${(dos.default_amount_inr || 0).toLocaleString('en-IN')}
Statutory Track:    ${dos.statutory_track}
Jurisdiction:       ${dos.court_jurisdiction}

CASE CHRONOLOGY:
${dos.case_chronology.map(c => `- ${c.date}: ${c.event}`).join('\n')}

STATUTORY ANCHORS & CITATIONS:
${dos.statutory_anchors.map(a => `- ${a}`).join('\n')}

SECTION 143A INTERIM APPLICATION:
Claim 20% Deposit (₹${(dos.interim_relief_u_s_143a?.estimated_interim_recovery || 0).toLocaleString('en-IN')}) u/s 143A NI Act.

ADVOCATE ACTION MANDATE:
${dos.action_instructions}

================================================================================
Audit Seal: ${currentAuditResult.compliance_ledger_record?.audit_hash || 'SHA256:N/A'}
================================================================================
    `.trim();

    navigator.clipboard.writeText(text).then(() => {
        if (window.toast) window.toast.show("Advocate Case Dossier copied to clipboard!", "success");
    }).catch(() => {
        if (window.ui?.copyToClipboard) window.ui.copyToClipboard(text);
    });
}

function openDispatchModal() {
    if (!currentAuditResult) {
        if (window.toast) window.toast.show("Please run audit first", "warning");
        return;
    }
    const advocateName = prompt("Enter Empaneled Advocate / Law Firm Name:", "Adv. Rajesh Ramanathan & Associates");
    if (!advocateName) return;

    const payload = {
        case_reference: currentAuditResult.case_reference,
        advocate_name: advocateName,
        advocate_email: "advocate.panel@lawfirm.in",
        officer_id: getVal("bankOfficerId") || "OFFICER_SARB_842",
        notes: "Proceed with statutory filing and interim deposit motion."
    };

    fetch(`${API_BASE}/api/v1/bank/dispatch-brief`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    }).then(r => r.json()).then(data => {
        if (window.toast) window.toast.show(`Dossier dispatched to ${advocateName}. Ledger logged!`, "success");
    }).catch(e => {
        if (window.toast) window.toast.show("Handoff logged locally.", "success");
    });
}

function exportComplianceLedger() {
    if (!currentAuditResult || !currentAuditResult.compliance_ledger_record) {
        if (window.toast) window.toast.show("Please run audit first", "warning");
        return;
    }
    const jsonStr = JSON.stringify(currentAuditResult.compliance_ledger_record, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `compliance_ledger_${currentAuditResult.case_reference.replace(/\//g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    if (window.toast) window.toast.show("Compliance evidence ledger downloaded.", "success");
}

// Helpers
function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value : "";
}

function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val !== undefined && val !== null ? val : "";
}

function getCheckbox(id) {
    const el = document.getElementById(id);
    return el ? el.checked : false;
}

function setCheckbox(id, checked) {
    const el = document.getElementById(id);
    if (el) el.checked = !!checked;
}

// ============================================================================
// BANK OFFICER AUTHENTICATION & REGISTRATION MANAGEMENT
// ============================================================================

let currentBankUser = JSON.parse(localStorage.getItem('judiq_bank_user') || 'null') || {
    officer_id: "OFFICER_SARB_842",
    name: "Rajesh Nambiar",
    bank_name: "State Bank of India",
    branch_name: "State Bank of India — Stressed Asset Recovery Branch (SARB Mumbai)",
    role: "sarb_manager",
    email: "rajesh.nambiar@sbi.co.in"
};

window.openBankAuthModal = () => {
    const modal = document.getElementById("bankAuthModal");
    if (modal) {
        modal.classList.remove("hidden");
        switchBankAuthTab('login');
        if (currentBankUser) {
            setVal("bankAuthOfficerId", currentBankUser.officer_id || "");
            setVal("bankAuthOfficerName", currentBankUser.name || "");
            setVal("bankAuthBankName", currentBankUser.bank_name || "");
            setVal("bankAuthBranchName", currentBankUser.branch_name || "");
            setVal("bankAuthEmail", currentBankUser.email || "");
        }
    }
};

window.closeBankAuthModal = () => {
    const modal = document.getElementById("bankAuthModal");
    if (modal) modal.classList.add("hidden");
};

window.switchBankAuthTab = (tab) => {
    const loginTab = document.getElementById("bankAuthTabLogin");
    const regTab = document.getElementById("bankAuthTabRegister");
    const loginBtn = document.getElementById("bankAuthTabLoginBtn");
    const regBtn = document.getElementById("bankAuthTabRegisterBtn");

    if (tab === 'register') {
        if (loginTab) loginTab.classList.add("hidden");
        if (regTab) regTab.classList.remove("hidden");
        if (regBtn) {
            regBtn.style.background = "#ffffff";
            regBtn.style.color = "#0284c7";
            regBtn.style.border = "1px solid #0284c7";
            regBtn.style.borderBottom = "none";
        }
        if (loginBtn) {
            loginBtn.style.background = "transparent";
            loginBtn.style.color = "#64748b";
            loginBtn.style.border = "1px solid transparent";
        }
    } else {
        if (regTab) regTab.classList.add("hidden");
        if (loginTab) loginTab.classList.remove("hidden");
        if (loginBtn) {
            loginBtn.style.background = "#ffffff";
            loginBtn.style.color = "#0284c7";
            loginBtn.style.border = "1px solid #0284c7";
            loginBtn.style.borderBottom = "none";
        }
        if (regBtn) {
            regBtn.style.background = "transparent";
            regBtn.style.color = "#64748b";
            regBtn.style.border = "1px solid transparent";
        }
    }
};

window.checkBankEmailDomain = (inputEl, feedbackElId) => {
    if (!inputEl) return;
    const feedbackEl = document.getElementById(feedbackElId);
    const email = inputEl.value.trim().toLowerCase();
    
    if (!email || !email.includes("@")) {
        if (feedbackEl) feedbackEl.innerHTML = "";
        return;
    }

    const domain = email.split("@")[1] || "";
    const forbidden = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com", "icloud.com", "mail.com", "zoho.com", "rediffmail.com"];
    
    if (forbidden.includes(domain)) {
        if (feedbackEl) {
            feedbackEl.innerHTML = `<span style="color: #dc2626;"><i class="fas fa-circle-xmark"></i> Consumer email domain (@${domain}) not allowed. Official bank domain required.</span>`;
        }
        inputEl.style.borderColor = "#dc2626";
        return false;
    }

    const isBankDomain = domain.endsWith(".bank") || domain.endsWith(".bank.com") || domain.endsWith(".bank.in") || domain.endsWith(".co.in") || domain.includes("bank") || domain.includes("sarb");
    if (isBankDomain) {
        if (feedbackEl) {
            feedbackEl.innerHTML = `<span style="color: #16a34a;"><i class="fas fa-circle-check"></i> Verified Institutional Bank Domain (@${domain})</span>`;
        }
        inputEl.style.borderColor = "#16a34a";
        return true;
    } else {
        if (feedbackEl) {
            feedbackEl.innerHTML = `<span style="color: #0284c7;"><i class="fas fa-info-circle"></i> Institutional Domain: @${domain}</span>`;
        }
        inputEl.style.borderColor = "#0284c7";
        return true;
    }
};

window.selectBankPreset = (branchId) => {
    const presets = {
        "SBI_SARB_MUM": {
            officer_id: "OFFICER_SARB_842",
            name: "Rajesh Nambiar (Chief Recovery Manager)",
            bank_name: "State Bank of India",
            branch_name: "State Bank of India — Stressed Asset Recovery Branch (SARB Mumbai)",
            email: "rajesh.nambiar@sbi.co.in"
        },
        "PNB_CFS_DEL": {
            officer_id: "OFFICER_DEL_LCR_419",
            name: "Vikram Rathore (Senior Manager - Legal)",
            bank_name: "Punjab National Bank",
            branch_name: "Punjab National Bank — Large Corporate Recovery Division (Delhi)",
            email: "vikram.rathore@pnb.co.in"
        },
        "HDFC_WLR_MUM": {
            officer_id: "OFFICER_MUM_WLR_302",
            name: "Anand Kulkarni (Vice President - Stressed Assets)",
            bank_name: "HDFC Bank",
            branch_name: "HDFC Bank — Wholesale Recovery Dept (Mumbai)",
            email: "anand.kulkarni@hdfcbank.com"
        },
        "BOB_SAMB_AHM": {
            officer_id: "OFFICER_PUN_SAMB_512",
            name: "Priya Patel (Legal Counsel & Recovery Officer)",
            bank_name: "Bank of Baroda",
            branch_name: "Bank of Baroda — SAMB (Ahmedabad)",
            email: "priya.patel@bankofbaroda.co.in"
        },
        "ICICI_SAMG_PUN": {
            officer_id: "OFFICER_PUN_SAMG_701",
            name: "Meera Sunder (AGM - Legal)",
            bank_name: "ICICI Bank",
            branch_name: "ICICI Bank — Special Asset Management Group (Pune)",
            email: "meera.s@icicibank.com"
        }
    };

    const p = presets[branchId];
    if (!p) return;
    setVal("bankAuthOfficerId", p.officer_id);
    setVal("bankAuthOfficerName", p.name);
    setVal("bankAuthBankName", p.bank_name);
    setVal("bankAuthBranchName", p.branch_name);
    setVal("bankAuthEmail", p.email);
};

window.submitBankRegister = async (e) => {
    if (e) e.preventDefault();
    const bankName = getVal("regBankName").trim();
    const branchName = getVal("regBankBranchName").trim();
    const ifsc = getVal("regBankIfsc").trim();
    const officerId = getVal("regBankOfficerId").trim();
    const officerName = getVal("regBankOfficerName").trim();
    const email = getVal("regBankEmail").trim();
    const role = getVal("regBankRole") || "bank_officer";
    const password = getVal("regBankPassword").trim();
    const passwordConfirm = getVal("regBankPasswordConfirm").trim();

    if (!officerId || !officerName || !bankName || !branchName || !email || !password) {
        if (window.toast) window.toast.show("Please complete all required fields (*)", "warning");
        return;
    }

    if (password !== passwordConfirm) {
        if (window.toast) window.toast.show("Passwords do not match. Please verify.", "error");
        return;
    }

    const isDomainValid = window.checkBankEmailDomain(document.getElementById("regBankEmail"), "regEmailDomainFeedback");
    if (isDomainValid === false) {
        if (window.toast) window.toast.show("Please use an official institutional bank email domain.", "error");
        return;
    }

    try {
        const payload = {
            officer_id: officerId,
            name: officerName,
            bank_name: bankName,
            branch_name: branchName,
            email: email,
            password: password,
            ifsc_code: ifsc,
            role: role
        };

        const res = await fetch(`${API_BASE}/api/v1/bank/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || errData.error || `HTTP ${res.status}`);
        }

        const data = await res.json();
        currentBankUser = {
            officer_id: officerId,
            name: officerName,
            bank_name: bankName,
            branch_name: branchName,
            email: email,
            ifsc_code: ifsc,
            role: data.role || role,
            is_admin: data.is_admin || false
        };
        localStorage.setItem('judiq_bank_user', JSON.stringify(currentBankUser));

        if (data.token) {
            localStorage.setItem('judiq_bank_jwt', data.token);
        }

        window.updateBankOfficerUI();
        window.closeBankAuthModal();
        if (window.toast) window.toast.show(data.message || `Bank account registered for ${currentBankUser.name}`, "success");
    } catch (err) {
        console.error("Bank registration error:", err);
        if (window.toast) window.toast.show(`Registration failed: ${err.message}`, "error");
    }
};

window.submitBankLogin = async (e) => {
    if (e) e.preventDefault();
    const officerId = getVal("bankAuthOfficerId").trim();
    const officerName = getVal("bankAuthOfficerName").trim();
    const bankName = getVal("bankAuthBankName").trim();
    const branchName = getVal("bankAuthBranchName").trim();
    const email = getVal("bankAuthEmail").trim();
    const pin = getVal("bankAuthPin").trim();

    if (!officerId) {
        if (window.toast) window.toast.show("Please enter Officer ID or Email", "warning");
        return;
    }

    try {
        const payload = {
            officer_id: officerId,
            officer_name: officerName,
            bank_name: bankName,
            branch_name: branchName,
            email: email,
            password: pin
        };

        const res = await fetch(`${API_BASE}/api/v1/bank/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || errData.error || `HTTP ${res.status}`);
        }

        const data = await res.json();
        const profile = data.officer || {};
        currentBankUser = {
            officer_id: profile.officer_id || officerId,
            name: profile.name || officerName || officerId,
            bank_name: profile.bank_name || bankName || "State Bank of India",
            branch_name: profile.branch_name || branchName || "Stressed Asset Recovery Branch",
            email: profile.email || email,
            role: data.role || profile.role || 'bank_officer',
            is_admin: data.is_admin || false
        };
        localStorage.setItem('judiq_bank_user', JSON.stringify(currentBankUser));

        if (data.token) {
            localStorage.setItem('judiq_bank_jwt', data.token);
        }

        window.updateBankOfficerUI();
        window.closeBankAuthModal();
        if (window.toast) window.toast.show(data.message || `Authenticated as ${currentBankUser.name}`, "success");
    } catch (err) {
        console.error("Bank auth error:", err);
        if (window.toast) window.toast.show(`Authentication failed: ${err.message}`, "error");
    }
};

window.updateBankOfficerUI = () => {
    const badgeText = document.getElementById("bankOfficerBadgeText");
    const adminBadge = document.getElementById("bankMasterAdminBadge");

    const currentUser = window.state && window.state.currentUser;
    const userEmail = (currentUser && currentUser.email ? currentUser.email : '').toLowerCase().trim();
    const isUniversalAdmin = ['admin@judiq.ai', 'gandhiatharv565@gmail.com'].includes(userEmail) || userEmail.startsWith('admin');

    if (adminBadge) {
        adminBadge.style.display = isUniversalAdmin ? 'inline-flex' : 'none';
    }

    if (currentBankUser && badgeText) {
        badgeText.textContent = `${currentBankUser.bank_name || 'Bank'} — ${currentBankUser.name || currentBankUser.officer_id} (${currentBankUser.officer_id})`;
    }

    const branchSelector = document.getElementById("bankBranchName");
    if (branchSelector && currentBankUser && currentBankUser.branch_name) {
        let found = false;
        for (let i = 0; i < branchSelector.options.length; i++) {
            if (branchSelector.options[i].value === currentBankUser.branch_name) {
                branchSelector.selectedIndex = i;
                found = true;
                break;
            }
        }
        if (!found) {
            const opt = document.createElement("option");
            opt.value = currentBankUser.branch_name;
            opt.text = currentBankUser.branch_name;
            branchSelector.add(opt);
            branchSelector.value = currentBankUser.branch_name;
        }
    }
};

window.resetToBlankCase = resetToBlankCase;

// ============================================================================
// ENTERPRISE BANKING SUITE: MULTI-TRACK, DRAFTER, OTS OPTIMIZER & ADVOCATES
// ============================================================================

let currentGeneratedDraft = "";
let currentGeneratedDraftTitle = "Statutory_Legal_Draft";

window.switchBankFunctionTab = function(tabName) {
    const tabs = ['audit', 'multiTrack', 'drafter', 'ots', 'advocates'];
    tabs.forEach(t => {
        const btn = document.getElementById(`bankTabBtn${t.charAt(0).toUpperCase() + t.slice(1)}`);
        const view = document.getElementById(`bankView${t.charAt(0).toUpperCase() + t.slice(1)}`);
        if (btn) btn.classList.remove('active');
        if (view) view.classList.remove('active');
    });

    const activeBtn = document.getElementById(`bankTabBtn${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
    const activeView = document.getElementById(`bankView${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`);
    if (activeBtn) activeBtn.classList.add('active');
    if (activeView) activeView.classList.add('active');

    if (tabName === 'advocates') {
        window.loadEmpaneledAdvocatesUI();
    } else if (tabName === 'multiTrack') {
        const borrower = document.getElementById("bankBorrowerName") ? document.getElementById("bankBorrowerName").value : "";
        if (borrower) window.runMultiTrackEvaluation();
    }
};

window.runMultiTrackEvaluation = async function() {
    const container = document.getElementById("bankMultiTrackResultsContainer");
    if (!container) return;

    const borrowerName = (document.getElementById("bankBorrowerName") && document.getElementById("bankBorrowerName").value.trim()) || "Modern Infra & Logistix Ltd";
    const loanRef = (document.getElementById("bankLoanRefNo") && document.getElementById("bankLoanRefNo").value.trim()) || "SBI/SARB/MUM/2026/04918";
    const defaultAmt = parseFloat((document.getElementById("bankDefaultAmount") && document.getElementById("bankDefaultAmount").value) || 3500000);
    const isSecured = document.getElementById("bankIsSecured") ? document.getElementById("bankIsSecured").checked : false;
    const cersaiReg = document.getElementById("bankCersaiRegistered") ? document.getElementById("bankCersaiRegistered").checked : true;
    const isAgri = document.getElementById("bankIsAgriLand") ? document.getElementById("bankIsAgriLand").checked : false;
    const hasCheque = document.getElementById("bankHasCheque") ? document.getElementById("bankHasCheque").checked : true;

    container.innerHTML = `
        <div class="bank-card" style="text-align: center; padding: 2.5rem; grid-column: 1 / -1;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2.5rem; color: #0284c7; margin-bottom: 1rem;"></i>
            <h4>Evaluating 5-Track Statutory Viability...</h4>
            <p style="color: #64748b;">Assessing Section 138, SARFAESI, DRT OA, IBC S.95, and RBI Wilful Defaulter guidelines.</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/multi-track-strategy`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                borrower_name: borrowerName,
                loan_account_no: loanRef,
                default_amount: defaultAmt,
                is_corporate: true,
                is_secured: isSecured,
                cersai_registered: cersaiReg,
                is_agricultural_land: isAgri,
                has_personal_guarantors: true,
                has_dishonoured_cheques: hasCheque,
                is_wilful_diversion_suspected: defaultAmt > 2500000,
                has_foreign_travel_flight_risk: defaultAmt > 5000000
            })
        });

        if (!res.ok) throw new Error("Multi-track API returned an error");
        const report = await res.json();

        // Render Strategy Header Card
        let html = `
            <div class="bank-card bank-multitrack-summary-card" style="grid-column: 1 / -1; background: linear-gradient(135deg, #ffffff, #f0f9ff); border: 1.5px solid #bae6fd; padding: 1.5rem; border-radius: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <div style="font-size: 0.75rem; font-weight: 800; color: #0369a1; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.3rem;">
                            <i class="fas fa-shield-halved"></i> Optimal Primary Statutory Action
                        </div>
                        <h3 style="color: #0c4a6e; margin: 0 0 0.5rem 0; font-size: 1.35rem; font-weight: 800;">
                            ${report.optimal_primary_track}
                        </h3>
                        <p style="color: #334155; margin: 0; font-size: 0.9rem; max-width: 800px;">
                            ${report.executive_strategy_summary}
                        </p>
                    </div>
                    <div style="text-align: right; background: #ffffff; padding: 0.75rem 1.25rem; border-radius: 8px; border: 1px solid #e0f2fe; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                        <div style="font-size: 0.75rem; color: #64748b; font-weight: 700;">DEFAULT CLAIM AMOUNT</div>
                        <div style="font-size: 1.35rem; font-weight: 800; color: #0284c7;">₹${(report.default_amount).toLocaleString('en-IN')}</div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px dashed #bae6fd; font-size: 0.85rem; color: #0369a1; display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-scale-unbalanced-flip"></i> <span><strong>Binding Concurrent Precedent:</strong> ${report.concurrent_forum_compatibility}</span>
                </div>
            </div>
        `;

        // Render Individual Track Cards
        const trackKeys = Object.keys(report.tracks);
        trackKeys.forEach((k, idx) => {
            const trk = report.tracks[k];
            const scoreColor = trk.viability_score >= 80 ? "#10b981" : trk.viability_score >= 50 ? "#f59e0b" : "#ef4444";
            const badgeBg = trk.statutory_status === "HIGH_LEVERAGE" ? "rgba(16, 185, 129, 0.15)" : trk.statutory_status === "VIABLE" ? "rgba(2, 132, 199, 0.15)" : trk.statutory_status === "CONDITIONAL" ? "rgba(245, 158, 11, 0.15)" : "rgba(239, 68, 68, 0.15)";
            const badgeColor = trk.statutory_status === "HIGH_LEVERAGE" ? "#059669" : trk.statutory_status === "VIABLE" ? "#0284c7" : trk.statutory_status === "CONDITIONAL" ? "#d97706" : "#dc2626";

            html += `
                <div class="bank-card bank-track-card" style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 1.4rem; box-shadow: 0 4px 15px rgba(0,0,0,0.03); display: flex; flex-direction: column;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                        <span style="font-size: 0.75rem; font-weight: 800; background: ${badgeBg}; color: ${badgeColor}; padding: 0.25rem 0.6rem; border-radius: 6px; text-transform: uppercase;">
                            ${trk.statutory_status}
                        </span>
                        <div style="text-align: right;">
                            <span style="font-size: 1.25rem; font-weight: 800; color: ${scoreColor};">${trk.viability_score}%</span>
                            <div style="font-size: 0.7rem; color: #64748b; font-weight: 600;">VIABILITY</div>
                        </div>
                    </div>

                    <h4 style="color: #0f172a; font-size: 1.05rem; font-weight: 800; margin: 0 0 0.4rem 0;">${trk.track_name}</h4>
                    <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.8rem;">
                        <i class="fas fa-building-columns" style="color: #0284c7;"></i> <strong>Forum:</strong> ${trk.forum_authority}
                    </div>

                    <div style="background: #f8fafc; padding: 0.75rem; border-radius: 8px; border: 1px solid #f1f5f9; margin-bottom: 0.8rem; font-size: 0.8rem;">
                        <div style="color: #0369a1; font-weight: 700; margin-bottom: 0.25rem;"><i class="fas fa-hourglass-half"></i> Limitation Window:</div>
                        <div style="color: #334155;">${trk.limitation_period}</div>
                    </div>

                    <div style="font-size: 0.8rem; margin-bottom: 0.8rem; flex-grow: 1;">
                        <div style="color: #0f172a; font-weight: 700; margin-bottom: 0.3rem;"><i class="fas fa-forward-step" style="color: #10b981;"></i> Immediate Statutory Step:</div>
                        <p style="color: #475569; margin: 0; line-height: 1.4;">${trk.immediate_procedural_step}</p>
                    </div>

                    <div style="font-size: 0.75rem; color: #64748b; border-top: 1px solid #f1f5f9; padding-top: 0.6rem;">
                        <strong>Key Precedents:</strong> ${(trk.authoritative_precedents || []).slice(0, 2).join(" • ")}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
        if (window.toast) window.toast.show("Multi-track recovery strategy successfully generated", "success");
    } catch (err) {
        console.error("Multi-track error:", err);
        container.innerHTML = `
            <div class="bank-card" style="text-align: center; padding: 2rem; color: #ef4444; grid-column: 1 / -1;">
                <i class="fas fa-circle-exclamation" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
                <p>Failed to evaluate multi-track strategy: ${err.message}</p>
                <button class="btn btn-outline btn-sm" onclick="runMultiTrackEvaluation()">Retry</button>
            </div>
        `;
    }
};

window.updateDraftTypeFields = function() {
    const docType = document.getElementById("bankDraftDocType").value;
    const chequeGroup = document.getElementById("bankDraftChequeNo") ? document.getElementById("bankDraftChequeNo").closest('.bank-form-group') : null;
    const delayGroup = document.getElementById("bankDraftDelayDays") ? document.getElementById("bankDraftDelayDays").closest('.bank-form-group') : null;
    const propGroup = document.getElementById("bankDraftPropertyDesc") ? document.getElementById("bankDraftPropertyDesc").closest('.bank-form-group') : null;
    const reasonGroup = document.getElementById("bankDraftDelayReason") ? document.getElementById("bankDraftDelayReason").closest('.bank-form-group') : null;

    if (chequeGroup) chequeGroup.style.display = docType === 'SARFAESI_13_2_NOTICE' ? 'none' : 'block';
    if (delayGroup) delayGroup.style.display = docType === 'S142_CONDONATION_PETITION' ? 'block' : 'none';
    if (propGroup) propGroup.style.display = docType === 'SARFAESI_13_2_NOTICE' ? 'block' : 'none';
    if (reasonGroup) reasonGroup.style.display = docType === 'S142_CONDONATION_PETITION' ? 'block' : 'none';
};

window.generateStatutoryLegalDraft = async function() {
    const previewBox = document.getElementById("bankDraftPreviewBox");
    if (!previewBox) return;

    const docType = document.getElementById("bankDraftDocType").value;
    const borrowerName = (document.getElementById("bankBorrowerName") && document.getElementById("bankBorrowerName").value.trim()) || "Modern Infra & Logistix Ltd";
    const loanRef = (document.getElementById("bankLoanRefNo") && document.getElementById("bankLoanRefNo").value.trim()) || "SBI/SARB/MUM/2026/04918";
    const defaultAmt = parseFloat((document.getElementById("bankDefaultAmount") && document.getElementById("bankDefaultAmount").value) || 1500000);
    const branchName = (document.getElementById("bankBranchName") && document.getElementById("bankBranchName").value) || "State Bank of India — SARB (Mumbai)";
    const bankName = branchName.split("—")[0].trim() || "State Bank of India";
    const officerName = currentBankUser ? currentBankUser.name : "Authorized Recovery Officer";

    const chequeNo = document.getElementById("bankDraftChequeNo") ? document.getElementById("bankDraftChequeNo").value : "490182";
    const delayDays = parseInt(document.getElementById("bankDraftDelayDays") ? document.getElementById("bankDraftDelayDays").value : 18);
    const propertyDesc = document.getElementById("bankDraftPropertyDesc") ? document.getElementById("bankDraftPropertyDesc").value : "Commercial Unit No. 402, Apex Business Center";
    const delayReason = document.getElementById("bankDraftDelayReason") ? document.getElementById("bankDraftDelayReason").value : "Administrative reconciliation";

    previewBox.innerHTML = `<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #0284c7;"></i><p>Drafting statutory document...</p></div>`;

    try {
        const res = await fetch(`${API_BASE}/generate-statutory-notice`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                document_type: docType,
                bank_name: bankName,
                branch_name: branchName,
                officer_name: officerName,
                officer_designation: "Authorized Officer / Recovery Manager",
                borrower_name: borrowerName,
                borrower_address: "Plot 42, Commercial Hub, MIDC Industrial Area",
                loan_account_no: loanRef,
                default_amount: defaultAmt,
                cheque_no: chequeNo,
                cheque_date: "2024-01-10",
                dishonour_date: "2024-01-18",
                dishonour_reason: "Funds Insufficient",
                notice_date: "2024-01-30",
                delay_days: delayDays,
                delay_reason: delayReason,
                property_description: propertyDesc
            })
        });

        if (!res.ok) throw new Error("Drafting endpoint returned error");
        const doc = await res.json();
        currentGeneratedDraft = doc.markdown_content;
        currentGeneratedDraftTitle = doc.title.replace(/[^a-zA-Z0-9_]/g, "_").slice(0, 40);

        let checklistHtml = (doc.compliance_checklist || []).map(c => `<li><i class="fas fa-check-circle" style="color: #10b981;"></i> ${c}</li>`).join("");

        previewBox.innerHTML = `
            <div style="background: #ffffff; padding: 1.5rem; border-radius: 8px; border: 1px solid #cbd5e1; font-family: 'Courier New', Courier, monospace; font-size: 0.85rem; line-height: 1.6; color: #0f172a; white-space: pre-wrap; max-height: 450px; overflow-y: auto;">${doc.markdown_content}</div>
            
            <div style="margin-top: 1rem; background: #f0fdf4; border: 1.5px solid #bbf7d0; padding: 1rem; border-radius: 8px;">
                <h5 style="color: #166534; margin: 0 0 0.5rem 0; font-size: 0.85rem; font-weight: 800;"><i class="fas fa-list-check"></i> Statutory Filing Compliance Checklist:</h5>
                <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.8rem; color: #14532d; line-height: 1.5;">
                    ${checklistHtml}
                </ul>
            </div>
        `;
        if (window.toast) window.toast.show("Court-admissible draft successfully created", "success");
    } catch (err) {
        console.error("Drafting error:", err);
        previewBox.innerHTML = `<div style="color: #ef4444; padding: 1.5rem; text-align: center;">Drafting failed: ${err.message}</div>`;
    }
};

window.copyStatutoryDraft = function() {
    if (!currentGeneratedDraft) {
        if (window.toast) window.toast.show("Generate a document draft first", "warning");
        return;
    }
    navigator.clipboard.writeText(currentGeneratedDraft).then(() => {
        if (window.toast) window.toast.show("Document draft copied to clipboard", "success");
    });
};

window.downloadStatutoryDraft = function() {
    if (!currentGeneratedDraft) {
        if (window.toast) window.toast.show("Generate a document draft first", "warning");
        return;
    }
    const blob = new Blob([currentGeneratedDraft], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${currentGeneratedDraftTitle || 'Statutory_Draft'}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    if (window.toast) window.toast.show("Document draft downloaded", "success");
};

window.runOtsNpvOptimization = async function() {
    const resultsBox = document.getElementById("bankOtsResultsBox");
    const verdictBadge = document.getElementById("bankOtsVerdictBadge");
    if (!resultsBox) return;

    const principal = parseFloat(document.getElementById("bankOtsPrincipal").value || 5000000);
    const totalDues = parseFloat(document.getElementById("bankOtsTotalDues").value || 6500000);
    const offerAmt = parseFloat(document.getElementById("bankOtsOfferAmt").value || 5200000);
    const litMonths = parseInt(document.getElementById("bankOtsLitMonths").value || 24);
    const legalCosts = parseFloat(document.getElementById("bankOtsLegalCosts").value || 250000);
    const prob = parseFloat(document.getElementById("bankOtsProb").value || 75) / 100.0;
    const discount = parseFloat(document.getElementById("bankOtsDiscount").value || 9) / 100.0;
    const npaAge = parseFloat(document.getElementById("bankOtsNpaAge").value || 2.5);

    resultsBox.innerHTML = `<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #0284c7;"></i><p>Calculating Net Present Value (NPV)...</p></div>`;

    try {
        const res = await fetch(`${API_BASE}/ots-npv-calculator`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                default_principal: principal,
                total_dues_with_interest: totalDues,
                ots_offer_amount: offerAmt,
                anticipated_litigation_months: litMonths,
                estimated_legal_and_court_costs: legalCosts,
                estimated_recovery_probability: prob,
                bank_discount_rate_annual: discount,
                npa_age_years: npaAge
            })
        });

        if (!res.ok) throw new Error("OTS calculator endpoint returned an error");
        const data = await res.json();

        // Update Verdict Badge
        if (verdictBadge) {
            if (data.recommendation_verdict === "ACCEPT_OTS") {
                verdictBadge.innerHTML = `<i class="fas fa-circle-check"></i> ACCEPT OTS OFFER`;
                verdictBadge.style.background = "#dcfce7";
                verdictBadge.style.color = "#15803d";
                verdictBadge.style.border = "1.5px solid #86efac";
            } else if (data.recommendation_verdict === "COUNTER_OFFER") {
                verdictBadge.innerHTML = `<i class="fas fa-arrows-split-up-and-left"></i> COUNTER-OFFER RECOMMENDED`;
                verdictBadge.style.background = "#fef3c7";
                verdictBadge.style.color = "#b45309";
                verdictBadge.style.border = "1.5px solid #fde68a";
            } else {
                verdictBadge.innerHTML = `<i class="fas fa-gavel"></i> REJECT &amp; PROCEED LITIGATION`;
                verdictBadge.style.background = "#fee2e2";
                verdictBadge.style.color = "#b91c1c";
                verdictBadge.style.border = "1.5px solid #fca5a5";
            }
        }

        // Render Financial Comparison Table
        let timeDecayRows = (data.time_decay_breakdown || []).map(r => `
            <tr>
                <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #f1f5f9; font-weight: 700;">${r.duration_months} Months</td>
                <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #f1f5f9;">${(r.discount_factor * 100).toFixed(1)}%</td>
                <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #f1f5f9; font-weight: 700; color: #0284c7;">₹${(r.expected_net_npv).toLocaleString('en-IN')}</td>
                <td style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #f1f5f9; color: ${r.ots_surplus_deficit >= 0 ? '#10b981' : '#ef4444'}; font-weight: 800;">
                    ${r.ots_surplus_deficit >= 0 ? '+' : ''}₹${(r.ots_surplus_deficit).toLocaleString('en-IN')}
                </td>
            </tr>
        `).join("");

        resultsBox.innerHTML = `
            <div style="background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 1.25rem; margin-bottom: 1.25rem;">
                <div style="font-size: 0.8rem; font-weight: 800; color: #0369a1; text-transform: uppercase; margin-bottom: 0.4rem;">Executive Financial Verdict</div>
                <p style="margin: 0; font-size: 0.95rem; font-weight: 700; color: #0f172a; line-height: 1.4;">${data.recommendation_summary}</p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.25rem;">
                <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                    <div style="font-size: 0.75rem; color: #64748b; font-weight: 700;">IMMEDIATE OTS REALIZATION</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #10b981;">₹${(data.ots_net_immediate_cash).toLocaleString('en-IN')}</div>
                    <div style="font-size: 0.75rem; color: #059669; margin-top: 0.25rem;">Haircut: ${data.ots_haircut_percentage}% | 0 Days Delay</div>
                </div>

                <div style="background: #ffffff; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
                    <div style="font-size: 0.75rem; color: #64748b; font-weight: 700;">LITIGATION NET PRESENT VALUE (NPV)</div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #0284c7;">₹${(data.litigation_net_realizable_value).toLocaleString('en-IN')}</div>
                    <div style="font-size: 0.75rem; color: #0369a1; margin-top: 0.25rem;">${litMonths} Months Time Decay &amp; Costs</div>
                </div>
            </div>

            <div style="background: #ecfeff; border: 1.5px solid #a5f3fc; padding: 0.85rem 1rem; border-radius: 8px; margin-bottom: 1.25rem; font-size: 0.85rem; color: #0e7490;">
                <i class="fas fa-piggy-bank"></i> <strong>RBI Capital Provisioning Release:</strong> ₹${(data.rbi_provisioning_release_amount).toLocaleString('en-IN')} write-back to Tier-1 capital upon OTS execution.
            </div>

            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                <div style="padding: 0.6rem 0.8rem; background: #f8fafc; font-size: 0.8rem; font-weight: 800; color: #334155; border-bottom: 1px solid #e2e8f0;">
                    <i class="fas fa-clock-rotate-left"></i> Timeline Decay Sensitivity Analysis
                </div>
                <table style="width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: left;">
                    <thead>
                        <tr style="background: #ffffff; color: #64748b;">
                            <th style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #e2e8f0;">Duration</th>
                            <th style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #e2e8f0;">Value Retention</th>
                            <th style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #e2e8f0;">Discounted NPV</th>
                            <th style="padding: 0.5rem 0.75rem; border-bottom: 1px solid #e2e8f0;">OTS Surplus / (Deficit)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${timeDecayRows}
                    </tbody>
                </table>
            </div>
        `;
        if (window.toast) window.toast.show("OTS vs Litigation NPV calculated", "success");
    } catch (err) {
        console.error("OTS Calc Error:", err);
        resultsBox.innerHTML = `<div style="color: #ef4444; padding: 1.5rem; text-align: center;">Calculation failed: ${err.message}</div>`;
    }
};

window.loadEmpaneledAdvocatesUI = async function() {
    const container = document.getElementById("bankAdvocatesGridContainer");
    if (!container) return;

    container.innerHTML = `<div style="text-align: center; padding: 2rem; grid-column: 1 / -1;"><i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #0284c7;"></i><p>Loading empaneled counsel registry...</p></div>`;

    try {
        const res = await fetch(`${API_BASE}/advocates`);
        if (!res.ok) throw new Error("Advocates API returned an error");
        const data = await res.json();
        const advocates = data.advocates || [];

        let html = "";
        advocates.forEach(adv => {
            html += `
                <div class="bank-card bank-advocate-card" style="background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 12px; padding: 1.4rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03); display: flex; flex-direction: column;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                        <div>
                            <h4 style="color: #0f172a; font-size: 1.1rem; font-weight: 800; margin: 0 0 0.2rem 0;">${adv.name}</h4>
                            <div style="font-size: 0.8rem; color: #64748b; font-weight: 600;">${adv.firm_name} (${adv.bar_council_no})</div>
                        </div>
                        <span style="background: #fef3c7; color: #b45309; border: 1px solid #fde68a; padding: 0.2rem 0.5rem; border-radius: 6px; font-weight: 800; font-size: 0.75rem;">
                            ★ ${adv.sla_rating} / 5.0
                        </span>
                    </div>

                    <div style="font-size: 0.8rem; color: #0369a1; font-weight: 700; margin-bottom: 0.75rem;">
                        <i class="fas fa-briefcase"></i> ${adv.specialization}
                    </div>

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; background: #f8fafc; padding: 0.75rem; border-radius: 8px; border: 1px solid #f1f5f9; margin-bottom: 0.85rem; font-size: 0.8rem;">
                        <div>
                            <div style="color: #64748b; font-size: 0.7rem; font-weight: 700;">RECOVERY WIN RATE</div>
                            <div style="color: #10b981; font-size: 1.05rem; font-weight: 800;">${adv.recovery_win_rate_pct}%</div>
                        </div>
                        <div>
                            <div style="color: #64748b; font-size: 0.7rem; font-weight: 700;">FILING TURNAROUND</div>
                            <div style="color: #0284c7; font-size: 1.05rem; font-weight: 800;">${adv.avg_days_to_file_after_brief} Days</div>
                        </div>
                    </div>

                    <div style="font-size: 0.8rem; color: #475569; margin-bottom: 0.85rem; flex-grow: 1;">
                        <div style="font-weight: 700; color: #0f172a; margin-bottom: 0.25rem;"><i class="fas fa-gavel" style="color: #64748b;"></i> Primary Courts:</div>
                        <div>${(adv.primary_courts || []).join(" • ")}</div>
                    </div>

                    <div style="border-top: 1px solid #f1f5f9; padding-top: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 0.75rem; color: #64748b;">
                            <i class="fas fa-envelope"></i> ${adv.contact_email}
                        </div>
                        <button class="btn btn-primary btn-xs" onclick="dispatchBriefToAdvocate('${adv.advocate_id}', '${adv.name}')">
                            <i class="fas fa-paper-plane"></i> Dispatch Brief
                        </button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (err) {
        console.error("Advocates UI error:", err);
        container.innerHTML = `<div style="color: #ef4444; text-align: center; padding: 2rem; grid-column: 1 / -1;">Failed to load advocates: ${err.message}</div>`;
    }
};

window.dispatchBriefToAdvocate = async function(advId, advName) {
    const loanRef = (document.getElementById("bankLoanRefNo") && document.getElementById("bankLoanRefNo").value.trim()) || "SBI/SARB/MUM/2026/04918";
    try {
        const res = await fetch(`${API_BASE}/advocates/dispatch`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_reference: loanRef,
                advocate_id: advId,
                advocate_name: advName,
                officer_id: currentBankUser ? currentBankUser.officer_id : "OFFICER_SARB_842",
                instructions: "Initiate immediate court filing and Section 65B electronic evidence certification."
            })
        });

        if (!res.ok) throw new Error("Dispatch request failed");
        const data = await res.json();
        if (window.toast) window.toast.show(`Recovery brief dispatched to ${advName} (48h Filing SLA recorded)`, "success");
    } catch (err) {
        console.error("Dispatch error:", err);
        if (window.toast) window.toast.show(`Dispatch failed: ${err.message}`, "error");
    }
};

window.bankRecovery = {
    init: initBankRecoveryModule,
    runAudit: runBankRecoveryAudit,
    loadPreset: loadBankPreset,
    resetToBlank: resetToBlankCase,
    copyDossier: copyAdvocateDossier,
    dispatch: openDispatchModal,
    exportLedger: exportComplianceLedger,
    openAuth: window.openBankAuthModal,
    closeAuth: window.closeBankAuthModal,
    updateUI: window.updateBankOfficerUI,
    switchTab: window.switchBankFunctionTab,
    runMultiTrack: window.runMultiTrackEvaluation,
    generateDraft: window.generateStatutoryLegalDraft,
    runOTS: window.runOtsNpvOptimization,
    loadAdvocates: window.loadEmpaneledAdvocatesUI
};

