# Security and privacy

Calculator calculations are offline, with no account connectors, telemetry, trading execution, remote scripts, backend or persistent trade storage. The packaged Windows app makes outbound HTTPS requests **only to check public GitHub Releases for updates**, and downloads the setup binary only after the user explicitly approves. Browser-only usage makes no network calls.

**Do not upload private information** to public issues, screenshots, pull requests or support messages.

- Never commit secrets, account information, local system details, trade exports, or logs.
- Review and update third-party build dependencies before running.
- Build the Windows executable in the isolated Python virtual environment.
- Executables/installers are currently **unsigned**. Windows SmartScreen may warn; add code signing before wide distribution.
- The updater checks exact GitHub release asset URLs, valid version tags, bounded payload size and SHA-256; it fails closed if metadata or checksums are invalid.
- The SHA-256 checksum comes from the same GitHub Release. It does not protect against a compromised GitHub publisher or malicious release automation.
- Releases are deliberately not overwritten; prefer audited, tagged releases from reviewed changes.
- Installer runs as the current Windows user; no administrator rights or system settings are required.
- A strict CSP prevents network requests from the calculator HTML/JavaScript. The Python desktop updater bridge is deliberately limited to check/install methods without caller-supplied URLs or commands.

For vulnerabilities, contact the maintainer privately via GitHub where available; avoid posting exploit details in public.
