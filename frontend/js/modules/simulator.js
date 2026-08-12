/**
 * JudiQ AI — Interactive Cross-Examination Risk Simulator & Legal Strategy Workbench
 * Dynamic courtroom simulation sandbox for testing defense strategies and analyzing survivability in real-time.
 */

export class JudiQStrategySimulator {
    constructor() {
        this.currentPreset = 's138_signature';
        this.init();
    }

    init() {
        window.selectSimulatorPreset = (presetKey) => this.loadPreset(presetKey);
        window.recalculateSimulatorScore = () => this.calculateScore();
    }

    loadPreset(presetKey) {
        this.currentPreset = presetKey;
        const presets = {
            s138_signature: {
                title: "Cheque Bounce (Sec 138) — Disputed Signature & Stop Payment",
                domain: "NI Act Section 138",
                noticeDelay: 12,
                debtExisted: true,
                securityCheque: false,
                signatureDisputed: true,
                evidence65B: true,
                baseScore: 68,
                attackVector: "Opposing counsel will demand forensic handwriting expert opinion under Sec. 45 Evidence Act and call the bank manager to verify specimen cards.",
                counterStrategy: "File application for comparison of signatures by State Forensic Science Laboratory; establish lack of authorization register.",
                ratio: "Linny D’Souza v. Vijay Kumar (2019) — Difference in signature requires strict proof of drawing under Sec. 138."
            },
            s138_notice_delay: {
                title: "Cheque Bounce (Sec 138) — Notice Delay > 30 Days",
                domain: "NI Act Section 138",
                noticeDelay: 42,
                debtExisted: true,
                securityCheque: false,
                signatureDisputed: false,
                evidence65B: true,
                baseScore: 25,
                attackVector: "Fatal limitation defect! Demand notice dispatched on Day 42, exceeding statutory 30-day window under Sec. 138(b).",
                counterStrategy: "Move application under Sec. 142(1)(b) proviso seeking condonation of delay with affidavit explaining sufficient cause.",
                ratio: "Prem Chand Vijay Kumar v. Yashpal Singh (2005) — Cause of action arises only once statutory notice condition is met strictly."
            },
            sarfaesi_npa: {
                title: "SARFAESI DRT Action — Defective Sec 13(2) Demand Notice",
                domain: "SARFAESI Act 2002",
                noticeDelay: 15,
                debtExisted: true,
                securityCheque: false,
                signatureDisputed: false,
                evidence65B: false,
                baseScore: 55,
                attackVector: "Bank failed to issue itemized breakup of principal & interest in Sec 13(2) notice and ignored borrower's Sec 13(3A) representation.",
                counterStrategy: "File Sec. 17 Appeal before DRT challenging symbolic possession under Sec 13(4) on grounds of non-compliance with statutory 3A reply.",
                ratio: "Mardia Chemicals Ltd. v. Union of India (2004) — Communication of reasons for rejecting representation is mandatory."
            },
            cyber_fraud_65b: {
                title: "Cyber Fraud & Commercial Breach — Missing 65B Certificate",
                domain: "Criminal Law / IT Act",
                noticeDelay: 0,
                debtExisted: false,
                securityCheque: false,
                signatureDisputed: false,
                evidence65B: false,
                baseScore: 35,
                attackVector: "WhatsApp chats, email printouts, and server logs presented without mandatory Section 65B Electronic Evidence Certificate.",
                counterStrategy: "Raise threshold objection during evidence stage against admissibility of secondary electronic evidence.",
                ratio: "Anvar P.V. v. P.K. Basheer (2014) & Arjun Panditrao Khotkar (2020) — S.65B Certificate is an indispensable condition precedent."
            }
        };

        const config = presets[presetKey] || presets.s138_signature;
        
        // Update DOM elements if present
        const titleEl = document.getElementById('simTitle');
        const attackEl = document.getElementById('simAttackVector');
        const counterEl = document.getElementById('simCounterStrategy');
        const ratioEl = document.getElementById('simRatio');
        const domainBadge = document.getElementById('simDomainBadge');

        if (titleEl) titleEl.textContent = config.title;
        if (attackEl) attackEl.textContent = config.attackVector;
        if (counterEl) counterEl.textContent = config.counterStrategy;
        if (ratioEl) ratioEl.textContent = config.ratio;
        if (domainBadge) domainBadge.textContent = config.domain;

        // Update form toggles
        const noticeInput = document.getElementById('simNoticeDelayInput');
        const sigCheck = document.getElementById('simSignatureCheck');
        const secCheck = document.getElementById('simSecurityCheck');
        const e65bCheck = document.getElementById('sim65BCheck');

        if (noticeInput) noticeInput.value = config.noticeDelay;
        if (sigCheck) sigCheck.checked = config.signatureDisputed;
        if (secCheck) secCheck.checked = config.securityCheque;
        if (e65bCheck) e65bCheck.checked = config.evidence65B;

        // Highlight active preset button
        document.querySelectorAll('.sim-preset-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.preset === presetKey);
        });

        this.calculateScore();
    }

    calculateScore() {
        const noticeDelay = parseInt(document.getElementById('simNoticeDelayInput')?.value || '15', 10);
        const sigDisputed = document.getElementById('simSignatureCheck')?.checked || false;
        const securityCheque = document.getElementById('simSecurityCheck')?.checked || false;
        const e65bPresent = document.getElementById('sim65BCheck')?.checked || false;

        let score = 90;

        if (noticeDelay > 30) {
            score -= 55; // Fatal limitation defect
        } else if (noticeDelay > 25) {
            score -= 10;
        }

        if (sigDisputed) score -= 20;
        if (securityCheque) score -= 15;
        if (!e65bPresent) score -= 25;

        score = Math.max(10, Math.min(99, score));

        // Update Score Gauge
        const scoreMeter = document.getElementById('simScoreMeter');
        const scoreVal = document.getElementById('simScoreValue');
        const scoreStatus = document.getElementById('simScoreStatus');

        if (scoreMeter) {
            scoreMeter.style.width = `${score}%`;
            if (score >= 75) {
                scoreMeter.style.background = 'linear-gradient(90deg, #10b981, #059669)';
            } else if (score >= 50) {
                scoreMeter.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
            } else {
                scoreMeter.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
            }
        }

        if (scoreVal) scoreVal.textContent = `${score}%`;
        if (scoreStatus) {
            if (score >= 75) {
                scoreStatus.textContent = "High Courtroom Survivability";
                scoreStatus.className = "sim-score-badge safe";
            } else if (score >= 50) {
                scoreStatus.textContent = "Moderate Risk — Defense Counter Required";
                scoreStatus.className = "sim-score-badge warning";
            } else {
                scoreStatus.textContent = "Fatal Procedural Vulnerability Detected";
                scoreStatus.className = "sim-score-badge danger";
            }
        }
    }
}
