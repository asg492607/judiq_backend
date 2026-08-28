/**
 * JudiQ AI - Opposing Counsel Intelligence UI Controller
 * Tracks opposing defense counsel strategies, win/loss rates, judge track records,
 * and community crowdsourced peer observations.
 */

window.loadOpposingCounselDirectory = async function(jurisdiction = "") {
    const listContainer = document.getElementById("opposingCounselList");
    if (!listContainer) return;

    listContainer.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #0284c7;"></i>
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.5rem;">Loading Opposing Counsel Intelligence Dossiers...</p>
        </div>
    `;

    try {
        const url = `${API_BASE}/api/v1/intel/counsel${jurisdiction ? `?jurisdiction=${encodeURIComponent(jurisdiction)}` : ''}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to load counsel directory");
        const data = await res.json();
        window.renderOpposingCounselCards(data.counsel || [], listContainer);
    } catch (err) {
        console.error("Counsel intel error:", err);
        listContainer.innerHTML = `<div style="color: #ef4444; padding: 1.5rem; text-align: center;">Error loading counsel intel: ${err.message}</div>`;
    }
};

window.renderOpposingCounselCards = function(counselList, container) {
    if (!container) return;

    if (counselList.length === 0) {
        container.innerHTML = `<div style="color: #64748b; text-align: center; padding: 2rem;">No opposing counsel found for the selected jurisdiction.</div>`;
        return;
    }

    container.innerHTML = counselList.map(c => {
        const topTactics = (c.signature_defense_strategies || []).slice(0, 2).map(s => `
            <li style="margin-bottom: 0.25rem; font-size: 0.78rem; color: #334155;">
                <strong style="color: #0369a1;">${s.strategy_name}</strong> (${s.frequency_percentage}% frequency)
            </li>
        `).join("");

        return `
            <div class="bank-card" style="padding: 1.25rem; border-radius: 8px; border: 1.5px solid #cbd5e1; background: #ffffff; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
                    <div>
                        <h4 style="margin: 0; font-size: 1rem; font-weight: 800; color: #0f172a;">${c.name}</h4>
                        <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.2rem;">
                            Bar ID: <strong>${c.bar_council_id}</strong> • ${c.primary_jurisdiction}
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: ${c.defense_win_rate >= 60 ? '#fee2e2' : '#fef3c7'}; color: ${c.defense_win_rate >= 60 ? '#b91c1c' : '#b45309'}; font-size: 0.75rem; font-weight: 800; padding: 0.25rem 0.6rem; border-radius: 9999px;">
                            ${c.defense_win_rate}% Defense Win Rate
                        </span>
                        <div style="font-size: 0.72rem; color: #64748b; margin-top: 0.2rem;">${c.total_cases_tracked} Tracked Cases</div>
                    </div>
                </div>

                <div style="background: #f8fafc; padding: 0.75rem; border-radius: 6px; margin-bottom: 0.75rem; border: 1px solid #e2e8f0;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #475569; margin-bottom: 0.35rem;"><i class="fas fa-chess-knight"></i> Signature Defense Tactics:</div>
                    <ul style="margin: 0; padding-left: 1.1rem; line-height: 1.4;">
                        ${topTactics}
                    </ul>
                </div>

                <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                    <button class="btn btn-sm btn-outline" onclick="analyzeOpposingCounselMatchup('${c.counsel_id}')" style="font-size: 0.78rem;">
                        <i class="fas fa-crosshairs"></i> Analyze Matchup
                    </button>
                </div>
            </div>
        `;
    }).join("");
};

window.analyzeOpposingCounselMatchup = async function(counselId) {
    const resultBox = document.getElementById("counselMatchupResultBox");
    if (!resultBox) return;

    resultBox.innerHTML = `
        <div style="text-align: center; padding: 2rem;">
            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #0284c7;"></i>
            <p style="color: #64748b; font-size: 0.85rem; margin-top: 0.5rem;">Simulating Tactical Matchup...</p>
        </div>
    `;

    try {
        const res = await fetch(`${API_BASE}/api/v1/intel/counsel/analyze-matchup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                counsel_id_or_name: counselId,
                presiding_judge_or_court: "Magistrate Court (Commercial)",
                dispute_type: "SECTION_138"
            })
        });

        if (!res.ok) throw new Error("Matchup evaluation failed");
        const matchup = await res.json();
        window.renderMatchupResultUI(matchup, resultBox);
    } catch (err) {
        console.error("Matchup error:", err);
        resultBox.innerHTML = `<div style="color: #ef4444; padding: 1.5rem; text-align: center;">Matchup analysis error: ${err.message}</div>`;
    }
};

window.renderMatchupResultUI = function(matchup, container) {
    if (!container || !matchup) return;

    const threatColors = {
        SEVERE: { bg: "#fee2e2", text: "#b91c1c", badge: "THREAT: SEVERE" },
        HIGH: { bg: "#ffedd5", text: "#c2410c", badge: "THREAT: HIGH" },
        MODERATE: { bg: "#fef9c3", text: "#a16207", badge: "THREAT: MODERATE" },
        LOW: { bg: "#dcfce7", text: "#15803d", badge: "THREAT: MANAGEABLE" }
    };
    const tStyle = threatColors[matchup.threat_level] || threatColors.HIGH;

    const roadmapHtml = (matchup.tactical_road_map || []).map(r => `
        <li style="margin-bottom: 0.4rem; font-size: 0.82rem; color: #1e293b; line-height: 1.4;">${r}</li>
    `).join("");

    const precedentsHtml = (matchup.recommended_precedents_to_cite || []).map(p => `
        <li style="margin-bottom: 0.35rem; font-size: 0.8rem; color: #0369a1; font-style: italic;">${p}</li>
    `).join("");

    container.innerHTML = `
        <div style="background: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 1.5rem; margin-top: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
                <div>
                    <h3 style="margin: 0; font-size: 1.1rem; font-weight: 900; color: #0f172a;">
                        Tactical Matchup: ${matchup.counsel_profile.name}
                    </h3>
                    <div style="font-size: 0.78rem; color: #64748b;">${matchup.counsel_profile.primary_jurisdiction}</div>
                </div>
                <span style="background: ${tStyle.bg}; color: ${tStyle.text}; font-size: 0.8rem; font-weight: 800; padding: 0.35rem 0.8rem; border-radius: 9999px;">
                    ${tStyle.badge}
                </span>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                <h5 style="margin: 0 0 0.4rem 0; font-size: 0.85rem; font-weight: 800; color: #334155;"><i class="fas fa-shield-virus"></i> Predicted Opponent Defense Strategy:</h5>
                <ul style="margin: 0; padding-left: 1.25rem; font-size: 0.82rem; color: #475569; line-height: 1.4;">
                    ${matchup.predicted_top_defenses.map(d => `<li>${d}</li>`).join("")}
                </ul>
            </div>

            <div style="background: #f0fdf4; border: 1.5px solid #bbf7d0; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                <h5 style="margin: 0 0 0.5rem 0; font-size: 0.85rem; font-weight: 800; color: #166534;"><i class="fas fa-road"></i> Recommended Prosecution Tactical Roadmap:</h5>
                <ul style="margin: 0; padding-left: 1.25rem;">
                    ${roadmapHtml}
                </ul>
            </div>

            <div style="background: #f0f9ff; border: 1px solid #bae6fd; padding: 1rem; border-radius: 6px;">
                <h5 style="margin: 0 0 0.4rem 0; font-size: 0.85rem; font-weight: 800; color: #0369a1;"><i class="fas fa-book-bookmark"></i> Precedents to Pre-empt Defense Tactics:</h5>
                <ul style="margin: 0; padding-left: 1.25rem;">
                    ${precedentsHtml}
                </ul>
            </div>
        </div>
    `;
};

window.submitPeerCounselIntel = async function(e) {
    if (e) e.preventDefault();
    const name = document.getElementById("contribCounselName") ? document.getElementById("contribCounselName").value.trim() : "";
    const court = document.getElementById("contribCourt") ? document.getElementById("contribCourt").value.trim() : "";
    const strategy = document.getElementById("contribStrategy") ? document.getElementById("contribStrategy").value.trim() : "";
    const precedent = document.getElementById("contribPrecedent") ? document.getElementById("contribPrecedent").value.trim() : "";
    const outcome = document.getElementById("contribOutcome") ? document.getElementById("contribOutcome").value : "SETTLED";

    if (!name || !strategy) {
        if (window.toast) window.toast.show("Please enter advocate name and observed defense strategy", "warning");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/v1/intel/counsel/contribute`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                counsel_name: name,
                court_jurisdiction: court || "District Court",
                defense_strategy_observed: strategy,
                precedent_used: precedent || "Section 138 Case Law",
                case_outcome: outcome,
                contributor_designation: "Practicing Advocate"
            })
        });

        const data = await res.json();
        if (window.toast) window.toast.show(data.message || "Thank you. Intel queued for verification.", "success");
        if (typeof window.closeModal === 'function') window.closeModal();
    } catch (err) {
        console.error("Contribution error:", err);
        if (window.toast) window.toast.show(`Submission failed: ${err.message}`, "error");
    }
};
