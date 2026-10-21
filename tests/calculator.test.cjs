'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { estimate, spreadFromQuotes } = require('../web/calculator.js');

function close(actual, expected, tolerance=1e-8) {
  assert.ok(Math.abs(actual - expected) < tolerance, String(actual) + ' differs from ' + String(expected));
}
test('screenshot: 10x, +1%, spread 2.05%', () => {
  const r = estimate({leverage:10, movePct:1, spreadPct:2.05});
  close(r.netPct, 7.95);
  close(r.breakEvenMovePct, .205);
  close(r.targetMovePct, .705);
});
test('Adobe: 15x, +0.5%, spread 1.35%', () => {
  const r = estimate({leverage:15, movePct:.5, spreadPct:1.35});
  close(r.netPct, 6.15);
  close(r.breakEvenMovePct, .09);
  close(r.targetMovePct, 6.35/15);
});
test('adverse move and other costs', () => {
  const r = estimate({leverage:15, movePct:-.5, spreadPct:1.35, feesPct:.1, slippagePct:.2});
  close(r.netPct, -9.15);
  assert.ok(r.maxSpreadForTargetPct < 0);
});
test('no move: spread is a loss', () => {
  const r = estimate({leverage:5, movePct:0, spreadPct:.45});
  close(r.netPct, -.45);
  close(r.breakEvenMovePct, .09);
});
test('bid ask spread uses ask denominator', () => {
  close(spreadFromQuotes(9.8,10), 2);
  close(spreadFromQuotes(10,10), 0);
});
test('input validation', () => {
  assert.throws(() => estimate({ leverage:0,movePct:1,spreadPct:0 }));
  assert.throws(() => estimate({ leverage:10,movePct:1,spreadPct:-1 }));
  assert.throws(() => estimate({ leverage:NaN,movePct:1,spreadPct:1 }));
  assert.throws(() => spreadFromQuotes(15,14));
  assert.throws(() => spreadFromQuotes(0,15));
});
test('huge adverse payoff is flagged', () => {
  assert.equal(estimate({leverage:15,movePct:-8,spreadPct:2}).approximationUnreliable, true);
});
