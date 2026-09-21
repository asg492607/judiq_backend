/**
 * UI Utility Module
 */
export const ui = {
    show(id) {
        const el = document.getElementById(id);
        if (el) el.classList.remove('hidden');
    },
    
    hide(id) {
        const el = document.getElementById(id);
        if (el) el.classList.add('hidden');
    },
    
    toggle(id, condition) {
        if (condition) this.show(id);
        else this.hide(id);
    },
    
    setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    },
    
    setHTML(id, html) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = html;
    },
    
    toast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let icon = 'info-circle';
        if (type === 'success') icon = 'check-circle';
        if (type === 'error') icon = 'exclamation-circle';
        if (type === 'warning') icon = 'exclamation-triangle';
        
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <div class="toast-content">${message}</div>
            <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.animation = 'slideOutRight 0.3s ease-in forwards';
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    },

    copyToClipboard(text, label = 'Content') {
        if (!text) return;
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                this.toast(`${label} copied to clipboard!`, 'success');
            }).catch(() => {
                this.fallbackCopy(text, label);
            });
        } else {
            this.fallbackCopy(text, label);
        }
    },

    fallbackCopy(text, label = 'Content') {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            this.toast(`${label} copied to clipboard!`, 'success');
        } catch (err) {
            this.toast('Failed to copy text', 'error');
        }
        document.body.removeChild(textArea);
    }
};

window.ui = ui;

/**
 * Screen switching logic
 */
export function switchScreen(targetScreenId) {
    // Public screens accessible without a paid subscription
    const publicScreens = [
        'landingScreen', 'loginScreen', 'registerScreen', 
        'termsScreen', 'privacyScreen', 'refundScreen', 'sharedReportScreen'
    ];

    const screens = [
        'landingScreen', 'loginScreen', 'registerScreen', 
        'dashboardScreen', 'caseWizardScreen', 
        'resultsScreen', 'termsScreen', 'privacyScreen', 'refundScreen',
        'draftGeneratorScreen', 'draftStudioScreen', 'quickAnalysisScreen',
        'reportScreen', 'sharedReportScreen', 'bankRecoveryScreen', 'adminPortalScreen',
        // ── CMS Screens ───────────────────────────────────────
        'cmsHomeScreen', 'caseListScreen', 'caseCreateScreen', 'caseDetailScreen',
        'clientListScreen', 'clientCreateScreen', 'clientDetailScreen',
        'documentLibraryScreen', 'draftWorkflowScreen',
        'teamManagementScreen', 'cmsAnalyticsScreen', 'auditTrailScreen'
    ];

    // Protection Gate: Require authentication AND paid subscription for all platform services
    if (!publicScreens.includes(targetScreenId)) {
        const currentUser = (window.state && window.state.currentUser) || (typeof window.supabaseClient !== 'undefined' && window.supabaseClient.auth);
        const hasGeneralAuth = !!currentUser || !!localStorage.getItem('judiq_token') || !!localStorage.getItem('judiq_jwt') || !!localStorage.getItem('judiq_active_user_email');

        if (!hasGeneralAuth) {
            if (ui && typeof ui.toast === 'function') {
                ui.toast("Please sign in or register to access the platform.", "warning");
            }
            screens.forEach(id => ui.hide(id));
            ui.show('loginScreen');
            return;
        }

        // Check if user is an administrator (exempt from subscription paywall)
        const role = (window.state && window.state.currentRole) || 
                     (currentUser && localStorage.getItem(`judiq_role_${currentUser.uid}`)) || '';
        const userEmail = ((currentUser && currentUser.email) || '').toLowerCase().trim();
        const userId = ((currentUser && (currentUser.uid || currentUser.id)) || '').toLowerCase().trim();
        const isAdmin = role === 'admin' || 
                        userEmail.includes('aixynztechnologies') || 
                        userId.includes('aixynztechnologies') || 
                        !!localStorage.getItem('judiq_admin_jwt');

        if (!isAdmin) {
            let isPaid = false;

            // 1. Check local plan record
            const planStr = localStorage.getItem('judiq_selected_plan');
            if (planStr) {
                try {
                    const plan = JSON.parse(planStr);
                    if (plan.status === 'ACTIVE' || plan.status === 'PAID') {
                        isPaid = true;
                    }
                } catch (e) {}
            }

            // 2. Check loaded state quota
            if (window.state && window.state.userQuota) {
                const q = window.state.userQuota;
                if ((q.plan_status === 'ACTIVE' || q.plan_status === 'PAID' || q.plan_status === 'APPROVED') && q.is_active) {
                    isPaid = true;
                } else if (q.plan_status === 'PENDING_PAYMENT' || !q.is_active || q.monthly_report_limit === 0) {
                    isPaid = false;
                }
            }

            if (!isPaid) {
                if (ui && typeof ui.toast === 'function') {
                    ui.toast("🔒 Subscription required. Please complete checkout to access the platform.", "warning");
                }
                screens.forEach(id => ui.hide(id));
                ui.show('landingScreen');
                window.location.hash = 'pricingSection';
                setTimeout(() => {
                    const pricingEl = document.getElementById('pricingSection');
                    if (pricingEl) pricingEl.scrollIntoView({ behavior: 'smooth' });
                    if (typeof window.subscribeToSelectedModularPlan === 'function') {
                        window.subscribeToSelectedModularPlan();
                    }
                }, 400);
                return;
            }
        }
    }

    // Auth gate for bankRecoveryScreen: require officer or account login
    if (targetScreenId === 'bankRecoveryScreen') {
        const bankUserStr = localStorage.getItem('judiq_bank_user');
        const hasBankJwt = !!localStorage.getItem('judiq_bank_jwt');
        const currentUser = (window.state && window.state.currentUser) || (typeof window.supabaseClient !== 'undefined' && window.supabaseClient.auth);
        const hasGeneralAuth = !!currentUser || !!localStorage.getItem('judiq_token');

        if (!bankUserStr && !hasBankJwt && !hasGeneralAuth) {
            if (window.toast) {
                window.toast.show("Please sign in or register with your institutional credentials to access the Recovery OS.", "warning");
            }
            if (typeof window.openBankAuthModal === 'function') {
                window.openBankAuthModal();
            }
            return;
        }
    }

    screens.forEach(id => ui.hide(id));
    ui.show(targetScreenId);
    
    // Reset scroll
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Reactive Destination Screen Initializers
    if (targetScreenId === 'caseWizardScreen' && typeof window.renderWizardStep === 'function') {
        window.renderWizardStep();
    } else if (targetScreenId === 'dashboardScreen' && typeof window.renderDashboard === 'function') {
        window.renderDashboard();
    } else if (targetScreenId === 'caseListScreen' && typeof window.loadCasesList === 'function') {
        window.loadCasesList();
    } else if (targetScreenId === 'bankRecoveryScreen' && typeof window.updateBankOfficerUI === 'function') {
        window.updateBankOfficerUI();
    } else if (targetScreenId === 'draftStudioScreen') {
        if (typeof window.showStudioTypeSelection === 'function') {
            window.showStudioTypeSelection();
        } else if (typeof window.renderStudioDraftTypeGrid === 'function') {
            window.renderStudioDraftTypeGrid();
        }
    }

    // Dismiss tour overlay if switching away from dashboard
    const tourOverlay = document.getElementById('guidedTourOverlay');
    if (tourOverlay && targetScreenId !== 'dashboardScreen') {
        tourOverlay.classList.remove('open');
    }

    // First-time visit guided tour check (only if user stays on dashboard)
    if (targetScreenId === 'dashboardScreen') {
        const tourCompleted = localStorage.getItem('judiq_tour_completed') === 'true';
        if (!tourCompleted && typeof window.startGuidedTour === 'function') {
            setTimeout(() => {
                const activeScreen = document.querySelector('.main-screen:not(.hidden)');
                if (activeScreen && activeScreen.id === 'dashboardScreen') {
                    window.startGuidedTour();
                }
            }, 1000);
        }
    }
}
window.switchScreen = switchScreen;

