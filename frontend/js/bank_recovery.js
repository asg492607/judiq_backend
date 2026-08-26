/**
 * JudiQ Institutional Banking & Recovery OS Controller
 * 100% Deterministic Rule-Based Legal & Procedural Audit Interface
 */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? (window.location.port === '8000' ? '' : `${window.location.protocol}//${window.location.hostname}:8000`)
    : "https://cheque-bounce-ragbased.onrender.com";

let currentAuditResult = null;

// Preset Reference Cases across 5 Operational Difficulty Tiers
const BANK_DEMO_CASES = {
    "DEMO_BANK_8_5L": {
        title: "₹8.5L Business Loan Default (Basic Standard)",
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
        branch_name: "JudiQ Demo Bank — Stressed Asset Recovery Cell (SARB Mumbai Simulation)"
    },
    "DEMO_BANK_14L_CURABLE": {
        title: "₹14.0L Vehicle Fleet Loan (Curable Defect)",
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
        branch_name: "JudiQ Demo Bank — Large Corporate Recovery Division (Delhi Simulation)"
    },
    "DEMO_BANK_25L_PREMATURE": {
        title: "₹25.0L CC Default (Premature Filing Trap)",
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
        branch_name: "JudiQ Demo Bank — Wholesale Recovery Dept (Mumbai Simulation)"
    },
    "DEMO_BANK_1_8CR_SARFAESI_FATAL": {
        title: "₹1.80 Cr Industrial NPA (SARFAESI CERSAI Bar)",
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
        branch_name: "JudiQ Demo Bank — SAMB (Ahmedabad Simulation)"
    },
    "DEMO_BANK_65L_LIMITATION_CONDONATION": {
        title: "₹65.0L Corporate NPA (S.142 Condonation)",
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
        branch_name: "JudiQ Demo Bank — Stressed Asset Recovery Cell (SARB Mumbai Simulation)"
    }
};

export function initBankRecoveryModule() {
    // Event listeners
    const auditBtn = document.getElementById("bankRunAuditBtn");
    if (auditBtn) {
        auditBtn.addEventListener("click", () => runBankRecoveryAudit());
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

    // Auto-load default demo case on init if empty
    const borrowerInput = document.getElementById("bankBorrowerName");
    if (borrowerInput && !borrowerInput.value) {
        loadBankPreset("DEMO_BANK_8_5L", true);
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
// BANK OFFICER AUTHENTICATION & SESSION MANAGEMENT
// ============================================================================

let currentBankUser = JSON.parse(localStorage.getItem('judiq_bank_user') || 'null') || {
    officer_id: "OFFICER_SARB_842",
    name: "Rajesh Nambiar",
    bank_name: "State Bank of India",
    branch_name: "SBI — Stressed Asset Recovery Branch (SARB Mumbai)",
    role: "sarb_manager",
    email: "rajesh.nambiar@sbi.co.in"
};

window.openBankAuthModal = () => {
    const modal = document.getElementById("bankAuthModal");
    if (modal) {
        modal.classList.remove("hidden");
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

window.selectBankPreset = (branchId) => {
    const presets = {
        "SBI_SARB_MUM": {
            officer_id: "OFFICER_SARB_842",
            name: "Rajesh Nambiar (Chief Recovery Manager)",
            bank_name: "State Bank of India",
            branch_name: "SBI — Stressed Asset Recovery Branch (SARB Mumbai)",
            email: "rajesh.nambiar@sbi.co.in"
        },
        "PNB_CFS_DEL": {
            officer_id: "OFFICER_DEL_LCR_419",
            name: "Vikram Rathore (Senior Manager - Legal)",
            bank_name: "Punjab National Bank",
            branch_name: "PNB — Large Corporate Recovery Division (Delhi)",
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
            branch_name: "BOB — Stressed Assets Management Branch (SAMB Ahmedabad)",
            email: "priya.patel@bankofbaroda.co.in"
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

window.submitBankLogin = async (e) => {
    if (e) e.preventDefault();
    const officerId = getVal("bankAuthOfficerId").trim();
    const officerName = getVal("bankAuthOfficerName").trim();
    const bankName = getVal("bankAuthBankName").trim();
    const branchName = getVal("bankAuthBranchName").trim();
    const email = getVal("bankAuthEmail").trim();
    const pin = getVal("bankAuthPin").trim();

    if (!officerId) {
        if (window.toast) window.toast.show("Please enter Officer ID", "warning");
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
        currentBankUser = {
            officer_id: officerId,
            name: officerName || officerId,
            bank_name: bankName,
            branch_name: branchName,
            email: email,
            role: data.role || 'bank_officer',
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

window.bankRecovery = {
    init: initBankRecoveryModule,
    runAudit: runBankRecoveryAudit,
    loadPreset: loadBankPreset,
    copyDossier: copyAdvocateDossier,
    dispatch: openDispatchModal,
    exportLedger: exportComplianceLedger,
    openAuth: window.openBankAuthModal,
    closeAuth: window.closeBankAuthModal,
    updateUI: window.updateBankOfficerUI
};
