#!/usr/bin/env python3
"""Build a native, replaceable-library desktop bundle and a checksummed release archive."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

from firemod import __version__

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform not in ("linux", "win32"):
        raise SystemExit("Release builds currently support Linux and Windows.")
    if platform.machine().lower() not in ("amd64", "x86_64"):
        raise SystemExit("Release builds currently target x86_64 only.")
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir",
                    "--windowed", "--noupx", "--name", "Firemod", "--paths", str(ROOT / "src"),
                    "--specpath", str(ROOT / "build"), "--distpath", str(ROOT / "dist"),
                    "--workpath", str(ROOT / "build" / "pyinstaller"),
                    "--add-data", str(ROOT / "resources") + os.pathsep + "resources",
                    "--add-data", str(ROOT / "LICENSE") + os.pathsep + "resources/licenses",
                    "--add-data", str(ROOT / "THIRD_PARTY_NOTICES.md") + os.pathsep + "resources/licenses",
                    str(ROOT / "run.py")], cwd=ROOT, check=True)
    bundle = ROOT / "dist" / "Firemod"
    build_info = {"version": __version__, "python": sys.version, "platform": platform.platform(),
                  "machine": platform.machine(), "libc": platform.libc_ver(),
                  "cross_build_note": os.environ.get("FIREMOD_BUILD_NOTE", "Native build")}
    (bundle / "BUILD-INFO.json").write_text(json.dumps(build_info, indent=2) + "\n", encoding="utf-8")
    for filename in ("README.md", "README.en.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / filename, bundle / filename)
    system = "windows" if sys.platform == "win32" else "linux"
    name = f"Firemod-{__version__}-{system}-x86_64"
    if sys.platform == "win32":
        archive_path = output / (name + ".zip")
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(bundle.parent))
    else:
        archive_path = output / (name + ".tar.gz")
        with tarfile.open(archive_path, "w:gz", compresslevel=6) as archive:
            archive.add(bundle, arcname="Firemod")
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (output / (archive_path.name + ".sha256")).write_text(f"{digest}  {archive_path.name}\n")
    print("Release archive:", archive_path)
    print("SHA-256:", digest)


if __name__ == "__main__":
    main()
