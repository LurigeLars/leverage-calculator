"""No-network updater security and version tests."""
import hashlib
import io
import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from desktop import updater


def release(version="1.2.0", data=b"fake test installer"):
    tag = "v" + version
    size = len(data)
    base = f"https://github.com/{updater.REPOSITORY}/releases/download/{tag}/"
    return {
        "tag_name": tag,
        "draft": False,
        "prerelease": False,
        "assets": [
            {"name": updater.SETUP_NAME, "size": size, "browser_download_url": base + updater.SETUP_NAME,
             "digest": "sha256:" + hashlib.sha256(data).hexdigest()},
            {"name": updater.CHECKSUM_NAME, "size": 110, "browser_download_url": base + updater.CHECKSUM_NAME},
        ],
    }


class UpdateTests(unittest.TestCase):
    def test_versions(self):
        self.assertTrue(updater.parse_version("v1.10.0") > updater.parse_version("1.9.99"))
        for text in ("1.0", "v1.2.3rc1", "../v2.0.0", "v1.0.0/evil", "v1.2.3\n"):
            with self.assertRaises(updater.UpdateError):
                updater.parse_version(text)

    def test_latest_release_metadata(self):
        with patch.object(updater, "_read_url", return_value=json.dumps(release()).encode()):
            latest = updater.latest_release("1.1.0")
            self.assertTrue(latest["available"])
            self.assertEqual(latest["version"], "1.2.0")

    def test_rejects_downgrade(self):
        with patch.object(updater, "_read_url", return_value=json.dumps(release()).encode()):
            self.assertFalse(updater.latest_release("1.2.0")["available"])
            self.assertFalse(updater.latest_release("1.3.0")["available"])

    def test_rejects_untrusted_asset_url(self):
        wrong = release()
        wrong["assets"][0]["browser_download_url"] = "https://untrusted.example/setup.exe"
        with patch.object(updater, "_read_url", return_value=json.dumps(wrong).encode()):
            with self.assertRaises(updater.UpdateError):
                updater.latest_release("1.1.0")

    def test_rejects_prerelease_and_oversized_file(self):
        bad = release()
        bad["prerelease"] = True
        with patch.object(updater, "_read_url", return_value=json.dumps(bad).encode()):
            with self.assertRaises(updater.UpdateError):
                updater.latest_release("1.1.0")
        bad = release()
        bad["assets"][0]["size"] = updater.MAX_INSTALLER_BYTES + 1
        with patch.object(updater, "_read_url", return_value=json.dumps(bad).encode()):
            with self.assertRaises(updater.UpdateError):
                updater.latest_release("1.1.0")

    def test_checksum_rejected_if_malformed(self):
        for item in (b"invalid", b"0" * 64 + b" *LeverageCalculator-Setup.exe\n", b"", b"0" * 64 + b"  other.exe"):
            with self.assertRaises(updater.UpdateError):
                updater._parse_checksum(item)

    def test_installer_passes_hash_check(self):
        payload = b"fake test installer"
        metadata = release(data=payload)
        expected = hashlib.sha256(payload).hexdigest()
        with patch.object(updater, "_read_url", return_value=(expected + "  LeverageCalculator-Setup.exe\n").encode()), \
             patch.object(updater.urllib.request, "urlopen", return_value=io.BytesIO(payload)):
            installer = updater.download_verified_installer({
                "_tag": metadata["tag_name"],
                "_setup": metadata["assets"][0],
                "_checksum": metadata["assets"][1],
            })
        try:
            self.assertEqual(installer.read_bytes(), payload)
        finally:
            shutil.rmtree(installer.parent, ignore_errors=True)

    def test_corrupt_installer_is_rejected(self):
        payload = b"corrupted"
        metadata = release(data=payload)
        expected = hashlib.sha256(payload).hexdigest()
        with patch.object(updater, "_read_url", return_value=(expected + "  LeverageCalculator-Setup.exe\n").encode()), \
             patch.object(updater.urllib.request, "urlopen", return_value=io.BytesIO(b"bad bytes")):
            with self.assertRaises(updater.UpdateError):
                updater.download_verified_installer({
                    "_tag": metadata["tag_name"],
                    "_setup": metadata["assets"][0],
                    "_checksum": metadata["assets"][1],
                })

    def test_installation_disabled_outside_packaged_windows(self):
        outcome = updater.DesktopUpdater("1.1.0").install_update()
        self.assertFalse(outcome["ok"])

    def test_staging_does_not_start_installer_while_app_is_open(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            installer = Path(directory) / updater.SETUP_NAME
            installer.write_bytes(b"verified installer placeholder")
            with patch.object(updater.sys, "platform", "win32"), \
                 patch.object(updater.sys, "frozen", True, create=True), \
                 patch.object(updater, "latest_release", return_value={"available": True}), \
                 patch.object(updater, "download_verified_installer", return_value=installer), \
                 patch.object(updater.subprocess, "Popen") as spawn:
                desktop = updater.DesktopUpdater("1.1.2")
                result = desktop.install_update()
                self.assertTrue(result["ok"])
                spawn.assert_not_called()
                self.assertEqual(desktop._pending_installer, installer)

                launched = desktop.launch_after_window_closed()
                self.assertTrue(launched)
                spawn.assert_called_once()
                args = spawn.call_args.args[0]
                self.assertEqual(args[0], str(installer))
                self.assertEqual(args[1], "/UPGRADEPID=" + str(updater.os.getpid()))
                self.assertIn("/NORESTARTAPPLICATIONS", args)
                self.assertFalse(spawn.call_args.kwargs["shell"])
                self.assertIsNone(desktop._pending_installer)

    def test_close_for_update_only_when_installer_staged(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import Mock
        desktop = updater.DesktopUpdater("1.1.2")
        window = SimpleNamespace(destroy=Mock())
        with patch.dict(sys.modules, {"webview": SimpleNamespace(windows=[window])}):
            self.assertFalse(desktop.close_for_update()["ok"])
            window.destroy.assert_not_called()
            desktop._pending_installer = Path("verified-placeholder")
            self.assertTrue(desktop.close_for_update()["ok"])
            window.destroy.assert_called_once()

    def test_no_installer_launch_when_not_staged(self):
        with patch.object(updater.subprocess, "Popen") as spawn:
            self.assertFalse(updater.DesktopUpdater("1.1.2").launch_after_window_closed())
            spawn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
