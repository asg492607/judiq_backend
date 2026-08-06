/**
 * JudiQ — validation.js
 * Frontend input validation and sanitization for the multi-step case wizard.
 *
 * Exposed global:
 *   window.JudiQValidator
 *
 * No ES6 imports/exports — plain script tag compatible.
 */

  /* ─────────────────────────────────────────────────
   * Constants
   * ───────────────────────────────────────────────── */

  /** Maximum allowed amount (10 crore in base currency units) */
  var MAX_AMOUNT = 10_00_00_000; // 10,00,00,000

  /**
   * IFSC format:
   *   - 4 uppercase alphabetic characters (bank code)
   *   - literal '0' (zero)
   *   - 6 alphanumeric characters (branch code)
   * Total: 11 characters.
   */
  var IFSC_REGEX = /^[A-Z]{4}0[A-Z0-9]{6}$/;

  /** CSS class applied to invalid fields */
  var ERROR_FIELD_CLASS = 'judiq-field-error';

  /** CSS class applied to error message containers */
  var ERROR_MSG_CLASS = 'judiq-error-msg';

  /**
   * Step → required field IDs.
   * Keys match the `stepId` argument passed to validateFormStep().
   * Extend this map as new wizard steps are added.
   */
  var STEP_REQUIRED_FIELDS = {
    'step-1': ['case_id', 'case_title', 'complainant_type', 'filing_date', 'court_name', 'case_type'],
    'step-2': ['complainant_name', 'complainant_address', 'complainant_authorized', 'accused_name', 'accused_type', 'accused_address', 'directors_named'],
    'step-3': ['transaction_date', 'purpose', 'agreement_type', 'supporting_documents', 'debt_acknowledgment'],
    'step-4': ['cheque_number', 'cheque_date', 'cheque_amount', 'bank_name', 'cheque_type', 'post_dated'],
    'step-5': ['dishonour_date', 'dishonour_reason', 'bank_memo_received', 'presentation_date']
  };

  /**
   * Step → field-specific validators.
   * Each entry is a function (value) → string|null (error message or null).
   */
  var STEP_FIELD_VALIDATORS = {
    'step-3': { transaction_date: _runDateValidator },
    'step-4': { cheque_date: _runDateValidator, cheque_amount: _runAmountValidator },
    'step-5': { dishonour_date: _runDateValidator, presentation_date: _runDateValidator }
  };

  /* ─────────────────────────────────────────────────
   * Internal pure validator functions
   * (return null on success, error string on failure)
   * ───────────────────────────────────────────────── */

  function _runAmountValidator(val) {
    return JudiQValidator.validateAmount(val)
      ? null
      : 'Amount must be a positive number and cannot exceed ₹10,00,00,000 (10 crore).';
  }

  function _runDateValidator(val) {
    return JudiQValidator.validateDate(val)
      ? null
      : 'Date must be a valid past or present date (YYYY-MM-DD).';
  }

  function _runIFSCValidator(val) {
    return JudiQValidator.validateIFSC(val)
      ? null
      : 'IFSC code must be 11 characters: 4 letters, a zero, then 6 alphanumeric characters (e.g. SBIN0001234).';
  }

  /* ─────────────────────────────────────────────────
   * DOM helpers
   * ───────────────────────────────────────────────── */

  /**
   * Return the value of a form field by ID, or null if not found.
   * Handles <input>, <select>, <textarea>, and <input type="file">.
   *
   * @param {string} fieldId
   * @returns {string|FileList|null}
   */
  function _getFieldValue(fieldId) {
    var el = document.getElementById(fieldId);
    if (!el) return null;

    if (el.type === 'file') {
      return (el.files && el.files.length > 0) ? el.files : null;
    }
    if (el.type === 'checkbox') {
      return el.checked ? 'checked' : '';
    }
    return (el.value !== undefined) ? el.value : null;
  }

  /**
   * Apply error styling to a field element.
   * @param {HTMLElement} el
   * @param {string}      message
   */
  function _applyFieldError(el, message) {
    el.classList.add(ERROR_FIELD_CLASS);
    el.setAttribute('aria-invalid', 'true');

    // Avoid duplicate messages
    var msgId = ERROR_MSG_CLASS + '--' + el.id;
    var existing = document.getElementById(msgId);
    if (existing) {
      existing.textContent = message;
      return;
    }

    var msg = document.createElement('span');
    msg.id          = msgId;
    msg.className   = ERROR_MSG_CLASS;
    msg.textContent = message;
    msg.setAttribute('role', 'alert');
    msg.setAttribute('aria-live', 'polite');

    // Insert right after the field (or its parent label wrapper)
    var insertAfter = el.closest('[data-field-wrapper]') || el;
    if (insertAfter.parentNode) {
      insertAfter.parentNode.insertBefore(msg, insertAfter.nextSibling);
    }
  }

  /**
   * Remove error styling from a single field element.
   * @param {HTMLElement} el
   */
  function _clearFieldError(el) {
    el.classList.remove(ERROR_FIELD_CLASS);
    el.removeAttribute('aria-invalid');

    var msgId   = ERROR_MSG_CLASS + '--' + el.id;
    var msgEl   = document.getElementById(msgId);
    if (msgEl && msgEl.parentNode) {
      msgEl.parentNode.removeChild(msgEl);
    }
  }

  /* ─────────────────────────────────────────────────
   * JudiQValidator public API
   * ───────────────────────────────────────────────── */

  var JudiQValidator = {

    /* ── sanitizeString ──────────────────────────────────────────────── */

    /**
     * Strip script/style tags and potentially dangerous HTML attributes,
     * then trim surrounding whitespace.
     *
     * Uses DOMPurify when available; falls back to a regex-based approach.
     *
     * @param {*}      val — raw input (will be coerced to string)
     * @returns {string}  — cleaned, trimmed string
     */
    sanitizeString: function (val) {
      var str = (val === null || val === undefined) ? '' : String(val);

      if (typeof DOMPurify !== 'undefined') {
        // Allow zero HTML — plain text only
        return DOMPurify.sanitize(str, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] }).trim();
      }

      // Fallback: strip <script>, <style>, and all remaining HTML tags
      return str
        .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, '')
        .replace(/<[^>]*>/g, '')
        .trim();
    },

    /* ── validateFormStep ────────────────────────────────────────────── */

    /**
     * Validate all required fields for a given wizard step.
     * Also runs field-specific validators (amount, date, IFSC) where defined.
     *
     * @param {string} stepId   — e.g. 'step-1', 'step-3'
     * @param {object} formData — optional pre-collected key→value map;
     *                            if omitted, values are read from the DOM.
     * @returns {{ valid: boolean, errors: string[] }}
     */
    validateFormStep: function (stepId, formData) {
      var errors  = [];
      var fields  = STEP_REQUIRED_FIELDS[stepId] || [];
      var extra   = STEP_FIELD_VALIDATORS[stepId] || {};
      var data    = formData || {};

      fields.forEach(function (fieldId) {
        // Resolve value — prefer passed formData, then read from DOM
        var rawValue = (data[fieldId] !== undefined)
          ? data[fieldId]
          : _getFieldValue(fieldId);

        // ── Required check ───────────────────────────────────────────
        var isEmpty = (rawValue === null || rawValue === undefined);

        if (!isEmpty && typeof rawValue === 'string') {
          isEmpty = JudiQValidator.sanitizeString(rawValue) === '';
        }

        // FileList empty?
        if (!isEmpty && rawValue && typeof rawValue === 'object' && rawValue.length === 0) {
          isEmpty = true;
        }

        if (isEmpty) {
          errors.push(fieldId + ' is required.');
          return; // skip further checks for this field
        }

        // ── Field-specific validator ─────────────────────────────────
        if (extra[fieldId] && typeof extra[fieldId] === 'function') {
          var value  = (typeof rawValue === 'string')
            ? JudiQValidator.sanitizeString(rawValue)
            : rawValue;
          var errMsg = extra[fieldId](value);
          if (errMsg) {
            errors.push(fieldId + ': ' + errMsg);
          }
        }
      });

      return {
        valid:  errors.length === 0,
        errors: errors
      };
    },

    /* ── validateAmount ──────────────────────────────────────────────── */

    /**
     * Checks that the value is a finite positive number and does not
     * exceed 10 crore (₹10,00,00,000).
     *
     * @param {string|number} val
     * @returns {boolean}
     */
    validateAmount: function (val) {
      var num = parseFloat(String(val).replace(/,/g, ''));
      return (
        !isNaN(num) &&
        isFinite(num) &&
        num > 0 &&
        num <= MAX_AMOUNT
      );
    },

    /* ── validateDate ────────────────────────────────────────────────── */

    /**
     * Checks that the value is a valid calendar date that is not in the future.
     * Accepts ISO 8601 date strings (YYYY-MM-DD) and any string parseable by Date.
     *
     * @param {string} val
     * @returns {boolean}
     */
    validateDate: function (val) {
      if (!val || typeof val !== 'string') return false;

      var trimmed = val.trim();
      if (trimmed === '') return false;

      // Reject obviously non-date strings early
      // ISO 8601: YYYY-MM-DD
      var isoPattern = /^\d{4}-\d{2}-\d{2}$/;
      if (!isoPattern.test(trimmed)) {
        // Still attempt to parse other recognisable formats
        var parsed = new Date(trimmed);
        if (isNaN(parsed.getTime())) return false;
        // Ensure date is not in the future
        var today = new Date();
        today.setHours(23, 59, 59, 999);
        return parsed <= today;
      }

      var parts = trimmed.split('-');
      var year  = parseInt(parts[0], 10);
      var month = parseInt(parts[1], 10);
      var day   = parseInt(parts[2], 10);

      // Basic range checks
      if (year < 1900 || month < 1 || month > 12 || day < 1 || day > 31) {
        return false;
      }

      var date = new Date(year, month - 1, day);
      // Verify the Date object matches (catches Feb 30, etc.)
      if (
        date.getFullYear() !== year ||
        date.getMonth()    !== month - 1 ||
        date.getDate()     !== day
      ) {
        return false;
      }

      var now = new Date();
      now.setHours(23, 59, 59, 999);
      return date <= now;
    },

    /* ── validateIFSC ────────────────────────────────────────────────── */

    /**
     * Validates an Indian Financial System Code (IFSC).
     * Format: 4 uppercase alpha + '0' + 6 uppercase alphanumeric = 11 chars.
     *
     * @param {string} val
     * @returns {boolean}
     */
    validateIFSC: function (val) {
      if (!val || typeof val !== 'string') return false;
      var clean = val.trim().toUpperCase();
      return IFSC_REGEX.test(clean);
    },

    /* ── highlightErrors ─────────────────────────────────────────────── */

    /**
     * For each error string that starts with a known field ID prefix,
     * applies a red border and an error message element beneath the field.
     * Errors that cannot be mapped to a DOM element are skipped silently.
     *
     * Error string format (produced by validateFormStep):
     *   "<fieldId> is required."
     *   "<fieldId>: <message>"
     *
     * @param {string[]} errors — array of error strings
     */
    highlightErrors: function (errors) {
      if (!Array.isArray(errors)) return;

      errors.forEach(function (errStr) {
        if (typeof errStr !== 'string') return;

        // Parse fieldId from the error string
        var colonIdx = errStr.indexOf(':');
        var spaceIdx = errStr.indexOf(' ');
        var fieldId, message;

        if (colonIdx > -1 && (colonIdx < spaceIdx || spaceIdx === -1)) {
          // Format: "fieldId: message"
          fieldId = errStr.substring(0, colonIdx).trim();
          message = errStr.substring(colonIdx + 1).trim();
        } else if (spaceIdx > -1) {
          // Format: "fieldId is required."
          fieldId = errStr.substring(0, spaceIdx).trim();
          message = errStr;
        } else {
          // Cannot parse — skip
          return;
        }

        var el = fieldId ? document.getElementById(fieldId) : null;
        if (el) {
          _applyFieldError(el, message);
        }
      });
    },

    /* ── clearErrors ─────────────────────────────────────────────────── */

    /**
     * Remove all validation highlights and error messages from the page.
     * Call this before re-running validation or when the user navigates steps.
     */
    clearErrors: function () {
      // Remove error class and aria attributes from all flagged fields
      var errorFields = document.querySelectorAll('.' + ERROR_FIELD_CLASS);
      errorFields.forEach(function (el) {
        _clearFieldError(el);
      });

      // Remove any orphaned error message elements
      var orphanMsgs = document.querySelectorAll('.' + ERROR_MSG_CLASS);
      orphanMsgs.forEach(function (el) {
        if (el.parentNode) {
          el.parentNode.removeChild(el);
        }
      });
    }
  };

  /* ─────────────────────────────────────────────────
   * Inject companion CSS (if not already present)
   * ───────────────────────────────────────────────── */

  
    var STYLE_ID = 'judiq-validation-styles';
    if (!document.getElementById(STYLE_ID)) {
        var css = [
          '.' + ERROR_FIELD_CLASS + ' {',
          '  border-color: #ef4444 !important;',
          '  box-shadow: 0 0 0 2px rgba(239,68,68,0.35) !important;',
          '  outline: none;',
          '}',
          '.' + ERROR_MSG_CLASS + ' {',
          '  display: block;',
          '  margin-top: 4px;',
          '  font-size: 0.78rem;',
          '  font-family: "Inter","Segoe UI",sans-serif;',
          '  color: #ef4444;',
          '  line-height: 1.4;',
          '}'
        ].join('\n');

        var style  = document.createElement('style');
        style.id   = STYLE_ID;
        style.type = 'text/css';
        style.appendChild(document.createTextNode(css));

        var head = document.head || document.getElementsByTagName('head')[0];
        if (head) head.appendChild(style);
    }

  /* ─────────────────────────────────────────────────
   * Expose global
   * ───────────────────────────────────────────────── */

  export { JudiQValidator };


