# Security and privacy

The calculator is deliberately offline, without account connectors, telemetry, trading execution, remote scripts, a backend, or persistent trade storage.

**Do not upload private information** to public issues, screenshots, pull requests or support messages.

- Never commit secrets, account information, local system details, trade exports, or logs.
- Review and update third-party build dependencies before running.
- Build the Windows executable in the isolated Python virtual environment.
- Executables built locally are **unsigned** and should be verified before distribution.
- CSP prevents network requests from the calculator interface.

For vulnerabilities, contact the maintainer privately via GitHub where available; avoid posting exploit details in public.
