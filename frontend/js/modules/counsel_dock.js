/**
 * JudiQ AI — Co-Counsel Floating Assistant Dock
 * Interactive litigation assistant floating widget with quick prompt cards,
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
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 50px;
                padding: 0.75rem 1.25rem;
                display: flex;
                align-items: center;
                gap: 0.6rem;
                box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.5), 0 0 15px rgba(6, 182, 212, 0.3);
                cursor: pointer;
                font-family: var(--font-family, 'Outfit', sans-serif);
                font-weight: 600;
                font-size: 0.9rem;
                transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease;
            }
            .co-counsel-floating-btn:hover {
                transform: translateY(-3px) scale(1.03);
                box-shadow: 0 15px 30px -5px rgba(79, 70, 229, 0.7), 0 0 25px rgba(6, 182, 212, 0.5);
            }
            .co-counsel-floating-btn i {
                font-size: 1.1rem;
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
                width: 380px;
                max-width: calc(100vw - 2rem);
                height: 520px;
                max-height: calc(100vh - 7rem);
                background: rgba(11, 17, 32, 0.95);
                backdrop-filter: blur(20px);
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
                background: linear-gradient(90deg, rgba(31, 41, 55, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
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
                gap: 0.5rem;
                margin-top: 0.4rem;
            }
            .co-counsel-pill {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 20px;
                padding: 0.35rem 0.65rem;
                font-size: 0.76rem;
                color: #38bdf8;
                cursor: pointer;
                transition: background 0.2s, border-color 0.2s;
            }
            .co-counsel-pill:hover {
                background: rgba(56, 189, 248, 0.15);
                border-color: rgba(56, 189, 248, 0.4);
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
                    <span>JudIQ Co-Counsel Dock</span>
                </div>
                <button class="btn-icon" id="closeCoCounselBtn" style="background:transparent; border:none; color:#94a3b8; cursor:pointer; font-size:1.1rem;">
                    <i class="fas fa-xmark"></i>
                </button>
            </div>
            <div class="co-counsel-body" id="coCounselBody">
                <div class="co-counsel-welcome">
                    <strong><i class="fas fa-shield-halved"></i> Institutional Legal Assistant</strong>
                    <p style="margin: 0.4rem 0 0 0;">Ask about statutory deadlines, Section 138 defenses, cross-examination vectors, or precedent ratios.</p>
                    <div class="co-counsel-quick-pills">
                        <span class="co-counsel-pill" data-prompt="Cross-exam questions for Bank Manager on Return Memo">Bank Manager Cross-Exam</span>
                        <span class="co-counsel-pill" data-prompt="Statutory limitation timeline rules under S.138 NI Act">S.138 Limitation Rules</span>
                        <span class="co-counsel-pill" data-prompt="Supreme court ratio on security cheque vs legally enforceable debt">Security Cheque Ratios</span>
                        <span class="co-counsel-pill" data-prompt="Draft Section 313 CrPC defense statement key points">Section 313 Defense</span>
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

            setTimeout(() => {
                const aiResp = this.generateResponse(query);
                this.addMessage(aiResp, 'ai');
            }, 500);
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
                        setTimeout(() => {
                            const resp = this.generateResponse(promptText);
                            this.addMessage(resp, 'ai');
                        }, 400);
                    }
                }
            });
        }
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
        if (q.includes('cross') || q.includes('bank') || q.includes('manager')) {
            return `<strong><i class="fas fa-list-check"></i> Cross-Examination Vectors for Bank Manager:</strong><br>
1. <em>"Can you produce the original clearing register for [Date]?"</em><br>
2. <em>"Was the dishonour memo generated automatically or verified manually by a bank officer?"</em><br>
3. <em>"Is there an official audit record confirming the signature discrepancy code?"</em><br>
<small style="color:#38bdf8;">Tip: Mandatory under Sec. 146 NI Act presumption of bank memo authenticity.</small>`;
        }
        if (q.includes('limit') || q.includes('timeline') || q.includes('rule')) {
            return `<strong><i class="fas fa-clock"></i> Statutory Limitation Guide (S.138 NI Act):</strong><br>
• <strong>Demand Notice:</strong> Must be dispatched within <strong>30 days</strong> of Bank Memo.<br>
• <strong>Cure Period:</strong> Accused gets <strong>15 days</strong> from Notice receipt to pay.<br>
• <strong>Court Filing Window:</strong> Cause of action arises on Day 16. Complaint must be filed within <strong>30 days</strong> thereafter (Sec. 142(1)(b)).`;
        }
        if (q.includes('security') || q.includes('ratio')) {
            return `<strong><i class="fas fa-gavel"></i> Key Precedent Ratio:</strong><br>
<strong>Dashrath Rupsingh Rathod v. State of Maharashtra (2014)</strong> & <strong>Sampelly Satyanarayana Rao (2016):</strong><br>
<em>"A cheque given as security for an existing enforceable debt is fully covered under Section 138 if the debt subsists on the date of cheque presentation."</em>`;
        }
        return `<strong><i class="fas fa-brain"></i> Institutional Strategy Recommendation:</strong><br>
For "${query}", we recommend auditing documentary evidence compliance under Sec. 65B Indian Evidence Act and verifying statutory notice receipt proof (postage tracking / AD card).`;
    }
}
