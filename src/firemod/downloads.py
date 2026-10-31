from __future__ import annotations

import hashlib
import io
import sys
import urllib.request
import zipfile

from .paths import data_dir

URLS = {"win32": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
        "linux": "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"}


def download_adb(log=lambda _: None) -> str:
    if sys.platform not in URLS:
        raise RuntimeError("Automatic ADB setup is available for Linux and Windows.")
    url = URLS[sys.platform]
    log("Downloading Android Platform-Tools from dl.google.com…")
    with urllib.request.urlopen(url, timeout=60) as response:
        if not response.url.startswith("https://dl.google.com/"):
            raise RuntimeError("Unexpected download origin.")
        content = response.read(150 * 1024 * 1024 + 1)
    if len(content) > 150 * 1024 * 1024:
        raise RuntimeError("Download exceeds the expected size limit.")
    root = data_dir() / "platform-tools"
    root.mkdir(parents=True, exist_ok=True)
    files = ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll"] if sys.platform == "win32" else ["adb"]
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        # Never extract arbitrary archive paths. Read only known SDK members.
        for filename in files:
            target = root / filename
            target.with_suffix(target.suffix + ".tmp").write_bytes(archive.read("platform-tools/" + filename))
        for filename in files:
            target = root / filename
            target.with_suffix(target.suffix + ".tmp").replace(target)
            target.chmod(0o755)
        if "platform-tools/NOTICE.txt" in archive.namelist():
            (root / "NOTICE.txt").write_bytes(archive.read("platform-tools/NOTICE.txt"))
    log("Official SDK archive SHA-256: " + hashlib.sha256(content).hexdigest())
    return str(root / files[0])
