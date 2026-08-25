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
    const screens = [
        'landingScreen', 'loginScreen', 'registerScreen', 
        'roleScreen', 'dashboardScreen', 'caseWizardScreen', 
        'resultsScreen', 'termsScreen', 'privacyScreen', 'refundScreen',
        'draftGeneratorScreen', 'draftStudioScreen', 'quickAnalysisScreen',
        'reportScreen'
    ];
    
    screens.forEach(id => ui.hide(id));
    ui.show(targetScreenId);
    
    // Reset scroll
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // First-time visit guided tour check
    if (targetScreenId === 'dashboardScreen') {
        const tourCompleted = localStorage.getItem('judiq_tour_completed') === 'true';
        if (!tourCompleted && typeof window.startGuidedTour === 'function') {
            setTimeout(() => {
                window.startGuidedTour();
            }, 800);
        }
    }
}
window.switchScreen = switchScreen;

