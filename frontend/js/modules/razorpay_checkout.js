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

const API_BASE_URL = window.__JUDIQ_ENV__?.API_BASE_URL || (
    (window.location.origin && !window.location.origin.startsWith("file://") && (
        window.location.origin.includes("localhost") ||
        window.location.origin.includes("127.0.0.1") ||
        window.location.origin.includes("onrender.com")
    ))
        ? window.location.origin
        : "https://cheque-bounce-ragbased.onrender.com"
);

let _razorpayKeyId = null; // fetched once from backend

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Show a toast notification if the global `window.ui.toast` or `showToast` function exists,
 * otherwise fall back to console output.
 */
function _toast(message, type = 'info') {
    if (window.ui && typeof window.ui.toast === 'function') {
        window.ui.toast(message, type);
    } else if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    } else {
        console[type === 'error' ? 'error' : 'log']('[JudiQ Pay]', message);
    }
}

/**
 * Display a formal, professional celebration modal and particle animation upon payment verification.
 * Employs dignified celebration emojis (🎉 ✨ ⚖️) in a stately, institutional corporate manner.
 *
 * @param {object} options
 * @param {string} [options.payment_id]
 * @param {number|string} [options.quota]
 * @param {string} [options.plan_name]
 * @param {Function} [options.onProceed]
 */
function triggerPaymentCelebration(options = {}) {
    if (document.getElementById('paymentCelebrationOverlay')) return;

    const paymentId = options.payment_id || 'RZP_' + Math.random().toString(36).substring(2, 10).toUpperCase();
    const quota = options.quota || 25;
    const planName = options.plan_name || 'Section 138 Litigation OS';
    const onProceed = typeof options.onProceed === 'function' ? options.onProceed : null;

    // 1. Inject Styles if not already present
    if (!document.getElementById('judiqPaymentCelebrationStyles')) {
        const style = document.createElement('style');
        style.id = 'judiqPaymentCelebrationStyles';
        style.textContent = `
            @keyframes jqCelebrationFadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes jqCelebrationScaleUp {
                from { opacity: 0; transform: scale(0.9) translateY(14px); }
                to { opacity: 1; transform: scale(1) translateY(0); }
            }
            @keyframes jqCelebrationFloat {
                0%, 100% { transform: translateY(0px) rotate(0deg); }
                50% { transform: translateY(-7px) rotate(3deg); }
            }
            @keyframes jqCelebrationFall {
                0% {
                    transform: translateY(-20px) rotate(0deg);
                    opacity: 1;
                }
                85% {
                    opacity: 0.9;
                }
                100% {
                    transform: translateY(105vh) rotate(720deg);
                    opacity: 0;
                }
            }
            @keyframes jqPulseGlow {
                0%, 100% { box-shadow: 0 0 25px rgba(99, 102, 241, 0.25), 0 20px 50px rgba(0,0,0,0.6); }
                50% { box-shadow: 0 0 45px rgba(16, 185, 129, 0.35), 0 20px 50px rgba(0,0,0,0.7); }
            }
            .jq-celebration-overlay {
                position: fixed;
                inset: 0;
                z-index: 9999999;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(10, 15, 30, 0.88);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                padding: 1.25rem;
                animation: jqCelebrationFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            .jq-celebration-card {
                position: relative;
                width: 100%;
                max-width: 490px;
                background: linear-gradient(145deg, rgba(30, 41, 59, 0.97), rgba(15, 23, 42, 0.99));
                border: 1px solid rgba(99, 102, 241, 0.35);
                border-radius: 20px;
                padding: 32px 28px;
                text-align: center;
                color: #f8fafc;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                animation: jqCelebrationScaleUp 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards, jqPulseGlow 4s infinite ease-in-out;
            }
        `;
        document.head.appendChild(style);
    }

    // 2. Create Confetti & Celebration Streamers (Professional, Dignified Palette)
    const confettiContainer = document.createElement('div');
    confettiContainer.id = 'paymentCelebrationConfetti';
    confettiContainer.style.cssText = 'position: fixed; inset: 0; pointer-events: none; z-index: 9999998; overflow: hidden;';
    
    const colors = ['#f59e0b', '#fbbf24', '#10b981', '#34d399', '#6366f1', '#818cf8', '#ffffff'];
    const emojis = ['🎉', '✨', '🎖️', '⚖️'];

    // Generate ~36 dignified geometric confetti ribbons & dots
    for (let i = 0; i < 36; i++) {
        const piece = document.createElement('div');
        const color = colors[i % colors.length];
        const isCircle = i % 3 === 0;
        const width = isCircle ? (8 + Math.random() * 6) : (6 + Math.random() * 8);
        const height = isCircle ? width : (12 + Math.random() * 14);
        const left = Math.random() * 100;
        const duration = 2.4 + Math.random() * 1.8;
        const delay = Math.random() * 0.8;

        piece.style.cssText = `
            position: absolute;
            top: -25px;
            left: ${left}%;
            width: ${width}px;
            height: ${height}px;
            background: ${color};
            border-radius: ${isCircle ? '50%' : '3px'};
            opacity: 0.95;
            animation: jqCelebrationFall ${duration}s cubic-bezier(0.25, 0.46, 0.45, 0.94) ${delay}s forwards;
        `;
        confettiContainer.appendChild(piece);
    }

    // Generate 8 softly drifting celebratory emojis
    for (let i = 0; i < 8; i++) {
        const emo = document.createElement('div');
        emo.textContent = emojis[i % emojis.length];
        const left = 10 + Math.random() * 80;
        const duration = 2.8 + Math.random() * 1.5;
        const delay = Math.random() * 0.6;
        const size = 16 + Math.random() * 12;

        emo.style.cssText = `
            position: absolute;
            top: -30px;
            left: ${left}%;
            font-size: ${size}px;
            opacity: 0.9;
            filter: drop-shadow(0 2px 6px rgba(0,0,0,0.4));
            animation: jqCelebrationFall ${duration}s ease-in-out ${delay}s forwards;
        `;
        confettiContainer.appendChild(emo);
    }

    document.body.appendChild(confettiContainer);

    // 3. Create Formal Celebration Dialog Modal
    const overlay = document.createElement('div');
    overlay.id = 'paymentCelebrationOverlay';
    overlay.className = 'jq-celebration-overlay';

    overlay.innerHTML = `
        <div class="jq-celebration-card" role="dialog" aria-modal="true" aria-labelledby="celebrationTitle">
            <div style="display: inline-flex; align-items: center; gap: 8px; font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; color: #34d399; background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 9999px; padding: 5px 14px; margin-bottom: 16px;">
                <span>✨</span> PAYMENT VERIFIED &amp; CONFIRMED
            </div>
            
            <div style="font-size: 3.5rem; line-height: 1; margin-bottom: 14px; animation: jqCelebrationFloat 3s ease-in-out infinite;">
                🎉
            </div>

            <h2 id="celebrationTitle" style="font-size: 1.5rem; font-weight: 700; color: #ffffff; margin: 0 0 10px 0; letter-spacing: -0.02em;">
                Subscription Activated! 🎉
            </h2>

            <p style="font-size: 0.9rem; color: #94a3b8; line-height: 1.55; margin: 0 0 20px 0;">
                Hon’ble Counsel / Member, your transaction has been authenticated with Razorpay and recorded by 
                <strong style="color: #cbd5e1;">AIXYNZ Technologies Private Limited</strong>. Your litigation intelligence workspace is now active with immediate effect.
            </p>

            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 12px; padding: 14px 18px; margin-bottom: 22px; text-align: left; font-size: 0.83rem; line-height: 1.7;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #94a3b8;">Transaction ID:</span>
                    <span style="font-family: monospace; color: #38bdf8; font-weight: 600;">${paymentId}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="color: #94a3b8;">Litigation Engine:</span>
                    <span style="color: #cbd5e1; font-weight: 600;">${planName}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8;">Service Status:</span>
                    <span style="color: #34d399; font-weight: 600;">
                        <i class="fas fa-circle-check" style="margin-right: 4px;"></i>ACTIVE (${quota} Reports)
                    </span>
                </div>
            </div>

            <button id="btnProceedToWorkspace" type="button" style="width: 100%; padding: 13px 20px; font-size: 0.95rem; font-weight: 600; color: #ffffff; background: linear-gradient(135deg, #4f46e5, #6366f1); border: none; border-radius: 10px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4); transition: transform 0.15s ease, box-shadow 0.15s ease;">
                <span>Proceed to Litigation Workspace</span>
                <i class="fas fa-arrow-right"></i>
            </button>

            <div id="celebrationCountdownText" style="font-size: 0.78rem; color: #64748b; margin-top: 12px;">
                Auto-redirecting in 3s…
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    let dismissed = false;
    let countdown = 3;

    function cleanupAndProceed() {
        if (dismissed) return;
        dismissed = true;
        clearInterval(timerInterval);

        overlay.style.transition = 'opacity 0.25s ease-out';
        overlay.style.opacity = '0';

        setTimeout(() => {
            overlay.remove();
            confettiContainer.remove();
            if (typeof onProceed === 'function') {
                onProceed();
            }
        }, 250);
    }

    const btn = document.getElementById('btnProceedToWorkspace');
    if (btn) {
        btn.addEventListener('click', cleanupAndProceed);
    }

    const countdownText = document.getElementById('celebrationCountdownText');
    const timerInterval = setInterval(() => {
        countdown--;
        if (countdownText && countdown > 0) {
            countdownText.textContent = `Auto-redirecting in ${countdown}s…`;
        }
        if (countdown <= 0) {
            cleanupAndProceed();
        }
    }, 1000);
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
                        _toast('🎉 Payment verified successfully! Platform service is now active.', 'success');
                        triggerPaymentCelebration({
                            payment_id: razorpay_payment_id,
                            quota: result.quota || extraData.quota || 25,
                            onProceed: () => {
                                if (typeof onSuccess === 'function') {
                                    onSuccess({
                                        payment_id: razorpay_payment_id,
                                        order_id: razorpay_order_id,
                                        signature: razorpay_signature,
                                        quota: result.quota || extraData.quota || 25
                                    });
                                }
                            }
                        });
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
window.triggerPaymentCelebration = triggerPaymentCelebration;
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { judiqPay, triggerPaymentCelebration };
}
})();
