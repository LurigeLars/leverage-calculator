# Leverage Calculator

A compact, dark-mode **offline** calculator for leveraged trade scenarios. The UI matches a minimal Adobe opening-trade example, but the inputs also work for other underlying assets. **No login, trading API, telemetry, account connection, storage or network requests.**

## Run on Windows

**Without installing anything:** Select **Code → Download ZIP** on GitHub, extract the archive, and double-click `run-in-browser.cmd` to open the interactive calculator in your browser.

**Build a standalone Windows executable:** Install Python 3.12 or 3.13 from [python.org](https://www.python.org/downloads/windows/), then double-click `build-windows.cmd`. The script creates a private `.venv`, installs pinned build tools and generates `dist\LeverageCalculator.exe`. The executable requires Microsoft Edge WebView2 Runtime (usually present on Windows 11), **not** Python. The executable is unsigned and may trigger a Windows SmartScreen prompt.

The Windows executable must be built and tested on Windows. Numerical tests and offline-HTML assembly have been verified on Linux; no claim is made that a Windows binary has been successfully produced here.

## Features

- Preset **5× / 10× / 12× / 15×**, or custom leverage up to 100×
- Interactive underlying move and spread sliders, with editable numerical values
- Estimated net return, break-even move, and move required to reach target net return
- **Advanced settings:** target return, fees, slippage, investment amount, bid/ask spread calculator, copy summary
- Local-only calculation, with no backend or API dependencies

## Formula

Percentage inputs use percentage points: 1 means **1%**.

```text
Estimated net (%) = leverage × underlying move (%) − spread (%) − fees (%) − slippage (%)
Break-even move (%) = (spread + fees + slippage) / leverage
Move for target (%) = (target + spread + fees + slippage) / leverage
Max spread for target (%) = leverage × underlying move − target − fees − slippage
Spread from bid/ask (%) = (ask − bid) / ask × 100
```

The spread is counted **once for the round trip**, not twice. Example: 15×, Adobe +0.50%, spread 1.35% implies an estimated **+6.15%** before additional costs.

**Limitations:** The calculator is an educational first-order estimate, not a product-specific payoff engine or executable quote. Real certificates and derivatives may have reset effects, path dependency, changing leverage, knock-out/barrier terms, issuer repricing, FX exposure, funding costs, slippage and changing bid/ask. Large negative modeled outcomes can be unrealistic for fully paid certificates. No trading is performed and no market data is fetched. Not investment advice.

## Tests

Requires Node.js 18+:

```sh
node --test tests/calculator.test.cjs
```

## Source structure

- `web/` — HTML/CSS/JS calculator, no dependencies
- `desktop/main.py` — local offline pywebview/WebView2 wrapper
- `tests/` — pure-calculation tests
- `build-windows.cmd` — builds a one-file Windows application
- `run-in-browser.cmd` — opens the browser-only version

See [SECURITY.md](SECURITY.md) for privacy guidance.

MIT licensed. No personal financial details, credentials or trading-system files are included.
