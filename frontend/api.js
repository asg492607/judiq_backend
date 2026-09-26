import { API_BASE_URL } from './config.js?v=14';

function isJwtExpired(jwtToken) {
    if (!jwtToken || typeof jwtToken !== 'string') return true;
    try {
        const parts = jwtToken.split('.');
        if (parts.length !== 3) return true;
        const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
        if (payload.exp && (payload.exp * 1000) < (Date.now() + 30000)) {
            return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

/**
 * Fetch with automatic retry on transient failures and cold-boot waking.
 */
export async function fetchWithRetry(url, options = {}, maxRetries = 3, baseDelay = 1500) {
    let lastError;
    
    // Inject valid JWT Authorization (prioritize active admin JWT if valid)
    let adminToken = localStorage.getItem("judiq_admin_jwt");
    if (adminToken && isJwtExpired(adminToken)) {
        localStorage.removeItem("judiq_admin_jwt");
        adminToken = null;
    }

    let token = adminToken || localStorage.getItem("judiq_jwt");
    if (token && isJwtExpired(token)) {
        localStorage.removeItem("judiq_jwt");
        token = null;
    }

    if (!token && !url.includes('/auth/anonymous')) {
        try {
            const authRes = await fetch(`${API_BASE_URL}/api/v1/auth/anonymous`, { method: 'POST' });
            if (authRes.ok) {
                const authData = await authRes.json();
                token = authData.access_token;
                localStorage.setItem("judiq_jwt", token);
                // Also initialize the user_id in state if possible
                if (window.state) window.state.user_id = authData.user_id;
            }
        } catch (e) {
            console.warn("Failed to fetch anonymous JWT:", e);
        }
    }

    options.headers = options.headers || {};
    // Preserve caller-provided Authorization headers (e.g. admin JWT)
    if (!options.headers['Authorization'] && !options.headers['authorization']) {
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }
    }

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const controller = new AbortController();
            const timeoutMs = options.timeout || 90000;
            const timeout = setTimeout(() => controller.abort(), timeoutMs);
            let response;
            try {
                const { timeout: _customTimeout, ...fetchOpts } = options;
                response = await fetch(url, { ...fetchOpts, signal: controller.signal });
            } finally {
                clearTimeout(timeout);
            }
            if (response.status === 401 && !url.includes('/auth/anonymous') && !url.includes('/admin/')) {
                localStorage.removeItem("judiq_jwt");
                try {
                    const authRes = await fetch(`${API_BASE_URL}/api/v1/auth/anonymous`, { method: 'POST' });
                    if (authRes.ok) {
                        const authData = await authRes.json();
                        token = authData.access_token;
                        localStorage.setItem("judiq_jwt", token);
                        if (window.state) window.state.user_id = authData.user_id;
                        if (!options.headers['Authorization'] && !options.headers['authorization']) {
                            options.headers['Authorization'] = `Bearer ${token}`;
                        }
                        continue;
                    }
                } catch (e) {
                    console.error("Token refresh failed:", e);
                }
            }
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                // Backend may return: { error: "..." }, { message: "..." }, or { detail: "..." }
                let errorMsg = errorData.error || errorData.message || `API Error: ${response.status} ${response.statusText}`;
                if (errorData.detail) {
                    if (Array.isArray(errorData.detail)) {
                        errorMsg = "Validation Error: " + errorData.detail.map(d => `${d.loc.join('.')}: ${d.msg}`).join(', ');
                    } else {
                        errorMsg = errorData.detail;
                    }
                }
                const error = new Error(errorMsg);
                error.status = response.status;
                throw error;
            }
            return response;
        } catch (err) {
            lastError = err;
            if (err.name === 'AbortError') {
                const secs = Math.round((options.timeout || 90000) / 1000);
                throw new Error(`Request timed out after ${secs} seconds.`);
            }
            const isNetworkOrCors = !err.status || err.message?.includes('fetch') || err.message?.includes('network');
            const retryable = isNetworkOrCors || err.status === 408 || err.status === 429 || err.status >= 500;
            if (attempt < maxRetries && retryable) {
                const delay = Math.round(baseDelay * Math.pow(1.8, attempt));
                await new Promise(r => setTimeout(r, delay));
            } else if (!retryable) {
                throw err;
            }
        }
    }
    throw lastError;
}

export const api = {
    async analyze(data) {
        const currentLang = (window.i18n && window.i18n.currentLang) || localStorage.getItem('judiq_lang') || 'en';
        const currentUser = window.state ? window.state.currentUser : null;
        const userId = (data && data.user_id) || (currentUser ? (currentUser.uid || currentUser.id) : '') || 'ANONYMOUS';
        const userEmail = (data && data.email) || (currentUser ? currentUser.email : '') || localStorage.getItem('judiq_active_user_email') || '';
        const userRole = (data && data.role) || (window.state && window.state.currentRole) || (currentUser && currentUser.role) || (currentUser ? localStorage.getItem(`judiq_role_${currentUser.uid}`) : '') || '';
        
        const payload = {
            language: currentLang,
            lang: currentLang,
            user_id: userId,
            email: userEmail,
            role: userRole,
            ...data
        };
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        let responseBody; try { responseBody = await response.json(); } catch (e) { throw new Error("Invalid JSON from server."); }
        return responseBody.data !== undefined
            ? { ...responseBody.data, ...responseBody }
            : responseBody;
    },
    
    async generatePdf(data) {
        const currentUser = window.state ? window.state.currentUser : null;
        const userId = (data && data.user_id) || (currentUser ? (currentUser.uid || currentUser.id) : '') || '';
        const userEmail = (data && data.email) || (currentUser ? currentUser.email : '') || localStorage.getItem('judiq_active_user_email') || '';
        const userRole = (data && data.role) || (window.state && window.state.currentRole) || (currentUser && currentUser.role) || (currentUser ? localStorage.getItem(`judiq_role_${currentUser.uid}`) : '') || '';

        const payload = {
            user_id: userId,
            email: userEmail,
            role: userRole,
            ...data
        };
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/documents/generate-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.blob(); } catch (e) { throw new Error("Failed to read file blob."); }
    },

    async generateDraftPdf(title, content, metadata = {}) {
        const currentUser = window.state ? window.state.currentUser : null;
        const userId = (metadata && metadata.user_id) || (currentUser ? (currentUser.uid || currentUser.id) : '') || '';
        const userEmail = (metadata && metadata.email) || (currentUser ? currentUser.email : '') || localStorage.getItem('judiq_active_user_email') || '';
        const userRole = (metadata && metadata.role) || (window.state && window.state.currentRole) || (currentUser && currentUser.role) || (currentUser ? localStorage.getItem(`judiq_role_${currentUser.uid}`) : '') || '';

        const draftType = (metadata && metadata.draft_type) || (window.activeDraftType && window.activeDraftType.id) || title;
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/documents/draft-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                title, 
                content, 
                draft_type: draftType,
                user_id: userId,
                email: userEmail,
                role: userRole,
                metadata 
            })
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || errData.detail || "Draft generation blocked: quota exceeded.");
        }
        try { return await response.blob(); } catch (e) { throw new Error("Failed to read draft blob."); }
    },

    async getRecentCases(userId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cases?user_id=${encodeURIComponent(userId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Invalid JSON from server."); }
    },

    async getCaseDetails(caseId, userId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cases/detail?case_id=${encodeURIComponent(caseId)}&user_id=${encodeURIComponent(userId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Invalid JSON from server."); }
    },

    async deleteCase(caseId, userId) {
        const uid = userId || localStorage.getItem('judiq_user_id') || 'ANONYMOUS';
        try {
            const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cases/delete?case_id=${encodeURIComponent(caseId)}&user_id=${encodeURIComponent(uid)}`, {
                method: 'DELETE'
            });
            return await response.json();
        } catch (err) {
            if (err.status === 405 || err.message?.includes('405') || err.message?.includes('Method Not Allowed')) {
                const postRes = await fetchWithRetry(`${API_BASE_URL}/api/v1/cases/delete?case_id=${encodeURIComponent(caseId)}&user_id=${encodeURIComponent(uid)}`, {
                    method: 'POST'
                });
                return await postRes.json();
            }
            throw err;
        }
    },

    // ── Case AI Chat & RAG Workspace ──────────────────────────────────────────
    async initCaseChat(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/case-chat/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Invalid response from case chat service."); }
    },

    async queryCaseChat(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/case-chat/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to process legal query."); }
    },

    async updateCaseFact(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/case-chat/update-fact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update case fact."); }
    },

    async generateCrossExam(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/case-chat/cross-exam`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to generate cross-examination."); }
    },

    async generateArguments(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/case-chat/arguments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to generate arguments."); }
    },

    async exportCaseFacts(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/case-chat/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to export case dossier."); }
    },

    async clearCaseChatHistory(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/case-chat/clear-history`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_id: caseId })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to clear chat history."); }
    },

    async getDraftHistory(caseId, draftType) {
        const response = await fetchWithRetry(
            `${API_BASE_URL}/api/v1/documents/draft/history?case_id=${encodeURIComponent(caseId)}&draft_type=${encodeURIComponent(draftType)}`
        );
        try { return await response.json(); } catch (e) { throw new Error("Invalid JSON from server."); }
    },

    async verifyMemo(formData) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/verify/memo`, {
            method: 'POST',
            body: formData
        }, 0);
        try { return await response.json(); } catch (e) { throw new Error("Invalid JSON from server."); }
    },

    async getUserQuota(userId, email = '') {
        const response = await fetchWithRetry(
            `${API_BASE_URL}/api/v1/user/quota?user_id=${encodeURIComponent(userId)}&email=${encodeURIComponent(email)}`
        );
        try { return await response.json(); } catch (e) { throw new Error("Failed to load user quota."); }
    },

    async verifyAdminAuth(email, password = '') {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/auth/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        try { return await response.json(); } catch (e) { throw new Error("Admin verification failed."); }
    },

    async getAdminStats(token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load admin stats."); }
    },

    async getAdminUsers(token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load user list."); }
    },

    async allocateUserQuota(userId, monthlyLimit, role = 'law_firm', email = '', token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users/allocate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ user_id: userId, monthly_limit: monthlyLimit, role, email })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update user quota."); }
    },

    async resetUserUsage(userId, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users/reset-usage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ user_id: userId })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to reset user usage."); }
    },

    async toggleUserStatus(userId, isActive, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users/toggle-status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ user_id: userId, is_active: isActive })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to toggle user status."); }
    },

    async submitSubscriptionPlan(planData) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/subscription/submit-plan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(planData)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to submit plan request."); }
    },

    async getPendingPlans(token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/pending-plans`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load pending plans."); }
    },

    async approvePlanRequest(userId, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/approve-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ user_id: userId })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to approve plan request."); }
    },

    async rejectPlanRequest(userId, reason = '', token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/reject-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ user_id: userId, reason })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to reject plan request."); }
    },

    // ── Bank Auth & Recovery OS Methods ──
    async bankLogin(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/bank/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Bank authentication failed."); }
    },

    async getBankProfile(officerId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/bank/auth/profile?officer_id=${encodeURIComponent(officerId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load bank profile."); }
    },

    async getBankBranches() {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/bank/branches`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load institutional branches."); }
    },

    // ── Admin Bank Operations Governance ──
    async getAdminBankStats(token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/bank/stats`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load bank stats."); }
    },

    async getAdminBankOfficers(token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/bank/officers`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load bank officers."); }
    },

    async createAdminBankOfficer(officerData, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/bank/officers/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(officerData)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to provision bank officer."); }
    },

    async allocateBankOfficerQuota(officerId, monthlyLimit, role, branchName, bankName, email, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/bank/officers/allocate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                officer_id: officerId,
                monthly_audit_limit: monthlyLimit,
                role: role,
                branch_name: branchName,
                bank_name: bankName,
                email: email
            })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update bank officer quota."); }
    },

    async toggleBankOfficerStatus(officerId, isActive, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/bank/officers/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ officer_id: officerId, is_active: isActive })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to toggle bank officer status."); }
    },

    async getAdminBankAudits(token, limit = 50) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/bank/audits?limit=${limit}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load bank audits."); }
    },

    async getSecurityLogs(token, limit = 50) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/security/logs?limit=${limit}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load security logs."); }
    },

    async bulkBonusQuotas(bonus, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users/bulk-bonus`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ bonus: parseInt(bonus, 10) })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to grant bulk quota bonus."); }
    },

    async createLitigatorAccount(data, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to create litigator account."); }
    },

    async createSpecialUserAccount(data, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users/create-special`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to create special user account."); }
    },

    async getSystemHealth(token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/system/health`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load system health."); }
    },

    async clearSystemCache(token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/system/cache/clear`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({})
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to clear system cache."); }
    },

    async getPlansCatalog(token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/plans/catalog`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load plans catalog."); }
    },

    async updatePlanCatalog(planData, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/plans/catalog/update`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(planData)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update plan in catalog."); }
    },

    async assignUserPlan(payload, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users/assign-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to assign plan to customer."); }
    },

    async extendUserValidity(payload, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/users/extend-validity`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to extend subscription validity."); }
    },

    async getDeploymentAlert() {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/system/deployment-alert`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load deployment alert."); }
    },

    async setDeploymentAlert(payload, token) {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/system/deployment-alert`, {
            method: 'POST',
            headers,
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update deployment alert."); }
    },

    async toggleDeploymentAlert(isActive, token) {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/system/deployment-alert/toggle`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ is_active: isActive })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to toggle deployment alert."); }
    },

    async getAdminPayments(token, limit = 100, status = '', userId = '') {
        let url = `${API_BASE_URL}/api/v1/admin/payments?limit=${limit}`;
        if (status && status !== 'ALL') url += `&status=${encodeURIComponent(status)}`;
        if (userId) url += `&user_id=${encodeURIComponent(userId)}`;
        const response = await fetchWithRetry(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load payment transactions."); }
    },

    async recordManualPayment(payload, token) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/payments/record-manual`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to record manual payment."); }
    },

    async getUnifiedLogs(token, limit = 100, action = '', userId = '') {
        let url = `${API_BASE_URL}/api/v1/admin/logs/all?limit=${limit}`;
        if (action && action !== 'ALL') url += `&action=${encodeURIComponent(action)}`;
        if (userId) url += `&user_id=${encodeURIComponent(userId)}`;
        const response = await fetchWithRetry(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to load activity logs."); }
    },

    async ingestPrecedent(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/ingest/precedents`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to ingest precedent."); }
    },

    // ══════════════════════════════════════════════════════════
    // CMS — CASE MANAGEMENT API
    // ══════════════════════════════════════════════════════════
    async createCase(caseData) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(caseData)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to create case."); }
    },

    async listCases(filters = {}) {
        const params = new URLSearchParams();
        if (filters.status) params.append('status', filters.status);
        if (filters.case_type) params.append('case_type', filters.case_type);
        if (filters.priority) params.append('priority', filters.priority);
        if (filters.search) params.append('search', filters.search);
        if (filters.page) params.append('page', filters.page);
        if (filters.limit) params.append('limit', filters.limit);
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases?${params.toString()}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to list cases."); }
    },

    async getCaseDetail(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load case detail."); }
    },

    async updateCase(caseId, updates) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update case."); }
    },

    async updateCaseStatus(caseId, status) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update status."); }
    },

    async deleteCmsCase(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}`, {
            method: 'DELETE'
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to archive case."); }
    },

    async shareCase(caseId, userIds) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/share`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_ids: userIds })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to share case."); }
    },

    async getCaseTimeline(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/timeline`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load timeline."); }
    },

    async analyzeCmsCase(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/analyze`, {
            method: 'POST'
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to run case analysis."); }
    },

    // ══════════════════════════════════════════════════════════
    // CMS — CLIENT MANAGEMENT API
    // ══════════════════════════════════════════════════════════
    async createClient(clientData) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/clients`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clientData)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to create client."); }
    },

    async listClients(filters = {}) {
        const params = new URLSearchParams();
        if (filters.search) params.append('search', filters.search);
        if (filters.client_type) params.append('client_type', filters.client_type);
        if (filters.page) params.append('page', filters.page);
        if (filters.limit) params.append('limit', filters.limit);
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/clients?${params.toString()}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to list clients."); }
    },

    async getClientDetail(clientId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/clients/${encodeURIComponent(clientId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load client detail."); }
    },

    async updateClient(clientId, updates) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/clients/${encodeURIComponent(clientId)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update client."); }
    },

    async linkClientToCase(caseId, clientId, role = 'creditor') {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/link-client`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ client_id: clientId, role })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to link client."); }
    },

    async unlinkClientFromCase(caseId, clientId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/unlink-client/${encodeURIComponent(clientId)}`, {
            method: 'DELETE'
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to unlink client."); }
    },

    // ══════════════════════════════════════════════════════════
    // CMS — DOCUMENT MANAGEMENT API
    // ══════════════════════════════════════════════════════════
    async uploadCmsDocument(caseId, formData) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/documents`, {
            method: 'POST',
            body: formData
        }, 0);
        try { return await response.json(); } catch (e) { throw new Error("Failed to upload document."); }
    },

    async listCmsDocuments(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/documents`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to list documents."); }
    },

    async getCmsDocumentDetail(documentId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/documents/${encodeURIComponent(documentId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load document."); }
    },

    async downloadCmsDocument(documentId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/documents/${encodeURIComponent(documentId)}/download`);
        try { return await response.blob(); } catch (e) { throw new Error("Failed to download document."); }
    },

    async deleteCmsDocument(documentId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/documents/${encodeURIComponent(documentId)}`, {
            method: 'DELETE'
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to delete document."); }
    },

    async generateS65BCert(documentId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/documents/${encodeURIComponent(documentId)}/s65b`, {
            method: 'POST'
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to generate certificate template."); }
    },

    async certifyDocument(documentId, certPayload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/documents/${encodeURIComponent(documentId)}/certify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(certPayload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to certify document."); }
    },

    // ══════════════════════════════════════════════════════════
    // CMS — DRAFT WORKFLOW API
    // ══════════════════════════════════════════════════════════
    async createCmsDraft(caseId, draftType = 'LEGAL_NOTICE', tone = 'standard', customContent = null) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/drafts`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ draft_type: draftType, tone, custom_content: customContent })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to create draft."); }
    },

    async listCmsDrafts(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/drafts`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to list drafts."); }
    },

    async getCmsDraftDetail(workflowId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/drafts/${encodeURIComponent(workflowId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load draft detail."); }
    },

    async updateCmsDraft(workflowId, content, assignedReviewer = null) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/drafts/${encodeURIComponent(workflowId)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, assigned_reviewer: assignedReviewer })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update draft."); }
    },

    async submitCmsDraft(workflowId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/drafts/${encodeURIComponent(workflowId)}/submit`, {
            method: 'POST'
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to submit draft."); }
    },

    async reviewCmsDraft(workflowId, comment, status = 'IN_REVISION') {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/drafts/${encodeURIComponent(workflowId)}/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comment, status })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to submit review."); }
    },

    async approveCmsDraft(workflowId, note = '') {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/drafts/${encodeURIComponent(workflowId)}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ note })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to approve draft."); }
    },

    async markCmsDraftFiled(workflowId, filedReference) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/drafts/${encodeURIComponent(workflowId)}/filed`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filed_reference: filedReference })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to mark draft as filed."); }
    },

    async exportCmsDraft(workflowId, format = 'pdf') {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/drafts/${encodeURIComponent(workflowId)}/export/${format}`);
        try { return await response.blob(); } catch (e) { throw new Error("Failed to export draft."); }
    },

    // ══════════════════════════════════════════════════════════
    // CMS — DEADLINE MANAGEMENT API
    // ══════════════════════════════════════════════════════════
    async calculateCaseDeadlines(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/deadlines/cases/${encodeURIComponent(caseId)}/deadlines/calculate`, {
            method: 'POST'
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to calculate deadlines."); }
    },

    async listCaseDeadlines(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/deadlines/cases/${encodeURIComponent(caseId)}/deadlines`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to list deadlines."); }
    },

    async completeDeadline(deadlineId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/deadlines/deadlines/${encodeURIComponent(deadlineId)}/complete`, {
            method: 'PATCH'
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to complete deadline."); }
    },

    async getUpcomingDeadlines() {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/deadlines/deadlines/upcoming`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load upcoming deadlines."); }
    },

    // ══════════════════════════════════════════════════════════
    // CMS — TEAM MANAGEMENT API
    // ══════════════════════════════════════════════════════════
    async addTeamMember(memberData) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/team/members`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(memberData)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to add team member."); }
    },

    async listTeamMembers(orgId = null) {
        const url = orgId ? `${API_BASE_URL}/api/v1/cms/team/members?org_id=${encodeURIComponent(orgId)}` : `${API_BASE_URL}/api/v1/cms/team/members`;
        const response = await fetchWithRetry(url);
        try { return await response.json(); } catch (e) { throw new Error("Failed to list team members."); }
    },

    async updateTeamMember(memberId, updates) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/team/members/${encodeURIComponent(memberId)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to update team member."); }
    },

    async toggleTeamMemberStatus(memberId, isActive) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/team/members/${encodeURIComponent(memberId)}/status`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to toggle status."); }
    },

    // ══════════════════════════════════════════════════════════
    // CMS — COMMUNICATION & AUDIT API
    // ══════════════════════════════════════════════════════════
    async sendCaseNotification(caseId, subject, message, channels = ['email'], recipientEmails = null) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/notify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject, message, channels, recipient_emails: recipientEmails })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to dispatch notification."); }
    },

    async getCaseCommunications(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/cases/${encodeURIComponent(caseId)}/communications`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load communications."); }
    },

    async getCaseAuditTrail(caseId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/audit/case/${encodeURIComponent(caseId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load audit trail."); }
    },

    async exportAuditCsv(caseId = null, userId = null) {
        const params = new URLSearchParams();
        if (caseId) params.append('case_id', caseId);
        if (userId) params.append('user_id', userId);
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cms/audit/export?${params.toString()}`);
        try { return await response.blob(); } catch (e) { throw new Error("Failed to export audit CSV."); }
    },

    // ══════════════════════════════════════════════════════════
    // CMS — REAL-TIME ANALYTICS API
    // ══════════════════════════════════════════════════════════
    async getCmsPortfolioStats() {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/analytics/portfolio`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load portfolio stats."); }
    },

    async getCmsCaseTypes() {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/analytics/case-types`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load case types."); }
    },

    async getCmsMonthlyTrends() {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/analytics/monthly`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load monthly trends."); }
    },

    async getCmsDeadlineHeatmap() {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/analytics/deadlines`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load deadline heatmap."); }
    },

    // ══════════════════════════════════════════════════════════
    // FORMAL SHARED REPORT API
    // ══════════════════════════════════════════════════════════
    baseUrl: API_BASE_URL,
    API_BASE_URL: API_BASE_URL,

    async createSharedReport(payload) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/reports/share`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to generate secure shared report."); }
    },

    async getSharedReport(shareId) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/reports/shared/${encodeURIComponent(shareId)}`);
        try { return await response.json(); } catch (e) { throw new Error("Failed to load shared report."); }
    },

    async verifySharedReportPassword(shareId, password) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/reports/shared/${encodeURIComponent(shareId)}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });
        try { return await response.json(); } catch (e) { throw new Error("Failed to verify report password."); }
    },

    // ── Document & Case Fact Intelligence ────────────────────────────────────

    /**
     * Upload documents → OCR → per-document fact extraction.
     * @param {FormData} formData — files[], doc_types (csv), workflow_type
     * @param {Function} [onUploadProgress] — optional callback (percent: number) => void
     */
    async docIntelExtract(formData, onUploadProgress = null) {
        if (!onUploadProgress) {
            const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/doc-intel/extract`, {
                method: 'POST',
                body: formData,
                timeout: 180000,
            });
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `Document extraction failed (${response.status})`);
            }
            return response.json();
        }

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${API_BASE_URL}/api/v1/doc-intel/extract`);
            xhr.timeout = 180000;

            const token = localStorage.getItem("judiq_admin_jwt") || localStorage.getItem("judiq_jwt");
            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }

            if (xhr.upload) {
                xhr.upload.onprogress = (e) => {
                    if (e.lengthComputable && e.total > 0) {
                        const pct = Math.min(100, Math.round((e.loaded / e.total) * 100));
                        try { onUploadProgress(pct); } catch (err) {}
                    }
                };
            }

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        resolve(data);
                    } catch (e) {
                        reject(new Error("Invalid response format from extraction engine."));
                    }
                } else {
                    let errMsg = `Document extraction failed (${xhr.status})`;
                    try {
                        const err = JSON.parse(xhr.responseText);
                        if (err.detail) errMsg = err.detail;
                    } catch (e) {}
                    reject(new Error(errMsg));
                }
            };

            xhr.onerror = () => reject(new Error("Network error during document upload."));
            xhr.ontimeout = () => reject(new Error("Document upload & OCR processing timed out."));
            xhr.send(formData);
        });
    },

    /**
     * Cross-document analysis: contradictions, missing facts/docs, timeline.
     * @param {string} sessionId
     * @param {string} workflowType
     */
    async docIntelAnalyze(sessionId, workflowType = 'cheque_bounce') {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/doc-intel/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, workflow_type: workflowType }),
            timeout: 120000,
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Analysis failed (${response.status})`);
        }
        return response.json();
    },

    /**
     * Submit lawyer-verified facts.
     * @param {string} sessionId
     * @param {Object} verifiedFacts — field → corrected value
     */
    async docIntelVerify(sessionId, verifiedFacts, resolvedContradictions = []) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/doc-intel/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                verified_facts: verifiedFacts,
                resolved_contradictions: resolvedContradictions,
            }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Verification failed (${response.status})`);
        }
        return response.json();
    },

    /**
     * Generate case story from VERIFIED facts only (never from raw extraction).
     * @param {string} sessionId
     * @param {Object} verifiedFacts
     * @param {string} workflowType
     */
    async docIntelCaseStory(sessionId, verifiedFacts, workflowType = 'cheque_bounce') {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/doc-intel/case-story`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                verified_facts: verifiedFacts,
                workflow_type: workflowType,
            }),
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Case story generation failed (${response.status})`);
        }
        return response.json();
    },
};





