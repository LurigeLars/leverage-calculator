"""Opt-in Windows installer updates from the project's public GitHub Releases.

Only the Python desktop wrapper accesses the network. The browser HTML keeps its
connect-src 'none' CSP and never receives a download URL or arbitrary command.
No credentials, local trade data, or telemetry are transmitted.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

REPOSITORY = "LurigeLars/leverage-calculator"
API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
SETUP_NAME = "LeverageCalculator-Setup.exe"
CHECKSUM_NAME = "SHA256SUMS.txt"
MAX_INSTALLER_BYTES = 160 * 1024 * 1024
MAX_METADATA_BYTES = 256 * 1024
MAX_CHECKSUM_BYTES = 16 * 1024
VERSION_PATTERN = re.compile(r"^v?([0-9]+)\.([0-9]+)\.([0-9]+)$")


class UpdateError(Exception):
    """An update could not be verified or installed safely."""


def parse_version(value: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise UpdateError("Invalid stable release version")
    return tuple(map(int, match.groups()))


def _read_url(url: str, limit: int) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json" if url == API_URL else "application/octet-stream",
            "User-Agent": "LeverageCalculator-Updater",
        },
    )
    with urllib.request.urlopen(req, timeout=12) as response:
        payload = response.read(limit + 1)
        if len(payload) > limit:
            raise UpdateError("Download exceeds allowed size")
        return payload


def _verified_release_url(url: str, tag: str, filename: str) -> str:
    expected = f"https://github.com/{REPOSITORY}/releases/download/{tag}/{filename}"
    if url != expected or urlsplit(url).scheme != "https":
        raise UpdateError("Unexpected release asset URL")
    return url


def _get_asset(release: dict, tag: str, name: str, size_limit: int) -> dict:
    found = [a for a in release.get("assets", []) if isinstance(a, dict) and a.get("name") == name]
    if len(found) != 1:
        raise UpdateError(f"Missing or ambiguous release asset: {name}")
    asset = found[0]
    url = asset.get("browser_download_url")
    _verified_release_url(url, tag, name)
    size = asset.get("size")
    if not isinstance(size, int) or not 0 < size <= size_limit:
        raise UpdateError(f"Invalid release asset size: {name}")
    return asset


def latest_release(current_version: str) -> dict:
    """Fetch and validate upstream release metadata; do not fetch binaries."""
    current = parse_version(current_version)
    try:
        release = json.loads(_read_url(API_URL, MAX_METADATA_BYTES))
    except (ValueError, OSError) as exc:
        raise UpdateError("Could not reach GitHub Releases") from exc

    if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
        raise UpdateError("Latest release is not a stable public release")
    tag = release.get("tag_name")
    candidate = parse_version(tag)
    if not tag.startswith("v"):
        raise UpdateError("Release tag must start with v")
    if candidate <= current:
        return {"available": False, "current_version": current_version}
    setup = _get_asset(release, tag, SETUP_NAME, MAX_INSTALLER_BYTES)
    checksum = _get_asset(release, tag, CHECKSUM_NAME, MAX_CHECKSUM_BYTES)
    return {
        "available": True,
        "current_version": current_version,
        "version": tag.removeprefix("v"),
        "_tag": tag,
        "_setup": setup,
        "_checksum": checksum,
    }


def _parse_checksum(content: bytes) -> str:
    try:
        lines = content.decode("ascii").splitlines()
    except UnicodeError as exc:
        raise UpdateError("Invalid checksum encoding") from exc
    expected = [re.fullmatch(r"([a-fA-F0-9]{64})  LeverageCalculator-Setup\.exe", x) for x in lines]
    if len(expected) != 1 or expected[0] is None:
        raise UpdateError("Missing or ambiguous installer checksum")
    return expected[0].group(1).lower()


def download_verified_installer(release: dict) -> Path:
    tag = release["_tag"]
    checksum_asset = release["_checksum"]
    setup_asset = release["_setup"]
    expected = _parse_checksum(_read_url(
        _verified_release_url(checksum_asset["browser_download_url"], tag, CHECKSUM_NAME),
        MAX_CHECKSUM_BYTES,
    ))
    # GitHub reports an independent digest in the asset metadata on supported API versions.
    api_digest = setup_asset.get("digest")
    if api_digest is not None and api_digest != "sha256:" + expected:
        raise UpdateError("Release asset digest disagrees with checksum")

    staging = Path(tempfile.mkdtemp(prefix="LeverageCalculator-update-"))
    installer = staging / SETUP_NAME
    h = hashlib.sha256()
    total = 0
    try:
        url = _verified_release_url(setup_asset["browser_download_url"], tag, SETUP_NAME)
        req = urllib.request.Request(url, headers={"User-Agent": "LeverageCalculator-Updater"})
        with urllib.request.urlopen(req, timeout=30) as response, installer.open("xb") as handle:
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_INSTALLER_BYTES:
                    raise UpdateError("Installer too large")
                h.update(chunk)
                handle.write(chunk)
        if total != setup_asset["size"] or h.hexdigest() != expected:
            raise UpdateError("Installer checksum or size mismatch")
        return installer
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


class DesktopUpdater:
    """Narrow API exposed to local, CSP-protected HTML through pywebview."""

    def __init__(self, current_version: str):
        parse_version(current_version)
        self.current_version = current_version
        self._busy = False
        self._pending_installer = None

    def check_for_updates(self) -> dict:
        try:
            release = latest_release(self.current_version)
            return {
                "ok": True,
                "available": release["available"],
                "current_version": self.current_version,
                "version": release.get("version"),
            }
        except Exception:
            # Never expose file paths, user information, or request internals to JS.
            return {"ok": False, "message": "GitHub update check unavailable. Try again later."}

    def install_update(self) -> dict:
        """Stage a verified update, but do not launch Setup while our EXE is running."""
        if self._busy:
            return {"ok": False, "message": "An update is already in progress."}
        if sys.platform != "win32" or not getattr(sys, "frozen", False):
            return {"ok": False, "message": "Install updates from the packaged Windows application."}
        self._busy = True
        try:
            release = latest_release(self.current_version)
            if not release["available"]:
                return {"ok": False, "message": "No newer stable release is available."}
            self._pending_installer = download_verified_installer(release)
            # Installer is launched only after the pywebview event loop closes.
            return {"ok": True, "message": "Update verified. Closing the application before setup."}
        except Exception:
            return {"ok": False, "message": "Update download or verification failed. No changes were installed."}
        finally:
            self._busy = False

    def close_for_update(self) -> dict:
        """Close the app only after a verified update has been staged."""
        if self._pending_installer is None:
            return {"ok": False, "message": "No verified update has been staged."}
        import webview
        # Closing the window ends webview.start(). Setup starts after that,
        # and waits for this process to exit before touching installed files.
        webview.windows[0].destroy()
        return {"ok": True}

    def launch_after_window_closed(self) -> bool:
        """Called by main() once the GUI loop has exited."""
        installer = self._pending_installer
        self._pending_installer = None
        if installer is None:
            return False
        if not installer.is_file():
            return False
        # Pass only our own numeric PID. Inno Setup waits until this very
        # process has exited; never terminate unrelated processes.
        subprocess.Popen(
            [str(installer), "/UPGRADEPID=" + str(os.getpid()), "/NORESTARTAPPLICATIONS"],
            shell=False,
            close_fds=True,
        )
        return True


def bundled_version() -> str:
    root = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
    version = (root / "VERSION").read_text(encoding="ascii").strip()
    parse_version(version)
    return version
