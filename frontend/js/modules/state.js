/**
 * JudiQ Centralized State Store
 * state.js — Singleton state management with pub/sub, localStorage persistence.
 *
 * Usage (plain script tag, no bundler):
 *   <script src="js/modules/state.js"></script>
 *   JudiQState.set('currentRole', 'judge');
 *   JudiQState.get('currentRole');
 *   JudiQState.subscribe('currentRole', (newVal, oldVal) => { ... });
 *   JudiQState.reset();
 */

  // ─── Constants ────────────────────────────────────────────────────────────────

  /** Keys persisted to localStorage. */
  var PERSISTED_KEYS = {
    currentRole: 'judiq_currentRole',
    currentExperienceMode: 'judiq_currentExperienceMode',
  };

  // ─── Default State ─────────────────────────────────────────────────────────────

  /**
   * Returns a fresh copy of the default application state.
   * @returns {Object}
   */
  function buildDefaultState() {
    return {
      currentUser: null,
      currentRole: _loadFromStorage('currentRole', null),
      currentStep: 0,
      totalSteps: 0,
      caseData: null,
      analysisResult: null,
      currentResultTab: 'summary',
      currentExperienceMode: _loadFromStorage('currentExperienceMode', 'standard'),
    };
  }

  // ─── Private Helpers ───────────────────────────────────────────────────────────

  /**
   * Safely read a value from localStorage.
   * Returns `fallback` on any error or if the item is absent.
   * @param {string} stateKey
   * @param {*} fallback
   * @returns {*}
   */
  function _loadFromStorage(stateKey, fallback) {
    var lsKey = PERSISTED_KEYS[stateKey];
    if (!lsKey) return fallback;
    try {
      var raw = localStorage.getItem(lsKey);
      if (raw === null) return fallback;
      return JSON.parse(raw);
    } catch (e) {
      console.warn('[JudiQState] Failed to read "' + lsKey + '" from localStorage:', e);
      return fallback;
    }
  }

  /**
   * Safely write a value to localStorage.
   * Silently swallows errors (e.g. private browsing, storage quota exceeded).
   * @param {string} stateKey
   * @param {*} value
   */
  function _saveToStorage(stateKey, value) {
    var lsKey = PERSISTED_KEYS[stateKey];
    if (!lsKey) return;
    try {
      if (value === null || value === undefined) {
        localStorage.removeItem(lsKey);
      } else {
        localStorage.setItem(lsKey, JSON.stringify(value));
      }
    } catch (e) {
      console.warn('[JudiQState] Failed to write "' + lsKey + '" to localStorage:', e);
    }
  }

  /**
   * Shallow equality check used to avoid firing redundant callbacks.
   * @param {*} a
   * @param {*} b
   * @returns {boolean}
   */
  function _isEqual(a, b) {
    if (a === b) return true;
    // For objects / arrays do a shallow comparison so that identical
    // primitives-only structures are treated as equal.
    if (
      a !== null &&
      b !== null &&
      typeof a === 'object' &&
      typeof b === 'object'
    ) {
      var aKeys = Object.keys(a);
      var bKeys = Object.keys(b);
      if (aKeys.length !== bKeys.length) return false;
      for (var i = 0; i < aKeys.length; i++) {
        var k = aKeys[i];
        if (a[k] !== b[k]) return false;
      }
      return true;
    }
    return false;
  }

  // ─── State Store Factory ────────────────────────────────────────────────────────

  var _state = buildDefaultState();

  /**
   * Map of key → Array<Function> for subscriber callbacks.
   * @type {Object.<string, Function[]>}
   */
  var _subscribers = {};

  /**
   * Notify all subscribers registered for a given key.
   * Errors thrown inside callbacks are caught and logged to prevent one
   * misbehaving subscriber from breaking the rest.
   * @param {string} key
   * @param {*} newValue
   * @param {*} oldValue
   */
  function _notify(key, newValue, oldValue) {
    var callbacks = _subscribers[key];
    if (!callbacks || callbacks.length === 0) return;
    for (var i = 0; i < callbacks.length; i++) {
      try {
        callbacks[i](newValue, oldValue, key);
      } catch (e) {
        console.error(
          '[JudiQState] Subscriber callback error for key "' + key + '":',
          e
        );
      }
    }
  }

  // ─── Public API ────────────────────────────────────────────────────────────────

  /**
   * JudiQState — centralized application state singleton.
   *
   * @namespace JudiQState
   */
  var JudiQState = {

    /**
     * Retrieve the current value for a state key.
     * Returns `undefined` for unknown keys.
     * @param {string} key
     * @returns {*}
     */
    get: function (key) {
      if (!Object.prototype.hasOwnProperty.call(_state, key)) {
        console.warn('[JudiQState] get() called with unknown key: "' + key + '"');
        return undefined;
      }
      return _state[key];
    },

    /**
     * Update the value of a state key and notify subscribers.
     * Subscribers are only called when the value actually changes.
     * Persisted keys are automatically synced to localStorage.
     *
     * @param {string} key   — Must be a recognised state key.
     * @param {*}      value — The new value to set.
     * @returns {boolean}    — true if the value changed, false otherwise.
     */
    set: function (key, value) {
      if (!Object.prototype.hasOwnProperty.call(_state, key)) {
        console.warn('[JudiQState] set() called with unknown key: "' + key + '"');
        return false;
      }

      var oldValue = _state[key];

      if (_isEqual(oldValue, value)) {
        return false; // No change — skip notification.
      }

      _state[key] = value;

      // Persist to localStorage if this is a persisted key.
      if (PERSISTED_KEYS[key]) {
        _saveToStorage(key, value);
      }

      _notify(key, value, oldValue);
      return true;
    },

    /**
     * Register a callback to be invoked whenever `key` changes.
     * Returns an unsubscribe function for cleanup.
     *
     * @param {string}   key      — State key to watch.
     * @param {Function} callback — Called with (newValue, oldValue, key).
     * @returns {Function}        — Call to remove the subscription.
     */
    subscribe: function (key, callback) {
      if (typeof callback !== 'function') {
        console.error('[JudiQState] subscribe() requires a callback function for key: "' + key + '"');
        return function () {}; // no-op unsubscribe
      }

      if (!_subscribers[key]) {
        _subscribers[key] = [];
      }

      _subscribers[key].push(callback);

      // Return an unsubscribe function.
      return function unsubscribe() {
        var list = _subscribers[key];
        if (!list) return;
        var idx = list.indexOf(callback);
        if (idx !== -1) {
          list.splice(idx, 1);
        }
      };
    },

    /**
     * Reset all state to defaults and clear persisted localStorage entries.
     * All subscribers for every key are notified of the change.
     */
    reset: function () {
      var fresh = buildDefaultState();

      // Wipe persisted storage first.
      for (var persistedKey in PERSISTED_KEYS) {
        if (Object.prototype.hasOwnProperty.call(PERSISTED_KEYS, persistedKey)) {
          try {
            localStorage.removeItem(PERSISTED_KEYS[persistedKey]);
          } catch (e) {
            // Silently ignore storage errors during reset.
          }
        }
      }

      // Apply new defaults and notify subscribers for changed keys.
      for (var key in fresh) {
        if (Object.prototype.hasOwnProperty.call(fresh, key)) {
          var oldValue = _state[key];
          _state[key] = fresh[key];
          if (!_isEqual(oldValue, fresh[key])) {
            _notify(key, fresh[key], oldValue);
          }
        }
      }
    },

    /**
     * Returns a shallow snapshot of the entire current state.
     * Useful for debugging; do not mutate the returned object.
     * @returns {Object}
     */
    snapshot: function () {
      var snap = {};
      for (var key in _state) {
        if (Object.prototype.hasOwnProperty.call(_state, key)) {
          snap[key] = _state[key];
        }
      }
      return snap;
    },

    /**
     * Returns the list of all recognised state keys.
     * @returns {string[]}
     */
    keys: function () {
      return Object.keys(_state);
    },
  };

  // ─── Global Export ─────────────────────────────────────────────────────────────

  export { JudiQState };


