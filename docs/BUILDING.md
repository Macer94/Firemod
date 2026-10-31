# Build and release

## Desktop

Use Python 3.12 on x86_64 Linux or Windows:

```bash
python -m venv .venv
# Activate the environment for your OS.
python -m pip install -r requirements-build.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m pytest -q
ruff check src tests scripts
python scripts/build_desktop.py
```

Native executables and replaceable shared libraries are in `dist/Firemod`; release archives and SHA-256 files are in `artifacts/`. Keep the complete directory together.

PyInstaller targets the OS of its Python interpreter. Build Windows on Windows, or under a Windows Python interpreter in a suitable Wine environment. Linux Python cannot produce a Windows executable by renaming its output. Public CI uses separate Ubuntu 22.04 and Windows Server 2022 jobs and smoke-tests each packaged GUI.

Build Linux on the oldest distribution you intend to support. Newer hosts can collect libraries requiring newer glibc. The pinned PySide6 wheels require the glibc version in the selected Qt wheel (official Linux packages target Ubuntu 22.04 or newer). Debian/Ubuntu desktop dependencies may include `libegl1`, `libopengl0`, `libxcb-cursor0`, and `libxkbcommon-x11-0`.

## Android

Corresponding source is under `android/helper` and `android/bridge`. Versioned APK/JAR files under `resources/android` have SHA-256 checksums plus an Android-source digest in `manifest.json`; tests and installation verify these assets.

Rebuild with JDK 17+ and Android SDK platform 36 / build-tools 36.0.0:

```bash
export JAVA_HOME=/path/to/jdk
export ANDROID_HOME=/path/to/android-sdk
python scripts/build_android.py
```

The script is intended for Linux. Desktop CI uses the checked-in, verified Android artifacts and does not need the SDK or private signing key.

The release signing key is outside Git at `~/.local/share/firemod-signing/release.keystore`. Override `FIREMOD_KEYSTORE` and `FIREMOD_KEYSTORE_PASSWORD`. The default local-build password is not a production secret: maintainers should set a private password and retain the key securely. Never commit signing keys or ADB authorization keys. Losing/changing the key prevents updating APKs signed by the previous key.

The companion targets API 22. The bridge is a Java main class started with `app_process`, not an APK. Luncher 0.4.0 is the unmodified upstream signed APK; its versioned source URL is in the asset manifest.

## Release workflow

The GitHub workflow runs tests and packaging on pull requests, main pushes, and manual dispatch. Actions are pinned to immutable commits. After review:

```bash
git tag v0.1.0
git push origin main --tags
```

A tag builds both operating systems, then creates a **draft release** with Linux/Windows packages, the companion APK/JAR, and SHA256SUMS. Review and publish that draft. GitHub source-code archives correspond to the tag and include Android source and build scripts. No credentials are included in the app or repository.
