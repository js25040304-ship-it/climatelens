/* Shared display rules. No scientific calculation is performed here. */
(function (root) {
  'use strict';
  const isNumber = v => typeof v === 'number' && Number.isFinite(v);
  function number(value, digits = 3) {
    if (!isNumber(value)) return '—';
    return new Intl.NumberFormat('en-US', {notation: 'standard', maximumSignificantDigits: digits, useGrouping: true}).format(Object.is(value, -0) ? 0 : value);
  }
  function pValue(value) {
    if (!isNumber(value) || value < 0 || value > 1) return '—';
    if (value < 0.001) return '< 0.001';
    let display = number(value);
    // Do not let rounding switch the displayed side of the 0.05 decision.
    if ((Number(display.replaceAll(',', '')) < 0.05) !== (value < 0.05)) display = String(value);
    return display;
  }
  const unit = value => ({C: '°C', 'mm/year': 'mm/year', 'kW-hr/m^2/day': 'kWh/m²/day'}[value] || value || '');
  function excluded(items) {
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    if (!items?.length) return ['No years excluded. Every retained year has 12 valid months.'];
    return items.map(item => {
      const missing = (item.missing_or_invalid_months || []).map(m => months[m - 1]).filter(Boolean);
      return `${item.year} — missing or invalid months: ${missing.length === 12 ? 'all 12 months' : missing.join(', ') || 'not specified'}. This year was excluded, not interpolated.`;
    });
  }
  const reasons = {
    no_key: 'No AI key is configured. Prepared scientific guidance is shown; your analysis and PDF still work.',
    timeout: 'The AI provider timed out. Prepared scientific guidance is shown instead.',
    auth: 'The AI provider rejected authentication. Prepared guidance is shown; ask the project owner to check the server configuration.',
    http_error: 'The AI provider could not complete the request. Prepared scientific guidance is shown instead.',
    bad_response: 'The AI provider returned an unreadable response. Prepared scientific guidance is shown instead.',
    snapshot: 'Shared preview: prepared guidance about the saved NASA record. No external AI service is connected.'
  };
  function reason(code) { return code ? (reasons[code] || 'Prepared guidance is being used because the AI service is unavailable.') : ''; }
  function scopeError(s, lastYear) {
    if (!s.city || !s.variable) return 'Choose a location and variable. Unrecognized fields need your review.';
    if (!Number.isInteger(s.start) || !Number.isInteger(s.end) || s.start < 2001 || s.end > lastYear || s.start > s.end) return `Use whole calendar years from 2001 to ${lastYear}, with the end year after the start year.`;
    if (s.end - s.start < 9) return 'Choose at least 10 calendar years to investigate a long-term trend.';
    return '';
  }
  function gate() { let epoch = 0; return {next: () => ++epoch, current: () => epoch, isCurrent: ticket => ticket === epoch}; }
  const api = {number, pValue, unit, excluded, reason, scopeError, gate};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.ClimateUI = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
