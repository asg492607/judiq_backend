/**
 * error_handler.js — JudiQ Global Error Boundary
 *
 * Provides:
 *  - window.onerror           : catches all synchronous JS errors
 *  - window.unhandledrejection: catches all unhandled promise rejections
 *  - window.JudiQError.report : central error reporting (console + toast + telemetry)
 *  - window.JudiQError.wrap   : HOF that wraps async functions with auto-reporting
 *
 * NO ES6 imports/exports — plain IIFE pattern.
 */

    /* ------------------------------------------------------------------ */
    /*  Constants                                                           */
    /* ------------------------------------------------------------------ */

    var API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? "http://127.0.0.1:8000" : "https://cheque-bounce-ragbased.onrender.com";
    var TELEMETRY_ENDPOINT = API_BASE_URL + '/api/v1/telemetry/error';
    var BANNER_ID          = 'judiqErrorBanner';
    var IS_DEV             = (
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1' ||
        window.location.hostname === ''
    );

    /* ------------------------------------------------------------------ */
    /*  Banner helpers                                                      */
    /* ------------------------------------------------------------------ */

    /**
     * Lazily creates and returns the #judiqErrorBanner element.
     * The banner is a slim, non-intrusive strip at the top of the viewport.
     */
    function _getOrCreateBanner() {
        var existing = document.getElementById(BANNER_ID);
        if (existing) return existing;

        var banner = document.createElement('div');
        banner.id = BANNER_ID;
        // Slim, non-intrusive banner — NOT a full-screen red bar
        banner.style.cssText = [
            'position: fixed',
            'top: 0',
            'left: 0',
            'right: 0',
            'z-index: 999990',
            'background: #1e1e2e',
            'color: #f38ba8',
            'font-family: system-ui, sans-serif',
            'font-size: 13px',
            'line-height: 1.5',
            'padding: 6px 48px 6px 14px',
            'border-bottom: 2px solid #f38ba8',
            'box-shadow: 0 2px 8px rgba(0,0,0,0.4)',
            'display: none',
            'word-break: break-word'
        ].join('; ');

        // Dismiss button
        var closeBtn = document.createElement('button');
        closeBtn.textContent = '✕';
        closeBtn.title = 'Dismiss';
        closeBtn.style.cssText = [
            'position: absolute',
            'right: 10px',
            'top: 50%',
            'transform: translateY(-50%)',
            'background: transparent',
            'border: none',
            'color: #f38ba8',
            'font-size: 15px',
            'cursor: pointer',
            'line-height: 1',
            'padding: 0 4px'
        ].join('; ');
        closeBtn.addEventListener('click', function () {
            banner.style.display = 'none';
        });

        banner.appendChild(closeBtn);

        // Inject as early as possible — try body first, fall back to documentElement
        var target = document.body || document.documentElement;
        if (target) {
            target.insertBefore(banner, target.firstChild);
        }

        return banner;
    }

    /**
     * Shows the banner with a message.
     * In production: generic, friendly text.
     * In dev: full technical details.
     */
    function _showBanner(summary, detail) {
        // Defer if DOM not ready yet
        if (!document.body) {
            document.addEventListener('DOMContentLoaded', function () {
                _showBanner(summary, detail);
            });
            return;
        }

        var banner = _getOrCreateBanner();
        var icon   = '⚠️';

        if (IS_DEV) {
            // Full technical details for developers
            banner.innerHTML = '';
            var closeBtn = banner.querySelector('button');

            var msgNode = document.createElement('span');
            msgNode.textContent = icon + ' [DEV] ' + summary + (detail ? ' — ' + detail : '');
            banner.insertBefore(msgNode, closeBtn);
        } else {
            // Friendly, non-alarming message for end users
            banner.innerHTML = '';
            var closeBtn2 = banner.querySelector('button');

            var msgNode2 = document.createElement('span');
            msgNode2.textContent = icon + ' Something went wrong. The JudiQ team has been notified. Please refresh if issues persist.';
            banner.insertBefore(msgNode2, closeBtn2);
        }

        banner.style.display = 'block';
    }

    /* ------------------------------------------------------------------ */
    /*  Telemetry (fire-and-forget)                                        */
    /* ------------------------------------------------------------------ */

    /**
     * Sends error details to the telemetry endpoint.
     * Never throws — completely safe to call from within error handlers.
     */
    function _sendTelemetry(payload) {
        try {
            fetch(TELEMETRY_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                // Do not block page unload
                keepalive: true
            }).catch(function () {
                /* swallow — telemetry must never propagate errors */
            });
        } catch (e) {
            /* swallow */
        }
    }

    /* ------------------------------------------------------------------ */
    /*  JudiQError public API                                               */
    /* ------------------------------------------------------------------ */

    var JudiQError = {};

    /**
     * JudiQError.report(error, context)
     *
     * Central reporting function:
     *  (a) Logs to console.error with context
     *  (b) Shows a toast via showToast if available
     *  (c) Fires telemetry to /api/v1/telemetry/error (never throws)
     *
     * @param {Error|string} error   - The error object or message string
     * @param {string}       context - Short description of where/what failed
     */
    JudiQError.report = function report(error, context) {
        var ctx  = context || 'Unknown context';
        var msg  = (error && error.message) ? error.message : String(error);
        var stack = (error && error.stack) ? error.stack : null;

        // (a) Console
        console.error('[JudiQError] ' + ctx + ' →', error);

        // (b) Toast
        try {
            if (typeof showToast === 'function') {
                showToast('Error: ' + msg, 'error');
            } else if (typeof JudiQ_UI !== 'undefined' && JudiQ_UI && typeof JudiQ_UI.showToast === 'function') {
                JudiQ_UI.showToast('Error: ' + msg, 'error');
            }
        } catch (toastErr) {
            /* swallow — toast must never propagate */
        }

        // (c) Telemetry
        _sendTelemetry({
            timestamp: new Date().toISOString(),
            context:   ctx,
            message:   msg,
            stack:     stack,
            url:       window.location ? window.location.href : null,
            userAgent: navigator.userAgent
        });
    };

    /**
     * JudiQError.wrap(fn, context)
     *
     * Higher-order function that wraps an async (or sync) function
     * in a try/catch that automatically calls JudiQError.report on failure.
     *
     * @param  {Function} fn      - The function to wrap
     * @param  {string}   context - Label for error reports
     * @returns {Function}         Wrapped function with identical signature
     */
    JudiQError.wrap = function wrap(fn, context) {
        var ctx = context || (fn.name ? fn.name + '()' : 'anonymous');
        return function wrappedByJudiQ() {
            try {
                var result = fn.apply(this, arguments);
                // Handle promises (async functions return a Promise)
                if (result && typeof result.then === 'function') {
                    return result.catch(function (err) {
                        JudiQError.report(err, ctx);
                        // Re-throw so callers can still handle it if they want
                        throw err;
                    });
                }
                return result;
            } catch (err) {
                JudiQError.report(err, ctx);
                throw err;
            }
        };
    };

    /* ------------------------------------------------------------------ */
    /*  Global window.onerror                                               */
    /* ------------------------------------------------------------------ */

    window.onerror = function judiqGlobalOnError(message, source, lineno, colno, error) {
        var summary = message;
        var detail  = source ? (source + ':' + lineno + ':' + colno) : '';

        // Always log
        console.error('[JudiQError] Uncaught JS error:', message, '\n  at', detail, '\n', error);

        // Show banner
        _showBanner(summary, detail);

        // Report (skip toast for global handler to avoid double-noise)
        _sendTelemetry({
            timestamp: new Date().toISOString(),
            context:   'window.onerror',
            message:   String(message),
            source:    source || null,
            lineno:    lineno || null,
            colno:     colno  || null,
            stack:     (error && error.stack) ? error.stack : null,
            url:       window.location ? window.location.href : null,
            userAgent: navigator.userAgent
        });

        // Return false to allow default browser error handling to continue
        return false;
    };

    /* ------------------------------------------------------------------ */
    /*  Global unhandledrejection                                           */
    /* ------------------------------------------------------------------ */

    window.addEventListener('unhandledrejection', function judiqUnhandledRejection(event) {
        var reason  = event.reason;
        var msg     = (reason && reason.message) ? reason.message : String(reason);
        var stack   = (reason && reason.stack)   ? reason.stack   : null;

        // Always log
        console.error('[JudiQError] Unhandled Promise rejection:', reason);

        // Show banner
        _showBanner('Unhandled Promise rejection: ' + msg, null);

        // Telemetry
        _sendTelemetry({
            timestamp: new Date().toISOString(),
            context:   'window.unhandledrejection',
            message:   msg,
            stack:     stack,
            url:       window.location ? window.location.href : null,
            userAgent: navigator.userAgent
        });
    });

    /* ------------------------------------------------------------------ */
    /*  Expose globally                                                     */
    /* ------------------------------------------------------------------ */

    window.JudiQError = JudiQError;

    /* ------------------------------------------------------------------ */
    /*  Pre-create the banner as soon as the DOM is ready                  */
    /* ------------------------------------------------------------------ */

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            _getOrCreateBanner();
        });
    } else {
        _getOrCreateBanner();
    }


