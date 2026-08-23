/**
 * JudiQ AI — Co-Counsel Floating Assistant Dock
 * Single Unified Interactive litigation assistant floating widget with quick prompt cards,
 * statutory citation lookup, and strategy brief generator.
 */

export class JudiQCoCounselDock {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.init();
    }

    init() {
        this.injectStyles();
        this.renderDockUI();
        this.bindEvents();
    }

    injectStyles() {
        if (document.getElementById('coCounselDockStyles')) return;
        const style = document.createElement('style');
        style.id = 'coCounselDockStyles';
        style.textContent = `
            .co-counsel-floating-btn {
                position: fixed;
                bottom: 1.5rem;
                right: 1.5rem;
                z-index: 9990;
                background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 50px;
                padding: 0.75rem 1.35rem;
                display: flex;
                align-items: center;
                gap: 0.65rem;
                box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.5), 0 0 15px rgba(6, 182, 212, 0.3);
                cursor: pointer;
                font-family: var(--font-family, 'Outfit', sans-serif);
                font-weight: 600;
                font-size: 0.92rem;
                transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease;
            }
            .co-counsel-floating-btn:hover {
                transform: translateY(-3px) scale(1.03);
                box-shadow: 0 15px 30px -5px rgba(79, 70, 229, 0.7), 0 0 25px rgba(6, 182, 212, 0.5);
            }
            .co-counsel-floating-btn i {
                font-size: 1.15rem;
                animation: pulseGlow 2s infinite ease-in-out;
            }
            @keyframes pulseGlow {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.15); opacity: 0.9; }
            }
            .co-counsel-drawer {
                position: fixed;
                bottom: 5.5rem;
                right: 1.5rem;
                width: 420px;
                max-width: calc(100vw - 2rem);
                height: 560px;
                max-height: calc(100vh - 7rem);
                background: rgba(11, 17, 32, 0.96);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 18px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(14, 165, 233, 0.15);
                z-index: 9991;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                transition: opacity 0.3s ease, transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.3s;
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                pointer-events: none;
                visibility: hidden;
            }
            .co-counsel-drawer.active {
                opacity: 1;
                transform: translateY(0) scale(1);
                pointer-events: all;
                visibility: visible;
            }
            .co-counsel-header {
                padding: 1rem 1.2rem;
                background: linear-gradient(90deg, rgba(31, 41, 55, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .co-counsel-header-title {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                font-family: 'Cinzel', serif;
                font-size: 1.05rem;
                font-weight: 700;
                color: #f8fafc;
            }
            .co-counsel-body {
                flex: 1;
                padding: 1rem;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 0.85rem;
                font-size: 0.88rem;
                line-height: 1.5;
            }
            .co-counsel-welcome {
                background: rgba(14, 165, 233, 0.08);
                border: 1px solid rgba(14, 165, 233, 0.2);
                border-radius: 12px;
                padding: 0.85rem;
                color: #cbd5e1;
            }
            .co-counsel-quick-pills {
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
                margin-top: 0.5rem;
            }
            .co-counsel-pill {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 20px;
                padding: 0.35rem 0.65rem;
                font-size: 0.76rem;
                color: #38bdf8;
                cursor: pointer;
                transition: background 0.2s, border-color 0.2s, color 0.2s;
            }
            .co-counsel-pill:hover {
                background: rgba(56, 189, 248, 0.18);
                border-color: rgba(56, 189, 248, 0.45);
                color: #ffffff;
            }
            .co-counsel-msg {
                padding: 0.75rem 1rem;
                border-radius: 12px;
                max-width: 88%;
                font-size: 0.85rem;
                word-wrap: break-word;
            }
            .co-counsel-msg.user {
                align-self: flex-end;
                background: var(--primary-600, #4338ca);
                color: #ffffff;
            }
            .co-counsel-msg.ai {
                align-self: flex-start;
                background: rgba(30, 41, 59, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: #e2e8f0;
            }
            .co-counsel-typing {
                display: flex;
                gap: 0.35rem;
                padding: 0.6rem 0.9rem;
                align-self: flex-start;
                background: rgba(30, 41, 59, 0.8);
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            .co-counsel-typing span {
                width: 6px;
                height: 6px;
                background: #38bdf8;
                border-radius: 50%;
                animation: ccTypingBounce 1.4s infinite ease-in-out both;
            }
            .co-counsel-typing span:nth-child(1) { animation-delay: -0.32s; }
            .co-counsel-typing span:nth-child(2) { animation-delay: -0.16s; }
            .co-counsel-typing span:nth-child(3) { animation-delay: 0s; }
            @keyframes ccTypingBounce {
                0%, 80%, 100% { transform: scale(0.3); opacity: 0.4; }
                40% { transform: scale(1); opacity: 1; }
            }
            .co-counsel-footer {
                padding: 0.75rem 1rem;
                border-top: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(15, 23, 42, 0.95);
                display: flex;
                gap: 0.5rem;
            }
            .co-counsel-input {
                flex: 1;
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 0.5rem 0.75rem;
                color: #ffffff;
                font-size: 0.85rem;
                outline: none;
            }
            .co-counsel-input:focus {
                border-color: #38bdf8;
            }
            @media (max-width: 640px) {
                .co-counsel-floating-btn {
                    bottom: 1rem;
                    right: 1rem;
                    padding: 0.6rem 0.95rem;
                    font-size: 0.82rem;
                }
                .co-counsel-drawer {
                    bottom: 4.5rem;
                    right: 0.5rem;
                    left: 0.5rem;
                    width: auto;
                    max-width: calc(100vw - 1rem);
                    height: calc(100vh - 5.5rem);
                    max-height: 82vh;
                    border-radius: 16px;
                }
                .co-counsel-input {
                    font-size: 16px !important;
                }
                .co-counsel-header {
                    padding: 0.75rem 1rem;
                }
                .co-counsel-body {
                    padding: 0.75rem;
                    gap: 0.65rem;
                }
                .co-counsel-msg {
                    max-width: 92%;
                    padding: 0.65rem 0.85rem;
                    font-size: 0.82rem;
                }
                .co-counsel-quick-pills {
                    gap: 0.35rem;
                }
                .co-counsel-pill {
                    font-size: 0.72rem;
                    padding: 0.28rem 0.55rem;
                }
            }
        `;
        document.head.appendChild(style);
    }

    renderDockUI() {
        const btn = document.createElement('button');
        btn.className = 'co-counsel-floating-btn';
        btn.id = 'coCounselToggleBtn';
        btn.innerHTML = `<i class="fas fa-robot"></i> <span>AI Co-Counsel</span>`;
        document.body.appendChild(btn);

        const drawer = document.createElement('div');
        drawer.className = 'co-counsel-drawer';
        drawer.id = 'coCounselDrawer';
        drawer.innerHTML = `
            <div class="co-counsel-header">
                <div class="co-counsel-header-title">
                    <i class="fas fa-scale-balanced" style="color: #38bdf8;"></i>
                    <span>JudIQ AI Co-Counsel</span>
                </div>
                <button class="btn-icon" id="closeCoCounselBtn" style="background:transparent; border:none; color:#94a3b8; cursor:pointer; font-size:1.1rem;">
                    <i class="fas fa-xmark"></i>
                </button>
            </div>
            <div class="co-counsel-body" id="coCounselBody">
                <div class="co-counsel-welcome">
                    <strong><i class="fas fa-shield-halved"></i> Institutional Litigation Assistant</strong>
                    <p style="margin: 0.4rem 0 0 0;">Ask about statutory timelines, Section 138 defenses, cross-examination vectors, director liability, or precedent ratios.</p>
                    <div class="co-counsel-quick-pills">
                        <span class="co-counsel-pill" data-prompt="What are the essential ingredients of a Section 138 offence?">Core Elements S.138</span>
                        <span class="co-counsel-pill" data-prompt="What is the statutory timeline to serve a demand notice and file complaint?">Statutory Timelines</span>
                        <span class="co-counsel-pill" data-prompt="Cross-exam questions for Bank Manager on Return Memo">Bank Manager Cross-Exam</span>
                        <span class="co-counsel-pill" data-prompt="Can company directors be prosecuted under Section 141 for a bounced cheque?">Director Liability (S.141)</span>
                        <span class="co-counsel-pill" data-prompt="Supreme court ratio on security cheque vs legally enforceable debt">Security Cheque Ratios</span>
                        <span class="co-counsel-pill" data-prompt="Draft Section 313 CrPC defense statement key points">Section 313 Defense</span>
                        <span class="co-counsel-pill" data-prompt="What is the maximum penalty and punishment under Section 138?">Maximum Penalties</span>
                    </div>
                </div>
            </div>
            <div class="co-counsel-footer">
                <input type="text" id="coCounselInput" class="co-counsel-input" placeholder="Type legal query or precedent search..." />
                <button id="sendCoCounselBtn" class="btn btn-primary btn-sm" style="padding: 0.4rem 0.8rem; border-radius: 8px;">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        `;
        document.body.appendChild(drawer);
    }

    bindEvents() {
        const toggleBtn = document.getElementById('coCounselToggleBtn');
        const closeBtn = document.getElementById('closeCoCounselBtn');
        const drawer = document.getElementById('coCounselDrawer');
        const sendBtn = document.getElementById('sendCoCounselBtn');
        const input = document.getElementById('coCounselInput');
        const body = document.getElementById('coCounselBody');

        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.isOpen = !this.isOpen;
                drawer.classList.toggle('active', this.isOpen);
                if (this.isOpen && input) input.focus();
            });
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.isOpen = false;
                drawer.classList.remove('active');
            });
        }

        const handleSend = () => {
            const query = input.value.trim();
            if (!query) return;
            this.addMessage(query, 'user');
            input.value = '';

            const loader = this.showTypingIndicator();

            setTimeout(() => {
                if (loader) loader.remove();
                const aiResp = this.generateResponse(query);
                this.addMessage(aiResp, 'ai');
            }, 600);
        };

        if (sendBtn) sendBtn.addEventListener('click', handleSend);
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') handleSend();
            });
        }

        if (body) {
            body.addEventListener('click', (e) => {
                const pill = e.target.closest('.co-counsel-pill');
                if (pill) {
                    const promptText = pill.getAttribute('data-prompt');
                    if (promptText) {
                        this.addMessage(promptText, 'user');
                        const loader = this.showTypingIndicator();
                        setTimeout(() => {
                            if (loader) loader.remove();
                            const resp = this.generateResponse(promptText);
                            this.addMessage(resp, 'ai');
                        }, 500);
                    }
                }
            });
        }
    }

    showTypingIndicator() {
        const body = document.getElementById('coCounselBody');
        if (!body) return null;
        const typingDiv = document.createElement('div');
        typingDiv.className = 'co-counsel-typing';
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        body.appendChild(typingDiv);
        body.scrollTop = body.scrollHeight;
        return typingDiv;
    }

    addMessage(text, sender) {
        const body = document.getElementById('coCounselBody');
        if (!body) return;
        const msgDiv = document.createElement('div');
        msgDiv.className = `co-counsel-msg ${sender}`;
        msgDiv.innerHTML = text.replace(/\n/g, '<br>');
        body.appendChild(msgDiv);
        body.scrollTop = body.scrollHeight;
    }

    generateResponse(query) {
        const q = query.toLowerCase();

        // 1. Ingredients / Core elements of S.138
        if (q.includes('ingredient') || q.includes('element') || (q.includes('core') && q.includes('138'))) {
            return `<strong><i class="fas fa-scale-balanced"></i> Essential Ingredients of Section 138 NI Act:</strong><br>
1. <strong>Legally Enforceable Debt:</strong> Cheque must be issued for discharge of a debt or other liability (Sec. 139 presumption).<br>
2. <strong>Presentation Window:</strong> Presented to bank within validity (3 months).<br>
3. <strong>Dishonour Memo:</strong> Dishonoured due to insufficiency of funds or exceeds arrangement.<br>
4. <strong>Statutory Demand Notice:</strong> Written notice dispatched within <strong>30 days</strong> of return memo.<br>
5. <strong>15-Day Cure Failure:</strong> Drawer fails to pay within <strong>15 days</strong> of receipt. Cause of action arises on Day 16.`;
        }

        // 2. Timeline / Limitation
        if (q.includes('limit') || q.includes('timeline') || q.includes('deadline') || q.includes('notice period') || q.includes('limitation period')) {
            return `<strong><i class="fas fa-clock"></i> Statutory Limitation Timelines (S.138 & 142 NI Act):</strong><br>
• <strong>Statutory Notice:</strong> Must be dispatched within <strong>30 days</strong> of receipt of the Bank Dishonour Memo.<br>
• <strong>15-Day Cure Period:</strong> Drawer gets 15 days from notice receipt to pay the demanded amount.<br>
• <strong>Court Complaint Window:</strong> Cause of action triggers on Day 16. Complaint must be filed before the JMFC/MM court within exactly <strong>30 days</strong> thereafter (Sec. 142(1)(b)).<br>
<small style="color:#f59e0b;">Late filings require a formal Condonation of Delay application showing sufficient cause.</small>`;
        }

        // 3. What if drawer fails to pay after notice period
        if (q.includes('fail') && q.includes('pay')) {
            return `<strong><i class="fas fa-gavel"></i> Drawer Failure to Pay after 15 Days:</strong><br>
Once the 15-day statutory cure period expires without complete payment, the payee secures an actionable criminal cause of action. You must file the formal complaint under Sec. 138/142 in the jurisdictional Magistrate court within the subsequent 30-day window.`;
        }

        // 4. Directors / Section 141 Vicarious Liability
        if (q.includes('director') || q.includes('141') || q.includes('company') || q.includes('vicarious')) {
            return `<strong><i class="fas fa-building-columns"></i> Corporate & Director Liability (Section 141 NI Act):</strong><br>
• <strong>Active Role Requirement:</strong> The complaint must contain specific averments that the director was in charge of and responsible for the conduct of the business at the time of cheque issuance.<br>
• <strong>Managing Directors / Signatories:</strong> Prima facie deemed responsible without detailed averments (<em>SMS Pharmaceuticals Ltd. v. Neeta Bhalla</em>).<br>
• <strong>Independent / Non-Executive Directors:</strong> Protected if not involved in day-to-day operations unless specific active involvement is pleaded and proved.`;
        }

        // 5. Penalties and punishment
        if (q.includes('penalt') || q.includes('punish') || q.includes('jail') || q.includes('imprisonment') || q.includes('fine')) {
            return `<strong><i class="fas fa-handcuffs"></i> Maximum Penalty & Punishment (Section 138 NI Act):</strong><br>
• <strong>Imprisonment:</strong> Up to <strong>2 years</strong>.<br>
• <strong>Monetary Fine:</strong> Up to <strong>twice (2x) the cheque amount</strong>, or both.<br>
• <strong>Interim Compensation (Sec. 143A):</strong> Court can order accused to pay up to 20% of the cheque amount during trial.`;
        }

        // 6. Bank Manager Cross-Exam
        if (q.includes('cross') || q.includes('bank') || q.includes('manager') || q.includes('memo')) {
            return `<strong><i class="fas fa-list-check"></i> Cross-Examination Vectors for Bank Manager:</strong><br>
1. <em>"Can you produce the original clearing register and log for the date of dishonour?"</em><br>
2. <em>"Was the dishonour memo generated automatically or verified manually by an authorized bank officer?"</em><br>
3. <em>"Is there an official audit record confirming the reason code (funds insufficient vs stop payment)?"</em><br>
<small style="color:#38bdf8;">Tip: Sec. 146 NI Act creates a rebuttable presumption in favor of the Bank Memo authenticity.</small>`;
        }

        // 7. Security Cheque Ratios
        if (q.includes('security') || q.includes('ratio') || q.includes('precedent')) {
            return `<strong><i class="fas fa-scale-balanced"></i> Security Cheque Landmark Ratio:</strong><br>
<strong>Sampelly Satyanarayana Rao (2016) & Sripati Singh (2021):</strong><br>
<em>"A cheque issued as security for a loan or contingent liability is enforceable under Section 138 if the liability had crystallized and was legally subsisting on the date of presentation."</em>`;
        }

        // 8. Section 313 CrPC
        if (q.includes('313') || q.includes('statement') || q.includes('defense statement')) {
            return `<strong><i class="fas fa-shield"></i> Section 313 CrPC Defense Statement Strategy:</strong><br>
• Disclose specific defense theory: misuse of signed blank security cheque, lack of underlying consideration, or excess claim.<br>
• Reserve right to lead defense evidence under Sec. 315 CrPC (DW-1 examination) to rebut the statutory presumption under Sec. 139.`;
        }

        // Default Institutional Recommendation
        return `<strong><i class="fas fa-brain"></i> Institutional Strategy Recommendation:</strong><br>
For "${query}", we recommend reviewing the primary documents (Cheque, Return Memo, Statutory Notice, Postal Tracking) against statutory deadlines and ensuring electronic evidence compliance under Sec. 65B Indian Evidence Act.`;
    }
}
