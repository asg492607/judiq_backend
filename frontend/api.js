import { API_BASE_URL } from './config.js?v=14';

/**
 * Fetch with automatic retry on transient failures.
 */
export async function fetchWithRetry(url, options = {}, maxRetries = 2, baseDelay = 2000) {
    let lastError;
    
    // Inject JWT Authorization
    let token = localStorage.getItem("judiq_jwt");
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
            console.error("Failed to fetch anonymous JWT:", e);
        }
    }

    if (token) {
        options.headers = options.headers || {};
        options.headers['Authorization'] = `Bearer ${token}`;
    }

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 90000); // 90s timeout
            let response;
            try {
                response = await fetch(url, { ...options, signal: controller.signal });
            } finally {
                clearTimeout(timeout);
            }
            if (response.status === 401 && !url.includes('/auth/anonymous')) {
                localStorage.removeItem("judiq_jwt");
                try {
                    const authRes = await fetch(`${API_BASE_URL}/api/v1/auth/anonymous`, { method: 'POST' });
                    if (authRes.ok) {
                        const authData = await authRes.json();
                        token = authData.access_token;
                        localStorage.setItem("judiq_jwt", token);
                        if (window.state) window.state.user_id = authData.user_id;
                        options.headers = options.headers || {};
                        options.headers['Authorization'] = `Bearer ${token}`;
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
                throw new Error('Request timed out after 90 seconds.');
            }
            const retryable = !err.status || err.status === 408 || err.status === 429 || err.status >= 500;
            if (attempt < maxRetries && retryable) {
                const delay = baseDelay * Math.pow(2, attempt);
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
        const payload = {
            language: currentLang,
            lang: currentLang,
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
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/documents/generate-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        try { return await response.blob(); } catch (e) { throw new Error("Failed to read file blob."); }
    },

    async generateDraftPdf(title, content, metadata = {}) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/documents/draft-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content, metadata })
        });
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
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/cases/delete?case_id=${encodeURIComponent(caseId)}&user_id=${encodeURIComponent(userId)}`, {
            method: 'DELETE'
        });
        try { return await response.json(); } catch (e) { throw new Error("Invalid JSON from server."); }
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

    async verifyAdminAuth(email) {
        const response = await fetchWithRetry(`${API_BASE_URL}/api/v1/admin/auth/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
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
    }
};


