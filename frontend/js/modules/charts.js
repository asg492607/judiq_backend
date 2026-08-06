/**
 * JudiQ — charts.js
 * Chart.js registry and rendering helpers.
 * Prevents memory leaks by tracking and destroying chart instances before recreation.
 *
 * Dependencies (must be loaded before this script):
 *   - Chart.js  (global `Chart`)
 *   - DOMPurify (global `DOMPurify`) — used defensively when accepting label strings
 *
 * Exposed globals:
 *   window.ChartRegistry
 *   window.renderAdversarialCharts
 *   window.renderScoreBreakdownChart
 */

  /* ─────────────────────────────────────────────────
   * Internal helpers
   * ───────────────────────────────────────────────── */

  /**
   * Safely sanitize a label string via DOMPurify when available,
   * otherwise fall back to basic tag-stripping.
   * @param {string} str
   * @returns {string}
   */
  function _sanitizeLabel(str) {
    if (typeof str !== 'string') return String(str);
    if (typeof DOMPurify !== 'undefined') {
      return DOMPurify.sanitize(str, { ALLOWED_TAGS: [] });
    }
    // Fallback: strip tags manually
    return str.replace(/<[^>]*>/g, '').trim();
  }

  /**
   * Resolve a canvas element by ID. Throws a descriptive error if not found.
   * @param {string} id
   * @returns {HTMLCanvasElement}
   */
  function _getCanvas(id) {
    var el = document.getElementById(id);
    if (!el) {
      throw new Error('[JudiQ/charts] Canvas element not found: #' + id);
    }
    if (el.tagName.toLowerCase() !== 'canvas') {
      throw new Error('[JudiQ/charts] Element #' + id + ' is not a <canvas>.');
    }
    return el;
  }

  /**
   * Ensure Chart.js is available.
   * @throws {Error} if Chart global is missing.
   */
  function _assertChartJs() {
    if (typeof Chart === 'undefined') {
      throw new Error(
        '[JudiQ/charts] Chart.js is not loaded. ' +
        'Please include Chart.js before charts.js.'
      );
    }
  }

  /* ─────────────────────────────────────────────────
   * ChartRegistry
   * ───────────────────────────────────────────────── */

  /**
   * A registry that tracks live Chart.js instances by canvas element ID.
   * Always call `register` (never `new Chart`) so instances are tracked
   * and old instances are properly destroyed before a replacement is created.
   */
  var ChartRegistry = (function () {
    /** @type {Map<string, Chart>} */
    var _map = new Map();

    /**
     * Destroy any existing chart for `id`, create a new one from `config`,
     * store it, and return the new instance.
     *
     * @param {string}           id     — canvas element ID
     * @param {object}           config — Chart.js configuration object
     * @returns {Chart}
     */
    function register(id, config) {
      _assertChartJs();

      // Destroy existing instance to prevent "Canvas is already in use" errors
      if (_map.has(id)) {
        try {
          _map.get(id).destroy();
        } catch (e) {
          console.warn('[JudiQ/charts] Error destroying chart #' + id + ':', e);
        }
        _map.delete(id);
      }

      var canvas = _getCanvas(id);
      var instance = new Chart(canvas, config);
      _map.set(id, instance);
      return instance;
    }

    /**
     * Destroy a single chart instance and remove it from the registry.
     * No-op if the ID is not registered.
     *
     * @param {string} id — canvas element ID
     */
    function destroy(id) {
      if (!_map.has(id)) return;
      try {
        _map.get(id).destroy();
      } catch (e) {
        console.warn('[JudiQ/charts] Error destroying chart #' + id + ':', e);
      }
      _map.delete(id);
    }

    /**
     * Destroy all registered chart instances and clear the registry.
     * Call this before re-rendering an entire results panel.
     */
    function destroyAll() {
      _map.forEach(function (instance, id) {
        try {
          instance.destroy();
        } catch (e) {
          console.warn('[JudiQ/charts] Error destroying chart #' + id + ':', e);
        }
      });
      _map.clear();
    }

    /**
     * Returns the number of currently registered charts (useful for debugging).
     * @returns {number}
     */
    function size() {
      return _map.size;
    }

    /**
     * Returns whether a chart is currently registered for the given ID.
     * @param {string} id
     * @returns {boolean}
     */
    function has(id) {
      return _map.has(id);
    }

    return {
      register:   register,
      destroy:    destroy,
      destroyAll: destroyAll,
      size:       size,
      has:        has
    };
  })();

  /* ─────────────────────────────────────────────────
   * Shared chart defaults
   * ───────────────────────────────────────────────── */

  /** JudiQ brand palette */
  var COLORS = {
    primary:       'rgba(99, 102, 241, 1)',    // indigo-500
    primaryLight:  'rgba(99, 102, 241, 0.18)',
    danger:        'rgba(239, 68, 68, 1)',     // red-500
    dangerLight:   'rgba(239, 68, 68, 0.18)',
    warning:       'rgba(245, 158, 11, 1)',    // amber-500
    warningLight:  'rgba(245, 158, 11, 0.18)',
    success:       'rgba(16, 185, 129, 1)',    // emerald-500
    successLight:  'rgba(16, 185, 129, 0.18)',
    muted:         'rgba(107, 114, 128, 0.5)', // gray-500 faded
    gridLine:      'rgba(15, 23, 42, 0.08)',
    tickColor:     'rgba(71, 85, 105, 0.8)'
  };

  /** Common font settings */
  var FONT = { family: "'Inter', 'Segoe UI', sans-serif", size: 12 };

  /** Shared axis grid/tick style */
  function _axisDefaults(axisTitle) {
    return {
      grid:  { color: COLORS.gridLine, drawBorder: false },
      ticks: { color: COLORS.tickColor, font: FONT },
      title: axisTitle
        ? { display: true, text: axisTitle, color: 'rgba(15, 23, 42, 0.85)', font: Object.assign({}, FONT, { size: 13, weight: '600' }) }
        : { display: false }
    };
  }

  /** Common plugin defaults (legend + tooltip) */
  function _pluginDefaults(legendPosition) {
    return {
      legend: {
        display:  legendPosition !== 'none',
        position: legendPosition || 'top',
        labels:   { color: COLORS.tickColor, font: FONT, usePointStyle: true }
      },
      tooltip: {
        backgroundColor: 'rgba(15,23,42,0.92)',
        titleColor:      '#f8fafc',
        bodyColor:       '#cbd5e1',
        borderColor:     COLORS.primary,
        borderWidth:     1,
        cornerRadius:    8,
        padding:         10
      }
    };
  }

  /* ─────────────────────────────────────────────────
   * Survivability line-chart config builder
   * ───────────────────────────────────────────────── */

  /**
   * Build Chart.js config for the survivability (causality delta) line chart.
   * @param {object|null} causalityDelta  — data.causality_delta from API
   * @returns {object} Chart.js config
   */
  function _buildSurvivabilityConfig(causalityDelta) {
    // ── Graceful fallback ──────────────────────────────────────────────────
    var labels, values;

    if (
      causalityDelta &&
      Array.isArray(causalityDelta.labels) &&
      causalityDelta.labels.length > 0 &&
      Array.isArray(causalityDelta.values) &&
      causalityDelta.values.length > 0
    ) {
      labels = causalityDelta.labels.map(_sanitizeLabel);
      values = causalityDelta.values.map(Number);
    } else {
      // Fallback: illustrative generic curve
      labels = ['Baseline', 'After Attack 1', 'After Attack 2', 'After Attack 3', 'Final'];
      values = [100, 78, 55, 42, 38];
      console.info(
        '[JudiQ/charts] survivabilityChart: no causality_delta data; using fallback.'
      );
    }

    return {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label:           'Case Survivability (%)',
            data:            values,
            borderColor:     COLORS.primary,
            backgroundColor: COLORS.primaryLight,
            fill:            true,
            tension:         0.42,
            pointRadius:     5,
            pointHoverRadius: 7,
            pointBackgroundColor: COLORS.primary,
            borderWidth:     2
          }
        ]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        animation:           { duration: 600, easing: 'easeOutQuart' },
        plugins:             _pluginDefaults('top'),
        scales: {
          x: _axisDefaults('Adversarial Stage'),
          y: Object.assign({}, _axisDefaults('Survivability (%)'), {
            min:  0,
            max:  100,
            ticks: Object.assign({}, _axisDefaults().ticks, {
              callback: function (v) { return v + '%'; }
            })
          })
        }
      }
    };
  }

  /* ─────────────────────────────────────────────────
   * Attack radar-chart config builder
   * ───────────────────────────────────────────────── */

  /**
   * Build Chart.js config for the attack surface radar chart.
   * @param {Array|null} issues  — data.issues[] from API
   * @returns {object} Chart.js config
   */
  function _buildAttackConfig(issues) {
    var labels, values;

    // Define standard categories to guarantee exactly 5 beautiful axes on the radar chart
    var categories = {
      'Procedural Compliance': 15,
      'Evidence Strength': 15,
      'Jurisdictional Veracity': 15,
      'Statutory Compliance': 15,
      'Witness Credibility': 15
    };

    if (Array.isArray(issues) && issues.length > 0) {
      // Map severity to attack exposure percentage
      var severityScore = { FATAL: 95, CRITICAL: 85, HIGH: 70, MEDIUM: 45, LOW: 25, INFO: 10 };

      issues.forEach(function (issue) {
        if (!issue) return;
        
        var risk = (issue.risk || issue.text || issue.title || '').toLowerCase();
        var category = (issue.category || issue.type || '').toLowerCase();
        
        var targetCat = 'Procedural Compliance';
        if (category === 'evidentiary' || risk.includes('memo') || risk.includes('cheque') || risk.includes('proof') || risk.includes('evidence') || risk.includes('contradiction') || risk.includes('itr') || risk.includes('capacity')) {
          targetCat = 'Evidence Strength';
        } else if (category === 'jurisdictional' || risk.includes('jurisdiction') || risk.includes('court')) {
          targetCat = 'Jurisdictional Veracity';
        } else if (category === 'statutory' || risk.includes('statute') || risk.includes('rule') || risk.includes('act')) {
          targetCat = 'Statutory Compliance';
        } else if (risk.includes('witness') || risk.includes('credibility')) {
          targetCat = 'Witness Credibility';
        } else if (category === 'procedural' || risk.includes('notice') || risk.includes('delay') || risk.includes('time') || risk.includes('premature')) {
          targetCat = 'Procedural Compliance';
        }
        
        var score = severityScore[(issue.severity || '').toUpperCase()] || 40;
        if (score > categories[targetCat]) {
          categories[targetCat] = score;
        }
      });

      labels = Object.keys(categories);
      values = labels.map(function (k) { return categories[k]; });
    } else {
      // Clean baseline profile when no issues are found
      labels = Object.keys(categories);
      values = [15, 15, 15, 15, 15]; // low risk exposure across all dimensions
    }

    return {
      type: 'radar',
      data: {
        labels: labels,
        datasets: [
          {
            label:                'Attack Exposure',
            data:                 values,
            borderColor:          COLORS.danger,
            backgroundColor:      COLORS.dangerLight,
            pointBackgroundColor: COLORS.danger,
            pointBorderColor:     '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor:     COLORS.danger,
            borderWidth:          2,
            pointRadius:          4,
            pointHoverRadius:     6
          }
        ]
      },
      options: {
        responsive:          true,
        maintainAspectRatio: false,
        animation:           { duration: 600, easing: 'easeOutQuart' },
        plugins:             _pluginDefaults('top'),
        scales: {
          r: {
            min:          0,
            max:          100,
            ticks: {
              display:    false,
              stepSize:   25
            },
            grid:  { color: COLORS.gridLine },
            angleLines: { color: COLORS.gridLine },
            pointLabels: {
              color: 'rgba(30, 41, 59, 0.9)',
              font:  Object.assign({}, FONT, { size: 13, weight: '600' })
            }
          }
        }
      }
    };
  }

  /* ─────────────────────────────────────────────────
   * renderAdversarialCharts
   * ───────────────────────────────────────────────── */

  /**
   * Render both adversarial charts (survivability line + attack radar).
   * Destroys any existing instances first to prevent leaks.
   * Deferred with requestAnimationFrame to ensure the DOM is fully painted.
   *
   * @param {object} data — API response object containing:
   *   - data.causality_delta  {object}  (optional)
   *   - data.issues           {Array}   (optional)
   */
  function renderAdversarialCharts(data) {
    _assertChartJs();

    var payload = data || {};

    requestAnimationFrame(function () {
      // ── Survivability line chart ──────────────────────────────────────
      try {
        ChartRegistry.register(
          'survivabilityChart',
          _buildSurvivabilityConfig(payload.causality_delta || null)
        );
      } catch (err) {
        console.error('[JudiQ/charts] Failed to render survivabilityChart:', err);
      }

      // ── Attack radar chart ────────────────────────────────────────────
      try {
        ChartRegistry.register(
          'attackChart',
          _buildAttackConfig(payload.issues || null)
        );
      } catch (err) {
        console.error('[JudiQ/charts] Failed to render attackChart:', err);
      }
    });
  }

  /* ─────────────────────────────────────────────────
   * renderScoreBreakdownChart
   * ───────────────────────────────────────────────── */

  /**
   * Render a horizontal bar chart showing pillar-level score breakdown.
   * Deferred with requestAnimationFrame.
   *
   * @param {Array<{label: string, score: number, max?: number}>} pillarData
   *   Array of pillar objects. `score` should be 0–100 (or 0–`max`).
   *   Example:
   *     [
   *       { label: 'Evidence',    score: 72, max: 100 },
   *       { label: 'Procedure',   score: 88, max: 100 },
   *       { label: 'Credibility', score: 55, max: 100 }
   *     ]
   */
  function renderScoreBreakdownChart(pillarData) {
    _assertChartJs();

    var items = Array.isArray(pillarData) && pillarData.length > 0
      ? pillarData
      : [
          { label: 'Evidence Strength',  score: 70 },
          { label: 'Procedural Compliance', score: 85 },
          { label: 'Witness Credibility', score: 60 },
          { label: 'Legal Precedent',    score: 75 },
          { label: 'Document Integrity', score: 90 }
        ];

    var labels = items.map(function (p) { return _sanitizeLabel(p.label || 'Pillar'); });
    var scores = items.map(function (p) { return Number(p.score) || 0; });

    // Derive bar colours by score threshold
    var bgColors = scores.map(function (s) {
      if (s >= 75) return COLORS.success;
      if (s >= 50) return COLORS.warning;
      return COLORS.danger;
    });

    var config = {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label:            'Pillar Score',
            data:             scores,
            backgroundColor:  bgColors,
            borderRadius:     6,
            borderSkipped:    false,
            barThickness:     22
          }
        ]
      },
      options: {
        indexAxis:           'y',
        responsive:          true,
        maintainAspectRatio: false,
        animation:           { duration: 600, easing: 'easeOutQuart' },
        plugins: Object.assign({}, _pluginDefaults('none'), {
          legend: { display: false }
        }),
        scales: {
          x: Object.assign({}, _axisDefaults('Score'), {
            min:  0,
            max:  100,
            ticks: Object.assign({}, _axisDefaults().ticks, {
              callback: function (v) { return v + '%'; }
            })
          }),
          y: _axisDefaults()
        }
      }
    };

    requestAnimationFrame(function () {
      try {
        ChartRegistry.register('scoreBreakdownChart', config);
      } catch (err) {
        console.error('[JudiQ/charts] Failed to render scoreBreakdownChart:', err);
      }
    });
  }

  /* ─────────────────────────────────────────────────
   * Expose globals
   * ───────────────────────────────────────────────── */

  export { ChartRegistry };
  export { renderAdversarialCharts };
  export { renderScoreBreakdownChart };


