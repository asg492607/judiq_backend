/**
 * JudiQ AI - Statutory Compliance Auditor UI Controller
 * Systematically audits Section 138 & banking recovery case facts against statutory rules.
 * Renders structured gap cards, authoritative precedents, remedies, and action priorities.
 */

window.performComplianceAudit = async function(caseData) {
    const auditContainer = document.getElementById("complianceAuditResults") || document.getElementById("bankRecoveryAuditResults");
    if (!auditContainer) return;

    auditContainer.innerHTML = `
        <div style="text-align: center; padding: 2.5rem;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #0284c7; margin-bottom: 0.75rem;"></i>
            <p style="color: #64748b; font-weight: 600;">Executing 12-Pillar Statutory Compliance Audit...</p>
        </div>
    `;

    try {
        const payload = caseData || {
            case_id: (document.getElementById("bankLoanRefNo") && document.getElementById("bankLoanRefNo").value) || "CASE-2026-AUDIT",
            borrower_name: (document.getElementById("bankBorrowerName") && document.getElementById("bankBorrowerName").value) || "Debtor Entity",
            amount: parseFloat((document.getElementById("bankDefaultAmount") && document.getElementById("bankDefaultAmount").value) || 1500000),
            cheque_date: (document.getElementById("bankChequeDate") && document.getElementById("bankChequeDate").value) || "2024-01-10",
            dishonor_date: (document.getElementById("bankDishonourDate") && document.getElementById("bankDishonourDate").value) || "2024-01-18",
            notice_sent_date: (document.getElementById("bankNoticeSentDate") && document.getElementById("bankNoticeSentDate").value) || "2024-01-30",
            notice_received_date: (document.getElementById("bankNoticeDeliveryDate") && document.getElementById("bankNoticeDeliveryDate").value) || "2024-02-04",
            complaint_filed_date: (document.getElementById("bankComplaintFilingDate") && document.getElementById("bankComplaintFilingDate").value) || "2024-02-28",
            defendant_is_company: document.getElementById("bankIsCorporate") ? document.getElementById("bankIsCorporate").checked : true,
            company_arraigned: document.getElementById("bankCompanyArraigned") ? document.getElementById("bankCompanyArraigned").checked : true,
            director_averments: (document.getElementById("bankDirectorAverments") && document.getElementById("bankDirectorAverments").value) || "SPECIFIC",
            s65b_certificate: document.getElementById("bankHas65b") ? document.getElementById("bankHas65b").checked : false,
            has_postal_tracking: document.getElementById("bankHasPostReceipt") ? document.getElementById("bankHasPostReceipt").checked : true,
            is_secured: document.getElementById("bankIsSecured") ? document.getElementById("bankIsSecured").checked : true,
            is_agricultural_land: document.getElementById("bankAssetType") ? document.getElementById("bankAssetType").value === 'AGRICULTURAL' : false,
            cersai_registered: document.getElementById("bankCersaiCheck") ? document.getElementById("bankCersaiCheck").checked : true
        };

        const res = await fetch(`${API_BASE}/api/v1/analyze/section138`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `HTTP ${res.status}`);
        }

        const report = await res.json();
        window.renderComplianceReportUI(report, auditContainer);

        if (window.toast) {
            window.toast.show(`Compliance Audit Complete: ${report.compliance_rating}`, report.fatal_gaps > 0 ? "error" : "success");
        }
    } catch (err) {
        console.error("Compliance audit error:", err);
        auditContainer.innerHTML = `
            <div style="background: #fef2f2; border: 1.5px solid #fecaca; padding: 1.5rem; border-radius: 8px; color: #b91c1c;">
                <h4 style="margin: 0 0 0.5rem 0;"><i class="fas fa-circle-exclamation"></i> Audit Execution Failed</h4>
                <p style="margin: 0;">${err.message}</p>
            </div>
        `;
    }
};

window.renderComplianceReportUI = function(report, container) {
    if (!container || !report) return;

    const severityConfig = {
        FATAL: { bg: "#fef2f2", border: "#ef4444", text: "#991b1b", badge: "#dc2626", icon: "fa-ban" },
        CURABLE: { bg: "#fffbeb", border: "#f59e0b", text: "#92400e", badge: "#d97706", icon: "fa-wrench" },
        STRATEGIC: { bg: "#fefce8", border: "#eab308", text: "#854d0e", badge: "#ca8a04", icon: "fa-shield-halved" },
        WARNING: { bg: "#fff7ed", border: "#f97316", text: "#9a3412", badge: "#ea580c", icon: "fa-triangle-exclamation" },
        INFO: { bg: "#f0fdf4", border: "#22c55e", text: "#166534", badge: "#16a34a", icon: "fa-circle-info" }
    };

    const ratingColors = {
        HIGH_COMPLIANCE: { bg: "#dcfce7", text: "#15803d", label: "HIGH STATUTORY COMPLIANCE" },
        CURABLE_GAPS: { bg: "#fef3c7", text: "#b45309", label: "CURABLE PROCEDURAL GAPS DETECTED" },
        CRITICAL_STATUTORY_DEFECTS: { bg: "#fee2e2", text: "#b91c1c", label: "CRITICAL STATUTORY DEFECTS (DO NOT FILE)" }
    };

    const currentRating = ratingColors[report.compliance_rating] || ratingColors.CURABLE_GAPS;

    let gapCardsHtml = report.gaps.map(gap => {
        const style = severityConfig[gap.severity] || severityConfig.INFO;
        let stepsHtml = "";
        if (gap.steps && gap.steps.length > 0) {
            stepsHtml = `
                <div style="margin-top: 0.75rem; background: rgba(255,255,255,0.7); padding: 0.75rem; border-radius: 6px; border: 1px solid rgba(0,0,0,0.06);">
                    <div style="font-size: 0.78rem; font-weight: 700; color: ${style.text}; margin-bottom: 0.35rem;"><i class="fas fa-list-ol"></i> Step-by-Step Remediation:</div>
                    <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.78rem; color: #334155; line-height: 1.4;">
                        ${gap.steps.map(s => `<li>${s}</li>`).join("")}
                    </ul>
                </div>
            `;
        }

        return `
            <div style="background: ${style.bg}; border-left: 5px solid ${style.border}; border-top: 1px solid ${style.border}40; border-right: 1px solid ${style.border}40; border-bottom: 1px solid ${style.border}40; padding: 1.25rem; border-radius: 8px; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
                    <span style="background: ${style.badge}; color: #ffffff; font-size: 0.72rem; font-weight: 800; padding: 0.2rem 0.6rem; border-radius: 9999px; letter-spacing: 0.05em; display: inline-flex; align-items: center; gap: 0.35rem;">
                        <i class="fas ${style.icon}"></i> ${gap.severity} DEFECT
                    </span>
                    <span style="font-size: 0.78rem; font-weight: 700; color: #475569; font-family: monospace;">${gap.rule_id}</span>
                </div>
                
                <h4 style="margin: 0 0 0.4rem 0; font-size: 0.95rem; font-weight: 800; color: ${style.text};">
                    ${gap.statute}
                </h4>
                
                <div style="font-size: 0.82rem; color: #1e293b; margin-bottom: 0.4rem;">
                    <strong>Authoritative Precedent:</strong> <span style="color: #0369a1; font-style: italic;">${gap.precedent}</span>
                </div>
                
                <div style="font-size: 0.82rem; color: #334155; margin-bottom: 0.4rem;">
                    <strong>Factual Finding:</strong> ${gap.finding}
                </div>
                
                <div style="font-size: 0.82rem; color: #b91c1c; margin-bottom: 0.5rem;">
                    <strong>Legal Impact:</strong> ${gap.impact}
                </div>
                
                <div style="background: #ffffff; padding: 0.75rem; border-radius: 6px; border: 1px solid #cbd5e1; font-size: 0.82rem; color: #0f172a;">
                    <strong style="color: #0284c7;"><i class="fas fa-check-circle"></i> Recommended Legal Remedy:</strong> ${gap.remedy}
                </div>
                
                ${stepsHtml}
            </div>
        `;
    }).join("");

    let nextStepsHtml = (report.next_steps || []).map((step, idx) => `
        <li style="display: flex; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.5rem; font-size: 0.82rem; color: #1e293b;">
            <input type="checkbox" id="auditStep_${idx}" style="margin-top: 0.2rem; cursor: pointer;">
            <label for="auditStep_${idx}" style="cursor: pointer; line-height: 1.4;">${step}</label>
        </li>
    `).join("");

    container.innerHTML = `
        <div style="margin-bottom: 1.5rem;">
            <!-- Header Score & Rating Badge -->
            <div style="display: flex; align-items: center; justify-content: space-between; background: #f8fafc; border: 1.5px solid #e2e8f0; padding: 1.25rem; border-radius: 10px; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Procedural Compliance Index</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #0f172a;">
                        ${report.compliance_score}<span style="font-size: 1rem; color: #94a3b8;">/100</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="background: ${currentRating.bg}; color: ${currentRating.text}; font-size: 0.82rem; font-weight: 800; padding: 0.4rem 0.9rem; border-radius: 9999px; display: inline-block;">
                        ${currentRating.label}
                    </span>
                    <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.35rem;">
                        ${report.fatal_gaps} Fatal • ${report.curable_gaps} Curable • ${report.warnings} Warnings
                    </div>
                </div>
            </div>

            <!-- Executive Recommendation Box -->
            <div style="background: #f0f9ff; border: 1.5px solid #bae6fd; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <h4 style="margin: 0 0 0.5rem 0; font-size: 0.9rem; font-weight: 800; color: #0369a1; display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-gavel"></i> Strategic Compliance Recommendation:
                </h4>
                <p style="margin: 0; font-size: 0.84rem; color: #0c4a6e; line-height: 1.5;">${report.recommendation}</p>
            </div>

            <!-- Gap Cards Stream -->
            <h4 style="font-size: 0.95rem; font-weight: 800; color: #1e293b; margin: 0 0 1rem 0;">
                <i class="fas fa-microscope" style="color: #0284c7;"></i> Detailed Statutory Gap Analysis (${report.total_gaps} Findings)
            </h4>
            
            ${gapCardsHtml || '<div style="color: #10b981; font-weight: 600; padding: 1.5rem; text-align: center;">No statutory gaps identified. Case conforms to all tested milestones.</div>'}

            <!-- Prioritised Action Checklist -->
            <div style="margin-top: 1.5rem; background: #ffffff; border: 1.5px solid #cbd5e1; padding: 1.25rem; border-radius: 8px;">
                <h4 style="margin: 0 0 0.75rem 0; font-size: 0.9rem; font-weight: 800; color: #0f172a; display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-list-check" style="color: #10b981;"></i> Pre-Filing Prioritized Action Checklist:
                </h4>
                <ul style="margin: 0; padding-left: 0.25rem; list-style: none;">
                    ${nextStepsHtml}
                </ul>
            </div>
        </div>
    `;
};
