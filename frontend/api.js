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
    }
};


