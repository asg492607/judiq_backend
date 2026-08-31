/**
 * JudiQ AI — Enterprise Reactive State Store
 * Provides pub/sub state management, immutability guarantees, and backward compatibility.
 */

class JudiQStore {
    constructor(initialState = {}) {
        this._state = {
            currentUser: null,
            currentRole: null,
            userDomain: 'ni_act',
            currentStep: 1,
            totalSteps: 9,
            caseData: {},
            currentExperienceMode: 'executive',
            analysisResult: null,
            activeCaseId: null,
            activeClientId: null,
            cmsActiveTab: 'overview',
            cmsListFilters: {
                status: 'all',
                case_type: 'all',
                priority: 'all',
                search: '',
                page: 1
            },
            ...initialState
        };
        this._listeners = new Set();
        this._keyListeners = new Map();
    }

    /**
     * Get current snapshot of state
     */
    getState() {
        return this._state;
    }

    /**
     * Select a specific property from state
     */
    get(key, defaultValue = null) {
        return this._state[key] !== undefined ? this._state[key] : defaultValue;
    }

    /**
     * Set a property with change notification
     */
    set(key, value) {
        const prevValue = this._state[key];
        if (prevValue === value) return;

        this._state[key] = value;
        this._notifyKey(key, value, prevValue);
        this._notifyAll();
    }

    /**
     * Merge multiple properties atomically
     */
    update(partialState) {
        let hasChanged = false;
        const changes = [];

        for (const [key, value] of Object.entries(partialState)) {
            const prevValue = this._state[key];
            if (prevValue !== value) {
                this._state[key] = value;
                changes.push({ key, value, prevValue });
                hasChanged = true;
            }
        }

        if (hasChanged) {
            changes.forEach(({ key, value, prevValue }) => {
                this._notifyKey(key, value, prevValue);
            });
            this._notifyAll();
        }
    }

    /**
     * Subscribe to all state changes
     */
    subscribe(callback) {
        this._listeners.add(callback);
        return () => this._listeners.delete(callback);
    }

    /**
     * Subscribe to changes on a specific key
     */
    subscribeKey(key, callback) {
        if (!this._keyListeners.has(key)) {
            this._keyListeners.set(key, new Set());
        }
        this._keyListeners.get(key).add(callback);
        return () => this._keyListeners.get(key)?.delete(callback);
    }

    /**
     * Dispatch structured actions
     */
    dispatch(actionType, payload) {
        switch (actionType) {
            case 'SET_USER':
                this.update({ currentUser: payload });
                break;
            case 'SET_ROLE':
                this.update({ currentRole: payload });
                break;
            case 'SET_DOMAIN':
                this.update({ userDomain: payload });
                break;
            case 'SET_CASE_DATA':
                this.update({ caseData: { ...this._state.caseData, ...payload } });
                break;
            case 'SET_ANALYSIS_RESULT':
                this.update({ analysisResult: payload });
                break;
            case 'RESET_CASE':
                this.update({ caseData: {}, analysisResult: null, currentStep: 1 });
                break;
            default:
                if (typeof actionType === 'function') {
                    actionType(this);
                }
        }
    }

    _notifyAll() {
        this._listeners.forEach(fn => {
            try { fn(this._state); } catch (e) { console.error('Store subscriber error:', e); }
        });
    }

    _notifyKey(key, value, prevValue) {
        const listeners = this._keyListeners.get(key);
        if (listeners) {
            listeners.forEach(fn => {
                try { fn(value, prevValue); } catch (e) { console.error(`Store key subscriber error [${key}]:`, e); }
            });
        }
    }

    /**
     * Attach backward-compatible Proxy to window.state
     */
    attachGlobalProxy() {
        const store = this;
        window.state = new Proxy(store._state, {
            get(target, prop) {
                return target[prop];
            },
            set(target, prop, value) {
                store.set(prop, value);
                return true;
            }
        });
        window.judiqStore = store;
    }
}

export const store = new JudiQStore();
