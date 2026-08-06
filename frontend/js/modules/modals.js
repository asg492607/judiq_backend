// =============================================================================
// JUDIQ — MODAL SYSTEM  (modals.js)
// =============================================================================
// Exposes window.JudiQModals.
// No ES6 imports/exports — plain script tag compatible.
// Requires DOMPurify to be loaded before this file.
// =============================================================================

    // -------------------------------------------------------------------------
    // CONSTANTS
    // -------------------------------------------------------------------------
    var DISCLAIMER_KEY = 'judiq_disclaimer_accepted';
    var OPEN_CLASS = 'jq-modal--open';
    var BACKDROP_CLASS = 'jq-modal-backdrop';
    var TRANSITION_MS = 200; // match CSS transition duration

    // -------------------------------------------------------------------------
    // SAFE HTML
    // -------------------------------------------------------------------------
    function safeHtml(html) {
        if (window.DOMPurify) return window.DOMPurify.sanitize(html);
        var d = document.createElement('div');
        d.textContent = html;
        return d.innerHTML;
    }

    function escHtml(str) {
        if (typeof str !== 'string') str = String(str || '');
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // -------------------------------------------------------------------------
    // INJECT BASE STYLES (once)
    // -------------------------------------------------------------------------
    function injectStyles() {
        if (document.getElementById('jq-modal-styles')) return;
        var style = document.createElement('style');
        style.id = 'jq-modal-styles';
        style.textContent = [
            /* Backdrop */
            '.jq-modal-backdrop {',
            '  position: fixed; inset: 0; z-index: 9000;',
            '  background: rgba(0,0,0,0.55);',
            '  display: flex; align-items: center; justify-content: center;',
            '  opacity: 0; pointer-events: none;',
            '  transition: opacity ' + TRANSITION_MS + 'ms ease;',
            '}',
            '.jq-modal-backdrop.jq-modal--open {',
            '  opacity: 1; pointer-events: auto;',
            '}',
            /* Modal box */
            '.jq-modal {',
            '  position: relative;',
            '  background: #fff;',
            '  border-radius: 12px;',
            '  box-shadow: 0 20px 60px rgba(0,0,0,0.3);',
            '  padding: 32px 28px 24px;',
            '  width: 90%; max-width: 540px; max-height: 85vh;',
            '  display: flex; flex-direction: column;',
            '  transform: translateY(-20px);',
            '  transition: transform ' + TRANSITION_MS + 'ms ease;',
            '}',
            '.jq-modal-backdrop.jq-modal--open .jq-modal {',
            '  transform: translateY(0);',
            '}',
            /* Close button */
            '.jq-modal__close {',
            '  position: absolute; top: 14px; right: 16px;',
            '  background: none; border: none; cursor: pointer;',
            '  font-size: 20px; line-height: 1; color: #6b7280;',
            '  padding: 4px 8px; border-radius: 6px;',
            '  transition: background 150ms;',
            '}',
            '.jq-modal__close:hover { background: #f3f4f6; color: #111; }',
            /* Title */
            '.jq-modal__title {',
            '  font-size: 1.15rem; font-weight: 700;',
            '  color: #111827; margin: 0 0 16px;',
            '}',
            /* Body */
            '.jq-modal__body {',
            '  flex: 1; overflow-y: auto;',
            '  font-size: 0.925rem; line-height: 1.65;',
            '  color: #374151;',
            '}',
            /* Footer */
            '.jq-modal__footer {',
            '  display: flex; justify-content: flex-end; gap: 10px;',
            '  margin-top: 20px; padding-top: 16px;',
            '  border-top: 1px solid #e5e7eb;',
            '}',
            /* Buttons */
            '.jq-btn {',
            '  padding: 9px 20px; border-radius: 8px;',
            '  font-size: 0.9rem; font-weight: 600;',
            '  cursor: pointer; border: none;',
            '  transition: opacity 150ms, background 150ms;',
            '}',
            '.jq-btn:hover { opacity: 0.88; }',
            '.jq-btn--primary { background: #1d4ed8; color: #fff; }',
            '.jq-btn--secondary { background: #e5e7eb; color: #374151; }',
            '.jq-btn--danger { background: #dc2626; color: #fff; }',
            /* Disclaimer-specific */
            '.jq-modal--disclaimer .jq-modal { max-width: 600px; }',
            '.jq-modal--disclaimer .jq-modal__body {',
            '  max-height: 50vh; border: 1px solid #e5e7eb;',
            '  border-radius: 6px; padding: 12px 14px;',
            '  background: #f9fafb;',
            '}'
        ].join('\n');
        document.head.appendChild(style);
    }

    // -------------------------------------------------------------------------
    // MODAL REGISTRY
    // Maps modalId -> { backdrop element, resolve fn (for confirm) }
    // -------------------------------------------------------------------------
    var registry = {};

    // -------------------------------------------------------------------------
    // CORE: createBackdrop
    // -------------------------------------------------------------------------
    function createBackdrop(modalId, extraClass) {
        var backdrop = document.createElement('div');
        backdrop.className = BACKDROP_CLASS + (extraClass ? ' ' + extraClass : '');
        backdrop.setAttribute('data-modal-id', modalId);
        backdrop.setAttribute('role', 'dialog');
        backdrop.setAttribute('aria-modal', 'true');

        // Click outside modal content → close
        backdrop.addEventListener('click', function (e) {
            if (e.target === backdrop) {
                JudiQModals.close(modalId);
            }
        });

        document.body.appendChild(backdrop);
        return backdrop;
    }

    // -------------------------------------------------------------------------
    // OPEN / CLOSE
    // -------------------------------------------------------------------------
    function openModal(modalId) {
        // Support HTML-defined modals (backdrop already in DOM)
        var existing = document.querySelector('[data-modal-id="' + modalId + '"].' + BACKDROP_CLASS);
        if (existing) {
            existing.classList.add(OPEN_CLASS);
            trapFocus(existing);
            return;
        }
        // Dynamically-created modals stored in registry
        if (registry[modalId]) {
            registry[modalId].backdrop.classList.add(OPEN_CLASS);
            trapFocus(registry[modalId].backdrop);
        }
    }

    function closeModal(modalId) {
        var entry = registry[modalId];
        if (entry) {
            entry.backdrop.classList.remove(OPEN_CLASS);
            // Allow transition to finish, then remove from DOM
            setTimeout(function () {
                if (entry.backdrop && entry.backdrop.parentNode) {
                    entry.backdrop.parentNode.removeChild(entry.backdrop);
                }
                delete registry[modalId];
            }, TRANSITION_MS + 50);
            if (typeof entry.onClose === 'function') entry.onClose();
            return;
        }
        // HTML-defined modal
        var el = document.querySelector('[data-modal-id="' + modalId + '"].' + BACKDROP_CLASS);
        if (el) el.classList.remove(OPEN_CLASS);
    }

    // -------------------------------------------------------------------------
    // FOCUS TRAP
    // -------------------------------------------------------------------------
    function trapFocus(container) {
        var focusable = container.querySelectorAll(
            'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusable.length) return;
        focusable[0].focus();
    }

    // -------------------------------------------------------------------------
    // CONFIRM DIALOG
    // -------------------------------------------------------------------------
    function confirmDialog(message, onConfirm, onCancel) {
        var modalId = 'jq-confirm-' + Date.now();
        var backdrop = createBackdrop(modalId);

        var modal = document.createElement('div');
        modal.className = 'jq-modal';
        modal.setAttribute('role', 'alertdialog');
        modal.setAttribute('aria-labelledby', modalId + '-title');

        modal.innerHTML = safeHtml(
            '<h2 class="jq-modal__title" id="' + escHtml(modalId) + '-title">Confirm Action</h2>' +
            '<div class="jq-modal__body">' + escHtml(message) + '</div>' +
            '<div class="jq-modal__footer">' +
                '<button class="jq-btn jq-btn--secondary" data-action="cancel">Cancel</button>' +
                '<button class="jq-btn jq-btn--primary" data-action="confirm">Confirm</button>' +
            '</div>'
        );

        backdrop.appendChild(modal);

        registry[modalId] = {
            backdrop: backdrop,
            onClose: null
        };

        modal.querySelector('[data-action="confirm"]').addEventListener('click', function () {
            closeModal(modalId);
            if (typeof onConfirm === 'function') onConfirm();
        });

        modal.querySelector('[data-action="cancel"]').addEventListener('click', function () {
            closeModal(modalId);
            if (typeof onCancel === 'function') onCancel();
        });

        // Small tick to allow CSS transition
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                openModal(modalId);
            });
        });
    }

    // -------------------------------------------------------------------------
    // LEGAL DISCLAIMER MODAL
    // -------------------------------------------------------------------------
    function legalDisclaimerModal(text) {
        var modalId = 'jq-legal-disclaimer';

        // Don't duplicate
        if (registry[modalId]) return;

        var backdrop = createBackdrop(modalId, 'jq-modal--disclaimer');

        var modal = document.createElement('div');
        modal.className = 'jq-modal';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-labelledby', 'jq-disclaimer-title');
        modal.setAttribute('aria-describedby', 'jq-disclaimer-body');

        var defaultText = text || [
            '<strong>Legal Disclaimer</strong>',
            '<p>JudiQ is an AI-assisted legal research and case management platform. ',
            'It is intended to assist legal professionals and does <em>not</em> constitute ',
            'legal advice. All analyses, summaries, and generated content should be ',
            'independently verified by a qualified attorney before being relied upon in ',
            'any legal proceeding.</p>',
            '<p>By using JudiQ you acknowledge that:</p>',
            '<ul>',
            '<li>AI-generated content may contain errors or omissions.</li>',
            '<li>JudiQ assumes no liability for decisions made based on its output.</li>',
            '<li>Case data submitted is processed in accordance with the JudiQ Privacy Policy.</li>',
            '<li>You are responsible for ensuring compliance with applicable data-protection laws.</li>',
            '</ul>'
        ].join('');

        modal.innerHTML = safeHtml(
            '<h2 class="jq-modal__title" id="jq-disclaimer-title">' +
                '<i class="fas fa-gavel" style="color:#1d4ed8;margin-right:8px;"></i>' +
                'Legal Disclaimer &amp; Terms of Use' +
            '</h2>' +
            '<div class="jq-modal__body" id="jq-disclaimer-body">' + defaultText + '</div>' +
            '<div class="jq-modal__footer">' +
                '<button class="jq-btn jq-btn--secondary" data-action="decline">Decline</button>' +
                '<button class="jq-btn jq-btn--primary" data-action="accept">I Understand &amp; Accept</button>' +
            '</div>'
        );

        backdrop.appendChild(modal);

        registry[modalId] = {
            backdrop: backdrop,
            onClose: null
        };

        modal.querySelector('[data-action="accept"]').addEventListener('click', function () {
            try { localStorage.setItem(DISCLAIMER_KEY, 'true'); } catch (_) {}
            closeModal(modalId);
        });

        modal.querySelector('[data-action="decline"]').addEventListener('click', function () {
            closeModal(modalId);
            // Optionally redirect or disable features
            if (typeof window.JudiQModals._onDisclaimerDecline === 'function') {
                window.JudiQModals._onDisclaimerDecline();
            }
        });

        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                openModal(modalId);
            });
        });
    }

    // -------------------------------------------------------------------------
    // FIRST-VISIT DISCLAIMER CHECK
    // -------------------------------------------------------------------------
    function checkFirstVisitDisclaimer() {
        var accepted = false;
        try { accepted = localStorage.getItem(DISCLAIMER_KEY) === 'true'; } catch (_) {}
        if (!accepted) {
            legalDisclaimerModal();
        }
    }

    // -------------------------------------------------------------------------
    // KEYBOARD — global Escape to close topmost modal
    // -------------------------------------------------------------------------
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape' && e.keyCode !== 27) return;
        // Close the most-recently-opened modal
        var ids = Object.keys(registry);
        if (ids.length) {
            closeModal(ids[ids.length - 1]);
        } else {
            // HTML-defined modals
            var openBackdrops = document.querySelectorAll('.' + BACKDROP_CLASS + '.' + OPEN_CLASS);
            if (openBackdrops.length) {
                var last = openBackdrops[openBackdrops.length - 1];
                last.classList.remove(OPEN_CLASS);
            }
        }
    });

    // -------------------------------------------------------------------------
    // DATA-ATTRIBUTE AUTO-WIRING
    // data-modal-open="modalId"  → click opens that modal
    // data-modal-close="modalId" → click closes that modal
    // -------------------------------------------------------------------------
    function wireDataAttributes() {
        document.querySelectorAll('[data-modal-open]').forEach(function (el) {
            el.addEventListener('click', function () {
                openModal(el.getAttribute('data-modal-open'));
            });
        });

        document.querySelectorAll('[data-modal-close]').forEach(function (el) {
            el.addEventListener('click', function () {
                closeModal(el.getAttribute('data-modal-close'));
            });
        });

        // Wire close buttons inside HTML-defined backdrops
        document.querySelectorAll('.' + BACKDROP_CLASS + ' .jq-modal__close').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var backdrop = btn.closest('.' + BACKDROP_CLASS);
                if (backdrop) backdrop.classList.remove(OPEN_CLASS);
            });
        });

        // Backdrop-click for HTML-defined modals
        document.querySelectorAll('.' + BACKDROP_CLASS).forEach(function (backdrop) {
            backdrop.addEventListener('click', function (e) {
                if (e.target === backdrop) {
                    backdrop.classList.remove(OPEN_CLASS);
                }
            });
        });
    }

    // -------------------------------------------------------------------------
    // DOM READY
    // -------------------------------------------------------------------------
    function onDOMReady(fn) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', fn);
        } else {
            fn();
        }
    }

    onDOMReady(function () {
        injectStyles();
        wireDataAttributes();
        checkFirstVisitDisclaimer();
    });

    // -------------------------------------------------------------------------
    // PUBLIC API
    // -------------------------------------------------------------------------
    var JudiQModals = {
        /**
         * Open a modal by ID.
         * Works for HTML-defined modals (data-modal-id="<id>") and dynamic ones.
         * @param {string} modalId
         */
        open: openModal,

        /**
         * Close a modal by ID.
         * @param {string} modalId
         */
        close: closeModal,

        /**
         * Show a confirmation dialog.
         * @param {string} message
         * @param {Function} onConfirm
         * @param {Function} [onCancel]
         */
        confirm: confirmDialog,

        /**
         * Show the legal disclaimer modal with a custom text (HTML allowed, will be sanitized).
         * @param {string} [text] - Optional HTML body text. Defaults to standard JudiQ disclaimer.
         */
        legalDisclaimer: legalDisclaimerModal,

        /**
         * Re-check and show disclaimer if not yet accepted.
         */
        checkDisclaimer: checkFirstVisitDisclaimer,

        /**
         * Reset the disclaimer acceptance (for testing / account switch).
         */
        resetDisclaimer: function () {
            try { localStorage.removeItem(DISCLAIMER_KEY); } catch (_) {}
        },

        /**
         * Override this to handle disclaimer decline (e.g. redirect away).
         * @type {Function|null}
         */
        _onDisclaimerDecline: null,

        /**
         * Re-wire data-attribute bindings (call after dynamic DOM insertions).
         */
        rewire: wireDataAttributes,

        /**
         * Inject modal styles manually (called automatically on DOMReady).
         */
        injectStyles: injectStyles
    };

    export { JudiQModals };

    


