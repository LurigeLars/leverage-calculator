"""Offline Windows desktop wrapper for Leverage Calculator.

All CSS and JavaScript are inlined from bundled local assets.
No browser navigation, HTTP server, network, or data persistence.
"""
from __future__ import annotations

import base64
import hashlib
import re
import sys
from pathlib import Path


def assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "web"
    return Path(__file__).resolve().parent.parent / "web"


def script_hash(content: str) -> str:
    raw_digest = hashlib.sha256(content.encode("utf-8")).digest()
    return "'sha256-" + base64.b64encode(raw_digest).decode("ascii") + "'"


def build_offline_html() -> str:
    """Assemble self-contained HTML with a strict CSP and local assets only."""
    assets = assets_dir()
    html = (assets / "index.html").read_text(encoding="utf-8")
    css = (assets / "styles.css").read_text(encoding="utf-8")
    scripts = [(assets / name).read_text(encoding="utf-8") for name in ("calculator.js", "app.js")]

    csp = (
        "default-src 'none'; "
        "script-src " + " ".join(script_hash(code) for code in scripts) + "; "
        "style-src " + script_hash(css) + "; "
        "img-src data:; connect-src 'none'; object-src 'none'; "
        "base-uri 'none'; form-action 'none'"
    )
    html, num_meta = re.subn(
        r'<meta http-equiv="Content-Security-Policy"[^>]*>',
        '<meta http-equiv="Content-Security-Policy" content="' + csp + '">',
        html,
        count=1,
    )
    if num_meta != 1:
        raise RuntimeError("Content Security Policy meta tag is missing")
    html = html.replace('<link rel="stylesheet" href="styles.css">', '<style>' + css + '</style>')
    for name in ("calculator.js", "app.js"):
        tag = '<script defer src="' + name + '"></script>'
        if tag not in html:
            raise RuntimeError("Expected offline asset missing: " + name)
        html = html.replace(tag, '')
    html = html.replace('</body>', ''.join('<script>' + code + '</script>' for code in scripts) + '</body>')
    return html


def main() -> None:
    import webview

    webview.create_window(
        "Leverage Calculator",
        html=build_offline_html(),
        width=1000,
        height=900,
        min_size=(700, 640),
        background_color="#050505",
        resizable=True,
    )
    webview.start(gui="edgechromium", debug=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        import ctypes
        msg = (
            f"The application could not start:\n\n{exc}\n\n"
            "Windows 11 usually includes WebView2. "
            "Install the WebView2 Runtime if needed."
        )
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(None, msg, "Leverage Calculator", 0x10)
        else:
            print(msg, file=sys.stderr)
        raise SystemExit(1)
