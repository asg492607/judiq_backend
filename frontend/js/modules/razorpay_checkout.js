/**
 * razorpay_checkout.js — JudiQ AI Razorpay Standard Checkout Integration
 *
 * Exposes:
 *   window.judiqPay(options)  — callable from anywhere in the app
 *
 * Usage:
 *   window.judiqPay({
 *     amount: 49900,           // paise  (e.g. 49900 = Rs.499)
 *     description: "JudiQ Pro Plan",
 *     prefill: { name: "Advocate Name", email: "user@email.com", contact: "9876543210" }
 *   })
 *
 * The Razorpay KEY_ID is embedded at module load time from the backend
 * (GET /api/v1/payments/key). The KEY_SECRET never leaves the server.
 */

(function () {
'use strict';

// Resolve backend API URL for Render deployment
const API_BASE_URL = window.__JUDIQ_ENV__?.API_BASE_URL || (
    (window.location.origin && !window.location.origin.startsWith("file://") && window.location.origin.includes("onrender.com"))
        ? window.location.origin
        : "https://cheque-bounce-ragbased.onrender.com"
);

let _razorpayKeyId = null; // fetched once from backend

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Show a toast notification if the global `showToast` function exists,
 * otherwise fall back to console output.
 */
function _toast(message, type = 'info') {
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    } else {
        console[type === 'error' ? 'error' : 'log']('[JudiQ Pay]', message);
    }
}

/**
 * Retrieve the JWT from localStorage (injected by fetchWithRetry in api.js).
 */
function _getAuthHeaders() {
    const token = localStorage.getItem('judiq_jwt');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}

/**
 * Fetch the Razorpay Key ID from the backend (public endpoint).
 * Called once per page load; result is cached.
 */
async function _fetchKeyId() {
    if (_razorpayKeyId) return _razorpayKeyId;
    try {
        const res = await fetch(`${API_BASE_URL}/api/v1/payments/key`, {
            method: 'GET',
            headers: _getAuthHeaders(),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        _razorpayKeyId = data.key_id;
        return _razorpayKeyId;
    } catch (err) {
        console.error('[JudiQ Pay] Failed to fetch Razorpay Key ID:', err);
        throw new Error('Payment gateway unavailable. Please try again later.');
    }
}

/**
 * Create a Razorpay order via the backend.
 * @param {number} amount — amount in paise
 * @param {string} currency
 * @param {string} receipt
 * @returns {{ order_id, amount, currency, receipt }}
 */
async function _createOrder(amount, currency = 'INR', receipt = '') {
    const res = await fetch(`${API_BASE_URL}/api/v1/payments/create-order`, {
        method: 'POST',
        headers: _getAuthHeaders(),
        body: JSON.stringify({ amount, currency, receipt }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Order creation failed (HTTP ${res.status})`);
    }
    return res.json();
}

/**
 * Verify the payment signature via the backend.
 * @returns {{ success: boolean, message: string }}
 */
async function _verifyPayment(razorpay_order_id, razorpay_payment_id, razorpay_signature, extra = {}) {
    const res = await fetch(`${API_BASE_URL}/api/v1/payments/verify-payment`, {
        method: 'POST',
        headers: _getAuthHeaders(),
        body: JSON.stringify({ 
            razorpay_order_id, 
            razorpay_payment_id, 
            razorpay_signature,
            user_id: extra.user_id || '',
            email: extra.email || '',
            modules: extra.modules || ['s138'],
            quota: extra.quota || 25,
            amount: extra.amount || 499.0
        }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Verification failed (HTTP ${res.status})`);
    }
    return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Initiate a Razorpay Standard Checkout flow.
 *
 * @param {object} options
 * @param {number}   options.amount       — Amount in paise. Min 100.
 * @param {string}  [options.currency]    — Default: "INR"
 * @param {string}  [options.description] — Shown in the Razorpay modal
 * @param {string}  [options.receipt]     — Custom receipt identifier
 * @param {object}  [options.prefill]     — { name, email, contact }
 * @param {object}  [options.notes]       — Arbitrary key-value notes
 * @param {Function}[options.onSuccess]   — Called with payment data on success
 * @param {Function}[options.onFailure]   — Called with error on failure/dismiss
 */
async function judiqPay({
    amount,
    currency = 'INR',
    description = 'JudiQ AI — Legal Intelligence Platform',
    receipt = '',
    prefill = {},
    notes = {},
    onSuccess = null,
    onFailure = null,
} = {}) {
    // Guard: Razorpay SDK must be loaded
    if (typeof window.Razorpay === 'undefined') {
        const msg = 'Razorpay SDK is not loaded. Check your internet connection.';
        _toast(msg, 'error');
        if (typeof onFailure === 'function') onFailure(new Error(msg));
        return;
    }

    // Validate amount
    if (!amount || amount < 100) {
        const msg = 'Payment amount must be at least ₹1 (100 paise).';
        _toast(msg, 'error');
        if (typeof onFailure === 'function') onFailure(new Error(msg));
        return;
    }

    try {
        _toast('Initialising payment…', 'info');

        // Step 1: fetch public key + create server-side order concurrently
        const [keyId, order] = await Promise.all([
            _fetchKeyId(),
            _createOrder(amount, currency, receipt || `judiq_${Date.now()}`),
        ]);

        // Step 2: open Razorpay modal
        const rzpOptions = {
            key: keyId,
            amount: order.amount,
            currency: order.currency,
            name: 'JudiQ AI',
            description,
            order_id: order.order_id,
            prefill: {
                name: prefill.name || '',
                email: prefill.email || '',
                contact: prefill.contact || '',
            },
            notes,
            theme: { color: '#1a1a2e' },

            handler: async function (response) {
                const { razorpay_payment_id, razorpay_order_id, razorpay_signature } = response;
                try {
                    _toast('Verifying payment…', 'info');
                    const extraData = {
                        user_id: (notes && notes.user_id) || (prefill && prefill.email) || '',
                        email: (prefill && prefill.email) || '',
                        modules: notes && notes.modules ? notes.modules.split(',') : ['s138'],
                        quota: notes && notes.cases_quota ? parseInt(notes.cases_quota, 10) : 25,
                        amount: amount / 100
                    };
                    const result = await _verifyPayment(
                        razorpay_order_id,
                        razorpay_payment_id,
                        razorpay_signature,
                        extraData
                    );
                    if (result.success) {
                        _toast('Payment successful! Platform service is now active.', 'success');
                        if (typeof onSuccess === 'function') {
                            onSuccess({
                                payment_id: razorpay_payment_id,
                                order_id: razorpay_order_id,
                                signature: razorpay_signature,
                                quota: result.quota
                            });
                        }
                    } else {
                        throw new Error(result.message || 'Verification failed.');
                    }
                } catch (verifyErr) {
                    _toast(`Payment verification failed: ${verifyErr.message}`, 'error');
                    if (typeof onFailure === 'function') onFailure(verifyErr);
                }
            },

            modal: {
                ondismiss: function () {
                    _toast('Payment cancelled. Platform services remain locked until subscription is activated.', 'warning');
                    if (typeof onFailure === 'function') {
                        onFailure(new Error('User dismissed the payment modal.'));
                    }
                },
            },
        };

        const rzp = new window.Razorpay(rzpOptions);

        rzp.on('payment.failed', function (response) {
            const errMsg = response.error?.description || 'Payment failed.';
            _toast(`Payment failed: ${errMsg}`, 'error');
            if (typeof onFailure === 'function') onFailure(new Error(errMsg));
        });

        rzp.open();

    } catch (err) {
        _toast(`Payment error: ${err.message}`, 'error');
        if (typeof onFailure === 'function') onFailure(err);
    }
}

// Attach to window so it is usable from any script, module, or inline onclick
window.judiqPay = judiqPay;
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { judiqPay };
}
})();
