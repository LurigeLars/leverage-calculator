(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const elements = {
    leverage: $('leverage-custom'),
    move: $('move-value'),
    moveRange: $('move-range'),
    spread: $('spread-value'),
    spreadRange: $('spread-range'),
    target: $('target-value'),
    fees: $('fees-value'),
    slippage: $('slippage-value'),
    capital: $('capital-value')
  };
  const percent = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const sek = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'SEK', maximumFractionDigits: 0 });
  let current = null;

  function numeric(input, fallback) {
    const normalized = input.value.trim().replace(',', '.');
    if (normalized === '') return fallback;
    const value = Number(normalized);
    return Number.isFinite(value) ? value : fallback;
  }
  function signed(value) {
    return (value > 0 ? '+' : '') + percent.format(value) + ' %';
  }
  function setSelectedLeverage(leverage) {
    document.querySelectorAll('[data-leverage]').forEach((button) => {
      const on = Number(button.dataset.leverage) === leverage;
      button.classList.toggle('is-selected', on);
      button.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }
  function syncSlider(slider, value) {
    slider.min = Math.min(Number(slider.min), value);
    slider.max = Math.max(Number(slider.max), value);
    slider.value = String(value);
    slider.setAttribute('aria-valuetext', signed(value));
  }
  function refresh() {
    const leverage = numeric(elements.leverage, NaN);
    const movePct = numeric(elements.move, NaN);
    const spreadPct = numeric(elements.spread, NaN);
    const targetPct = numeric(elements.target, NaN);
    const feesPct = numeric(elements.fees, NaN);
    const slippagePct = numeric(elements.slippage, NaN);
    const capital = numeric(elements.capital, NaN);

    const valid = [leverage, movePct, spreadPct, targetPct, feesPct, slippagePct].every(Number.isFinite)
      && leverage > 0 && leverage <= 100 && movePct >= -100 && movePct <= 100
      && spreadPct >= 0 && targetPct >= 0 && feesPct >= 0 && slippagePct >= 0;

    if (!valid) {
      $('model-warning').hidden = false;
      $('model-warning').textContent = 'Check the inputs: leverage must be above 0 and at most 100; costs and target cannot be negative.';
      $('net-result').textContent = '–';
      current = null;
      return;
    }

    current = { leverage, movePct, spreadPct, targetPct, feesPct, slippagePct, capital };
    const result = LeverageCalculator.estimate(current);
    current.result = result;

    setSelectedLeverage(leverage);
    syncSlider(elements.moveRange, movePct);
    syncSlider(elements.spreadRange, spreadPct);

    const output = $('net-result');
    output.textContent = signed(result.netPct);
    output.className = 'result ' + (result.netPct > 0.00001 ? 'positive' : result.netPct < -0.00001 ? 'negative' : 'neutral');
    $('break-even').textContent = signed(result.breakEvenMovePct);
    $('target-move').textContent = signed(result.targetMovePct);
    $('target-label').textContent = '+' + String(targetPct) + '%';

    const maxSpread = $('max-spread');
    if (result.maxSpreadForTargetPct < 0) {
      maxSpread.textContent = 'Not achievable';
      maxSpread.classList.add('negative-text');
    } else {
      maxSpread.textContent = percent.format(result.maxSpreadForTargetPct) + ' %';
      maxSpread.classList.remove('negative-text');
    }

    const moneyShown = Number.isFinite(capital) && capital > 0;
    $('money-row').hidden = !moneyShown;
    if (moneyShown) $('money-result').textContent = (result.netPct > 0 ? '+' : '') + sek.format(capital * result.netPct / 100);

    const warning = $('model-warning');
    warning.hidden = !result.approximationUnreliable;
    if (result.approximationUnreliable) {
      warning.textContent = 'Warning: the linear approximation is unreliable for this large leverage-amplified move. A fully paid certificate cannot normally fall below zero, while other products may have barriers.';
    }
  }

  document.querySelectorAll('[data-leverage]').forEach((button) => {
    button.addEventListener('click', () => {
      elements.leverage.value = button.dataset.leverage;
      refresh();
    });
  });

  [['moveRange', 'move'], ['spreadRange', 'spread']].forEach(([rangeName, numberName]) => {
    elements[rangeName].addEventListener('input', () => {
      elements[numberName].value = elements[rangeName].value;
      refresh();
    });
  });

  [elements.leverage, elements.move, elements.spread, elements.target, elements.fees,
   elements.slippage, elements.capital].forEach((input) => input.addEventListener('input', refresh));

  [elements.leverage, elements.move, elements.spread, elements.target,
   elements.fees, elements.slippage].forEach((input) => {
    input.addEventListener('change', () => {
      if (input.value.trim() === '') {
        const defaults = {
          'leverage-custom': 15, 'move-value': 0.5, 'spread-value': 1.35,
          'target-value': 5, 'fees-value': 0, 'slippage-value': 0
        };
        input.value = String(defaults[input.id]);
      }
      refresh();
    });
  });

  $('apply-quotes').addEventListener('click', () => {
    const error = $('quote-error');
    error.hidden = true;
    try {
      const bid = numeric($('bid-value'), NaN);
      const ask = numeric($('ask-value'), NaN);
      const spread = LeverageCalculator.spreadFromQuotes(bid, ask);
      elements.spread.value = String(Number(spread.toFixed(4)));
      refresh();
    } catch (_) {
      error.textContent = 'Enter valid prices. Both must be positive and bid must not exceed ask.';
      error.hidden = false;
    }
  });

  $('copy-summary').addEventListener('click', async () => {
    if (!current) return;
    const c = current;
    const summary = [
      'Leverage Calculator (simplified model)',
      'Leverage: ' + c.leverage + '×',
      'Underlying move: ' + signed(c.movePct),
      'Spread: ' + percent.format(c.spreadPct) + ' %',
      'Other costs: ' + percent.format(c.feesPct + c.slippagePct) + ' %',
      'Estimated net return: ' + signed(c.result.netPct),
      'Break-even: ' + signed(c.result.breakEvenMovePct),
      'Underlying move for +' + c.targetPct + '% net: ' + signed(c.result.targetMovePct),
      'Model values only, not an executable instrument quote.'
    ].join('\n');
    const button = $('copy-summary');
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(summary);
      } else {
        const tmp = document.createElement('textarea');
        tmp.value = summary;
        tmp.style.position = 'fixed';
        tmp.style.opacity = '0';
        document.body.appendChild(tmp);
        tmp.select();
        const ok = document.execCommand('copy');
        tmp.remove();
        if (!ok) throw new Error('Clipboard unavailable');
      }
      button.textContent = 'Copied!';
    } catch (_) {
      button.textContent = 'Copy blocked';
    }
    setTimeout(() => { button.textContent = 'Copy summary'; }, 1800);
  });

  refresh();
})();
