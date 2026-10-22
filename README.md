# Leverage Calculator

A compact, dark-mode **offline** calculator for leveraged trade scenarios. The UI matches a minimal Adobe opening-trade example, but the inputs also work for other underlying assets. **No login, trading API, telemetry, account connection or trade-data storage.** The Windows app checks only the public GitHub Releases API at startup for software updates; the calculator itself remains offline.

## Run on Windows

**Without installing anything:** Select **Code → Download ZIP** on GitHub, extract the archive, and double-click `run-in-browser.cmd` to open the interactive calculator in your browser.

**Recommended: install the latest Windows version:** Download `LeverageCalculator-Setup.exe` from [GitHub Releases](https://github.com/LurigeLars/leverage-calculator/releases/latest) and follow the installer. Subsequent updates can be initiated from **Advanced settings → Install update**. The installer is unsigned and Windows SmartScreen may warn.

**Build a standalone Windows executable:** Install Python 3.12 or 3.13 from [python.org](https://www.python.org/downloads/windows/), then double-click `build-windows.cmd`. The script creates a private `.venv`, installs pinned build tools and generates `dist\LeverageCalculator.exe`. The executable requires Microsoft Edge WebView2 Runtime (usually present on Windows 11), **not** Python. The executable is unsigned and may trigger a Windows SmartScreen prompt.

GitHub Actions builds and tests the Windows executable and installer on a Windows runner. A built package is **not** equivalent to interactive testing on the end user's device. The local build script creates the portable executable; the CI workflow also builds the update-capable Windows installer.

## Features

- Preset **5× / 10× / 12× / 15×**, or custom leverage up to 100×
- Interactive underlying move and spread sliders, with editable numerical values
- Estimated net return, break-even move, and move required to reach target net return
- **Advanced settings:** target return, fees, slippage, investment amount, bid/ask spread calculator, copy summary
- Local-only calculation, with no backend or market-data API dependencies
- **Opt-in Windows updates:** checks the public GitHub Releases API at startup and on request; only downloads an installer after user confirmation; verifies SHA-256 before opening the normal user-level setup wizard
- Browser-only version never makes network requests

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
python -m unittest discover -s tests -p "test_*.py" -v
```

## Source structure

- `web/` — HTML/CSS/JS calculator, no dependencies
- `desktop/main.py` — local pywebview/WebView2 wrapper
- `desktop/updater.py` — narrowly scoped GitHub Releases updater; checks SHA-256 before launching a user-approved setup wizard
- `installer/LeverageCalculator.iss` — Windows per-user installer, built by CI
- `VERSION` — software version used by update check and releases
- `tests/` — pure-calculation tests
- `build-windows.cmd` — builds a one-file Windows application
- `run-in-browser.cmd` — opens the browser-only version

See [SECURITY.md](SECURITY.md) for privacy guidance.

MIT licensed. No personal financial details, credentials or trading-system files are included.

## Release process

1. Develop and review changes in a pull request; require a successful Windows build/test run.
2. Update `VERSION` to the intended new semantic version, then merge to `main`.
3. In **Actions → Build Windows and Publish Release → Run workflow**, select **main** and check **publish_release**.
4. The workflow tests the app, builds the `.exe` and Inno Setup installer, writes `SHA256SUMS.txt`, and publishes a versioned GitHub Release only if those steps pass. It refuses to overwrite existing release tags.
5. On the next Windows-app launch, the app checks for the newer release. Click **Install update** and confirm to download and verify the installer. The application then closes itself and hands off to setup. The installer waits for the original process to exit before replacing files. No unattended update is performed.

Only public release metadata (no personal account or trade data) is requested from GitHub. No API token is needed. The updater validates an expected GitHub URL, release format, installer size, and SHA-256. A checksum hosted alongside a binary proves transfer integrity against the release record, **not** publisher authenticity against a compromised GitHub account; signing and verified release provenance remain recommended for broader distribution.

### Updating from v1.1.0 or v1.1.1

These early versions could launch the new installer while the old program was still running, triggering an Inno Setup `unable to automatically close all applications` error. For the first upgrade to v1.1.2: cancel any failed installation, fully close `LeverageCalculator.exe` (check Windows Task Manager → Details if needed), and launch the new setup file manually from [GitHub Releases](https://github.com/LurigeLars/leverage-calculator/releases/latest). **Do not choose `Ignore error and continue`**. From v1.1.2 onward, the desktop updater closes its window and Inno Setup waits for the original process to terminate.
