/**
 * JudiQ Enterprise Features UI Controller
 * Integrates Executive Analytics Dashboard, Statutory Deadline Calendar Sync,
 * and Opposing Defense Counsel Matchup Simulation.
 */

window.loadAnalyticsDashboardUI = async function() {
    const container = document.getElementById("bankAnalyticsContainer");
    if (!container) return;

    container.innerHTML = `
        <div style="text-align: center; padding: 3rem; grid-column: 1 / -1;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2.5rem; color: #0284c7; margin-bottom: 1rem;"></i>
            <h4 style="color: #1e293b; font-weight: 700;">Loading Executive Portfolio Analytics...</h4>
            <p style="color: #64748b;">Aggregating 5-tier portfolio distributions, compliance trends, and court benchmarks.</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/api/v1/analytics/executive`);
        if (!res.ok) throw new Error("Failed to load analytics");
        const data = await res.json();
        window.renderAnalyticsDashboard(data, container);
    } catch (err) {
        console.error("Analytics load error:", err);
        container.innerHTML = `
            <div style="background: #fef2f2; border: 1.5px solid #fecaca; padding: 1.5rem; border-radius: 8px; color: #b91c1c;">
                <h4><i class="fas fa-circle-exclamation"></i> Analytics Error</h4>
                <p>${err.message}</p>
            </div>
        `;
    }
};

window.renderAnalyticsDashboard = function(data, container) {
    if (!container || !data) return;

    const tierColors = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"];

    const tierRowsHtml = (data.portfolio_tier_breakdown || []).map((t, idx) => `
        <div style="margin-bottom: 1.25rem; background: #f8fafc; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; flex-wrap: wrap; gap: 0.5rem;">
                <div style="font-weight: 800; font-size: 0.9rem; color: #0f172a;">${t.tier_name}</div>
                <div style="font-size: 0.82rem; font-weight: 700; color: ${tierColors[idx % tierColors.length]};">
                    ${t.count} Cases (${t.percentage}%) • ₹${(t.aggregate_exposure / 10000000).toFixed(2)} Cr Exposure
                </div>
            </div>
            <div style="width: 100%; height: 8px; background: #e2e8f0; border-radius: 9999px; overflow: hidden; margin-bottom: 0.5rem;">
                <div style="width: ${t.percentage}%; height: 100%; background: ${tierColors[idx % tierColors.length]}; border-radius: 9999px;"></div>
            </div>
            <div style="font-size: 0.78rem; color: #475569;">
                <strong style="color: #0284c7;"><i class="fas fa-arrow-right"></i> Recommended Action:</strong> ${t.recommended_primary_action}
            </div>
        </div>
    `).join("");

    const judgeRowsHtml = (data.judge_benchmark_patterns || []).map(j => `
        <div style="background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
                <h5 style="margin: 0; font-size: 0.95rem; font-weight: 800; color: #0f172a;">${j.court_jurisdiction}</h5>
                <span style="background: #dcfce7; color: #15803d; font-size: 0.75rem; font-weight: 800; padding: 0.25rem 0.6rem; border-radius: 9999px;">
                    ${j.conviction_rate}% Conviction / Decreed
                </span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.5rem; margin-bottom: 0.75rem; font-size: 0.78rem; color: #64748b;">
                <div><strong>Tracked Matters:</strong> ${j.total_matters_tracked}</div>
                <div><strong>Settlement Rate:</strong> ${j.settlement_rate}%</div>
                <div><strong>Avg Trial Velocity:</strong> ${j.avg_trial_duration_months} Months</div>
            </div>
            <div style="background: #f0f9ff; padding: 0.6rem 0.75rem; border-radius: 6px; font-size: 0.78rem; color: #0369a1; border: 1px solid #bae6fd;">
                <strong>Procedural Focus:</strong> ${j.key_procedural_focus}
            </div>
        </div>
    `).join("");

    container.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1.5rem; width: 100%;">
            <!-- High-Level KPI Summary Cards -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;">
                <div class="bank-card" style="padding: 1.25rem; border-left: 4px solid #0284c7; background: #ffffff;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Total Cases Analyzed</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #0f172a; margin-top: 0.25rem;">${data.total_cases_analyzed}</div>
                    <div style="font-size: 0.75rem; color: #10b981; margin-top: 0.25rem;"><i class="fas fa-arrow-trend-up"></i> Active Recovery Portfolio</div>
                </div>
                <div class="bank-card" style="padding: 1.25rem; border-left: 4px solid #10b981; background: #ffffff;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Mean Compliance Score</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #0f172a; margin-top: 0.25rem;">${data.overall_mean_compliance_score}<span style="font-size: 1rem; color: #94a3b8;">/100</span></div>
                    <div style="font-size: 0.75rem; color: #10b981; margin-top: 0.25rem;"><i class="fas fa-shield-check"></i> High Courtroom Survivability</div>
                </div>
                <div class="bank-card" style="padding: 1.25rem; border-left: 4px solid #f59e0b; background: #ffffff;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Settlement Conversion</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #0f172a; margin-top: 0.25rem;">${data.overall_settlement_conversion_rate}%</div>
                    <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">OTS &amp; Mediation Resolution</div>
                </div>
                <div class="bank-card" style="padding: 1.25rem; border-left: 4px solid #8b5cf6; background: #ffffff;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Aggregate Debt Managed</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #0f172a; margin-top: 0.25rem;">₹${(data.total_aggregate_debt_value / 10000000).toFixed(1)} Cr</div>
                    <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.25rem;">Across 5 Recovery Tracks</div>
                </div>
            </div>

            <!-- Two Column: Portfolio Breakdown & Judge Patterns -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 1.5rem;">
                <div class="bank-panel">
                    <div class="bank-panel-header">
                        <h4><i class="fas fa-layer-group"></i> 5-Tier Portfolio Distribution</h4>
                        <span class="badge-subtle">Risk Tiers</span>
                    </div>
                    <div style="padding: 1.25rem;">
                        ${tierRowsHtml}
                    </div>
                </div>

                <div class="bank-panel">
                    <div class="bank-panel-header">
                        <h4><i class="fas fa-gavel"></i> Forum &amp; Court Benchmarks</h4>
                        <span class="badge-subtle">Empirical Data</span>
                    </div>
                    <div style="padding: 1.25rem;">
                        ${judgeRowsHtml}
                    </div>
                </div>
            </div>

            <!-- ROI Summary Box -->
            <div style="background: linear-gradient(135deg, #0c4a6e, #0369a1); color: #ffffff; padding: 1.5rem; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <h4 style="margin: 0 0 0.4rem 0; font-size: 1.1rem; font-weight: 900;"><i class="fas fa-bolt"></i> Institutional Efficiency Gain</h4>
                    <p style="margin: 0; font-size: 0.85rem; color: #bae6fd;">
                        Prevented <strong>${data.roi_summary.procedural_dismissals_prevented} procedural dismissals</strong> and saved <strong>${data.roi_summary.estimated_legal_hours_saved} legal drafting hours</strong>.
                    </p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 0.8rem; color: #7dd3fc; text-transform: uppercase; font-weight: 700;">Section 143A Cashflow Unlocked</div>
                    <div style="font-size: 1.6rem; font-weight: 900; color: #ffffff;">₹${(data.roi_summary.interim_cashflow_unlocked_s143a / 100000).toFixed(1)} Lakhs</div>
                </div>
            </div>
        </div>
    `;
};

window.loadDeadlinesCalendarUI = async function() {
    const container = document.getElementById("bankDeadlinesContainer");
    if (!container) return;

    const ref = (document.getElementById("bankLoanRefNo") && document.getElementById("bankLoanRefNo").value.trim()) || "CASE-2026-001";
    const borrower = (document.getElementById("bankBorrowerName") && document.getElementById("bankBorrowerName").value.trim()) || "Borrower Entity";
    const memoDate = (document.getElementById("bankDishonourDate") && document.getElementById("bankDishonourDate").value) || "2026-08-10";
    const noticeDate = (document.getElementById("bankDeliveryDate") && document.getElementById("bankDeliveryDate").value) || "2026-08-20";

    container.innerHTML = `
        <div style="text-align: center; padding: 3rem; grid-column: 1 / -1;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2.5rem; color: #0284c7; margin-bottom: 1rem;"></i>
            <h4 style="color: #1e293b; font-weight: 700;">Calculating Statutory Deadlines...</h4>
            <p style="color: #64748b;">Applying Section 138(b), Section 142, and Section 10 General Clauses Act court holiday rules.</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/api/v1/deadlines/calculate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                case_reference: ref,
                borrower_or_accused_name: borrower,
                dispute_type: "SECTION_138",
                dishonour_memo_date: memoDate,
                notice_received_date: noticeDate
            })
        });

        if (!res.ok) throw new Error("Failed to calculate deadlines");
        const report = await res.json();
        window.renderDeadlinesCalendar(report, container);
    } catch (err) {
        console.error("Deadline error:", err);
        container.innerHTML = `<div style="color: #ef4444; padding: 1.5rem; text-align: center;">Deadline Calculation Error: ${err.message}</div>`;
    }
};

window.renderDeadlinesCalendar = function(report, container) {
    if (!container || !report) return;

    const urgencyStyles = {
        CRITICAL_TODAY: { bg: "#fef2f2", border: "#ef4444", text: "#991b1b", badge: "CRITICAL: TODAY" },
        URGENT_7_DAYS: { bg: "#fff7ed", border: "#ea580c", text: "#9a3412", badge: "URGENT: DUE IN 7 DAYS" },
        UPCOMING_14_DAYS: { bg: "#fefce8", border: "#ca8a04", text: "#854d0e", badge: "UPCOMING: 14 DAYS" },
        SAFE: { bg: "#f0fdf4", border: "#16a34a", text: "#166534", badge: "WITHIN LIMITATION" },
        EXPIRED_NEEDS_CONDONATION: { bg: "#faf5ff", border: "#9333ea", text: "#6b21a8", badge: "EXPIRED (S.142 CONDONATION)" }
    };

    const cardsHtml = (report.deadlines || []).map(d => {
        const style = urgencyStyles[d.urgency_level] || urgencyStyles.SAFE;
        const remindersHtml = (d.smart_reminder_dates || []).map(r => `<span style="background: rgba(0,0,0,0.05); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.72rem; font-family: monospace;">${r}</span>`).join(" ");

        return `
            <div style="background: ${style.bg}; border-left: 5px solid ${style.border}; border-top: 1px solid ${style.border}40; border-right: 1px solid ${style.border}40; border-bottom: 1px solid ${style.border}40; padding: 1.25rem; border-radius: 8px; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
                    <div>
                        <h4 style="margin: 0; font-size: 1rem; font-weight: 800; color: ${style.text};">${d.title}</h4>
                        <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.2rem;">${d.statutory_basis}</div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: ${style.border}; color: #ffffff; font-size: 0.72rem; font-weight: 800; padding: 0.25rem 0.6rem; border-radius: 9999px;">
                            ${style.badge}
                        </span>
                        <div style="font-size: 0.85rem; font-weight: 900; color: #0f172a; margin-top: 0.25rem;">Due: ${d.due_date} (${d.days_remaining} days)</div>
                    </div>
                </div>

                <div style="background: #ffffff; padding: 0.75rem; border-radius: 6px; border: 1px solid #cbd5e1; margin-bottom: 0.75rem; font-size: 0.82rem; color: #1e293b;">
                    <strong style="color: #0284c7;"><i class="fas fa-circle-exclamation"></i> Mandatory Action:</strong> ${d.mandatory_action}
                </div>

                <div style="font-size: 0.78rem; color: #b91c1c; margin-bottom: 0.5rem;">
                    <strong>Consequence of Missing:</strong> ${d.consequence_of_missing}
                </div>

                <div style="font-size: 0.75rem; color: #475569; display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;">
                    <strong><i class="fas fa-bell"></i> Smart Alerts:</strong> ${remindersHtml}
                </div>
            </div>
        `;
    }).join("");

    container.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 1.25rem; width: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; background: #f8fafc; border: 1.5px solid #cbd5e1; padding: 1.25rem; border-radius: 8px; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <h3 style="margin: 0; font-size: 1.1rem; font-weight: 900; color: #0f172a;">
                        <i class="fas fa-calendar-check" style="color: #0284c7;"></i> Statutory Limitation &amp; Alert Schedule
                    </h3>
                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.2rem;">Case Ref: <strong>${report.case_reference}</strong> • Party: <strong>${report.borrower_name}</strong></div>
                </div>
                <a href="${API_BASE}${report.ical_export_url}" download="judiq_deadlines_${report.case_reference}.ics" class="btn btn-primary" style="font-size: 0.82rem; display: inline-flex; align-items: center; gap: 0.45rem;">
                    <i class="fas fa-calendar-plus"></i> Export to Google / Outlook Calendar (.ics)
                </a>
            </div>

            <div style="margin-top: 0.5rem;">
                ${cardsHtml || '<div style="color: #64748b; text-align: center; padding: 2rem;">No statutory deadlines calculated.</div>'}
            </div>
        </div>
    `;
};
