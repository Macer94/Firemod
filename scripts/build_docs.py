#!/usr/bin/env python3
"""Package the public guides separately without replacing application release binaries."""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from firemod import __version__

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = [ROOT / name for name in (
        "README.md", "README.en.md", "AGENTS.md", "CONTRIBUTING.md", "LICENSE",
        "THIRD_PARTY_NOTICES.md", "docs/firemod-preview.png", "docs/benchmark.json",
    )]
    files.extend((ROOT / "docs").glob("*.md"))
    files.extend((ROOT / "resources/licenses").glob("*.txt"))
    output = ROOT / "artifacts"
    output.mkdir(exist_ok=True)
    archive = output / f"Firemod-{__version__}-documentation.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path in sorted(set(files)):
            relative = path.relative_to(ROOT)
            package.write(path, "Firemod-documentation/" + relative.as_posix())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name + ".sha256").write_text(
        f"{digest}  {archive.name}\n", encoding="utf-8")
    print("Documentation archive:", archive)
    print("SHA-256:", digest)


if __name__ == "__main__":
    main()
