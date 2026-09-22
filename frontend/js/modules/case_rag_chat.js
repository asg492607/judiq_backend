/**
 * JudiQ AI — Multilingual Case RAG Intelligence Workspace
 * ========================================================
 * Interactive Legal Co-Counsel powered by Google Gemini RAG.
 * Features:
 *   - Multilingual interaction in English, Hindi (हिन्दी), and Marathi (मराठी)
 *   - Grounded case facts & evidence question-answering
 *   - Live Fact-Sync cards with 1-click case state updates
 *   - Dedicated Cross-Examination & Courtroom Argument generation
 *   - Seamless handoff to 12-pillar legal analysis with updated facts
 *   - Instant export and download of verified fact dossiers
 */

import { api } from '../../api.js?v=54';
import { ui } from '../../ui.js?v=54';
import { escapeHtml } from './utils.js?v=54';

export class CaseRagChatWorkspace {
    constructor() {
        this.isOpen = false;
        this.currentMode = 'qa'; // 'qa' | 'cross_exam' | 'arguments'
        this.currentLang = 'en'; // 'en' | 'hi' | 'mr'
        this.caseData = {};
        this.docIntel = {};
        this.chatHistory = [];
        this.init();
    }

    init() {
        this.injectStyles();
        this.renderWorkspaceDOM();
        this.bindEvents();
    }

    injectStyles() {
        if (document.getElementById('caseRagChatStyles')) return;
        const style = document.createElement('style');
        style.id = 'caseRagChatStyles';
        style.textContent = `
            .case-rag-modal-backdrop {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(15, 23, 42, 0.45);
                backdrop-filter: blur(8px);
                z-index: 9995;
                display: none;
                align-items: center;
                justify-content: center;
                opacity: 0;
                transition: opacity 0.25s ease;
            }
            .case-rag-modal-backdrop.active {
                display: flex;
                opacity: 1;
            }
            .case-rag-window {
                width: 92vw;
                max-width: 1020px;
                height: 88vh;
                max-height: 860px;
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 20px;
                display: flex;
                flex-direction: column;
                box-shadow: 0 25px 60px -15px rgba(15, 23, 42, 0.22), 0 0 0 1px rgba(15, 23, 42, 0.05);
                overflow: hidden;
                font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                animation: scaleUpIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            }
            @keyframes scaleUpIn {
                from { transform: scale(0.96); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            .case-rag-header {
                padding: 1rem 1.5rem;
                background: #ffffff;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 0.8rem;
            }
            .case-rag-title-area {
                display: flex;
                align-items: center;
                gap: 0.85rem;
            }
            .case-rag-icon-badge {
                width: 42px;
                height: 42px;
                border-radius: 12px;
                background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #ffffff;
                font-size: 1.15rem;
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
            }
            .case-rag-title-area h3 {
                margin: 0;
                font-size: 1.1rem;
                font-weight: 700;
                color: #0f172a;
                display: flex;
                align-items: center;
                gap: 0.6rem;
                letter-spacing: -0.01em;
            }
            .case-rag-id-chip {
                font-size: 0.75rem;
                background: #eef2ff;
                color: #4338ca;
                border: 1px solid #c7d2fe;
                padding: 0.2rem 0.6rem;
                border-radius: 6px;
                font-weight: 600;
                letter-spacing: 0.02em;
            }
            .case-rag-controls {
                display: flex;
                align-items: center;
                gap: 0.65rem;
            }
            .case-rag-mode-pills {
                display: flex;
                background: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 9px;
                padding: 3px;
                gap: 2px;
            }
            .case-rag-mode-btn {
                background: transparent;
                border: none;
                color: #64748b;
                padding: 0.4rem 0.8rem;
                font-size: 0.82rem;
                font-weight: 600;
                border-radius: 7px;
                cursor: pointer;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                display: flex;
                align-items: center;
                gap: 0.4rem;
            }
            .case-rag-mode-btn:hover {
                color: #0f172a;
            }
            .case-rag-mode-btn.active {
                background: #ffffff;
                color: #4338ca;
                box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
                font-weight: 700;
            }
            .case-rag-lang-select {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                color: #0f172a;
                padding: 0.4rem 0.75rem;
                border-radius: 8px;
                font-size: 0.82rem;
                font-weight: 600;
                cursor: pointer;
                outline: none;
                transition: border-color 0.2s;
            }
            .case-rag-lang-select:focus {
                border-color: #4f46e5;
                box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
            }
            .case-rag-clear-btn {
                background: #fff1f2;
                border: 1px solid #fecdd3;
                color: #e11d48;
                padding: 0.4rem 0.75rem;
                border-radius: 8px;
                font-size: 0.8rem;
                font-weight: 600;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                transition: all 0.2s;
            }
            .case-rag-clear-btn:hover {
                background: #ffe4e6;
                border-color: #fda4af;
                color: #be123c;
            }
            .case-rag-close-btn {
                background: transparent;
                border: none;
                color: #94a3b8;
                cursor: pointer;
                font-size: 1.25rem;
                padding: 0.35rem 0.6rem;
                border-radius: 8px;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .case-rag-close-btn:hover {
                color: #dc2626;
                background: #fee2e2;
            }
            .case-rag-body {
                flex: 1;
                overflow-y: auto;
                padding: 1.5rem;
                display: flex;
                flex-direction: column;
                gap: 1.1rem;
                background: #f8fafc;
            }
            .case-rag-msg {
                max-width: 84%;
                line-height: 1.62;
                font-size: 0.92rem;
                border-radius: 16px;
                padding: 1rem 1.3rem;
                position: relative;
                word-wrap: break-word;
            }
            .case-rag-msg.user {
                align-self: flex-end;
                background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
                color: #ffffff;
                border-bottom-right-radius: 4px;
                box-shadow: 0 4px 14px rgba(79, 70, 229, 0.2);
            }
            .case-rag-msg.user strong {
                color: #ffffff;
            }
            .case-rag-msg.ai {
                align-self: flex-start;
                background: #ffffff;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-bottom-left-radius: 4px;
                box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
            }
            .case-rag-msg.ai h2, .case-rag-msg.ai h3, .case-rag-msg.ai h4 {
                color: #0f172a;
                font-weight: 700;
                margin: 0.75rem 0 0.35rem 0;
                letter-spacing: -0.01em;
            }
            .case-rag-msg.ai h2:first-child, .case-rag-msg.ai h3:first-child, .case-rag-msg.ai h4:first-child {
                margin-top: 0;
            }
            .case-rag-msg.ai strong {
                color: #0f172a;
                font-weight: 700;
            }
            .case-rag-msg.ai code.case-rag-code {
                background: #f1f5f9;
                color: #4338ca;
                padding: 0.15rem 0.4rem;
                border-radius: 5px;
                font-size: 0.85em;
                border: 1px solid #e2e8f0;
            }
            .case-rag-msg.ai hr.case-rag-hr {
                border: none;
                border-top: 1px solid #e2e8f0;
                margin: 0.85rem 0;
            }
            .case-rag-msg.ai ul.case-rag-list, .case-rag-msg.ai ol.case-rag-list {
                margin: 0.45rem 0;
                padding-left: 1.35rem;
            }
            .case-rag-msg.ai ul.case-rag-list li, .case-rag-msg.ai ol.case-rag-list li {
                margin-bottom: 0.3rem;
            }
            .case-rag-citations {
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
                margin-top: 0.85rem;
                padding-top: 0.75rem;
                border-top: 1px dashed #e2e8f0;
            }
            .case-rag-citation-chip {
                background: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
                font-size: 0.74rem;
                padding: 0.2rem 0.55rem;
                border-radius: 6px;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
            }
            .case-rag-fact-card {
                background: #f5f3ff;
                border: 1px solid #c7d2fe;
                border-radius: 12px;
                padding: 0.85rem 1.1rem;
                margin-top: 0.85rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                flex-wrap: wrap;
            }
            .case-rag-fact-card strong {
                color: #3730a3 !important;
                font-size: 0.88rem;
            }
            .case-rag-fact-card span {
                font-size: 0.84rem;
                color: #334155;
            }
            .case-rag-fact-actions {
                display: flex;
                gap: 0.5rem;
            }
            .btn-fact-apply {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: #ffffff;
                border: none;
                padding: 0.4rem 0.85rem;
                border-radius: 7px;
                font-size: 0.8rem;
                font-weight: 700;
                cursor: pointer;
                box-shadow: 0 2px 6px rgba(16, 185, 129, 0.25);
                transition: all 0.2s;
            }
            .btn-fact-apply:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 10px rgba(16, 185, 129, 0.4);
            }
            .btn-fact-dismiss {
                background: #ffffff;
                color: #64748b;
                border: 1px solid #cbd5e1;
                padding: 0.4rem 0.75rem;
                border-radius: 7px;
                font-size: 0.8rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            .btn-fact-dismiss:hover {
                background: #f1f5f9;
                color: #0f172a;
            }
            .case-rag-quick-prompts {
                padding: 0.75rem 1.4rem;
                background: #ffffff;
                border-top: 1px solid #e2e8f0;
                display: flex;
                gap: 0.55rem;
                overflow-x: auto;
                scrollbar-width: thin;
            }
            .case-rag-prompt-chip {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                color: #475569;
                padding: 0.4rem 0.85rem;
                border-radius: 20px;
                font-size: 0.79rem;
                font-weight: 500;
                white-space: nowrap;
                cursor: pointer;
                transition: all 0.2s;
            }
            .case-rag-prompt-chip:hover {
                background: #eef2ff;
                border-color: #6366f1;
                color: #4338ca;
                transform: translateY(-1px);
            }
            .case-rag-footer {
                padding: 0.95rem 1.4rem;
                background: #ffffff;
                border-top: 1px solid #e2e8f0;
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }
            .case-rag-input-row {
                display: flex;
                gap: 0.75rem;
                align-items: flex-end;
            }
            .case-rag-textarea {
                flex: 1;
                background: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 12px;
                color: #0f172a;
                padding: 0.75rem 1rem;
                font-size: 0.92rem;
                resize: none;
                max-height: 120px;
                min-height: 46px;
                outline: none;
                font-family: inherit;
                line-height: 1.45;
                transition: all 0.2s;
            }
            .case-rag-textarea:focus {
                border-color: #4f46e5;
                background: #ffffff;
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.12);
            }
            .case-rag-send-btn {
                background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
                color: #ffffff;
                border: none;
                border-radius: 12px;
                width: 46px;
                height: 46px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.15rem;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25);
                transition: all 0.2s;
            }
            .case-rag-send-btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 16px rgba(79, 70, 229, 0.35);
            }
            .case-rag-action-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.75rem;
                flex-wrap: wrap;
            }
            .btn-rag-analyze {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: #ffffff;
                border: none;
                padding: 0.55rem 1.2rem;
                border-radius: 9px;
                font-size: 0.86rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
                transition: all 0.2s;
            }
            .btn-rag-analyze:hover {
                transform: translateY(-1px);
                box-shadow: 0 6px 16px rgba(16, 185, 129, 0.45);
            }
            .btn-rag-export {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                color: #334155;
                padding: 0.55rem 1rem;
                border-radius: 9px;
                font-size: 0.83rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.45rem;
                cursor: pointer;
                transition: all 0.2s;
            }
            .btn-rag-export:hover {
                background: #f1f5f9;
                color: #0f172a;
                border-color: #94a3b8;
            }
            .case-rag-typing {
                display: inline-flex;
                gap: 4px;
                padding: 0.6rem 0.9rem;
                background: #e2e8f0;
                border-radius: 14px;
                align-self: flex-start;
            }
            .case-rag-typing span {
                width: 6px;
                height: 6px;
                background: #6366f1;
                border-radius: 50%;
                animation: typingBounce 1.4s infinite ease-in-out both;
            }
            .case-rag-typing span:nth-child(1) { animation-delay: -0.32s; }
            .case-rag-typing span:nth-child(2) { animation-delay: -0.16s; }
            @keyframes typingBounce {
                0%, 80%, 100% { transform: scale(0); }
                40% { transform: scale(1); }
            }
            .case-rag-history-divider {
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 1rem 0;
                position: relative;
                width: 100%;
            }
            .case-rag-history-divider::before {
                content: '';
                position: absolute;
                left: 0;
                right: 0;
                height: 1px;
                background: #e2e8f0;
            }
            .case-rag-history-divider span {
                position: relative;
                background: #ffffff;
                padding: 0.25rem 0.9rem;
                font-size: 0.75rem;
                color: #64748b;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
                display: inline-flex;
                align-items: center;
                gap: 0.4rem;
                font-weight: 500;
            }

            /* Dark mode adaptive overrides */
            [data-theme="dark"] .case-rag-modal-backdrop {
                background: rgba(7, 11, 20, 0.82);
            }
            [data-theme="dark"] .case-rag-window {
                background: #0e1424;
                border-color: rgba(255, 255, 255, 0.1);
                box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.75);
            }
            [data-theme="dark"] .case-rag-header {
                background: #141c30;
                border-bottom-color: rgba(255, 255, 255, 0.08);
            }
            [data-theme="dark"] .case-rag-title-area h3 {
                color: #f8fafc;
            }
            [data-theme="dark"] .case-rag-mode-pills {
                background: rgba(15, 23, 42, 0.7);
                border-color: rgba(255, 255, 255, 0.1);
            }
            [data-theme="dark"] .case-rag-mode-btn {
                color: #94a3b8;
            }
            [data-theme="dark"] .case-rag-mode-btn.active {
                background: #4f46e5;
                color: #ffffff;
            }
            [data-theme="dark"] .case-rag-lang-select {
                background: #0e1424;
                border-color: rgba(255, 255, 255, 0.15);
                color: #f8fafc;
            }
            [data-theme="dark"] .case-rag-body {
                background: #070b14;
            }
            [data-theme="dark"] .case-rag-msg.ai {
                background: #141c30;
                color: #e2e8f0;
                border-color: rgba(255, 255, 255, 0.08);
            }
            [data-theme="dark"] .case-rag-msg.ai h2,
            [data-theme="dark"] .case-rag-msg.ai h3,
            [data-theme="dark"] .case-rag-msg.ai h4,
            [data-theme="dark"] .case-rag-msg.ai strong {
                color: #f8fafc;
            }
            [data-theme="dark"] .case-rag-quick-prompts,
            [data-theme="dark"] .case-rag-footer {
                background: #0e1424;
                border-top-color: rgba(255, 255, 255, 0.08);
            }
            [data-theme="dark"] .case-rag-textarea {
                background: #141c30;
                border-color: rgba(255, 255, 255, 0.15);
                color: #f8fafc;
            }
            [data-theme="dark"] .case-rag-prompt-chip {
                background: #141c30;
                border-color: rgba(255, 255, 255, 0.1);
                color: #cbd5e1;
            }
            [data-theme="dark"] .btn-rag-export {
                background: #141c30;
                border-color: rgba(255, 255, 255, 0.15);
                color: #f8fafc;
            }
            [data-theme="dark"] .case-rag-fact-card {
                background: rgba(79, 70, 229, 0.15);
                border-color: rgba(99, 102, 241, 0.4);
            }
            [data-theme="dark"] .case-rag-fact-card strong {
                color: #a5b4fc !important;
            }
            [data-theme="dark"] .case-rag-fact-card span {
                color: #e2e8f0;
            }
            [data-theme="dark"] .case-rag-history-divider::before {
                background: rgba(255, 255, 255, 0.1);
            }
            [data-theme="dark"] .case-rag-history-divider span {
                background: #141c30;
                border-color: rgba(255, 255, 255, 0.1);
                color: #94a3b8;
            }
        `;
        document.head.appendChild(style);
    }

    renderWorkspaceDOM() {
        const modal = document.createElement('div');
        modal.className = 'case-rag-modal-backdrop';
        modal.id = 'caseRagModal';
        modal.innerHTML = `
            <div class="case-rag-window">
                <div class="case-rag-header">
                    <div class="case-rag-title-area">
                        <div class="case-rag-icon-badge">
                            <i class="fas fa-scale-balanced"></i>
                        </div>
                        <div>
                            <h3 id="ragCaseTitle">Case Intelligence Workspace <span class="case-rag-id-chip" id="ragCaseId">INIT</span></h3>
                        </div>
                    </div>
                    <div class="case-rag-controls">
                        <div class="case-rag-mode-pills">
                            <button class="case-rag-mode-btn active" data-mode="qa"><i class="fas fa-comments"></i> Case Q&A</button>
                            <button class="case-rag-mode-btn" data-mode="cross_exam"><i class="fas fa-gavel"></i> Cross-Exam</button>
                            <button class="case-rag-mode-btn" data-mode="arguments"><i class="fas fa-shield-halved"></i> Arguments</button>
                        </div>
                        <select class="case-rag-lang-select" id="ragLangSelect">
                            <option value="en">English</option>
                            <option value="mr">मराठी</option>
                            <option value="hi">हिन्दी</option>
                        </select>
                        <button class="case-rag-clear-btn" id="clearRagChatBtn" title="Clear chat history and restart consultation">
                            <i class="fas fa-trash-can"></i> Clear
                        </button>
                        <button class="case-rag-close-btn" id="closeRagModalBtn" title="Close Workspace">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>

                <div class="case-rag-body" id="ragChatBody">
                    <!-- Messages will be populated here -->
                </div>

                <div class="case-rag-quick-prompts" id="ragQuickPrompts">
                    <!-- Localized Quick Prompts -->
                </div>

                <div class="case-rag-footer">
                    <div class="case-rag-input-row">
                        <textarea class="case-rag-textarea" id="ragInput" placeholder="Ask about case facts, statutory deadlines, or update details..." rows="1"></textarea>
                        <button class="case-rag-send-btn" id="ragSendBtn" title="Send Query">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                    <div class="case-rag-action-bar">
                        <button class="btn-rag-export" id="ragExportBtn">
                            <i class="fas fa-file-arrow-down"></i> Download Fact Dossier
                        </button>
                        <button class="btn-rag-analyze" id="ragAnalyzeBtn">
                            <i class="fas fa-chart-line"></i> Run Analysis on Updated Facts
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    bindEvents() {
        const modal = document.getElementById('caseRagModal');
        const closeBtn = document.getElementById('closeRagModalBtn');
        const clearBtn = document.getElementById('clearRagChatBtn');
        const sendBtn = document.getElementById('ragSendBtn');
        const input = document.getElementById('ragInput');
        const langSelect = document.getElementById('ragLangSelect');
        const modeBtns = document.querySelectorAll('.case-rag-mode-btn');
        const exportBtn = document.getElementById('ragExportBtn');
        const analyzeBtn = document.getElementById('ragAnalyzeBtn');

        if (closeBtn) closeBtn.addEventListener('click', () => this.close());
        if (clearBtn) clearBtn.addEventListener('click', () => this.handleClearChat());
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.close();
            });
        }

        if (sendBtn) sendBtn.addEventListener('click', () => this.handleSend());
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSend();
                }
            });
            input.addEventListener('input', () => {
                input.style.height = 'auto';
                input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
            });
        }

        if (langSelect) {
            langSelect.addEventListener('change', (e) => {
                this.currentLang = e.target.value;
                this.renderQuickPrompts();
            });
        }

        modeBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                modeBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentMode = btn.dataset.mode;
                this.handleModeSwitch(this.currentMode);
            });
        });

        if (exportBtn) exportBtn.addEventListener('click', () => this.handleExport());
        if (analyzeBtn) analyzeBtn.addEventListener('click', () => this.handleRunAnalysis());
    }

    open(caseData = {}, docIntel = {}) {
        this.caseData = { ...caseData };
        this.docIntel = { ...docIntel };
        this.isOpen = true;

        const modal = document.getElementById('caseRagModal');
        const titleEl = document.getElementById('ragCaseTitle');
        const body = document.getElementById('ragChatBody');

        const caseId = this.caseData.case_id || this.docIntel.session_id || (window.state && window.state.caseId) || 'CSE-' + Date.now();
        this.caseData.case_id = caseId;
        this.docIntel.session_id = this.docIntel.session_id || caseId;
        this.activeCaseId = caseId;

        // Clean human-readable title resolution
        let comp = this.caseData.complainant_name;
        if (Array.isArray(comp) && comp.length) comp = comp[0].value || comp[0];
        let acc = this.caseData.accused_name;
        if (Array.isArray(acc) && acc.length) acc = acc[0].value || acc[0];

        let caseTitle = this.caseData.case_title || this.caseData.case_name;
        if (!caseTitle || caseTitle === 'Untitled Case' || caseTitle === 'null' || caseTitle === 'Active Case') {
            if (comp && acc && comp !== 'Complainant' && acc !== 'Accused') {
                caseTitle = `${comp} vs. ${acc}`;
            } else if (comp && comp !== 'Complainant') {
                caseTitle = `${comp} Matter`;
            } else if (acc && acc !== 'Accused') {
                caseTitle = `Matter against ${acc}`;
            } else {
                caseTitle = 'Section 138 Case Intelligence';
            }
        }

        if (titleEl) {
            titleEl.innerHTML = `${escapeHtml(caseTitle)} <span class="case-rag-id-chip" id="ragCaseId">${escapeHtml(caseId)}</span>`;
        }
        if (body) body.innerHTML = '';

        if (modal) modal.classList.add('active');

        this.renderQuickPrompts();
        this.initializeSession(caseId);
    }

    close() {
        this.isOpen = false;
        const modal = document.getElementById('caseRagModal');
        if (modal) modal.classList.remove('active');
    }

    renderQuickPrompts() {
        const container = document.getElementById('ragQuickPrompts');
        if (!container) return;

        const prompts = {
            en: [
                { label: 'Limitation Period Audit', prompt: 'Audit the statutory limitation period under Section 138 & 142 NI Act for this case.' },
                { label: 'Bank Memo Cross-Exam', prompt: 'Generate cross-examination questions for the Bank Manager regarding the dishonour memo.' },
                { label: 'Section 139 Presumption', prompt: 'How can the accused rebut the Section 139 legal presumption in this case?' },
                { label: 'Director Liability (S.141)', prompt: 'Does the complaint fulfill S.M.S. Pharma criteria for Section 141 vicarious liability?' },
                { label: 'Missing Evidentiary Links', prompt: 'Identify any missing evidentiary links or forensic gaps in our document record.' }
            ],
            mr: [
                { label: 'मर्यादा कालावधी तपास (Limitation)', prompt: 'या खटल्यातील कलम १३८ व १४२ नुसार नोटीस व तक्रारीचा मर्यादा कालावधी तपासा.' },
                { label: 'बँक व्यवस्थापक उलट तपासणी', prompt: 'अनादर मेमोच्या वैधतेबाबत बँक व्यवस्थापकासाठी उलट तपासणीचे प्रश्न तयार करा.' },
                { label: 'कलम १३९ गृहीतक खंडन', prompt: 'कलम १३९ चे कायदेशीर अनुमान आरोपी कशा प्रकारे खंडित करू शकतो?' },
                { label: 'संचालक जबाबदारी (कलम १४१)', prompt: 'कंपनीच्या संचालकांना आरोपी बनवण्यासाठी विशिष्ट आरोपांची आवश्यकता पूर्ण झाली आहे का?' },
                { label: 'पुराव्यातील उणिवा', prompt: 'आपल्या कागदपत्रांमध्ये कोणत्या कायदेशीर किंवा पुराव्याच्या उणिवा आहेत?' }
            ],
            hi: [
                { label: 'समय-सीमा जांच (Limitation)', prompt: 'धारा 138 और 142 NI Act के तहत इस केस की कानूनी नोटिस और परिवाद की समय-सीमा जांचें।' },
                { label: 'बैंक मेमो पर जिरह', prompt: 'बैंक रिटर्न मेमो के संबंध में बैंक प्रबंधक के लिए जिरह (Cross-examination) के प्रश्न बनाएं।' },
                { label: 'धारा 139 विधिक उपधारणा', prompt: 'धारा 139 की विधिक उपधारणा को अभियुक्त किन आधारों पर खंडित कर सकता है?' },
                { label: 'कंपनी डायरेक्टर दायित्व (141)', prompt: 'क्या कंपनी के निदेशकों के विरुद्ध धारा 141 के आवश्यक आरोप पूरे हैं?' },
                { label: 'दस्तावेजी कमियां', prompt: 'हमारे वर्तमान दस्तावेजी रिकॉर्ड में कौन से साक्ष्य या कानूनी लिंक गायब हैं?' }
            ]
        };

        const activePrompts = prompts[this.currentLang] || prompts.en;
        container.innerHTML = activePrompts.map(p => `
            <span class="case-rag-prompt-chip" data-prompt="${escapeHtml(p.prompt)}">${escapeHtml(p.label)}</span>
        `).join('');

        container.querySelectorAll('.case-rag-prompt-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const query = chip.dataset.prompt;
                const input = document.getElementById('ragInput');
                if (input) input.value = query;
                this.handleSend();
            });
        });
    }

    async initializeSession(caseId) {
        this.showTypingIndicator();
        try {
            const res = await api.initCaseChat({
                case_id: caseId,
                case_data: this.caseData,
                doc_intel: this.docIntel,
                language: this.currentLang
            });
            this.removeTypingIndicator();

            if (res.all_facts && typeof res.all_facts === 'object' && Object.keys(res.all_facts).length > 0) {
                this.docIntel = this.docIntel || {};
                this.docIntel.all_facts = { ...(this.docIntel.all_facts || {}), ...res.all_facts };
            }
            if (res.case_data && typeof res.case_data === 'object' && Object.keys(res.case_data).length > 0) {
                this.caseData = { ...(this.caseData || {}), ...res.case_data };
            }
            if (res.active_facts && typeof res.active_facts === 'object' && Object.keys(res.active_facts).length > 0) {
                this.caseData = { ...(this.caseData || {}), ...res.active_facts };
            }
            if (window.state) {
                window.state.caseData = { ...(window.state.caseData || {}), ...(this.caseData || {}) };
                if (this.docIntel) {
                    window.state.docIntel = { ...(window.state.docIntel || {}), ...this.docIntel };
                }
            }

            const body = document.getElementById('ragChatBody');
            if (res.history && res.history.length > 0) {
                if (body) {
                    const divider = document.createElement('div');
                    divider.className = 'case-rag-history-divider';
                    divider.innerHTML = `<span><i class="fas fa-history"></i> Resumed Session • ${res.history.length} previous messages</span>`;
                    body.appendChild(divider);
                }
                res.history.forEach(msg => {
                    this.addMessage(
                        msg.content,
                        msg.role === 'user' ? 'user' : 'ai',
                        msg.citations || [],
                        msg.proposed_updates || [],
                        false
                    );
                });
                this.addMessage(
                    `Consultation reconnected for **${caseId}**. All case facts, verified documents, and statutory context are live. Continue asking questions or clarifying details below.`,
                    'ai',
                    [],
                    [],
                    false
                );
            } else if (res.greeting) {
                this.addMessage(res.greeting, 'ai');
            }
        } catch (err) {
            this.removeTypingIndicator();
            this.addMessage(`Initialized session for ${caseId}. Ask any query regarding case facts, statutory limitation, or cross-examination.`, 'ai');
        }
    }

    async handleClearChat() {
        const caseId = this.caseData.case_id || this.docIntel?.session_id;
        if (!caseId) return;
        if (!confirm("Are you sure you want to clear chat history and restart consultation for this case?")) {
            return;
        }
        try {
            await api.clearCaseChatHistory(caseId);
            this.chatHistory = [];
            const body = document.getElementById('ragChatBody');
            if (body) body.innerHTML = '';
            ui.toast('Chat history cleared.', 'info');
            this.initializeSession(caseId);
        } catch (err) {
            ui.toast(`Failed to clear history: ${err.message}`, 'error');
        }
    }

    async handleSend() {
        const input = document.getElementById('ragInput');
        if (!input) return;
        const query = input.value.trim();
        if (!query) return;

        this.addMessage(query, 'user');
        input.value = '';
        input.style.height = 'auto';

        this.showTypingIndicator();

        try {
            const res = await api.queryCaseChat({
                case_id: this.caseData.case_id,
                query: query,
                case_data: this.caseData,
                doc_intel: this.docIntel,
                chat_history: this.chatHistory,
                language: this.currentLang
            });

            this.removeTypingIndicator();

            if (res.answer) {
                this.addMessage(res.answer, 'ai', res.citations, res.proposed_updates);
            }
        } catch (err) {
            this.removeTypingIndicator();
            this.addMessage(`Error processing query: ${err.message}`, 'ai');
        }
    }

    async handleModeSwitch(mode) {
        if (mode === 'cross_exam') {
            this.showTypingIndicator();
            try {
                const res = await api.generateCrossExam({
                    case_id: this.caseData.case_id,
                    witness_role: 'complainant',
                    case_data: this.caseData,
                    doc_intel: this.docIntel,
                    language: this.currentLang
                });
                this.removeTypingIndicator();
                this.addMessage(res.questions_text || 'Cross-examination questions ready.', 'ai');
            } catch (err) {
                this.removeTypingIndicator();
                this.addMessage(`Failed to generate cross-examination: ${err.message}`, 'ai');
            }
        } else if (mode === 'arguments') {
            this.showTypingIndicator();
            try {
                const res = await api.generateArguments({
                    case_id: this.caseData.case_id,
                    argument_type: 'framing_notice',
                    case_data: this.caseData,
                    doc_intel: this.docIntel,
                    language: this.currentLang
                });
                this.removeTypingIndicator();
                this.addMessage(res.arguments_text || 'Courtroom arguments ready.', 'ai');
            } catch (err) {
                this.removeTypingIndicator();
                this.addMessage(`Failed to generate arguments: ${err.message}`, 'ai');
            }
        }
    }

    async applyFactUpdate(field, value, cardElement) {
        try {
            const res = await api.updateCaseFact({
                case_id: this.caseData.case_id || 'ACTIVE_CASE',
                field: field,
                value: value
            });
            this.caseData[field] = value;
            if (window.state && window.state.caseData) {
                window.state.caseData[field] = value;
            }

            // Sync with local storage
            try {
                let localCases = JSON.parse(localStorage.getItem('judiq_recent_cases_v1') || '[]');
                const cid = this.caseData.case_id;
                localCases = localCases.map(c => {
                    if (c.id === cid) {
                        c.case_data = { ...(c.case_data || {}), [field]: value };
                    }
                    return c;
                });
                localStorage.setItem('judiq_recent_cases_v1', JSON.stringify(localCases));
            } catch (_) {}

            ui.toast(`Updated ${field} to ${value} in case state.`, 'success');
            if (cardElement) {
                cardElement.innerHTML = `
                    <div style="color: #10b981; font-weight: 600; font-size: 0.82rem;">
                        <i class="fas fa-check-circle"></i> Applied to active case state: <strong>${escapeHtml(field)}</strong> = ${escapeHtml(String(value))}
                    </div>
                `;
            }
        } catch (err) {
            ui.toast(`Failed to update fact: ${err.message}`, 'error');
        }
    }

    async handleExport() {
        try {
            ui.toast('Exporting verified case fact dossier...', 'info');
            const res = await api.exportCaseFacts({
                case_id: this.caseData.case_id,
                case_data: this.caseData,
                doc_intel: this.docIntel,
                language: this.currentLang
            });

            if (res.markdown) {
                const blob = new Blob([res.markdown], { type: 'text/markdown;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Case_Facts_${this.caseData.case_id || 'Dossier'}.md`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                ui.toast('Dossier downloaded successfully.', 'success');
            }
        } catch (err) {
            ui.toast(`Export failed: ${err.message}`, 'error');
        }
    }

    handleRunAnalysis() {
        this.close();
        ui.toast('Initiating 12-pillar legal analysis on updated facts...', 'info');

        // Pass updated facts to analysis runner
        const activeFacts = {
            ...(this.docIntel?.all_facts || {}),
            ...(window.state?.caseData || {}),
            ...this.caseData
        };

        const cleanFacts = (typeof window.normalizeCaseFacts === 'function')
            ? window.normalizeCaseFacts(activeFacts)
            : activeFacts;

        if (typeof window.startCaseAnalysis === 'function') {
            window.startCaseAnalysis(cleanFacts);
        } else if (typeof window.runAnalysis === 'function') {
            window.runAnalysis(cleanFacts);
        } else {
            console.log('Case analysis initiated with facts:', cleanFacts);
            ui.toast('Updated case facts loaded into analysis wizard.', 'success');
        }
    }

    formatMarkdown(text) {
        if (!text) return '';
        let escaped = escapeHtml(text);

        // Section Headers
        escaped = escaped.replace(/^### (.*$)/gim, '<h4 class="case-rag-h4">$1</h4>');
        escaped = escaped.replace(/^## (.*$)/gim, '<h3 class="case-rag-h3">$1</h3>');
        escaped = escaped.replace(/^# (.*$)/gim, '<h2 class="case-rag-h2">$1</h2>');

        // Bold & Italic
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/__(.*?)__/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*([^\*]+?)\*/g, '<em>$1</em>');

        // Code / Citations / IDs
        escaped = escaped.replace(/`([^`]+)`/g, '<code class="case-rag-code">$1</code>');

        // Dividers
        escaped = escaped.replace(/^---$/gim, '<hr class="case-rag-hr">');

        // Parse lists line by line
        const lines = escaped.split('\n');
        let inUl = false;
        let inOl = false;
        let result = [];

        for (let line of lines) {
            const trimmed = line.trim();
            const isBullet = trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ');
            const isNumber = /^\d+\.\s/.test(trimmed);

            if (isBullet) {
                if (!inUl) {
                    if (inOl) { result.push('</ol>'); inOl = false; }
                    result.push('<ul class="case-rag-list">');
                    inUl = true;
                }
                const content = trimmed.replace(/^(\*|-|•)\s+/, '');
                result.push(`<li>${content}</li>`);
            } else if (isNumber) {
                if (!inOl) {
                    if (inUl) { result.push('</ul>'); inUl = false; }
                    result.push('<ol class="case-rag-list">');
                    inOl = true;
                }
                const content = trimmed.replace(/^\d+\.\s+/, '');
                result.push(`<li>${content}</li>`);
            } else {
                if (inUl) { result.push('</ul>'); inUl = false; }
                if (inOl) { result.push('</ol>'); inOl = false; }
                result.push(line);
            }
        }
        if (inUl) result.push('</ul>');
        if (inOl) result.push('</ol>');

        return result.join('<br>')
            .replace(/<br><(ul|ol|hr|h2|h3|h4)/g, '<$1')
            .replace(/<\/(ul|ol|hr|h2|h3|h4)><br>/g, '</$1>');
    }

    addMessage(text, sender, citations = [], proposedUpdates = [], trackInHistory = true) {
        const body = document.getElementById('ragChatBody');
        if (!body) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = `case-rag-msg ${sender}`;

        // Format rich markdown (headings, bold, lists, code)
        msgDiv.innerHTML = this.formatMarkdown(text);

        // Render Citations with clean icons
        if (citations && citations.length > 0) {
            const citDiv = document.createElement('div');
            citDiv.className = 'case-rag-citations';
            citations.forEach(c => {
                const span = document.createElement('span');
                span.className = 'case-rag-citation-chip';
                let icon = 'fas fa-quote-left';
                if (/section|कलम|धारा/i.test(c)) icon = 'fas fa-book-bookmark';
                else if (/\.(pdf|jpg|jpeg|png|tiff)/i.test(c)) icon = 'fas fa-file-lines';
                span.innerHTML = `<i class="${icon}"></i> ${escapeHtml(c)}`;
                citDiv.appendChild(span);
            });
            msgDiv.appendChild(citDiv);
        }

        // Render Fact Update Cards
        if (proposedUpdates && proposedUpdates.length > 0) {
            proposedUpdates.forEach(u => {
                const card = document.createElement('div');
                card.className = 'case-rag-fact-card';
                card.innerHTML = `
                    <div>
                        <strong><i class="fas fa-edit"></i> Proposed Fact Update:</strong>
                        <span>${escapeHtml(u.label || u.field)}: <em>${escapeHtml(String(u.old_value || 'None'))}</em> ➔ <strong>${escapeHtml(String(u.value))}</strong></span>
                    </div>
                    <div class="case-rag-fact-actions">
                        <button class="btn-fact-apply"><i class="fas fa-check"></i> Apply to Case</button>
                        <button class="btn-fact-dismiss">Dismiss</button>
                    </div>
                `;

                card.querySelector('.btn-fact-apply').addEventListener('click', () => {
                    this.applyFactUpdate(u.field, u.value, card);
                });
                card.querySelector('.btn-fact-dismiss').addEventListener('click', () => {
                    card.remove();
                });

                msgDiv.appendChild(card);
            });
        }

        body.appendChild(msgDiv);
        body.scrollTop = body.scrollHeight;

        if (trackInHistory) {
            this.chatHistory.push({ role: sender === 'user' ? 'user' : 'model', parts: text });
        }
    }

    showTypingIndicator() {
        const body = document.getElementById('ragChatBody');
        if (!body) return;
        this.removeTypingIndicator();
        const typingDiv = document.createElement('div');
        typingDiv.className = 'case-rag-typing';
        typingDiv.id = 'ragTypingIndicator';
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        body.appendChild(typingDiv);
        body.scrollTop = body.scrollHeight;
    }

    removeTypingIndicator() {
        const el = document.getElementById('ragTypingIndicator');
        if (el) el.remove();
    }
}

// Global Singleton
export const caseRagWorkspace = new CaseRagChatWorkspace();

// Wire to window for easy access from other modules
if (typeof window !== 'undefined') {
    window.caseRagWorkspace = caseRagWorkspace;
    window.openCaseRagChat = (caseData, docIntel) => {
        caseRagWorkspace.open(caseData, docIntel);
    };
    window.closeCaseRagChat = () => {
        caseRagWorkspace.close();
    };
}
