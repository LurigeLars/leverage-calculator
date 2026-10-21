/**
 * Offline first-order leverage estimator. Percent values use percentage points.
 * No network access, storage, user accounts, or execution features.
 */
(function (root) {
  'use strict';

  function requireFinite(value, name) {
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      throw new RangeError(name + ' must be a finite number');
    }
    return value;
  }

  function estimate(input) {
    const leverage = requireFinite(input.leverage, 'leverage');
    const movePct = requireFinite(input.movePct, 'movePct');
    const spreadPct = requireFinite(input.spreadPct, 'spreadPct');
    const targetPct = requireFinite(input.targetPct === undefined ? 5 : input.targetPct, 'targetPct');
    const feesPct = requireFinite(input.feesPct === undefined ? 0 : input.feesPct, 'feesPct');
    const slippagePct = requireFinite(input.slippagePct === undefined ? 0 : input.slippagePct, 'slippagePct');

    if (leverage <= 0 || leverage > 100) throw new RangeError('leverage must be between 0 and 100');
    if (spreadPct < 0 || feesPct < 0 || slippagePct < 0) throw new RangeError('Costs cannot be negative');
    if (targetPct < 0) throw new RangeError('targetPct cannot be negative');

    const costsPct = spreadPct + feesPct + slippagePct;
    const grossPct = leverage * movePct;
    const netPct = grossPct - costsPct;
    return {
      grossPct,
      costsPct,
      netPct,
      breakEvenMovePct: costsPct / leverage,
      targetMovePct: (targetPct + costsPct) / leverage,
      maxSpreadForTargetPct: grossPct - targetPct - feesPct - slippagePct,
      maxSpreadForBreakevenPct: grossPct - feesPct - slippagePct,
      approximationUnreliable: Math.abs(grossPct) >= 30 || netPct <= -100
    };
  }

  function spreadFromQuotes(bid, ask) {
    requireFinite(bid, 'bid');
    requireFinite(ask, 'ask');
    if (bid <= 0 || ask <= 0 || bid > ask) {
      throw new RangeError('Require 0 < bid <= ask');
    }
    return ((ask - bid) / ask) * 100;
  }

  const api = Object.freeze({ estimate, spreadFromQuotes });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.LeverageCalculator = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
