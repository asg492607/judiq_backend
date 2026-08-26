import { firebaseConfig, roleActions, wizardSteps } from '../config.js?v=14';
import { api } from '../api.js?v=14';
import { ui, switchScreen } from '../ui.js?v=14';
import { renderWizardStep } from '../wizard.js?v=14';
import { renderResults, switchResultTab } from '../renderer.js?v=14';
import { DRAFT_TYPES, formatDraftDate, numberToWords } from '../draft_templates.js?v=14';
import { escapeHtml } from './modules/utils.js?v=14';

// Import sub-modules to register their exports or initialize their global interfaces
import { JudiQModals } from './modules/modals.js?v=14';
import { renderAdversarialCharts, renderScoreBreakdownChart } from './modules/charts.js?v=14';
import { JudiQValidator } from './modules/validation.js?v=14';
import { JudiQCoCounselDock } from './modules/counsel_dock.js?v=14';
import { JudiQStrategySimulator } from './modules/simulator.js?v=14';


import { store } from './modules/store.js?v=14';

// Initialize Firebase
if (typeof firebase !== 'undefined') {
    firebase.initializeApp(firebaseConfig);
}
const auth = typeof firebase !== 'undefined' ? firebase.auth() : null;

// Enterprise Reactive State Initialization
store.attachGlobalProxy();

// Expose charts to window for switchResultTab access
window.renderAdversarialCharts = renderAdversarialCharts;
window.renderScoreBreakdownChart = renderScoreBreakdownChart;

/**
 * Initialize the application
 */
document.addEventListener('DOMContentLoaded', () => {
    setupAuthListeners();
    setupFormListeners();
    initTheme();
    
    // Initialize Co-Counsel Dock & Strategy Simulator
    window.judiqDock = new JudiQCoCounselDock();
    window.judiqSimulator = new JudiQStrategySimulator();

    const loadingScreen = document.getElementById('loadingScreen');
    if (loadingScreen) {
        ui.hide('loadingScreen');
    }
    if (window.calculateSandboxTimelines) {
        window.calculateSandboxTimelines();
    }

    // Scroll reveal observer
    const revealElements = document.querySelectorAll('.reveal-on-scroll');
    if (revealElements.length > 0 && 'IntersectionObserver' in window) {
        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.05,
            rootMargin: '0px 0px -40px 0px'
        });
        revealElements.forEach(el => revealObserver.observe(el));
    }

    // Initialize Readiness Checklist & Precedents
    if (window.updateReadinessProgress) {
        window.updateReadinessProgress();
    }
    if (window.filterPrecedentsList) {
        window.filterPrecedentsList();
    }
});

function setupAuthListeners() {
    // Bind click events for navigation
    const showRegisterEl = document.getElementById('showRegister');
    if (showRegisterEl) showRegisterEl.addEventListener('click', (e) => { e.preventDefault(); window.showRegister(); });

    const showLoginEl = document.getElementById('showLogin');
    if (showLoginEl) showLoginEl.addEventListener('click', (e) => { e.preventDefault(); window.showLogin(); });

    const navLoginBtn = document.getElementById('navLoginBtn');
    if (navLoginBtn) navLoginBtn.addEventListener('click', () => window.showLogin());

    const navRegisterBtn = document.getElementById('navRegisterBtn');
    if (navRegisterBtn) navRegisterBtn.addEventListener('click', () => window.showRegister());

    const heroLoginBtn = document.getElementById('heroLoginBtn');
    if (heroLoginBtn) heroLoginBtn.addEventListener('click', () => window.showLogin());

    const heroGetStartedBtn = document.getElementById('heroGetStartedBtn');
    if (heroGetStartedBtn) heroGetStartedBtn.addEventListener('click', () => window.showRegister());

    const mobileNavLoginBtn = document.getElementById('mobileNavLoginBtn');
    if (mobileNavLoginBtn) mobileNavLoginBtn.addEventListener('click', () => { window.toggleMobileNav(false); window.showLogin(); });

    const mobileNavRegisterBtn = document.getElementById('mobileNavRegisterBtn');
    if (mobileNavRegisterBtn) mobileNavRegisterBtn.addEventListener('click', () => { window.toggleMobileNav(false); window.showRegister(); });

    if (!auth) {
        // Fallback for non-Firebase environment (dev/offline testing)
        console.warn('Firebase is not available, running in offline/demo mode.');
        const mockUser = { email: 'demo@judiq.ai', uid: 'demo_user_123' };
        window.state.currentUser = mockUser;
        ui.setText('userEmail', mockUser.email);
        window.selectRole('law_firm');
        return;
    }

    auth.onAuthStateChanged(user => {
        window.state.currentUser = user;
        if (user) {
            const userEmailEl = document.getElementById('userEmail');
            if (userEmailEl) ui.setText('userEmail', user.email);

            // Read permanently locked domain (defaults to ni_act for legacy accounts)
            const savedDomain = localStorage.getItem(`judiq_domain_${user.uid}`) || 'ni_act';
            window.state.userDomain = savedDomain;

            const savedRole = localStorage.getItem(`judiq_role_${user.uid}`);
            if (savedRole) {
                window.state.currentRole = savedRole;
                renderDashboard();
                switchScreen('dashboardScreen');
            } else {
                // Apply domain class to role screen before showing it
                const roleScreen = document.getElementById('roleScreen');
                if (roleScreen) {
                    roleScreen.classList.remove('role-screen--sarfaesi', 'role-screen--ni');
                    if (savedDomain === 'sarfaesi') roleScreen.classList.add('role-screen--sarfaesi');
                }
                switchScreen('roleScreen');
            }
        } else {
            switchScreen('landingScreen');
        }
    });
}

export function loginLocally(email, domain = 'ni_act', role = 'law_firm') {
    const cleanEmail = (email && email.trim()) || 'advocate@judiq.ai';
    const uid = 'user_' + Math.abs(cleanEmail.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a; }, 0)).toString(36);
    const mockUser = {
        email: cleanEmail,
        uid: uid,
        displayName: cleanEmail.split('@')[0]
    };
    window.state.currentUser = mockUser;
    
    // Save domain
    const savedDomain = localStorage.getItem(`judiq_domain_${uid}`) || domain || 'ni_act';
    localStorage.setItem(`judiq_domain_${uid}`, savedDomain);
    window.state.userDomain = savedDomain;
    
    // Save role
    const savedRole = localStorage.getItem(`judiq_role_${uid}`) || role || 'law_firm';
    localStorage.setItem(`judiq_role_${uid}`, savedRole);
    window.state.currentRole = savedRole;
    
    const userEmailEl = document.getElementById('userEmail');
    if (userEmailEl) ui.setText('userEmail', mockUser.email);
    
    renderDashboard();
    switchScreen('dashboardScreen');
    if (window.ui && typeof window.ui.toast === 'function') {
        window.ui.toast(`Signed in as ${cleanEmail}`, 'success');
    }
}

window.loginAsGuest = (domain = 'ni_act') => {
    loginLocally('advocate@judiq.ai', domain, 'law_firm');
};

function setupFormListeners() {
    const loginForm = document.getElementById('loginForm');
    const loginError = document.getElementById('loginError');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('loginEmail').value.trim();
            const pass = document.getElementById('loginPassword').value;
            const btn = loginForm.querySelector('button[type="submit"]');

            if (loginError) {
                loginError.textContent = '';
                loginError.classList.remove('show');
            }
            if (btn) btn.classList.add('loading');
            
            try {
                if (auth && typeof auth.signInWithEmailAndPassword === 'function') {
                    try {
                        await auth.signInWithEmailAndPassword(email, pass);
                    } catch (signInErr) {
                        const code = (signInErr?.code || '').toLowerCase();
                        const msg = (signInErr?.message || '').toLowerCase();
                        
                        // If Firebase Auth provider is not enabled in Firebase Console (e.g. OPERATION_NOT_ALLOWED, API_KEY_INVALID, etc.)
                        if (code.includes('operation-not-allowed') || code.includes('api-key') || code.includes('project-not-found') || code.includes('configuration-not-found') || code.includes('unauthorized-domain') || msg.includes('operation_not_allowed')) {
                            console.info('Firebase Auth project provider disabled, seamlessly activating local advocate session:', signInErr?.message || signInErr);
                            loginLocally(email);
                        } else if (code.includes('invalid-login-credentials') || code.includes('user-not-found')) {
                            try {
                                const cred = await auth.createUserWithEmailAndPassword(email, pass);
                                const defaultDomain = 'all';
                                localStorage.setItem(`judiq_domain_${cred.user.uid}`, defaultDomain);
                                window.state.userDomain = defaultDomain;
                                if (window.ui && typeof window.ui.toast === 'function') {
                                    window.ui.toast(`Account created for ${email}`, 'success');
                                }
                            } catch (createErr) {
                                const createCode = (createErr?.code || '').toLowerCase();
                                if (createCode.includes('email-already-in-use') || createCode.includes('wrong-password')) {
                                    if (loginError) {
                                        loginError.textContent = "Incorrect password for this existing account.";
                                        loginError.classList.add('show');
                                    }
                                } else if (createCode.includes('weak-password')) {
                                    if (loginError) {
                                        loginError.textContent = "Password should be at least 6 characters.";
                                        loginError.classList.add('show');
                                    }
                                } else {
                                    // Seamless local fallback
                                    loginLocally(email);
                                }
                            }
                        } else if (code.includes('wrong-password')) {
                            if (loginError) {
                                loginError.textContent = "Incorrect password. Please try again.";
                                loginError.classList.add('show');
                            }
                        } else if (code.includes('invalid-email')) {
                            if (loginError) {
                                loginError.textContent = "Please enter a valid email address.";
                                loginError.classList.add('show');
                            }
                        } else {
                            loginLocally(email);
                        }
                    }
                } else {
                    loginLocally(email);
                }
            } catch (err) {
                console.info('Activating local user session:', err?.message || err);
                loginLocally(email);
            } finally {
                if (btn) btn.classList.remove('loading');
            }
        });
    }

    const registerForm = document.getElementById('registerForm');
    const registerError = document.getElementById('registerError');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('registerEmail').value.trim();
            const pass = document.getElementById('registerPassword').value;
            const confirmPass = document.getElementById('registerConfirmPassword').value;
            const domain = document.getElementById('registerDomain')?.value || 'ni_act';
            const btn = registerForm.querySelector('button[type="submit"]');

            if (registerError) {
                registerError.textContent = '';
                registerError.classList.remove('show');
            }

            if (pass !== confirmPass) {
                if (registerError) {
                    registerError.textContent = "Passwords do not match";
                    registerError.classList.add('show');
                }
                return;
            }

            // Domain must be selected — one-time permanent lock
            if (!domain) {
                const errEl = document.getElementById('domainPickerError');
                if (errEl) errEl.classList.add('visible');
                return;
            }

            if (btn) btn.classList.add('loading');

            try {
                if (auth && typeof auth.createUserWithEmailAndPassword === 'function') {
                    const cred = await auth.createUserWithEmailAndPassword(email, pass);
                    localStorage.setItem(`judiq_domain_${cred.user.uid}`, domain);
                    window.state.userDomain = domain;
                } else {
                    loginLocally(email, domain);
                }
            } catch (err) {
                const code = err?.code || '';
                if (code.includes('email-already-in-use')) {
                    if (registerError) {
                        registerError.textContent = "An account with this email already exists. Please sign in instead.";
                        registerError.classList.add('show');
                    }
                } else if (code.includes('weak-password')) {
                    if (registerError) {
                        registerError.textContent = "Password is too weak. Please use at least 6 characters.";
                        registerError.classList.add('show');
                    }
                } else if (code.includes('invalid-email')) {
                    if (registerError) {
                        registerError.textContent = "Please enter a valid email address.";
                        registerError.classList.add('show');
                    }
                } else {
                    console.info('Firebase registration unavailable, creating local user session:', err?.message || err);
                    loginLocally(email, domain);
                }
            } finally {
                if (btn) btn.classList.remove('loading');
            }
        });
    }
}

/**
 * Global navigation exports for HTML onclick bindings
 */
window.showLogin = () => switchScreen('loginScreen');
window.showRegister = () => switchScreen('registerScreen');
window.showLanding = () => switchScreen('landingScreen');
window.showTerms = () => switchScreen('termsScreen');
window.showPrivacy = () => switchScreen('privacyScreen');
window.showRefund = () => switchScreen('refundScreen');
window.showDashboard = () => switchScreen('dashboardScreen');

/**
 * Domain picker — called from register screen onclick
 * Supports all 6 domain options with immediate visual feedback
 */
window.selectRegisterDomain = (domain) => {
    const domainCards = ['all', 'composite', 'ni', 'sarfaesi', 'criminal', 'civil'];
    domainCards.forEach(d => {
        const card = document.getElementById(`domainCard_${d}`);
        if (card) card.classList.remove('selected--all', 'selected--composite', 'selected--ni', 'selected--sarfaesi', 'selected--criminal', 'selected--civil');
    });

    const activeCard = document.getElementById(`domainCard_${domain === 'ni_act' ? 'ni' : domain}`);
    if (activeCard) {
        activeCard.classList.add(`selected--${domain === 'ni_act' ? 'ni' : domain}`);
    }

    const input = document.getElementById('registerDomain');
    if (input) input.value = domain;

    const errEl = document.getElementById('domainPickerError');
    if (errEl) errEl.classList.remove('visible');
};

/**
 * Switch active legal domain dynamically inside dashboard
 */
window.switchUserDomain = (domain, tabEl) => {
    window.state.userDomain = domain;
    if (window.state.currentUser) {
        localStorage.setItem(`judiq_domain_${window.state.currentUser.uid}`, domain);
    }
    document.querySelectorAll('.domain-switch-tab').forEach(t => t.classList.remove('active'));
    if (tabEl) {
        tabEl.classList.add('active');
    } else {
        const targetTab = document.getElementById(`tab_domain_${domain === 'ni_act' ? 'ni' : domain}`);
        if (targetTab) targetTab.classList.add('active');
    }
    renderDashboard();
    if (window.ui && typeof window.ui.toast === 'function') {
        const names = {
            all: 'Full Practice (All Modules)',
            composite: 'Multi-Track (SARFAESI + 138 + Criminal)',
            ni_act: 'Section 138 Cheque Bounce',
            sarfaesi: 'SARFAESI / DRT Enforcement',
            criminal: 'Criminal Law (BNS / IPC)',
            civil: 'Civil & Commercial Suits'
        };
        window.ui.toast(`Switched to ${names[domain] || domain}`, 'info');
    }
};

window.logout = () => {
    if (auth && typeof auth.signOut === 'function') {
        auth.signOut().catch(() => {});
    }
    window.state.currentUser = null;
    switchScreen('landingScreen');
    if (window.ui && typeof window.ui.toast === 'function') {
        window.ui.toast('Logged out successfully', 'info');
    }
};

window.selectRole = (role) => {
    window.state.currentRole = role;
    if (window.state.currentUser) {
        localStorage.setItem(`judiq_role_${window.state.currentUser.uid}`, role);
    }
    renderDashboard();
    switchScreen('dashboardScreen');
};

function renderDashboard() {
    const role = window.state.currentRole || 'citizen';
    const domain = (window.state.userDomain || 'all').toLowerCase();

    // Update active tab highlight in quick-switch bar
    document.querySelectorAll('.domain-switch-tab').forEach(t => t.classList.remove('active'));
    const activeTab = document.getElementById(`tab_domain_${domain === 'ni_act' ? 'ni' : domain}`) || document.getElementById('tab_domain_all');
    if (activeTab) activeTab.classList.add('active');

    // Domain badge in dashboard nav
    const dashNav = document.querySelector('#dashboardScreen .nav-brand');
    if (dashNav) {
        let badge = dashNav.querySelector('.domain-badge');
        if (!badge) {
            badge = document.createElement('span');
            dashNav.appendChild(badge);
        }
        if (domain === 'composite') {
            badge.className = 'domain-badge domain-badge--composite';
            badge.innerHTML = '<i class="fas fa-bolt"></i> Multi-Track Composite';
        } else if (domain === 'criminal') {
            badge.className = 'domain-badge domain-badge--criminal';
            badge.innerHTML = '<i class="fas fa-user-shield"></i> Criminal Law (IPC/BNS)';
        } else if (domain === 'civil') {
            badge.className = 'domain-badge domain-badge--civil';
            badge.innerHTML = '<i class="fas fa-balance-scale"></i> Civil / CPC Litigation';
        } else if (domain === 'sarfaesi') {
            badge.className = 'domain-badge domain-badge--sarfaesi';
            badge.innerHTML = '<i class="fas fa-university"></i> SARFAESI / DRT';
        } else if (domain === 'ni_act') {
            badge.className = 'domain-badge domain-badge--ni';
            badge.innerHTML = '<i class="fas fa-file-invoice-dollar"></i> NI Act — S.138';
        } else {
            badge.className = 'domain-badge domain-badge--all';
            badge.innerHTML = '<i class="fas fa-layer-group"></i> Full Practice OS (All Domains)';
        }
    }

    // Domain-specific stats and actions
    const grid = document.getElementById('actionCardsGrid');
    if (grid) {
        const allCases = JSON.parse(localStorage.getItem('judiq_recent_cases_v1') || '[]');
        
        if (domain === 'composite') {
            const domainCases = allCases.filter(c => c.domain === 'composite' || (c.case_data && String(c.case_data.case_type).toLowerCase().includes('composite')));
            const total = domainCases.length;

            grid.innerHTML = `
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-bolt" style="color:#f59e0b;"></i>
                    <h3>Multi-Track Concurrent Legal Action (SARFAESI + 138 + Criminal)</h3>
                </div>
                <div class="domain-stats-grid" style="grid-column:1/-1;">
                    <div class="domain-stat-card" style="border-left: 4px solid #f59e0b;">
                        <div class="dsc-icon"><i class="fas fa-layer-group" style="color:#f59e0b;"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${total}</div><div class="dsc-label">Multi-Track Matters Evaluated</div></div>
                    </div>
                    <div class="domain-stat-card" style="border-left: 4px solid #10b981;">
                        <div class="dsc-icon"><i class="fas fa-sync" style="color:#10b981;"></i></div>
                        <div class="dsc-content"><div class="dsc-value">3 Tracks</div><div class="dsc-label">Concurrent Statutory Engines</div></div>
                    </div>
                </div>
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-rocket" style="color:#f59e0b;"></i>
                    <h3>Multi-Track Quick Actions</h3>
                </div>
                <div class="domain-actions-grid" style="grid-column:1/-1;">
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'Multi-Track (SARFAESI + 138 + Criminal)'})">
                        <div class="dac-icon" style="color:#f59e0b;"><i class="fas fa-bolt"></i></div>
                        <div class="dac-title">Run Unified Multi-Track Analysis</div>
                        <div class="dac-sub">Simultaneously evaluate SARFAESI asset recovery, Sec 138 cheque prosecution, and Criminal cheating charges on a single loan account.</div>
                    </div>
                    <div class="domain-action-card" onclick="window.loadCompositeDemoCase()">
                        <div class="dac-icon" style="color:#10b981;"><i class="fas fa-file-invoice"></i></div>
                        <div class="dac-title">Load Multi-Track Demo Scenario</div>
                        <div class="dac-sub">Pre-populate a high-value loan default with concurrent cheque bounce & SARFAESI actions.</div>
                    </div>
                    <div class="domain-action-card" onclick="window.showDraftStudio()" style="border: 2px solid rgba(16,185,129,0.35); background: rgba(16,185,129,0.05);">
                        <div class="dac-icon" style="color:#10b981;"><i class="fas fa-file-contract"></i></div>
                        <div class="dac-title">Generate Legal Draft</div>
                        <div class="dac-sub">Open the Draft Studio — 13 court-ready documents: notices, complaints, affidavits & SARFAESI notices.</div>
                    </div>
                </div>
            `;
        } else if (domain === 'criminal') {
            const domainCases = allCases.filter(c => c.domain === 'criminal' || (c.case_data && c.case_data.case_type === 'criminal'));
            const total = domainCases.length;
            const highBail = domainCases.filter(c => c.analysis_result && c.analysis_result.bail_assessment && c.analysis_result.bail_assessment.probability === 'HIGH').length;

            grid.innerHTML = `
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-user-shield" style="color:#ef4444;"></i>
                    <h3>Criminal Law Intelligence Overview</h3>
                </div>
                <div class="domain-stats-grid" style="grid-column:1/-1;">
                    <div class="domain-stat-card domain-stat-card--criminal" style="border-left: 4px solid #ef4444;">
                        <div class="dsc-icon"><i class="fas fa-gavel" style="color:#ef4444;"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${total}</div><div class="dsc-label">Criminal Cases Analyzed</div></div>
                    </div>
                    <div class="domain-stat-card domain-stat-card--criminal" style="border-left: 4px solid #10b981;">
                        <div class="dsc-icon"><i class="fas fa-key" style="color:#10b981;"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${highBail}</div><div class="dsc-label">High Bail Probability</div></div>
                    </div>
                </div>
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-bolt" style="color:#f59e0b;"></i>
                    <h3>Quick Actions</h3>
                </div>
                <div class="domain-actions-grid" style="grid-column:1/-1;">
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'Criminal'})">
                        <div class="dac-icon" style="color:#ef4444;"><i class="fas fa-search"></i></div>
                        <div class="dac-title">Analyse Criminal Case</div>
                        <div class="dac-sub">IPC/BNS & CrPC/BNSS audit, S.438 Bail & S.482 Bhajan Lal Quashing</div>
                    </div>
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'Criminal', offense_type:'420', contract_exists:true})">
                        <div class="dac-icon" style="color:#f59e0b;"><i class="fas fa-balance-scale"></i></div>
                        <div class="dac-title">S.420 / Civil Dispute Audit</div>
                        <div class="dac-sub">Test civil dispute quashing grounds under Bhajan Lal & Hridaya Ranjan precedent</div>
                    </div>
                    <div class="domain-action-card" onclick="window.loadCriminalDemoCase()">
                        <div class="dac-icon" style="color:#ef4444;"><i class="fas fa-file-invoice"></i></div>
                        <div class="dac-title">Load Demo Criminal Case</div>
                        <div class="dac-sub">Pre-fill S.420/406 IPC financial fraud scenario with quashing defence grounds</div>
                    </div>
                    <div class="domain-action-card" onclick="window.showDraftStudio()" style="border: 2px solid rgba(16,185,129,0.35); background: rgba(16,185,129,0.05);">
                        <div class="dac-icon" style="color:#10b981;"><i class="fas fa-file-contract"></i></div>
                        <div class="dac-title">Generate Legal Draft</div>
                        <div class="dac-sub">Open Draft Studio — generate criminal complaints, bail petitions, affidavits & BSA certificates.</div>
                    </div>
                </div>
            `;
        } else if (domain === 'civil') {
            const domainCases = allCases.filter(c => c.domain === 'civil' || (c.case_data && c.case_data.case_type === 'civil'));
            const total = domainCases.length;

            grid.innerHTML = `
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-balance-scale" style="color:#8b5cf6;"></i>
                    <h3>Civil & Commercial Litigation Overview</h3>
                </div>
                <div class="domain-stats-grid" style="grid-column:1/-1;">
                    <div class="domain-stat-card" style="border-left: 4px solid #8b5cf6;">
                        <div class="dsc-icon"><i class="fas fa-file-alt" style="color:#8b5cf6;"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${total}</div><div class="dsc-label">Civil Suits Analyzed</div></div>
                    </div>
                </div>
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-bolt" style="color:#f59e0b;"></i>
                    <h3>Quick Actions</h3>
                </div>
                <div class="domain-actions-grid" style="grid-column:1/-1;">
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'Civil'})">
                        <div class="dac-icon" style="color:#8b5cf6;"><i class="fas fa-search"></i></div>
                        <div class="dac-title">Analyse Civil Suit</div>
                        <div class="dac-sub">CPC Plaint, Written Statement, Order 39 Injunction & Limitation Audit</div>
                    </div>
                    <div class="domain-action-card" onclick="window.loadCivilDemoCase()">
                        <div class="dac-icon" style="color:#8b5cf6;"><i class="fas fa-file-invoice"></i></div>
                        <div class="dac-title">Load Demo Civil Suit</div>
                        <div class="dac-sub">Pre-fill Commercial Specific Performance suit with Order 39 interim injunction</div>
                    </div>
                    <div class="domain-action-card" onclick="window.showDraftStudio()" style="border: 2px solid rgba(16,185,129,0.35); background: rgba(16,185,129,0.05);">
                        <div class="dac-icon" style="color:#10b981;"><i class="fas fa-file-contract"></i></div>
                        <div class="dac-title">Generate Legal Draft</div>
                        <div class="dac-sub">Open Draft Studio — generate plaints, written statements, affidavits & interim injunctions.</div>
                    </div>
                </div>
            `;
        } else if (domain === 'sarfaesi') {
            const domainCases = allCases.filter(c => c.domain === 'sarfaesi');
            const npaCases = domainCases.length;
            const cersaiIssues = domainCases.filter(c => c.case_data && c.case_data.cersai_registered === false).length;
            const highRisk = domainCases.filter(c => c.risk_level === 'CRITICAL').length;

            grid.innerHTML = `
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-chart-bar" style="color:#10b981;"></i>
                    <h3>Account Overview</h3>
                </div>
                <div class="domain-stats-grid" style="grid-column:1/-1;">
                    <div class="domain-stat-card domain-stat-card--sarfaesi">
                        <div class="dsc-icon dsc-icon--sarfaesi"><i class="fas fa-file-invoice"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${npaCases}</div><div class="dsc-label">NPA Cases Analyzed</div></div>
                    </div>
                    <div class="domain-stat-card domain-stat-card--sarfaesi">
                        <div class="dsc-icon dsc-icon--sarfaesi"><i class="fas fa-shield-alt"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${cersaiIssues}</div><div class="dsc-label">CERSAI Issues</div></div>
                    </div>
                    <div class="domain-stat-card domain-stat-card--sarfaesi">
                        <div class="dsc-icon dsc-icon--sarfaesi"><i class="fas fa-exclamation-triangle"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${highRisk}</div><div class="dsc-label">High-Risk Accounts</div></div>
                    </div>
                </div>
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-bolt" style="color:#10b981;"></i>
                    <h3>Quick Actions</h3>
                </div>
                <div class="domain-actions-grid" style="grid-column:1/-1;">
                    <div class="domain-action-card domain-action-card--sarfaesi" onclick="startCaseAnalysis({case_type:'SARFAESI'})">
                        <div class="dac-icon dac-icon--sarfaesi"><i class="fas fa-search"></i></div>
                        <div class="dac-title">Analyse SARFAESI Case</div>
                        <div class="dac-sub">Run full NPA enforcement audit — CERSAI, S.13(2), S.14, DRT</div>
                    </div>
                    <div class="domain-action-card" onclick="window.loadSarfaesiDemoCase()">
                        <div class="dac-icon" style="color:#f59e0b;"><i class="fas fa-building"></i></div>
                        <div class="dac-title">Load Demo SARFAESI Case</div>
                        <div class="dac-sub">Pre-fill a commercial real-estate NPA scenario with full S.13 enforcement details</div>
                    </div>
                    <div class="domain-action-card" onclick="window.showDraftStudio()" style="border: 2px solid rgba(16,185,129,0.35); background: rgba(16,185,129,0.05);">
                        <div class="dac-icon" style="color:#10b981;"><i class="fas fa-file-contract"></i></div>
                        <div class="dac-title">Generate Legal Draft</div>
                        <div class="dac-sub">Open Draft Studio — generate SARFAESI s.13(2) notices, DRT applications & possession letters.</div>
                    </div>
                </div>
            `;
        } else if (domain === 'ni_act') {
            const domainCases = allCases.filter(c => !c.domain || c.domain === 'ni_act');
            const totalCases = domainCases.length;
            const fatalCases = domainCases.filter(c => c.verdict === 'DO NOT FILE').length;
            const strongCases = domainCases.filter(c => (c.score || 0) >= 70).length;

            grid.innerHTML = `
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-chart-bar" style="color:#3b82f6;"></i>
                    <h3>Account Overview</h3>
                </div>
                <div class="domain-stats-grid" style="grid-column:1/-1;">
                    <div class="domain-stat-card domain-stat-card--ni">
                        <div class="dsc-icon dsc-icon--ni"><i class="fas fa-gavel"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${totalCases}</div><div class="dsc-label">Cases Analysed</div></div>
                    </div>
                    <div class="domain-stat-card domain-stat-card--ni">
                        <div class="dsc-icon dsc-icon--ni"><i class="fas fa-check-circle"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${strongCases}</div><div class="dsc-label">Strong Cases (≥70)</div></div>
                    </div>
                    <div class="domain-stat-card domain-stat-card--ni">
                        <div class="dsc-icon dsc-icon--ni"><i class="fas fa-times-circle"></i></div>
                        <div class="dsc-content"><div class="dsc-value">${fatalCases}</div><div class="dsc-label">Fatal Defects Found</div></div>
                    </div>
                </div>
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-bolt" style="color:#3b82f6;"></i>
                    <h3>Quick Actions</h3>
                </div>
                <div class="domain-actions-grid" style="grid-column:1/-1;">
                    <div class="domain-action-card domain-action-card--ni" onclick="startCaseAnalysis({case_type:'Cheque Bounce'})">
                        <div class="dac-icon dac-icon--ni"><i class="fas fa-search"></i></div>
                        <div class="dac-title">Analyse S.138 Case</div>
                        <div class="dac-sub">Run adversarial weakness scan — Limitation, Notice, Instrument, Debt</div>
                    </div>
                    <div class="domain-action-card domain-action-card--ni" onclick="loadDemoCase()">
                        <div class="dac-icon dac-icon--ni"><i class="fas fa-bolt"></i></div>
                        <div class="dac-title">Load Demo Case</div>
                        <div class="dac-sub">Instantly preview a pre-populated cheque bounce scenario</div>
                    </div>
                    <div class="domain-action-card" onclick="window.showDraftStudio()" style="border: 2px solid rgba(16,185,129,0.35); background: rgba(16,185,129,0.05);">
                        <div class="dac-icon" style="color:#10b981;"><i class="fas fa-file-contract"></i></div>
                        <div class="dac-title">Generate Legal Draft</div>
                        <div class="dac-sub">Open Draft Studio — demand notices, criminal complaints, reply notices, affidavits & BSA certificates.</div>
                    </div>
                </div>
            `;
        } else {
            // "ALL" DOMAINS — Unified Multi-Domain Command Center
            const totalCases = allCases.length;
            grid.innerHTML = `
                <div class="domain-section-header" style="grid-column:1/-1;">
                    <i class="fas fa-layer-group" style="color:#38bdf8;"></i>
                    <h3>Institutional Litigation OS — All Legal Modules</h3>
                </div>
                <div class="domain-actions-grid" style="grid-column:1/-1; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));">
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'Multi-Track (SARFAESI + 138 + Criminal)'})" style="border: 2px solid rgba(245, 158, 11, 0.4); background: rgba(245, 158, 11, 0.05);">
                        <div class="dac-icon" style="color:#f59e0b;"><i class="fas fa-bolt"></i></div>
                        <div class="dac-title">Multi-Track Composite Action</div>
                        <div class="dac-sub">Evaluate SARFAESI + Section 138 + Criminal Fraud simultaneously on a single debt account.</div>
                    </div>
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'Cheque Bounce'})">
                        <div class="dac-icon" style="color:#3b82f6;"><i class="fas fa-file-invoice-dollar"></i></div>
                        <div class="dac-title">NI Act — Section 138</div>
                        <div class="dac-sub">Cheque dishonour memo, 30-day notice, S.139 presumption, and S.143A compensation.</div>
                    </div>
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'SARFAESI'})">
                        <div class="dac-icon" style="color:#10b981;"><i class="fas fa-university"></i></div>
                        <div class="dac-title">SARFAESI & DRT Recovery</div>
                        <div class="dac-sub">Secured asset enforcement, CERSAI verification, S.13(2)/13(4) notices, DM S.14 physical possession.</div>
                    </div>
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'Criminal'})">
                        <div class="dac-icon" style="color:#ef4444;"><i class="fas fa-user-shield"></i></div>
                        <div class="dac-title">Criminal Law (BNS & IPC)</div>
                        <div class="dac-sub">Cheating (S.318/420), CBT (S.316/406), Anticipatory/Regular Bail, and S.482 Quashing.</div>
                    </div>
                    <div class="domain-action-card" onclick="startCaseAnalysis({case_type:'Civil'})">
                        <div class="dac-icon" style="color:#8b5cf6;"><i class="fas fa-balance-scale"></i></div>
                        <div class="dac-title">Civil & Commercial Suits</div>
                        <div class="dac-sub">Specific performance, commercial debt recovery, and Order 39 interim injunctions.</div>
                    </div>
                    <div class="domain-action-card" onclick="window.showDraftStudio()" style="border: 2px solid rgba(16,185,129,0.35); background: rgba(16,185,129,0.05); grid-column: 1 / -1;">
                        <div class="dac-icon" style="color:#10b981;"><i class="fas fa-file-contract"></i></div>
                        <div class="dac-title" style="font-size: 1.05rem;">📄 Draft Studio — Generate Any Legal Document</div>
                        <div class="dac-sub">13 court-ready templates: demand notices, criminal complaints, bail petitions, SARFAESI s.13(2) notices, affidavits, BSA certificates, reply notices & more — enter your inputs and generate instantly.</div>
                    </div>
                </div>
            `;
        }
    }

    const roleBadge = document.getElementById('userRoleBadge');
    if (roleBadge) {
        roleBadge.textContent = role.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
        roleBadge.className = `user-role-badge role-${role}`;
    }

    // Personalization header greeting updates
    const greetingEl = document.getElementById('dashboardGreeting');
    const subtitleEl = document.getElementById('dashboardSubtitle');
    if (greetingEl && window.state.currentUser) {
        const uid = window.state.currentUser.uid;
        const savedProfileStr = localStorage.getItem(`judiq_profile_${uid}`);
        let name = window.state.currentUser.displayName || window.state.currentUser.email.split('@')[0];
        let firm = '';
        if (savedProfileStr) {
            try {
                const profile = JSON.parse(savedProfileStr);
                if (profile.displayName) name = profile.displayName;
                if (profile.firmName) firm = profile.firmName;
            } catch (_) {}
        }
        greetingEl.textContent = `Welcome, Counsel ${name}`;
        const domainLabels = {
            all: 'Full Practice Litigation Command Center',
            composite: 'Multi-Track Composite Platform',
            criminal: 'Criminal Law Platform',
            civil: 'Civil & Commercial Litigation Strategist',
            sarfaesi: 'SARFAESI / DRT Platform',
            ni_act: 'NI Act — Section 138 Platform'
        };
        const domainLabel = domainLabels[domain] || 'Institutional Legal Intelligence OS';
        if (subtitleEl) {
            subtitleEl.textContent = firm
                ? `${domainLabel} | ${firm} — Find the weakness before the courtroom does.`
                : `${domainLabel} — Find the weakness before the courtroom does.`;
        }
    }

    // Load domain-filtered recent activity
    if (window.loadRecentCases) {
        window.loadRecentCases();
    }
}

// Recent Cases / Activity History Management
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString(undefined, { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (_) {
        return dateStr;
    }
}

window.saveCaseToHistory = (caseData, analysisResult) => {
    try {
        const userId = window.state.currentUser ? window.state.currentUser.uid : 'ANONYMOUS';
        const caseId = caseData.case_id;
        if (!caseId) return;

        let localCases = [];
        try {
            localCases = JSON.parse(localStorage.getItem('judiq_recent_cases_v1') || '[]');
        } catch (_) {}

        const newCaseObj = {
            id: caseId,
            user_id: userId,
            domain: window.state.userDomain || 'ni_act',  // stamp domain permanently
            title: caseData.case_title || 'Untitled Case',
            date: new Date().toISOString(),
            score: analysisResult.score !== undefined ? analysisResult.score : 0,
            risk_level: analysisResult.risk_level || analysisResult.defence_risk || 'Unknown',
            verdict: analysisResult.verdict || 'Unknown',
            case_data: caseData,
            analysis_result: analysisResult
        };
        // Remove duplicates and put new one at the start
        localCases = localCases.filter(c => c.id !== caseId);
        localCases.unshift(newCaseObj);
        if (localCases.length > 20) {
            localCases.pop();
        }

        localStorage.setItem('judiq_recent_cases_v1', JSON.stringify(localCases));
        
        // Refresh dashboard view if it's currently rendered
        const recentCasesContainer = document.getElementById('recentCases');
        if (recentCasesContainer) {
            window.loadRecentCases();
        }
    } catch (err) {
        console.error('Failed to save case to history:', err);
    }
};

window.loadRecentCases = async () => {
    const container = document.getElementById('recentCases');
    if (!container) return;

    container.innerHTML = `
        <div style="display: flex; justify-content: center; align-items: center; padding: 2rem; color: var(--gray-500);">
            <i class="fas fa-spinner fa-spin" style="margin-right: 0.5rem;"></i> Loading recent activity...
        </div>
    `;

    try {
        let localCases = [];
        try {
            localCases = JSON.parse(localStorage.getItem('judiq_recent_cases_v1') || '[]');
        } catch (_) {}

        const userId = window.state.currentUser ? window.state.currentUser.uid : 'ANONYMOUS';
        const currentDomain = window.state.userDomain || 'ni_act';
        let backendCases = [];
        if (userId !== 'ANONYMOUS') {
            try {
                const res = await api.getRecentCases(userId);
                backendCases = Array.isArray(res) ? res : [];
            } catch (err) {
                console.warn('Failed to fetch recent cases from backend:', err);
            }
        }

        // Merge and de-duplicate by case ID
        const casesMap = new Map();

        // 1. Load backend case metadata
        backendCases.forEach(c => {
            casesMap.set(c.id, {
                id: c.id,
                user_id: c.user_id,
                title: c.title,
                date: c.date,
                score: c.score,
                risk_level: c.risk_level,
                verdict: c.verdict,
                fromBackend: true
            });
        });

        // 2. Overwrite / merge with local cases (which contain full details)
        localCases.forEach(c => {
            if (c.user_id === 'ANONYMOUS' || c.user_id === userId) {
                const existing = casesMap.get(c.id);
                casesMap.set(c.id, {
                    ...existing,
                    ...c,
                    fromBackend: existing ? true : false
                });
            }
        });

        const mergedCases = Array.from(casesMap.values())
            // Filter by user's domain — each user only sees their own domain's cases
            .filter(c => !c.domain || c.domain === currentDomain);
        mergedCases.sort((a, b) => new Date(b.date) - new Date(a.date));

        if (mergedCases.length === 0) {
            const emptyDiv = document.createElement('div');
            emptyDiv.style.cssText = 'text-align: center; padding: 2rem; border: 1px dashed var(--gray-300); border-radius: var(--radius-lg); color: var(--gray-400);';
            emptyDiv.innerHTML = '<i class="fas fa-folder-open" style="font-size: 1.5rem; margin-bottom: 0.5rem; display: block;"></i>No recent cases analyzed yet.';
            container.replaceChildren(emptyDiv);
            return;
        }

        container.replaceChildren(); // clear children safely

        mergedCases.forEach(c => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recent-case-item';
            itemDiv.style.cssText = 'display: flex; justify-content: space-between; align-items: center; width: 100%;';
            itemDiv.onclick = () => window.loadCaseFromHistory(c.id);

            const infoDiv = document.createElement('div');
            infoDiv.className = 'recent-case-info';
            
            const h4 = document.createElement('h4');
            h4.textContent = c.title || 'Untitled Case';
            
            const p = document.createElement('p');
            p.style.cssText = 'font-size: 0.75rem; color: var(--gray-400); margin-top: 0.25rem;';
            p.innerHTML = `ID: <strong>${escapeHtml(c.id)}</strong> | Updated: <strong>${formatDate(c.date)}</strong> | Verdict: <span style="color: var(--primary-400); font-weight: 600;">${escapeHtml(c.verdict)}</span>`;
            
            infoDiv.appendChild(h4);
            infoDiv.appendChild(p);

            const rightDiv = document.createElement('div');
            rightDiv.style.cssText = 'display: flex; align-items: center; gap: 1.5rem;';

            const scoreDiv = document.createElement('div');
            scoreDiv.className = 'recent-case-score';
            scoreDiv.style.cssText = 'min-width: 80px; text-align: center;';
            scoreDiv.textContent = `${c.score}/100`;

            const delBtn = document.createElement('button');
            delBtn.className = 'btn-delete-case';
            delBtn.title = 'Delete Case';
            delBtn.style.cssText = 'background: transparent; border: none; color: var(--error-500); cursor: pointer; padding: 0.5rem; font-size: 1rem; transition: color 0.2s; display: flex; align-items: center; justify-content: center;';
            delBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
            delBtn.onclick = (event) => {
                event.stopPropagation(); // Stop parent onclick
                window.deleteCaseFromHistory(c.id, event);
            };

            rightDiv.appendChild(scoreDiv);
            rightDiv.appendChild(delBtn);

            itemDiv.appendChild(infoDiv);
            itemDiv.appendChild(rightDiv);
            
            container.appendChild(itemDiv);
        });
    } catch (err) {
        console.error('Error rendering recent cases:', err);
        const errDiv = document.createElement('div');
        errDiv.style.cssText = 'color: var(--error-500); padding: 1rem;';
        errDiv.textContent = 'Failed to load recent cases.';
        container.replaceChildren(errDiv);
    }
};

window.loadCaseFromHistory = async (caseId) => {
    ui.show('analysisLoading');
    try {
        let localCases = [];
        try {
            localCases = JSON.parse(localStorage.getItem('judiq_recent_cases_v1') || '[]');
        } catch (_) {}

        const localCase = localCases.find(c => c.id === caseId);
        if (localCase && localCase.case_data && localCase.analysis_result) {
            window.state.caseData = localCase.case_data;
            window.state.analysisResult = localCase.analysis_result;
            ui.hide('analysisLoading');
            switchScreen('resultsScreen');
            renderResults(localCase.analysis_result);
            return;
        }

        const userId = window.state.currentUser ? window.state.currentUser.uid : 'ANONYMOUS';
        if (userId !== 'ANONYMOUS') {
            const response = await api.getCaseDetails(caseId, userId);
            if (response && response.case_data && response.analysis_result) {
                window.state.caseData = response.case_data;
                window.state.analysisResult = response.analysis_result;

                // Cache locally
                const newCaseObj = {
                    id: caseId,
                    user_id: userId,
                    title: response.case_data.case_title || 'Untitled Case',
                    date: new Date().toISOString(),
                    score: response.analysis_result.score !== undefined ? response.analysis_result.score : 0,
                    risk_level: response.analysis_result.risk_level || response.analysis_result.defence_risk || 'Unknown',
                    verdict: response.analysis_result.verdict || 'Unknown',
                    case_data: response.case_data,
                    analysis_result: response.analysis_result
                };
                localCases = localCases.filter(c => c.id !== caseId);
                localCases.unshift(newCaseObj);
                if (localCases.length > 20) localCases.pop();
                localStorage.setItem('judiq_recent_cases_v1', JSON.stringify(localCases));

                ui.hide('analysisLoading');
                switchScreen('resultsScreen');
                renderResults(response.analysis_result);
                return;
            }
        }
        throw new Error('Case details could not be retrieved.');
    } catch (err) {
        ui.hide('analysisLoading');
        ui.toast(err.message, 'error');
    }
};

window.deleteCaseFromHistory = async (caseId, event) => {
    if (event) event.stopPropagation();

    if (!confirm(`Are you sure you want to delete case ${caseId} from history?`)) {
        return;
    }

    try {
        let localCases = [];
        try {
            localCases = JSON.parse(localStorage.getItem('judiq_recent_cases_v1') || '[]');
        } catch (_) {}
        localCases = localCases.filter(c => c.id !== caseId);
        localStorage.setItem('judiq_recent_cases_v1', JSON.stringify(localCases));

        const userId = window.state.currentUser ? window.state.currentUser.uid : 'ANONYMOUS';
        if (userId !== 'ANONYMOUS') {
            await api.deleteCase(caseId, userId);
        }

        ui.toast('Case successfully removed from history.', 'success');
        window.loadRecentCases();
    } catch (err) {
        console.error('Failed to delete case:', err);
        ui.toast('Error deleting case.', 'error');
        window.loadRecentCases();
    }
};

// Wizard starting function
window.startCaseAnalysis = (initialData = null) => {
    window.state = window.state || {};
    let flatData = initialData ? (typeof window.flattenDemoData === 'function' ? window.flattenDemoData(initialData) : { ...initialData }) : {};
    window.state.currentStep = 1;
    window.state.caseData = flatData;
    try {
        localStorage.setItem('judiq_wizard_autosave', JSON.stringify(window.state.caseData));
    } catch (_) {}
    
    switchScreen('caseWizardScreen');
    if (typeof renderWizardStep === 'function') {
        renderWizardStep();
    }
};

window.setUserDomain = (domain) => {
    window.state = window.state || {};
    window.state.userDomain = domain;
    if (window.state.currentUser) {
        localStorage.setItem(`judiq_domain_${window.state.currentUser.uid}`, domain);
    }
    renderDashboard();
    if (window.ui && typeof window.ui.toast === 'function') {
        window.ui.toast(`Switched domain to ${domain.toUpperCase()}`, 'info');
    }
};

/**
 * Expose modal functions
 */
window.openLegalModal = (modalId, event) => {
    if (event) event.preventDefault();
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
    }
};
window.closeLegalModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
    }
};

// Close legal modal when clicking outside its content container
window.addEventListener('click', (event) => {
    if (event.target.classList.contains('legal-modal')) {
        event.target.classList.add('hidden');
    }
});

/**
 * Quick Analysis Mode Functions
 */
window.runQuickAnalysis = async () => {
    const amountEl = document.getElementById('qAmount');
    const chequeDateEl = document.getElementById('qChequeDate');
    const noticeDateEl = document.getElementById('qNoticeDate');
    const filingDateEl = document.getElementById('qFilingDate');
    const complainantEl = document.getElementById('qComplainant');
    const accusedEl = document.getElementById('qAccused');

    if (!amountEl || !chequeDateEl || !noticeDateEl || !filingDateEl || !complainantEl || !accusedEl) return;

    if (!amountEl.value || !chequeDateEl.value || !noticeDateEl.value || !filingDateEl.value || !complainantEl.value || !accusedEl.value) {
        ui.toast('Please fill in all required fields.', 'warning');
        return;
    }

    ui.show('analysisLoading');

    const quickData = {
        analysis_mode: "quick",
        user_id: window.state.currentUser ? window.state.currentUser.uid : 'ANONYMOUS',
        cheque_date: chequeDateEl.value,
        cheque_amount: parseFloat(amountEl.value) || 0,
        debt_amount: parseFloat(amountEl.value) || 0,
        notice_date: noticeDateEl.value,
        filing_date: filingDateEl.value,
        complainant_name: complainantEl.value,
        accused_name: accusedEl.value,
        original_cheque: document.getElementById('qChequePresent')?.checked ? "Yes - Original" : "No - Lost",
        dishonour_memo: document.getElementById('qDishonourMemo')?.checked ? "Yes - Original" : "No",
        notice_sent: document.getElementById('qNoticeSent')?.checked ? "Yes" : "No",
        supporting_documents: document.getElementById('qDebtProof')?.checked ? "Yes - All Documents" : "No Documents",
        
        // Defaults
        case_id: "CC/QUICK/" + Date.now().toString().slice(-4),
        case_title: `${complainantEl.value} vs ${accusedEl.value}`,
        court_name: "MM Court",
        case_type: "Cheque Bounce",
        complainant_type: "Individual",
        accused_type: "Individual",
        complainant_address: "Not Provided",
        accused_address: "Not Provided",
        directors_named: "Not Applicable",
        complainant_authorized: "Not Applicable",
        purpose: "Not Provided",
        agreement_type: "No Formal Agreement",
        debt_acknowledgment: "No",
        cheque_number: "000000",
        bank_name: "Default Bank",
        cheque_type: "Account Payee Cheque",
        post_dated: "No",
        dishonour_date: "",
        dishonour_reason: "Insufficient Funds",
        bank_memo_received: document.getElementById('qDishonourMemo').checked ? "Yes" : "No"
    };

    try {
        window.state.caseData = quickData;
        const result = await api.analyze(quickData);
        window.state.analysisResult = result;
        if (window.saveCaseToHistory) {
            window.saveCaseToHistory(quickData, result);
        }
        ui.hide('analysisLoading');
        switchScreen('resultsScreen');
        renderResults(result);
    } catch (err) {
        ui.hide('analysisLoading');
        ui.toast(err.message, 'error');
    }
};

window.expandToFullMode = () => {
    const amount = document.getElementById('qAmount')?.value || '';
    const chequeDate = document.getElementById('qChequeDate')?.value || '';
    const noticeDate = document.getElementById('qNoticeDate')?.value || '';
    const filingDate = document.getElementById('qFilingDate')?.value || '';
    const complainant = document.getElementById('qComplainant')?.value || '';
    const accused = document.getElementById('qAccused')?.value || '';

    window.state.currentStep = 1;
    window.state.caseData = {
        debt_amount: amount,
        cheque_amount: amount,
        cheque_date: chequeDate,
        notice_date: noticeDate,
        filing_date: filingDate,
        complainant_name: complainant,
        accused_name: accused,
        case_title: complainant && accused ? `${complainant} vs ${accused}` : ''
    };

    renderWizardStep();
    switchScreen('caseWizardScreen');
};

/**
 * Document Drafting System UI Flow
 */
let draftGenSource = 'dashboard';
let activeDraftType = null;

window.openDraftGeneratorScreen = (source) => {
    draftGenSource = source || (window.state.analysisResult && window.state.analysisResult.score ? 'results' : 'dashboard');
    switchScreen('draftGeneratorScreen');
    window.showDraftTypeSelection();
};

window.draftGenGoBack = () => {
    if (draftGenSource === 'results' && window.state.analysisResult && window.state.analysisResult.score) {
        switchScreen('resultsScreen');
    } else {
        switchScreen('dashboardScreen');
    }
};

window.showDraftTypeSelection = () => {
    ui.show('draftTypeSelection');
    ui.hide('draftInputForm');
    ui.hide('draftOutputView');
    renderDraftTypeGrid();
};

window.showDraftInputForm = () => {
    ui.hide('draftTypeSelection');
    ui.show('draftInputForm');
    ui.hide('draftOutputView');
};

window.showDraftOutputView = () => {
    ui.hide('draftTypeSelection');
    ui.hide('draftInputForm');
    ui.show('draftOutputView');
};

function renderDraftTypeGrid() {
    const grid = document.getElementById('draftTypeGrid');
    if (!grid) return;
    grid.innerHTML = DRAFT_TYPES.map(dt => `
        <div class="draft-type-card" onclick="selectDraftType('${dt.id}')">
            <div class="draft-type-num" style="background:${dt.color}18;color:${dt.color}">${dt.number}</div>
            <div class="draft-type-icon-wrap" style="color:${dt.color}">
                <i class="fas ${dt.icon}"></i>
            </div>
            <div class="draft-type-info">
                <h4>${dt.title}</h4>
                <span class="draft-type-sub">${dt.subtitle}</span>
                <p>${dt.description}</p>
            </div>
            <div class="draft-type-chevron" style="color:${dt.color}">
                <i class="fas fa-chevron-right"></i>
            </div>
        </div>
    `).join('');
}

window.selectDraftType = (id) => {
    activeDraftType = DRAFT_TYPES.find(dt => dt.id === id);
    if (!activeDraftType) return;

    const badge = document.getElementById('draftSelectedBadge');
    if (badge) {
        badge.innerHTML = `
            <span style="background:${activeDraftType.color}18;color:${activeDraftType.color};padding:0.3rem 1rem;border-radius:999px;font-size:0.8rem;font-weight:600;display:inline-flex;align-items:center;gap:0.4rem;">
                <i class="fas ${activeDraftType.icon}"></i> Type ${activeDraftType.number} of 13 &nbsp;·&nbsp; ${activeDraftType.subtitle}
            </span>`;
    }
    
    ui.setText('draftFormTitle', activeDraftType.title);
    ui.setText('draftFormSubtitle', activeDraftType.description);

    const pre = buildDraftPrefill();
    const body = document.getElementById('draftFormBody');
    if (body) {
        body.innerHTML = '<div class="draft-fields-grid">' + activeDraftType.fields.map(f => {
            const val = pre[f.name] || '';
            const isWide = f.type === 'textarea' || f.name.includes('address') || f.name.includes('details') || f.name.includes('purpose') || f.name.includes('notes');
            let inputHtml = '';
            if (f.type === 'textarea') {
                inputHtml = `<textarea id="dfield_${f.name}" class="draft-field-input" ${f.required ? 'required' : ''} placeholder="${f.placeholder || ''}" rows="3">${val}</textarea>`;
            } else if (f.type === 'select') {
                inputHtml = `<select id="dfield_${f.name}" class="draft-field-input" ${f.required ? 'required' : ''}>
                    <option value="">Select...</option>
                    ${(f.options || []).map(o => `<option value="${o}"${val === o ? ' selected' : ''}>${o}</option>`).join('')}
                </select>`;
            } else {
                inputHtml = `<input type="${f.type}" id="dfield_${f.name}" class="draft-field-input" ${f.required ? 'required' : ''} placeholder="${f.placeholder || ''}" value="${val}">`;
            }
            return `<div class="draft-field-group${isWide ? ' full-width' : ''}">
                <label class="draft-field-label" for="dfield_${f.name}">
                    ${f.label}${f.required ? ' <span class="req-star">*</span>' : ''}
                </label>${inputHtml}
            </div>`;
        }).join('') + '</div>';
    }

    window.showDraftInputForm();
};

function buildDraftPrefill() {
    const s = window.state.caseData || {};
    const map = {};
    if (s.complainant_name) map.complainant_name = s.complainant_name;
    if (s.complainant_address) map.complainant_address = s.complainant_address;
    if (s.accused_name) map.accused_name = s.accused_name;
    if (s.accused_address) map.accused_address = s.accused_address;
    if (s.cheque_number) map.cheque_number = s.cheque_number;
    if (s.cheque_date) map.cheque_date = s.cheque_date;
    if (s.cheque_amount) map.cheque_amount = s.cheque_amount;
    if (s.bank_name) map.bank_name = s.bank_name;
    if (s.branch_name) map.branch_name = s.branch_name;
    if (s.dishonour_date) map.dishonour_date = s.dishonour_date;
    if (s.dishonour_reason) map.dishonour_reason = s.dishonour_reason;
    if (s.court_name) map.court_name = s.court_name;
    if (s.case_id) map.case_number = s.case_id;
    if (s.filing_date) map.filing_date = s.filing_date;
    if (s.notice_date) map.notice_date = s.notice_date;
    if (s.purpose) map.transaction_purpose = s.purpose;
    return map;
}

window.generateDraftFromForm = () => {
    if (!activeDraftType) return;
    const missing = [];
    const data = {};
    for (const f of activeDraftType.fields) {
        const el = document.getElementById('dfield_' + f.name);
        if (!el) continue;
        const val = el.value.trim();
        if (f.required && !val) {
            missing.push(f.label);
            el.classList.add('field-error');
        } else {
            el.classList.remove('field-error');
            data[f.name] = val;
        }
    }
    if (missing.length > 0) {
        ui.toast('Please fill: ' + missing.slice(0, 3).join(', ') + (missing.length > 3 ? '...' : ''), 'error');
        return;
    }
    try {
        const txt = activeDraftType.generate(data);
        const textPreview = document.getElementById('generatedDraftContent');
        if (textPreview) textPreview.value = txt;
        
        const badge = document.getElementById('draftOutputBadge');
        if (badge) {
            badge.innerHTML = `
                <span style="background:${activeDraftType.color}18;color:${activeDraftType.color};padding:0.3rem 1rem;border-radius:999px;font-size:0.8rem;font-weight:600;display:inline-flex;align-items:center;gap:0.4rem;">
                    <i class="fas ${activeDraftType.icon}"></i> Draft ${activeDraftType.number} – ${activeDraftType.subtitle}
                </span>`;
        }
        ui.setText('draftOutputTitle', activeDraftType.title);
        window.showDraftOutputView();

        if (typeof verifyDraftTimelineS138 === 'function') {
            const tRes = verifyDraftTimelineS138(data);
            if (tRes.warnings && tRes.warnings.length > 0) {
                ui.toast('Timeline Alert: ' + tRes.warnings[0], 'warning');
            } else {
                ui.toast('Draft generated & Section 138 statutory timeline verified!', 'success');
            }
        } else {
            ui.toast('Draft generated successfully!', 'success');
        }
        if (caseId && activeDraftType) {
            const historyListEl = document.getElementById('draftHistoryList');
            if (historyListEl) {
                historyListEl.innerHTML = '<p style="color: var(--gray-400); font-size: 0.8rem; margin: 0; text-align: center; padding: 1rem 0;"><i class="fas fa-spinner fa-spin"></i> Loading history...</p>';
                api.getDraftHistory(caseId, activeDraftType.id)
                    .then(data => {
                        if (data.success && data.history && data.history.length > 0) {
                            historyListEl.innerHTML = data.history.map(item => {
                                const dt = new Date(item.created_at).toLocaleString();
                                return `
                                    <div class="history-item" style="padding: 0.75rem; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; cursor: pointer; transition: all 0.2s;" onclick="loadDraftVersion('${item.version}')">
                                        <div style="font-weight: 600; font-size: 0.85rem; color: #374151;">Version ${item.version}</div>
                                        <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">${dt}</div>
                                    </div>
                                `;
                            }).join('');
                            
                            window.loadDraftVersion = (version) => {
                                const found = data.history.find(h => String(h.version) === String(version));
                                if (found) {
                                    document.getElementById('generatedDraftContent').value = found.content;
                                    ui.toast(`Loaded Version ${version}`, 'success');
                                }
                            };
                        } else {
                            historyListEl.innerHTML = '<p style="color: #9ca3af; font-size: 0.8rem; margin: 0; text-align: center; padding: 1rem 0;">No versions saved yet.</p>';
                        }
                    })
                    .catch(err => {
                        console.error('History fetch error:', err);
                        historyListEl.innerHTML = '<p style="color: #ef4444; font-size: 0.8rem; margin: 0; text-align: center; padding: 1rem 0;">Failed to load history.</p>';
                    });
            }
        }
        ui.toast('Draft generated successfully!', 'success');
    } catch (err) {
        ui.toast('Error generating draft.', 'error');
        console.error('Draft error:', err);
    }
};

window.copyGeneratedDraft = () => {
    const ta = document.getElementById('generatedDraftContent');
    if (!ta) return;
    ta.select();
    document.execCommand('copy');
    ui.toast('Draft copied to clipboard!', 'success');
};

window.downloadGeneratedDraft = async () => {
    const content = document.getElementById('generatedDraftContent')?.value;
    if (!content) { ui.toast('Nothing to download', 'warning'); return; }
    
    // Create highly premium loading overlay
    const overlay = document.createElement('div');
    overlay.id = 'dossierLoadingOverlay';
    overlay.innerHTML = `
        <div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,0.85);z-index:10000;display:flex;flex-direction:column;justify-content:center;align-items:center;color:white;font-family:Inter,sans-serif;backdrop-filter:blur(10px);">
            <div style="width:60px;height:60px;border:4px solid rgba(56,189,248,0.2);border-top:4px solid #38bdf8;border-radius:50%;animation:dossierSpin 1s linear infinite;margin-bottom:24px;"></div>
            <style>@keyframes dossierSpin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
            <h2 style="font-size:28px;font-weight:800;margin:0 0 12px 0;background:linear-gradient(135deg,#e0f2fe,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:1px;">COMPILING DOSSIER</h2>
            <div id="dossierLoadingText" style="font-size:15px;color:#94a3b8;font-family:monospace;letter-spacing:0.5px;">Extracting AI Intelligence State...</div>
        </div>
    `;
    document.body.appendChild(overlay);

    const steps = [
        "Parsing Factual Timeline...",
        "Synthesizing Legal Reasoning...",
        "Structuring Defence Matrices...",
        "Applying Section 138 Statutes...",
        "Computing Cryptographic Hash...",
        "Rendering PDF Architecture..."
    ];
    let stepIdx = 0;
    const loadingInterval = setInterval(() => {
        const textEl = document.getElementById('dossierLoadingText');
        if(textEl && stepIdx < steps.length) {
            textEl.innerText = steps[stepIdx];
            stepIdx++;
        }
    }, 600);

    try {
        const title = activeDraftType ? activeDraftType.title : 'Legal Draft';
        
        // Extract full intelligence metadata
        const ar = window.state.analysisResult || {};
        
        const topDefences = (ar.defence_strategy || []).slice(0, 2).map(d => typeof d === 'string' ? d : d.argument);
        const topPrecedents = (ar.precedents || []).slice(0, 2).map(p => {
            if (typeof p === 'string') return p;
            const name = p.case || p.case_name || 'Landmark Case';
            const cit = p.citation || '';
            return cit ? `${name} [${cit}]` : name;
        });
        
        const metadata = { 
            caseId: ar.case_id || 'Unknown_Case',
            score: ar.score || null,
            riskLevel: ar.risk_level || 'Unknown',
            clientRole: (ar.case_data && ar.case_data.client_role) || 'Client',
            courtName: (ar.case_data && ar.case_data.court_name) || 'Competent Court',
            defences: topDefences,
            precedents: topPrecedents,
            analysis_result: ar
        };
        
        const blob = await api.generateDraftPdf(title, content, metadata);
        if (blob.size < 100) throw new Error('Received empty PDF');
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const draftTitle = metadata.docType || title || 'Dossier';
        a.download = getSanitizedCaseFilename(draftTitle, metadata, 'pdf');
        document.body.appendChild(a);
        a.click();
        
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
        
        ui.toast('Comprehensive Dossier Downloaded!', 'success');
    } catch (error) {
        console.error('Download draft error:', error);
        ui.toast('Failed to generate Dossier PDF.', 'error');
    } finally {
        clearInterval(loadingInterval);
        if (document.getElementById('dossierLoadingOverlay')) {
            document.getElementById('dossierLoadingOverlay').remove();
        }
    }
};

window.printGeneratedDraft = () => {
    const content = document.getElementById('generatedDraftContent')?.value;
    if (!content) return;
    const win = window.open('', '_blank');
    win.document.write(`<html><head><title>JUDIQ AI – Legal Draft</title>
    <style>body{font-family:'Courier New',monospace;font-size:12px;padding:2cm;line-height:1.8;white-space:pre-wrap;color:#111;}</style>
    </head><body>${content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</body></html>`);
    win.document.close(); win.print();
};

/**
 * Smart Upload Screen Functions
 */
window.openSmartUpload = () => {
    const modal = document.getElementById("uploadModal");
    if (!modal) return;
    modal.classList.remove("hidden");
    setTimeout(() => modal.classList.add("active"), 10);

    const zone = document.getElementById("uploadZone");
    const progress = document.getElementById("uploadProgress");
    const results = document.getElementById("extractionResults");
    if (zone) zone.classList.remove("hidden");
    if (progress) progress.classList.add("hidden");
    if (results) results.classList.add("hidden");
};

window.closeUploadModal = () => {
    const modal = document.getElementById("uploadModal");
    if (!modal) return;
    modal.classList.remove("active");
    setTimeout(() => modal.classList.add("hidden"), 300);
};

window.proceedWithExtractedText = () => {
    const preview = document.getElementById("extractedTextPreview");
    if (!preview) return;
    const text = preview.value;
    if (!text || text.length < 10) {
        ui.toast("Insufficient text to analyze", "warning");
        return;
    }

    window.closeUploadModal();

    const initialData = {
        purpose: text.substring(0, 1000),
        additional_notes: text
    };
    
    window.startCaseAnalysis(initialData);
    ui.toast("Wizard pre-filled with extracted data", "success");
};

function initUploadBindings() {
    const zone = document.getElementById("uploadZone");
    const input = document.getElementById("fileInput");

    if (!zone || !input) return;

    zone.addEventListener("dragover", (e) => {
        e.preventDefault();
        zone.classList.add("drag-over");
    });

    zone.addEventListener("dragleave", () => {
        zone.classList.remove("drag-over");
    });

    zone.addEventListener("drop", (e) => {
        e.preventDefault();
        zone.classList.remove("drag-over");
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    input.addEventListener("change", (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

async function handleFileUpload(file) {
    const zone = document.getElementById("uploadZone");
    const progress = document.getElementById("uploadProgress");
    const progressFill = document.getElementById("uploadProgressFill");
    const status = document.getElementById("uploadStatus");

    if (!zone || !progress || !progressFill || !status) return;

    zone.classList.add("hidden");
    progress.classList.remove("hidden");

    status.textContent = "Uploading document...";
    progressFill.style.width = "30%";

    const uploadData = new FormData();
    uploadData.append("file", file);

    try {
        status.textContent = "Extracting legal intelligence...";
        progressFill.style.width = "70%";

        const responseData = await api.verifyMemo(uploadData);

        if (responseData.status === "success" || responseData.status === "partial") {
            progressFill.style.width = "100%";
            setTimeout(() => {
                progress.classList.add("hidden");
                showExtractionResults(responseData.text);
                if (responseData.status === "partial") {
                    ui.toast("Some text could not be extracted", "warning");
                }
            }, 500);
        } else {
            throw new Error(responseData.message || "Upload failed");
        }
    } catch (error) {
        ui.toast(error.message, "error");
        zone.classList.remove("hidden");
        progress.classList.add("hidden");
    }
}

function showExtractionResults(text) {
    const results = document.getElementById("extractionResults");
    const preview = document.getElementById("extractedTextPreview");

    if (results && preview) {
        results.classList.remove("hidden");
        preview.value = text || "No text could be extracted from this document.";
    }
}

// Bind upload listener once the module executes
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initUploadBindings);
} else {
    initUploadBindings();
}

/**
 * Result Actions exports
 */
window.switchResultTab = switchResultTab;
window.viewStrategy = () => {
    if (!window.state.analysisResult) {
        ui.toast('Please analyze a case first.', 'warning');
        return;
    }
    switchScreen('resultsScreen');
    window.switchResultTab('strategy');
};
window.viewReports = () => {
    if (!window.state.analysisResult) {
        ui.toast('Please analyze a case first.', 'warning');
        return;
    }
    switchScreen('resultsScreen');
    window.switchResultTab('analysis');
};
window.viewGuidance = () => {
    if (!window.state.analysisResult) {
        ui.toast('Please analyze a case first.', 'warning');
        return;
    }
    switchScreen('resultsScreen');
    window.switchResultTab('strategy');
};
window.learnMode = () => {
    ui.toast('Learning mode coming soon! This will include educational case studies and tutorials.', 'info');
};
window.generateDraft = () => window.openDraftGeneratorScreen('dashboard');
window.backToResults = () => switchScreen('resultsScreen');
window.editAndReanalyze = () => switchScreen('caseWizardScreen');
window.startNewAnalysis = () => window.startCaseAnalysis();
window.startNewCase = () => {
    if (confirm('Start a new case? Your current analysis will remain in recent cases.')) {
        window.startCaseAnalysis();
    }
};

export function getSanitizedCaseFilename(prefix = 'Report', data = null, ext = 'pdf') {
    const d = data || window.state.analysisResult || window.state.caseData || {};
    const cd = (d && d.case_data) ? d.case_data : (d || {});
    
    // Extract most descriptive name available
    let title = cd.case_title || cd.case_caption || cd.title || '';
    if (!title && cd.complainant_name && cd.accused_name) {
        title = `${cd.complainant_name}_vs_${cd.accused_name}`;
    }
    if (!title && cd.bank_name && cd.borrower_name) {
        title = `${cd.bank_name}_vs_${cd.borrower_name}`;
    }
    if (!title && cd.case_id) {
        title = cd.case_id;
    }
    if (!title && d.case_id) {
        title = d.case_id;
    }
    if (!title) {
        title = 'Legal_Matter';
    }
    
    // Clean string for safe cross-platform file naming
    const safeTitle = String(title)
        .replace(/[^a-zA-Z0-9_\-\s]/g, '')
        .trim()
        .replace(/\s+/g, '_')
        .slice(0, 60);
        
    const safePrefix = String(prefix)
        .replace(/[^a-zA-Z0-9_\-\s]/g, '')
        .trim()
        .replace(/\s+/g, '_');
        
    return `JUDIQ_${safePrefix}_${safeTitle}.${ext.replace(/^\./, '')}`;
}
window.getSanitizedCaseFilename = getSanitizedCaseFilename;

window.downloadPDF = async () => {
    if (!window.state.analysisResult) {
        ui.toast('No analysis result available.', 'warning');
        return;
    }
    ui.toast('Generating professional PDF report...', 'info');
    try {
        const blob = await api.generatePdf(window.state.analysisResult);
        if (blob.size < 100) throw new Error('Received empty PDF');
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = getSanitizedCaseFilename('Report', window.state.analysisResult, 'pdf');
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        ui.toast('PDF report downloaded successfully!', 'success');
    } catch (err) {
        console.error('PDF Download Error:', err);
        ui.toast(`PDF Error: ${err.message}. Fetching text fallback.`, 'error');
        // Text fallback
        const result = window.state.analysisResult;
        const content = `JUDIQ AI CASE REPORT\nScore: ${result.score}/100\nVerdict: ${result.verdict}\n\nLegal Analysis:\n${result.legal_analysis || ''}`;
        const b = new Blob([content], { type: "text/plain" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(b);
        link.download = getSanitizedCaseFilename('Report', window.state.analysisResult, 'txt');
        link.click();
    }
};

window.generateReport = () => window.downloadPDF();

window.copyDraft = () => {
    const ta = document.getElementById("draftPreviewContent") || document.getElementById("draftContent");
    if (!ta || !ta.value) { ui.toast("No draft available", "warning"); return; }
    ta.select();
    document.execCommand('copy');
    ui.toast('Draft copied to clipboard!', 'success');
};

window.downloadDraft = () => {
    const ta = document.getElementById("draftPreviewContent") || document.getElementById("draftContent");
    if (!ta || !ta.value) { ui.toast("No draft available", "warning"); return; }
    const blob = new Blob([ta.value], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = getSanitizedCaseFilename('Draft', window.state.analysisResult || window.state.caseData, 'txt');
    a.click();
    URL.revokeObjectURL(url);
    ui.toast('Draft downloaded!', 'success');
};

window.printDraft = () => {
    const ta = document.getElementById("draftPreviewContent") || document.getElementById("draftContent");
    if (!ta || !ta.value) { ui.toast("No draft available", "warning"); return; }
    const win = window.open('', '_blank');
    win.document.write(`<html><head><title>JUDIQ AI – Legal Draft</title>
    <style>body{font-family:'Courier New',monospace;font-size:12px;padding:2cm;line-height:1.8;white-space:pre-wrap;color:#111;}</style>
    </head><body>${ta.value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</body></html>`);
    win.document.close(); win.print();
};

window.copyDraftFromPreview = window.copyDraft;
window.downloadDraftText = window.downloadDraft;
window.openDraftEditor = () => window.openDraftGeneratorScreen('results');

window.viewFullReport = () => {
    switchScreen('resultsScreen');
    window.switchResultTab('overview');
};

window.currentDraftTemplate = 'demand_notice';
window.currentDraftTone = 'standard';

window.onSelectDraftTemplate = (templateId) => {
    window.currentDraftTemplate = templateId;
    window.renderSelectedDraft();
};

window.setDraftTone = (tone, btnElement) => {
    window.currentDraftTone = tone;
    if (btnElement) {
        document.querySelectorAll('.btn-tone').forEach(b => b.classList.remove('active'));
        btnElement.classList.add('active');
    }
    if (window.ui) window.ui.toast(`Draft tone updated to: ${tone.toUpperCase()}`, 'info');
    window.renderSelectedDraft();
};

window.renderSelectedDraft = () => {
    const templateId = window.currentDraftTemplate || 'demand_notice';
    const templateObj = DRAFT_TYPES.find(t => t.id === templateId) || DRAFT_TYPES[0];
    const caseData = window.state.caseData || {};
    
    const d = {
        complainant_name: caseData.complainant_name || 'Apex Global Traders Pvt Ltd',
        complainant_address: caseData.complainant_address || 'Plot 42, Hinjewadi Phase 1, Pune, 411057',
        accused_name: caseData.accused_name || 'Vanguard Tech Solutions Pvt Ltd',
        accused_address: caseData.accused_address || 'Office 10, Wakad Road, Pune, 411057',
        cheque_number: caseData.cheque_number || '482019',
        cheque_date: caseData.cheque_date || '2026-04-10',
        cheque_amount: caseData.cheque_amount || 1550000,
        bank_name: caseData.bank_name || 'HDFC Bank Ltd',
        branch_name: caseData.branch_name || 'Hinjewadi Branch',
        dishonour_date: caseData.dishonour_date || '2026-05-02',
        dishonour_reason: caseData.dishonour_reason || 'Funds Insufficient',
        transaction_purpose: caseData.purpose || 'Supply of IT Hardware Equipment and Enterprise Servers',
        notice_date: caseData.notice_date || '2026-05-18',
        demand_days: '15 days',
        device_type: 'Samsung Galaxy S23 & Dell XPS Laptop',
        court_location: caseData.jurisdiction_city || 'Pune'
    };

    let text = templateObj.generate(d);
    
    if (window.currentDraftTone === 'aggressive') {
        text = text.replace(/Please treat this as a final opportunity to settle the matter amicably\./g, 
            'TAKE NOTICE that no further extensions will be granted, and strict criminal prosecution under Section 138 of the Negotiable Instruments Act along with punitive costs will be filed immediately upon expiry of the 15-day statutory deadline without further reference to you.');
    } else if (window.currentDraftTone === 'conciliatory') {
        text = text.replace(/Please treat this as a final opportunity to settle the matter amicably\./g, 
            'My client remains open to structured pre-trial settlement options provided your authorized representative contacts our counsel within 7 days of receipt of this notice.');
    }

    const preview = document.getElementById("draftPreviewContent");
    if (preview) {
        preview.value = text;
    }
};

window.downloadDraftWord = () => {
    const preview = document.getElementById("draftPreviewContent");
    if (!preview || !preview.value) {
        if (window.ui) window.ui.toast('No draft text available to download', 'warning');
        return;
    }
    const header = "<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><title>Legal Draft</title><style>body{font-family:'Courier New',Courier,monospace;font-size:11pt;line-height:1.6;}</style></head><body><pre style='font-family:inherit;white-space:pre-wrap;'>";
    const footer = "</pre></body></html>";
    const sourceHTML = header + preview.value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') + footer;
    
    const blob = new Blob(['\ufeff', sourceHTML], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const templateLabel = (window.currentDraftTemplate || 'Draft').replace(/_/g, ' ');
    a.download = getSanitizedCaseFilename(templateLabel, window.state.analysisResult || window.state.caseData, 'doc');
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    if (window.ui) window.ui.toast('Draft downloaded as Word document!', 'success');
};


window.toggleReasoning = () => {
    const trace = document.getElementById('reasoningTrace');
    const header = document.querySelector('.collapsible-header');
    if (trace) trace.classList.toggle('hidden');
    if (header) header.classList.toggle('open');
};

/**
 * Theme Toggling Logic

 */
function initTheme() {
    const savedTheme = localStorage.getItem('judiq_theme');
    const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
    
    if (savedTheme === 'light' || (!savedTheme && prefersLight)) {
        document.documentElement.setAttribute('data-theme', 'light');
        updateThemeIcons('light');
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        updateThemeIcons('dark');
    }
}

window.toggleTheme = () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('judiq_theme', newTheme);
    updateThemeIcons(newTheme);
};

function updateThemeIcons(theme) {
    const icons = document.querySelectorAll('.theme-toggle-btn i');
    icons.forEach(icon => {
        if (theme === 'light') {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    });
}

window.togglePricingPeriod = (isAnnual) => {
    const citizenPrice = document.getElementById('priceCitizen');
    const proPrice = document.getElementById('pricePro');
    const enterprisePrice = document.getElementById('priceEnterprise');
    
    const monthlyLabel = document.getElementById('billingMonthlyLabel');
    const annualLabel = document.getElementById('billingAnnualLabel');
    
    if (isAnnual) {
        if (citizenPrice) citizenPrice.textContent = '239';
        if (proPrice) proPrice.textContent = '479';
        if (enterprisePrice) enterprisePrice.textContent = '799';
        
        if (monthlyLabel) monthlyLabel.classList.remove('active');
        if (annualLabel) annualLabel.classList.add('active');
    } else {
        if (citizenPrice) citizenPrice.textContent = '299';
        if (proPrice) proPrice.textContent = '599';
        if (enterprisePrice) enterprisePrice.textContent = '999';
        
        if (monthlyLabel) monthlyLabel.classList.add('active');
        if (annualLabel) annualLabel.classList.remove('active');
    }
};

window.toggleFaqItem = (element) => {
    const item = element.closest('.faq-item');
    if (item) {
        item.classList.toggle('active');
    }
};

window.switchExplorerTab = (tabName, element) => {
    // Remove active class from all tabs
    document.querySelectorAll('.explorer-tab').forEach(tab => tab.classList.remove('active'));
    // Add active class to clicked tab
    if (element) element.classList.add('active');

    const titleEl = document.getElementById('explorerTitle');
    const descEl = document.getElementById('explorerDesc');
    const previewEl = document.getElementById('explorerPreview');
    if (!titleEl || !descEl || !previewEl) return;

    let lines = [];
    if (tabName === 'adversarial') {
        titleEl.textContent = 'Adversarial Opponent Simulation';
        descEl.textContent = 'Simulate critical opposing counsel cross-examination routes and see how the AI evaluates and flags vulnerabilities in real-time.';
        lines = [
            { text: '// Running Adversarial Opponent Simulation...', color: '#6b7280' },
            { text: '[INFO] Parsing complainant statement & matching against Indian Evidence Act Sec 45...', color: '#60a5fa' },
            { text: '[WARNING] Found high risk vulnerability in Sec 138 demand notice delivery timeline.', color: '#fbbf24' },
            { text: '[VULNERABILITY] Delivery occurred on day 32 (Statutory limit: 30 days).', color: '#f87171' },
            { text: '[RECOMMENDED COUNTER] Invoke General Clauses Act Sec 10 to plead court holiday exemption.', color: '#34d399' }
        ];
    } else if (tabName === 'contradiction') {
        titleEl.textContent = 'Evidence Contradiction Scan';
        descEl.textContent = 'Search uploads for mismatches between bank return memos, statutory legal notices, and witness testimonies automatically.';
        lines = [
            { text: '// Initiating Evidentiary Contradiction Scan...', color: '#6b7280' },
            { text: '[INFO] Document extracted: Bank Return Memo (Date: 2026-06-05, Reason: Insufficient Funds).', color: '#60a5fa' },
            { text: '[INFO] Document extracted: Legal Demand Notice (Date: 2026-06-08).', color: '#60a5fa' },
            { text: '[OK] Date validation: Legal Notice sent within 30 days of Dishonour Memo.', color: '#34d399' },
            { text: '[CONFLICT] Complainant oral testimony states cheque value was 10,00,000 INR, but Bank Memo registers 5,00,000 INR.', color: '#f87171' },
            { text: '[WARNING] Evidentiary mismatch detected. Prepare defense around Sec 139 presumption rebuttal.', color: '#fbbf24' }
        ];
    } else if (tabName === 'strategy') {
        titleEl.textContent = 'Courtroom Strategy & Precedent Routing';
        descEl.textContent = 'Retrieve judge challenge profiles and matching Supreme Court precedent citations to construct optimized defense briefs.';
        lines = [
            { text: '// Generating Courtroom Precedent Route...', color: '#6b7280' },
            { text: '[INFO] Query: Cheque bounce due to signature mismatch (Sec 138/139 IEA).', color: '#60a5fa' },
            { text: '[MATCH] Found relevant Supreme Court citation: Laxmi Dyechem v. State of Gujarat (2012).', color: '#34d399' },
            { text: '[RULE] Held: Signature mismatch does not escape Sec 138 liability if dishonour reasons are verified.', color: '#60a5fa' },
            { text: '[JUDGE PROFILE] Justice A. Mehta: 83% historic tendency to rule in favor of complainant on Sec 138 timeline compliance.', color: '#fbbf24' },
            { text: '[STRATEGY] Focus oral arguments strictly on delivery timeline validation rather than signature analysis.', color: '#34d399' }
        ];
    }

    // Typewriter effect: clear console and print line-by-line with a slight delay
    previewEl.innerHTML = '';
    
    // Store active timer ID to prevent overlapping typing animations if clicked rapidly
    if (window.explorerTypewriterTimer) {
        clearInterval(window.explorerTypewriterTimer);
    }
    
    let currentLineIdx = 0;
    const typeNextLine = () => {
        if (currentLineIdx < lines.length) {
            const line = lines[currentLineIdx];
            const p = document.createElement('p');
            p.style.color = line.color;
            p.style.margin = '0 0 0.5rem 0';
            p.style.opacity = '0';
            p.style.transform = 'translateY(5px)';
            p.style.transition = 'all 0.3s ease';
            p.textContent = line.text;
            previewEl.appendChild(p);
            
            // Force reflow and animate in
            setTimeout(() => {
                p.style.opacity = '1';
                p.style.transform = 'translateY(0)';
            }, 10);
            
            currentLineIdx++;
        } else {
            clearInterval(window.explorerTypewriterTimer);
            window.explorerTypewriterTimer = null;
        }
    };
    
    typeNextLine(); // Print first line immediately
    window.explorerTypewriterTimer = setInterval(typeNextLine, 350);
};

window.switchDocsTab = (tabName, element) => {
    // Toggle active class on sidebar buttons
    const container = element.closest('.docs-modal-container');
    if (!container) return;
    
    container.querySelectorAll('.docs-tab-btn').forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');

    // Toggle active class on content panes
    container.querySelectorAll('.docs-content-pane').forEach(pane => pane.classList.remove('active'));
    const targetPane = container.querySelector(`#docs-${tabName}`);
    if (targetPane) {
        targetPane.classList.add('active');
    }
};

window.submitContactForm = (event) => {
    event.preventDefault();
    const form = event.target;
    const btn = form.querySelector('button[type="submit"]');
    const name = document.getElementById('contactName').value;
    const email = document.getElementById('contactEmail').value;
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="btn-text">Sending...</span><span class="btn-loader" style="display:inline-block;"></span>';
    }

    setTimeout(() => {
        // Use our ui.toast system from ui.js
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast(`Message sent successfully! Thank you, ${name}.`, 'success');
        } else {
            alert(`Message sent successfully! Thank you, ${name}.`);
        }
        
        form.reset();
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<span class="btn-text">Send Message</span>';
        }
    }, 1500);
};

// Guided Tour State & Logic
let currentTourStep = 0;
const tourStepsData = [
    {
        title: "Welcome to JudiQ AI!",
        text: "Let's take a 1-minute quick tour of your new Litigation Command Center to learn the core features.",
        icon: "fa-balance-scale",
        target: null,
        nextLabel: "Start Tour",
        prevLabel: "Skip Tour"
    },
    {
        title: "Preloaded Demo Cases",
        text: "Want to see JudiQ in action immediately? Use these Civil or Criminal buttons in the top navigation to instantly load pre-populated case profiles.",
        icon: "fa-bolt",
        target: ".nav-brand div",
        nextLabel: "Next Step",
        prevLabel: "Back"
    },
    {
        title: "Litigation Action Center",
        text: "Launch a comprehensive Case Analysis, run a Quick Analysis, check uploads, or generate custom Legal Drafts.",
        icon: "fa-rocket",
        target: "#actionCardsGrid",
        nextLabel: "Next Step",
        prevLabel: "Back"
    },
    {
        title: "Recent Activity",
        text: "View and manage your past litigation histories, success scores, and active room logs here.",
        icon: "fa-history",
        target: ".recent-section",
        nextLabel: "Finish Tour",
        prevLabel: "Back"
    }
];

window.startGuidedTour = () => {
    currentTourStep = 0;
    const overlay = document.getElementById('guidedTourOverlay');
    if (overlay) {
        overlay.classList.add('open');
        renderTourStep();
    }
};

function renderTourStep() {
    const step = tourStepsData[currentTourStep];
    const titleEl = document.getElementById('tourTitle');
    const textEl = document.getElementById('tourText');
    const iconEl = document.getElementById('tourIcon');
    const prevBtn = document.getElementById('tourPrevBtn');
    const nextBtn = document.getElementById('tourNextBtn');
    const dots = document.querySelectorAll('.tour-dot');

    if (titleEl) titleEl.textContent = step.title;
    if (textEl) textEl.textContent = step.text;
    if (iconEl) iconEl.className = `fas ${step.icon} tour-icon`;
    if (prevBtn) prevBtn.textContent = step.prevLabel;
    if (nextBtn) nextBtn.textContent = step.nextLabel;

    // Update dots active class
    dots.forEach((dot, index) => {
        if (index === currentTourStep) dot.classList.add('active');
        else dot.classList.remove('active');
    });

    // Clear previous highlights
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));

    // Highlight target element
    if (step.target) {
        const targetEl = document.querySelector(step.target);
        if (targetEl) {
            targetEl.classList.add('tour-highlight');
            targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
}

window.nextTourStep = () => {
    if (currentTourStep < tourStepsData.length - 1) {
        currentTourStep++;
        renderTourStep();
    } else {
        window.closeGuidedTour();
    }
};

window.prevTourStep = () => {
    if (currentTourStep === 0) {
        window.closeGuidedTour();
    } else {
        currentTourStep--;
        renderTourStep();
    }
};

window.closeGuidedTour = () => {
    const overlay = document.getElementById('guidedTourOverlay');
    if (overlay) {
        overlay.classList.remove('open');
    }
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));
    try { localStorage.setItem('judiq_tour_completed', 'true'); } catch (_) {}
};

/* =============================================================================
   LANDING PAGE PREMIUM INTERACTIVITY (SANDBOX & NEWSLETTER)
   ============================================================================= */

window.calculateSandboxTimelines = () => {
    const memoVal = document.getElementById('sandboxMemoDate').value;
    const noticeVal = document.getElementById('sandboxNoticeDate').value;
    if (!memoVal || !noticeVal) return;

    const memoDate = new Date(memoVal);
    const noticeDate = new Date(noticeVal);
    
    // Calculate difference in days (ignoring daylight savings timezone shifts)
    const timeDiff = noticeDate.getTime() - memoDate.getTime();
    const dayDiff = Math.floor(timeDiff / (1000 * 3600 * 24));

    const statusBadge = document.getElementById('sandboxStatusBadge');
    const step1Item = document.getElementById('step1Item');
    const step1Date = document.getElementById('step1Date');
    const step1Desc = document.getElementById('step1Desc');
    const step2Date = document.getElementById('step2Date');
    const step3Date = document.getElementById('step3Date');

    const formatDate = (date) => {
        return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    };

    // Repayment Notice period is notice date + 15 days, so filing becomes legal on notice date + 16 days.
    const filingStartDate = new Date(noticeDate.getTime() + 16 * 24 * 60 * 60 * 1000);
    // Statutory filing window is 30 days starting from cause of action date, which is notice date + 15 + 30 = notice date + 45 days.
    const filingDeadlineDate = new Date(noticeDate.getTime() + 45 * 24 * 60 * 60 * 1000);

    if (step2Date) {
        step2Date.textContent = `Filing becomes legal on: ${formatDate(filingStartDate)}`;
    }
    if (step3Date) {
        step3Date.textContent = `Filing deadline: ${formatDate(filingDeadlineDate)}`;
    }

    if (dayDiff >= 0 && dayDiff <= 30) {
        if (statusBadge) {
            statusBadge.textContent = 'Compliant';
            statusBadge.className = 'status-badge compliant animate-pop';
            statusBadge.style.animation = 'none';
            statusBadge.offsetHeight; // force reflow
            statusBadge.style.animation = null;
        }
        if (step1Item) {
            step1Item.className = 'timeline-step-item success';
        }
        if (step1Date) {
            step1Date.textContent = `Interval: ${dayDiff} days (Compliant)`;
        }
        if (step1Desc) {
            step1Desc.textContent = `Demand notice served within the 30-day statutory window of the Bank Return Memo.`;
        }
    } else {
        if (statusBadge) {
            statusBadge.textContent = 'Vulnerable';
            statusBadge.className = 'status-badge vulnerable animate-pop';
            statusBadge.style.animation = 'none';
            statusBadge.offsetHeight; // force reflow
            statusBadge.style.animation = null;
        }
        if (step1Item) {
            step1Item.className = 'timeline-step-item danger';
        }
        if (step1Date) {
            if (dayDiff < 0) {
                step1Date.textContent = `Interval: Invalid (Notice date cannot be before Bank Return Memo date)`;
            } else {
                step1Date.textContent = `Interval: ${dayDiff} days (Vulnerable - exceeds 30-day limit)`;
            }
        }
        if (step1Desc) {
            if (dayDiff < 0) {
                step1Desc.textContent = `Warning: Notice Delivery Date is before the Bank Return Memo date. Please correct your dates.`;
            } else {
                step1Desc.textContent = `Vulnerability: Demand notice served ${dayDiff} days after Bank Return Memo. Exceeds the 30-day statutory limit under Section 138.`;
            }
        }
    }
};

window.submitNewsletterForm = (event) => {
    event.preventDefault();
    const emailInput = document.getElementById('newsletterEmail');
    if (!emailInput) return;
    const email = emailInput.value.trim();
    
    if (!email) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('Please enter a valid email address.', 'warning');
        } else {
            alert('Please enter a valid email address.');
        }
        return;
    }

    // Display success toast notification
    if (window.ui && typeof window.ui.toast === 'function') {
        window.ui.toast(`Subscription successful! Welcome to JudiQ Insights, ${email}.`, 'success');
    } else {
        alert(`Subscription successful! Welcome to JudiQ Insights, ${email}.`);
    }

    // Clear input
    emailInput.value = '';
};

/* =============================================================================
   LEGAL MODALS AND PERSONALIZATION
   ============================================================================= */

window.openLegalModal = (modalId, event) => {
    if (event) event.preventDefault();
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
    }
};

window.closeLegalModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('open');
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
};

window.openProfileModal = (event) => {
    if (event) event.preventDefault();
    
    // Load current values
    const user = window.state.currentUser;
    if (!user) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast("Please log in to edit profile", "warning");
        }
        return;
    }
    
    const uid = user.uid;
    const savedProfileStr = localStorage.getItem(`judiq_profile_${uid}`);
    let name = user.displayName || user.email.split('@')[0];
    let firm = '';
    let role = window.state.currentRole || 'law_firm';
    
    if (savedProfileStr) {
        try {
            const profile = JSON.parse(savedProfileStr);
            if (profile.displayName) name = profile.displayName;
            if (profile.firmName) firm = profile.firmName;
            if (profile.role) role = profile.role;
        } catch (_) {}
    }
    
    const nameInput = document.getElementById('profileDisplayName');
    const firmInput = document.getElementById('profileFirmName');
    const roleSelect = document.getElementById('profileRole');
    
    if (nameInput) nameInput.value = name;
    if (firmInput) firmInput.value = firm;
    if (roleSelect) roleSelect.value = role;
    
    window.openLegalModal('profileSettingsModal');
};

window.saveUserProfile = (event) => {
    event.preventDefault();
    const user = window.state.currentUser;
    if (!user) return;
    
    const name = document.getElementById('profileDisplayName').value.trim();
    const firm = document.getElementById('profileFirmName').value.trim();
    const role = document.getElementById('profileRole').value;
    
    const profile = {
        displayName: name,
        firmName: firm,
        role: role
    };
    
    localStorage.setItem(`judiq_profile_${user.uid}`, JSON.stringify(profile));
    localStorage.setItem(`judiq_role_${user.uid}`, role);
    
    window.state.currentRole = role;
    
    // Attempt updating user profile in Firebase Auth as well
    if (user.updateProfile) {
        user.updateProfile({ displayName: name }).catch(console.error);
    }
    
    // Refresh dashboard view and welcome greeting
    renderDashboard();
    
    if (window.ui && typeof window.ui.toast === 'function') {
        window.ui.toast("Profile settings saved successfully!", "success");
    } else {
        alert("Profile settings saved successfully!");
    }
    
    window.closeLegalModal('profileSettingsModal');
};

window.resendVerificationEmail = async (event) => {
    if (event) event.preventDefault();
    const user = window.state.currentUser;
    if (!user) return;
    
    const btn = event.target;
    if (btn) btn.disabled = true;
    
    try {
        if (typeof user.sendEmailVerification === 'function') {
            await user.sendEmailVerification();
            if (window.ui && typeof window.ui.toast === 'function') {
                window.ui.toast(`Verification email sent to: ${user.email}`, "success");
            } else {
                alert(`Verification email sent to: ${user.email}`);
            }
        } else {
            // Mock mode fallback
            if (window.ui && typeof window.ui.toast === 'function') {
                window.ui.toast(`Mock: Verification email successfully resent to ${user.email}.`, "success");
            } else {
                alert(`Mock: Verification email successfully resent to ${user.email}.`);
            }
        }
    } catch (err) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast(err.message, "error");
        } else {
            alert(err.message);
        }
    } finally {
        if (btn) btn.disabled = false;
    }
};

window.triggerPasswordResetEmail = async (event) => {
    if (event) event.preventDefault();
    const user = window.state.currentUser;
    if (!user) return;
    
    const btn = event.target;
    if (btn) btn.disabled = true;
    
    try {
        if (auth && typeof auth.sendPasswordResetEmail === 'function') {
            await auth.sendPasswordResetEmail(user.email);
            if (window.ui && typeof window.ui.toast === 'function') {
                window.ui.toast(`Password reset link sent to: ${user.email}`, "success");
            } else {
                alert(`Password reset link sent to: ${user.email}`);
            }
        } else {
            if (window.ui && typeof window.ui.toast === 'function') {
                window.ui.toast(`Mock: Password reset link successfully sent to ${user.email}.`, "success");
            } else {
                alert(`Mock: Password reset link successfully sent to ${user.email}.`);
            }
        }
    } catch (err) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast(err.message, "error");
        } else {
            alert(err.message);
        }
    } finally {
        if (btn) btn.disabled = false;
    }
};

window.changeUserPasswordDirect = async (event) => {
    event.preventDefault();
    const user = window.state.currentUser;
    if (!user) return;
    
    const newPass = document.getElementById('changePassNew').value;
    const confirmPass = document.getElementById('changePassConfirm').value;
    
    if (newPass !== confirmPass) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast("New passwords do not match", "warning");
        } else {
            alert("New passwords do not match");
        }
        return;
    }
    
    const btn = event.target.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    
    try {
        if (typeof user.updatePassword === 'function') {
            await user.updatePassword(newPass);
            if (window.ui && typeof window.ui.toast === 'function') {
                window.ui.toast("Password updated successfully!", "success");
            } else {
                alert("Password updated successfully!");
            }
        } else {
            if (window.ui && typeof window.ui.toast === 'function') {
                window.ui.toast("Mock: Password updated successfully!", "success");
            } else {
                alert("Mock: Password updated successfully!");
            }
        }
        document.getElementById('changePasswordForm').reset();
    } catch (err) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast(err.message, "error");
        } else {
            alert(err.message);
        }
    } finally {
        if (btn) btn.disabled = false;
    }
};

/* =============================================================================
   LITIGATION READINESS SUITE & FLOATING AI CHAT INTERACTIVITY
   ============================================================================= */

// Precedents Data
const landmarkPrecedents = [
    {
        title: "Basalingappa vs. Mudibasappa (2019)",
        tag: "Financial Capacity",
        text: "Held that if the financial capacity of the complainant is challenged in high-value cash loans, the complainant must prove their source of funds to establish an enforceable debt.",
        source: "5 SCC 418"
    },
    {
        title: "Rangappa vs. Srikanth (2010)",
        tag: "Debt Presumption",
        text: "Confirmed that Section 139 carries a strong presumption of debt. The debtor must raise a probable defense to rebut it; mere denial is insufficient.",
        source: "11 SCC 441"
    },
    {
        title: "Aneeta Hada vs. Godfather Travels (2012)",
        tag: "Company Liability",
        text: "Prosecution of company directors/officers under Section 141 is not maintainable unless the company itself is joined as a primary accused.",
        source: "5 SCC 661"
    },
    {
        title: "A.C. Narayanan vs. State of Maharashtra (2014)",
        tag: "Power of Attorney",
        text: "Prosecution filed through a Power of Attorney (POA) holder is maintainable provided the POA holder has personal knowledge of the transactions.",
        source: "11 SCC 790"
    },
    {
        title: "Dashrath Rupsingh Rathod vs. State of Maharashtra (2014)",
        tag: "Jurisdiction",
        text: "Territorial jurisdiction falls where the cheque is delivered for collection through the payee's bank (subsequently codified in S.142(2) NI Act).",
        source: "9 SCC 129"
    },
    {
        title: "Kishan Rao vs. Shankargouda (2018)",
        tag: "S.139 Presumption",
        text: "The accused cannot rebut the Section 139 presumption by merely denying the signature or the transaction; they must produce cogent rebutting evidence.",
        source: "8 SCC 165"
    },
    {
        title: "Yogendra Pratap Singh vs. Savitri Pandey (2014)",
        tag: "Premature Filing",
        text: "Held that a complaint filed before the expiry of the mandatory 15-day notice period is premature and non-maintainable.",
        source: "10 SCC 713"
    },
    {
        title: "MSR Leathers vs. S. Palaniappan (2013)",
        tag: "Multiple Presentment",
        text: "A cheque can be presented multiple times. The complainant can file a case upon default of any subsequent legal notice sent within 30 days.",
        source: "10 SCC 568"
    },
    {
        title: "Bir Singh vs. Mukesh Kumar (2019)",
        tag: "Blank Cheque",
        text: "A blank signed cheque handed over to a payee carries an implied authority to fill it up. It is fully valid and enforceable under Section 138.",
        source: "4 SCC 197"
    },
    {
        title: "Arnesh Kumar vs. State of Bihar (2014)",
        tag: "Arrest Guidelines",
        text: "Laid down strict guidelines against mechanical arrests in offences punishable with imprisonment under 7 years, notably matrimonial cases under S.498A.",
        source: "8 SCC 273"
    },
    {
        title: "Geeta Mehrotra vs. State of U.P. (2012)",
        tag: "498A Family Quashing",
        text: "Casual or general reference to family members in matrimonial complaints under Section 498A IPC does not justify active criminal proceedings.",
        source: "10 SCC 741"
    },
    {
        title: "Preeti Gupta vs. State of Jharkhand (2010)",
        tag: "Matrimonial Quashing",
        text: "Expressed concern over the growing trend of implicating distant relatives in domestic conflicts; quashed unspecific S.498A allegations.",
        source: "7 SCC 667"
    },
    {
        title: "Sampelly Satyanarayana Rao vs. IREDA (2016)",
        tag: "Security Cheque",
        text: "Once a debt is crystallized on the cheque date, even a security cheque is enforceable under Section 138 of the NI Act.",
        source: "10 SCC 458"
    },
    {
        title: "Dalmia Cement vs. Galaxy Traders (2001)",
        tag: "Strict Timelines",
        text: "Section 138 timelines are penal and mandatory. Timelines for notice, receipt, and filing must be calculated strictly without delay latitude.",
        source: "6 SCC 463"
    }
];

window.updateReadinessProgress = () => {
    const checks = document.querySelectorAll('.readiness-check');
    if (checks.length === 0) return;
    
    let checkedCount = 0;
    checks.forEach(check => {
        if (check.checked) checkedCount++;
    });
    
    const percentage = Math.round((checkedCount / checks.length) * 100);
    
    // Update progress text
    const textEl = document.getElementById('readinessProgressText');
    if (textEl) textEl.textContent = `${percentage}%`;
    
    // Update progress circle offset (circumference of r=40 circle is 2 * pi * 40 ≈ 251.2)
    const circleBar = document.getElementById('readinessCircleBar');
    if (circleBar) {
        const circumference = 251.2;
        const offset = circumference - (percentage / 100) * circumference;
        circleBar.style.strokeDashoffset = offset;
    }
    
    // Update status text
    const statusTextEl = document.getElementById('readinessStatusText');
    if (statusTextEl) {
        if (percentage === 0) {
            statusTextEl.textContent = "No documents checked.";
            statusTextEl.style.color = "var(--gray-400)";
        } else if (percentage < 40) {
            statusTextEl.textContent = "High Risk. Key evidence missing.";
            statusTextEl.style.color = "var(--danger-400)";
        } else if (percentage < 80) {
            statusTextEl.textContent = "Partial readiness. Notice served?";
            statusTextEl.style.color = "var(--warning-400)";
        } else if (percentage < 100) {
            statusTextEl.textContent = "Strong case files ready to compile.";
            statusTextEl.style.color = "var(--primary-400)";
        } else {
            statusTextEl.textContent = "100% Ready. Secure filing approved!";
            statusTextEl.style.color = "var(--success-400)";
        }
    }
};

window.filterPrecedentsList = () => {
    const searchInput = document.getElementById('precedentSearchInput');
    const container = document.getElementById('precedentsListContainer');
    if (!container) return;
    
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
    
    const filtered = landmarkPrecedents.filter(item => {
        return item.title.toLowerCase().includes(query) || 
               item.tag.toLowerCase().includes(query) || 
               item.text.toLowerCase().includes(query) ||
               item.source.toLowerCase().includes(query);
    });
    
    if (filtered.length === 0) {
        container.innerHTML = `<p style="color: var(--gray-500); font-size: 0.9rem; text-align: center; margin-top: 2rem;">No matching precedent authorities found.</p>`;
        return;
    }
    
    container.innerHTML = filtered.map(item => `
        <div class="citation-result-card" style="border-left: 3px solid var(--primary-500); transition: var(--transition-fast); margin-bottom: 0.75rem; padding: 0.85rem; background: var(--gray-100); border-radius: 0.5rem; border: 1px solid var(--gray-200);">
            <div class="citation-result-header" style="display:flex; align-items:center; justify-content:space-between; gap:0.5rem; margin-bottom:0.4rem;">
                <h4 class="citation-result-title" style="font-family: var(--font-serif); font-size:0.95rem; font-weight:700; color: var(--gray-900); margin:0;">
                    <i class="fas fa-gavel" style="color: #f59e0b; margin-right: 0.4rem; font-size: 0.8rem;"></i> ${item.title}
                </h4>
                <span class="citation-result-tag" style="background: rgba(14,165,233,0.12); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); font-size: 0.7rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 12px; text-transform: uppercase;">${item.tag}</span>
            </div>
            <p class="citation-result-text" style="font-size:0.83rem; color: var(--gray-700); line-height: 1.45; margin-bottom: 0.5rem;">${item.text}</p>
            <div style="display:flex; align-items:center; justify-content:space-between; font-size: 0.75rem; color: var(--gray-500); border-top: 1px solid var(--gray-200); padding-top: 0.4rem; margin-top: 0.4rem;">
                <span><i class="fas fa-book-open" style="margin-right:0.3rem;"></i> <strong>Citation:</strong> ${item.source} (Supreme Court)</span>
                <button onclick="navigator.clipboard.writeText('${item.title} (${item.source})'); if(window.ui && window.ui.toast) window.ui.toast('Citation copied to clipboard', 'info');" style="background: transparent; border: none; color: var(--primary-500); font-size: 0.72rem; cursor: pointer; display: flex; align-items: center; gap: 0.25rem;">
                    <i class="fas fa-copy"></i> Copy Citation
                </button>
            </div>
        </div>
    `).join('');
};

window.filterPrecedentByTag = (tagQuery, element) => {
    const searchInput = document.getElementById('precedentSearchInput');
    if (searchInput) {
        searchInput.value = tagQuery;
    }
    document.querySelectorAll('.precedent-tag-pill').forEach(btn => btn.classList.remove('active'));
    if (element) element.classList.add('active');
    window.filterPrecedentsList();
};



// ═══════════════════════════════════════════════════════════════
// DRAFT STUDIO — Standalone Draft Generator (accessible from dashboard)
// ═══════════════════════════════════════════════════════════════

let activeStudioDraftType = null;

/**
 * Open the Draft Studio screen from dashboard
 */
window.showDraftStudio = () => {
    switchScreen('draftStudioScreen');
    window.showStudioTypeSelection();
};

window.showStudioTypeSelection = () => {
    const sel = document.getElementById('studioTypeSelection');
    const form = document.getElementById('studioInputForm');
    const out = document.getElementById('studioOutputView');
    if (sel) sel.classList.remove('hidden');
    if (form) form.classList.add('hidden');
    if (out) out.classList.add('hidden');
    renderStudioDraftTypeGrid();
};

window.showStudioInputForm = () => {
    const sel = document.getElementById('studioTypeSelection');
    const form = document.getElementById('studioInputForm');
    const out = document.getElementById('studioOutputView');
    if (sel) sel.classList.add('hidden');
    if (form) form.classList.remove('hidden');
    if (out) out.classList.add('hidden');
};

window.showStudioOutputView = () => {
    const sel = document.getElementById('studioTypeSelection');
    const form = document.getElementById('studioInputForm');
    const out = document.getElementById('studioOutputView');
    if (sel) sel.classList.add('hidden');
    if (form) form.classList.add('hidden');
    if (out) out.classList.remove('hidden');
};

function renderStudioDraftTypeGrid() {
    const grid = document.getElementById('studioDraftTypeGrid');
    if (!grid) return;
    grid.innerHTML = DRAFT_TYPES.map(dt => `
        <div class="draft-type-card" onclick="window.selectStudioDraftType('${dt.id}')">
            <div class="draft-type-num" style="background:${dt.color}18;color:${dt.color}">${dt.number}</div>
            <div class="draft-type-icon-wrap" style="color:${dt.color}">
                <i class="fas ${dt.icon}"></i>
            </div>
            <div class="draft-type-info">
                <h4>${dt.title}</h4>
                <span class="draft-type-sub">${dt.subtitle}</span>
                <p>${dt.description}</p>
            </div>
            <div class="draft-type-chevron" style="color:${dt.color}">
                <i class="fas fa-chevron-right"></i>
            </div>
        </div>
    `).join('');
}

window.selectStudioDraftType = (id) => {
    activeStudioDraftType = DRAFT_TYPES.find(dt => dt.id === id);
    if (!activeStudioDraftType) return;

    const badge = document.getElementById('studioDraftSelectedBadge');
    if (badge) {
        badge.innerHTML = `
            <span style="background:${activeStudioDraftType.color}18;color:${activeStudioDraftType.color};padding:0.3rem 1rem;border-radius:999px;font-size:0.8rem;font-weight:600;display:inline-flex;align-items:center;gap:0.4rem;">
                <i class="fas ${activeStudioDraftType.icon}"></i> Type ${activeStudioDraftType.number} &nbsp;·&nbsp; ${activeStudioDraftType.subtitle}
            </span>`;
    }

    const titleEl = document.getElementById('studioFormTitle');
    const subtitleEl = document.getElementById('studioFormSubtitle');
    if (titleEl) titleEl.textContent = activeStudioDraftType.title;
    if (subtitleEl) subtitleEl.textContent = activeStudioDraftType.description;

    // Pre-fill from existing case data if any
    const pre = {};
    const s = window.state?.caseData || {};
    const preMap = {
        complainant_name: s.complainant_name, complainant_address: s.complainant_address,
        accused_name: s.accused_name, accused_address: s.accused_address,
        cheque_number: s.cheque_number, cheque_date: s.cheque_date,
        cheque_amount: s.cheque_amount, bank_name: s.bank_name,
        branch_name: s.branch_name, dishonour_date: s.dishonour_date || s.date_of_dishonour,
        dishonour_reason: s.dishonour_reason, court_name: s.court_name,
        notice_date: s.notice_date || s.date_of_notice, filing_date: s.filing_date
    };
    Object.assign(pre, preMap);

    const body = document.getElementById('studioFormBody');
    if (body) {
        body.innerHTML = '<div class="draft-fields-grid">' + activeStudioDraftType.fields.map(f => {
            const val = pre[f.name] || '';
            const isWide = f.type === 'textarea' || f.name.includes('address') || f.name.includes('details') || f.name.includes('purpose');
            let inputHtml = '';
            if (f.type === 'textarea') {
                inputHtml = `<textarea id="sfield_${f.name}" class="draft-field-input" ${f.required ? 'required' : ''} placeholder="${f.placeholder || ''}" rows="3">${val}</textarea>`;
            } else if (f.type === 'select') {
                inputHtml = `<select id="sfield_${f.name}" class="draft-field-input" ${f.required ? 'required' : ''}>
                    <option value="">Select...</option>
                    ${(f.options || []).map(o => `<option value="${o}"${val === o ? ' selected' : ''}>${o}</option>`).join('')}
                </select>`;
            } else {
                inputHtml = `<input type="${f.type}" id="sfield_${f.name}" class="draft-field-input" ${f.required ? 'required' : ''} placeholder="${f.placeholder || ''}" value="${val}">`;
            }
            return `<div class="draft-field-group${isWide ? ' full-width' : ''}">
                <label class="draft-field-label" for="sfield_${f.name}">
                    ${f.label}${f.required ? ' <span class="req-star">*</span>' : ''}
                </label>${inputHtml}
            </div>`;
        }).join('') + '</div>';
    }

    window.showStudioInputForm();
};

window.generateStudioDraft = () => {
    if (!activeStudioDraftType) return;
    const missing = [];
    const data = {};
    for (const f of activeStudioDraftType.fields) {
        const el = document.getElementById('sfield_' + f.name);
        if (!el) continue;
        const val = el.value.trim();
        if (f.required && !val) {
            missing.push(f.label);
            el.classList.add('field-error');
        } else {
            el.classList.remove('field-error');
            data[f.name] = val;
        }
    }
    if (missing.length > 0) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('Please fill required fields: ' + missing.slice(0, 3).join(', ') + (missing.length > 3 ? '...' : ''), 'error');
        }
        return;
    }
    try {
        const txt = activeStudioDraftType.generate(data);
        const ta = document.getElementById('studioDraftContent');
        if (ta) ta.value = txt;

        const badge = document.getElementById('studioDraftOutputBadge');
        if (badge) {
            badge.innerHTML = `<span style="background:${activeStudioDraftType.color}18;color:${activeStudioDraftType.color};padding:0.3rem 1rem;border-radius:999px;font-size:0.8rem;font-weight:600;display:inline-flex;align-items:center;gap:0.4rem;">
                <i class="fas ${activeStudioDraftType.icon}"></i> ${activeStudioDraftType.title}
            </span>`;
        }
        const titleEl = document.getElementById('studioDraftOutputTitle');
        if (titleEl) titleEl.textContent = activeStudioDraftType.title;

        window.showStudioOutputView();
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('Draft generated successfully!', 'success');
        }
    } catch (err) {
        console.error('Draft generation error:', err);
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('Failed to generate draft: ' + err.message, 'error');
        }
    }
};

window.copyStudioDraft = () => {
    const ta = document.getElementById('studioDraftContent');
    if (!ta || !ta.value) return;
    navigator.clipboard.writeText(ta.value).then(() => {
        if (window.ui && typeof window.ui.toast === 'function') window.ui.toast('Draft copied to clipboard!', 'success');
    }).catch(() => {
        ta.select();
        document.execCommand('copy');
        if (window.ui && typeof window.ui.toast === 'function') window.ui.toast('Draft copied!', 'success');
    });
};

window.downloadStudioDraft = () => {
    const ta = document.getElementById('studioDraftContent');
    if (!ta || !ta.value) return;
    const name = (activeStudioDraftType?.title || 'Legal_Draft').replace(/\s+/g, '_');
    const blob = new Blob([ta.value], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `JudiQ_${name}_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
};

window.printStudioDraft = () => {
    const ta = document.getElementById('studioDraftContent');
    if (!ta || !ta.value) return;
    const w = window.open('', '_blank');
    w.document.write(`<html><head><title>${activeStudioDraftType?.title || 'Legal Draft'}</title>
    <style>body{font-family:monospace;white-space:pre-wrap;padding:2cm;font-size:12pt;line-height:1.6;}</style>
    </head><body>${ta.value.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</body></html>`);
    w.document.close();
    w.print();
};



// ============================================================================
// WHAT-IF SCENARIO MODELER LOGIC
// ============================================================================

window.updateWhatIf = (key, value) => {
    if (!window.state.caseData) {
        window.state.caseData = {};
    }
    window.state.caseData[key] = value;
};

window.runAnalysis = async () => {
    if (!window.state.caseData) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('No case data available to analyze.', 'warning');
        }
        return;
    }
    
    if (window.ui && typeof window.ui.show === 'function') window.ui.show('analysisLoading');
    try {
        const userId = window.state.currentUser ? window.state.currentUser.uid : 'ANONYMOUS';
        const rawPayload = { ...window.state.caseData, user_id: userId };
        
        // If sanitizePayload is available (from wizard.js), use it, otherwise use raw
        const payload = typeof sanitizePayload === 'function' ? sanitizePayload(rawPayload) : rawPayload;
        
        const result = await api.analyze(payload);
        window.state.analysisResult = result;
        
        if (window.saveCaseToHistory) {
            window.saveCaseToHistory(payload, result);
        }
        
        if (window.ui && typeof window.ui.hide === 'function') window.ui.hide('analysisLoading');
        
        // Re-render the results dashboard with the new data
        if (typeof renderResults === 'function') {
            renderResults(result);
        }
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('Case successfully re-analyzed with new variables.', 'success');
        }
    } catch (err) {
        if (window.ui && typeof window.ui.hide === 'function') window.ui.hide('analysisLoading');
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('Error recalculating: ' + err.message, 'error');
        }
    }
};

// --- Copy Strategy Memo to Clipboard ---
window.copyStrategyMemoToClipboard = function() {
    const res = window.state.analysisResult;
    if (!res) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('No analysis report available to copy.', 'warning');
        } else {
            alert('No analysis report available to copy.');
        }
        return;
    }
    
    let memo = `# JUDIQ AI — Litigation Strategy & Weakness Audit Memo\n`;
    memo += `Generated on: ${new Date().toLocaleDateString()} | Domain: ${res.domain || 'Section 138 NI Act'}\n\n`;
    memo += `## 1. Viability & Score Summary\n`;
    memo += `- **Overall Score**: ${res.score !== undefined ? res.score : 'N/A'}/100\n`;
    memo += `- **Verdict**: ${res.verdict || 'ANALYZED'}\n`;
    if (res.summary) memo += `- **Summary**: ${res.summary}\n`;
    
    if (res.statutory_timeline || res.limitation) {
        memo += `\n## 2. Limitation & Procedural Audit\n`;
        if (res.limitation) {
            memo += `- **Status**: ${res.limitation.status || 'CHECKED'}\n`;
            memo += `- **Days Remaining**: ${res.limitation.days_remaining !== undefined ? res.limitation.days_remaining : 'N/A'}\n`;
        }
    }

    if (res.vulnerabilities && res.vulnerabilities.length > 0) {
        memo += `\n## 3. Adversarial Weaknesses & Vulnerabilities\n`;
        res.vulnerabilities.forEach((v, idx) => {
            const risk = typeof v === 'object' ? (v.risk || v.title || v.issue || JSON.stringify(v)) : String(v);
            memo += `${idx + 1}. ${risk}\n`;
        });
    }

    if (res.next_best_actions && res.next_best_actions.length > 0) {
        memo += `\n## 4. Recommended Next Actions\n`;
        res.next_best_actions.forEach((act, idx) => {
            memo += `${idx + 1}. ${act}\n`;
        });
    }
    
    memo += `\n---\n*Report generated by JudiQ AI Litigation Operating System.*`;
    
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(memo).then(() => {
            if (window.ui && typeof window.ui.toast === 'function') {
                window.ui.toast('Strategy Memo copied to clipboard in Markdown format!', 'success');
            } else {
                alert('Strategy Memo copied to clipboard!');
            }
        }).catch(err => {
            console.error('Clipboard copy failed:', err);
            if (window.ui && typeof window.ui.toast === 'function') {
                window.ui.toast('Failed to copy to clipboard.', 'error');
            }
        });
    } else {
        // Fallback for non-secure contexts
        const textarea = document.createElement('textarea');
        textarea.value = memo;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('Strategy Memo copied to clipboard!', 'success');
        }
    }
};

// --- Print Strategy Memo in High-Court Formal Format ---
window.printStrategyMemo = function() {
    const res = window.state.analysisResult;
    if (!res) {
        if (window.ui && typeof window.ui.toast === 'function') {
            window.ui.toast('No analysis report available to print.', 'warning');
        } else {
            alert('No analysis report available to print.');
        }
        return;
    }
    
    const printWin = window.open('', '_blank', 'width=900,height=800');
    if (!printWin) return;
    
    const today = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' });
    const score = res.score !== undefined ? res.score : 'N/A';
    const domain = res.domain || 'Section 138 NI Act / Criminal Jurisdiction';
    
    const html = `<!DOCTYPE html>
<html>
<head>
    <title>JUDIQ LITIGATION STRATEGY MEMORANDUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @media print {
            @page { margin: 20mm; }
            body { background: white !important; color: black !important; }
        }
        body { font-family: 'Inter', sans-serif; margin: 40px; color: #1e293b; line-height: 1.6; }
        .header-seal { text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 15px; margin-bottom: 25px; }
        .header-seal h1 { font-family: 'Cinzel', serif; font-size: 22px; letter-spacing: 0.1em; margin: 0; color: #0f172a; text-transform: uppercase; }
        .header-seal p { margin: 4px 0 0 0; font-size: 11px; color: #64748b; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
        .meta-box { display: flex; justify-content: space-between; background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 18px; border-radius: 6px; margin-bottom: 25px; font-size: 12px; }
        .section-title { font-family: 'Cinzel', serif; font-size: 14px; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 25px; color: #0f172a; font-weight: 700; }
        .score-badge { display: inline-block; padding: 4px 12px; background: #0f172a; color: white; font-weight: 700; border-radius: 4px; font-size: 14px; }
        .footer-seal { margin-top: 40px; padding-top: 15px; border-top: 1px dashed #cbd5e1; font-size: 10px; color: #94a3b8; text-align: center; }
    </style>
</head>
<body>
    <div class="header-seal">
        <h1>CONFIDENTIAL LITIGATION STRATEGY MEMORANDUM</h1>
        <p>JUDIQ AI ADVERSARIAL ENGINE • HIGH COURT & STATUTORY JURISDICTION SUITE</p>
    </div>
    <div class="meta-box">
        <div><strong>DATE:</strong> ${today}</div>
        <div><strong>DOMAIN:</strong> ${domain}</div>
        <div><strong>VIABILITY SCORE:</strong> <span class="score-badge">${score}/100</span></div>
    </div>
    <div class="section-title">1. EXECUTIVE SUMMARY & VERDICT</div>
    <p><strong>Verdict:</strong> ${res.verdict || 'ANALYZED'}</p>
    ${res.summary ? `<p>${res.summary}</p>` : ''}
    
    ${res.vulnerabilities && res.vulnerabilities.length ? `
    <div class="section-title">2. ADVERSARIAL VULNERABILITIES & DEFECTS</div>
    <ul>
        ${res.vulnerabilities.map(v => `<li>${typeof v === 'object' ? (v.risk || v.title || JSON.stringify(v)) : v}</li>`).join('')}
    </ul>` : ''}

    ${res.next_best_actions && res.next_best_actions.length ? `
    <div class="section-title">3. STRATEGIC COUNTERMEASURES & ACTIONS</div>
    <ol>
        ${res.next_best_actions.map(a => `<li>${a}</li>`).join('')}
    </ol>` : ''}

    <div class="footer-seal">
        CONFIDENTIAL & PRIVILEGED LEGAL WORK PRODUCT • GENERATED BY JUDIQ LITIGATION OS • RECORD HASH: ${Math.random().toString(36).substring(2, 10).toUpperCase()}
    </div>
    <script>
        window.onload = function() { window.print(); };
    </script>
</body>
</html>`;
    
    printWin.document.write(html);
    printWin.document.close();
};

// --- Command Palette Functions ---
window.toggleCommandPalette = function(forceState) {
    const modal = document.getElementById('commandPaletteModal');
    if (!modal) return;
    const input = document.getElementById('commandPaletteInput');
    
    const shouldOpen = forceState !== undefined ? forceState : !modal.classList.contains('open');
    if (shouldOpen) {
        modal.classList.add('open');
        if (input) {
            input.value = '';
            setTimeout(() => input.focus(), 100);
        }
        window.filterCommandPalette('');
    } else {
        modal.classList.remove('open');
    }
};

window.filterCommandPalette = function(query) {
    const q = (query || '').toLowerCase().trim();
    const container = document.getElementById('commandListContainer');
    if (!container) return;
    
    const items = container.querySelectorAll('.command-item');
    items.forEach(item => {
        const txt = item.innerText.toLowerCase();
        if (!q || txt.includes(q)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
};

window.executeCommand = function(cmd) {
    window.toggleCommandPalette(false);
    switch (cmd) {
        case 'demo_s138':
            if (window.loadDemoCase) window.loadDemoCase('clean_case');
            break;
        case 'demo_sarfaesi':
            if (window.loadDemoCase) window.loadDemoCase('sarfaesi_demo');
            break;
        case 'demo_s141':
            if (window.loadDemoCase) window.loadDemoCase('directors_missing');
            break;
        case 'new_s138':
            if (window.selectRegisterDomain) window.selectRegisterDomain('ni_act');
            if (window.startWizard) window.startWizard();
            break;
        case 'new_sarfaesi':
            if (window.selectRegisterDomain) window.selectRegisterDomain('sarfaesi');
            if (window.startWizard) window.startWizard();
            break;
        case 'print_memo':
            if (window.printStrategyMemo) window.printStrategyMemo();
            break;
        case 'copy_memo':
            if (window.copyStrategyMemoToClipboard) window.copyStrategyMemoToClipboard();
            break;
        case 'search_precedents':
            const el = document.getElementById('precedentSearchInput');
            if (el) { el.scrollIntoView({ behavior: 'smooth' }); el.focus(); }
            break;
        case 'nav_dashboard':
            if (window.showDashboard) window.showDashboard();
            break;
        case 'open_simulator':
            const simEl = document.getElementById('strategySimulatorSection');
            if (simEl) { simEl.scrollIntoView({ behavior: 'smooth' }); }
            break;
        case 'toggle_cocounsel':
            const toggleBtn = document.getElementById('coCounselToggleBtn');
            if (toggleBtn) { toggleBtn.click(); }
            break;
        case 'toggle_theme':
            if (window.toggleTheme) window.toggleTheme();
            break;
        case 'toggle_lang':
            if (window.toggleLanguage) window.toggleLanguage();
            break;
        default:
            break;
    }
};

// Global Keyboard Shortcut Listeners
document.addEventListener('keydown', (e) => {
    // Ctrl+K or Cmd+K
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        window.toggleCommandPalette();
    }
    // Escape key
    if (e.key === 'Escape') {
        const cmdModal = document.getElementById('commandPaletteModal');
        if (cmdModal && cmdModal.classList.contains('open')) {
            window.toggleCommandPalette(false);
        }
        window.toggleMobileNav(false);
    }
});

// Mobile Navigation Toggle
window.toggleMobileNav = (forceState) => {
    const drawer = document.getElementById('mobileNavDrawer');
    const backdrop = document.getElementById('mobileNavBackdrop');
    if (!drawer || !backdrop) return;

    const isOpen = typeof forceState === 'boolean' ? forceState : !drawer.classList.contains('open');
    if (isOpen) {
        drawer.classList.add('open');
        backdrop.classList.add('open');
        document.body.style.overflow = 'hidden';
    } else {
        drawer.classList.remove('open');
        backdrop.classList.remove('open');
        document.body.style.overflow = '';
    }
};

/**
 * Universal Case Analysis Starter
 */
window.startCaseAnalysis = (initialData = {}) => {
    window.state = window.state || {};
    window.state.caseData = { ...(initialData || {}) };
    window.state.currentStep = 1;
    try {
        localStorage.setItem('judiq_wizard_autosave', JSON.stringify(window.state.caseData));
    } catch (_) {}
    switchScreen('caseWizardScreen');
    if (typeof window.setCaseType === 'function' && initialData.case_type) {
        window.setCaseType(initialData.case_type);
    } else if (typeof renderWizardStep === 'function') {
        renderWizardStep();
    }
};

/**
 * Demo Case Loaders with Instant Preset Population
 */
window.loadDemoCase = () => {
    if (typeof window.loadSampleCaseData === 'function') {
        window.loadSampleCaseData(window.SAMPLE_NI_ACT_PRESET);
    }
};

window.loadSarfaesiDemoCase = () => {
    if (typeof window.loadSampleCaseData === 'function') {
        window.loadSampleCaseData(window.SAMPLE_SARFAESI_PRESET);
    }
};

window.loadCompositeDemoCase = () => {
    if (typeof window.loadSampleCaseData === 'function') {
        window.loadSampleCaseData(window.SAMPLE_COMPOSITE_PRESET);
    }
};

window.loadCriminalDemoCase = () => {
    if (typeof window.loadSampleCaseData === 'function') {
        window.loadSampleCaseData(window.SAMPLE_CRIMINAL_PRESET);
    }
};

window.loadCivilDemoCase = () => {
    if (typeof window.loadSampleCaseData === 'function') {
        window.loadSampleCaseData(window.SAMPLE_CIVIL_PRESET);
    }
};



