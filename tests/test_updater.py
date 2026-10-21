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


if __name__ == "__main__":
    unittest.main()
