# Build and release

[README](../README.md) · [Contributing](../CONTRIBUTING.md) · [Agent instructions](../AGENTS.md) · [User manual](USER_GUIDE.it.md)

These instructions cover the 0.1.0 implementation and the documentation updates on `main`. Build from the release tag to reproduce its source. Locked dependencies define the dependency set; timestamps, signing and build environments mean archives are not promised to be byte-for-byte reproducible.

## Desktop

Use Python 3.12 on x86_64 Linux or Windows. Follow the explicit Linux/PowerShell clone and virtualenv setup in the [README](../README.md#dal-sorgente). All `python` commands below refer to that virtualenv interpreter. ADB, an Android SDK and a connected TV are not required for desktop tests or packaging; ADB is needed when using a real device.

From the repository root and the prepared environment:

```bash
python -m pip install -r requirements-build.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m pytest -q
python -m ruff check src tests scripts
python scripts/build_desktop.py
```

Native executables and replaceable shared libraries are in `dist/Firemod`; release archives and SHA-256 files are in `artifacts/`. Keep the complete directory together. `BUILD-INFO.json` records the Python/platform/libc environment and optional `FIREMOD_BUILD_NOTE`. Builds from the updated `main` also copy README files, `AGENTS.md`, `CONTRIBUTING.md`, license/notices and `docs/` next to the executable so relative documentation links resolve. Frozen resources, APKs and license files are under `_internal/resources`.

| Host Python platform | Executable | Archive |
| --- | --- | --- |
| Linux x86_64 | `dist/Firemod/Firemod` | `artifacts/Firemod-0.1.0-linux-x86_64.tar.gz` |
| Windows x86_64 | `dist/Firemod/Firemod.exe` | `artifacts/Firemod-0.1.0-windows-x86_64.zip` |

The build script uses PyInstaller with `--onedir --windowed --noupx`. It cleans/replaces its generated bundle; do not keep unrelated user files there. There is no installer or code-signing step. Shared Qt libraries stay replaceable instead of being hidden inside a single executable.

PyInstaller targets the OS of its Python interpreter. Build Windows on Windows, or under a Windows Python interpreter in a suitable Wine environment. Linux Python cannot produce a Windows executable by renaming its output. Public CI uses separate Ubuntu 22.04 and Windows Server 2022 jobs and smoke-tests each packaged GUI.

Build Linux on the oldest distribution you intend to support. Newer hosts can collect libraries requiring newer glibc. Official Linux builds target Ubuntu 22.04 or newer; the Qt wheel's own glibc floor is not the only requirement once host libraries have been collected. The CI package list is authoritative in `.github/workflows/build.yml`; `scripts/Containerfile.linux` documents the local Ubuntu 22.04 builder. Do not upgrade Qt/requirements as a side effect of a documentation change.

Smoke-test the source and generated program:

```bash
QT_QPA_PLATFORM=offscreen python -m firemod.app --screenshot build/source-preview.png
QT_QPA_PLATFORM=offscreen ./dist/Firemod/Firemod --screenshot build/binary-preview.png
```

On Windows PowerShell:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
python -m firemod.app --screenshot build/source-preview.png
$process = Start-Process -FilePath '.\dist\Firemod\Firemod.exe' -ArgumentList '--screenshot', 'build/binary-preview.png' -PassThru -Wait
if ($process.ExitCode -ne 0 -or !(Test-Path 'build/binary-preview.png')) { throw 'Packaged GUI check failed' }
Remove-Item Env:QT_QPA_PLATFORM
```

Use a fresh output path/remove an old preview when diagnosing screenshot failures. These commands exercise demo data only and do not connect to a TV. Test actual device behavior separately when it is part of the authorized task. In 0.1.0 CLI JSON diagnostics should be run through the source Python entry point on Windows, because the frozen executable has no console.

## Android

Corresponding source is under `android/helper` and `android/bridge`. Versioned APK/JAR files under `resources/android` have SHA-256 checksums plus an Android-source digest in `manifest.json`; tests and installation verify these assets.

Rebuild with JDK 17+ and Android SDK platform 36 / build-tools 36.0.0:

```bash
export JAVA_HOME=/path/to/jdk
export ANDROID_HOME=/path/to/android-sdk
python scripts/build_android.py
```

The script is intended for Linux. `ANDROID_SDK_ROOT` is accepted when `ANDROID_HOME` is absent. `FIREMOD_BUILD_API` and `FIREMOD_BUILD_TOOLS` can override the installed compile platform/tools; this does not remove the runtime API-22 restriction. The script compiles Java with `--release 8`, uses D8, aligns and signs the helper APK, builds the bridge DEX JAR and rewrites the asset manifest. Intermediate files are in ignored `android/build/`. No Fire TV is needed for compilation.

Desktop CI uses the checked-in, verified Android artifacts and does not need the SDK or private signing key. Tests verify SHA-256 of APK/JAR assets, presence of `classes.dex`, the companion namespace/no-Internet declaration and the Android-source digest. `.gitattributes` keeps source line endings consistent. If Android source changes, rebuild assets and commit the matching manifest with the source; do not just edit a hash to suppress a failure.

The release signing key is outside Git at `~/.local/share/firemod-signing/release.keystore`. Override `FIREMOD_KEYSTORE` and `FIREMOD_KEYSTORE_PASSWORD`; the script uses alias `firemod`. If no key exists it generates one for that path. The default local-build password is not a production secret: maintainers should set a private password and retain the key securely. Never commit signing keys, their passwords or ADB authorization keys. Losing/changing the key prevents updating APKs signed by the previous key. A contributor's newly signed APK is not interchangeable with the existing release signing identity.

The companion targets API 22. The bridge is a Java main class started with `app_process`, not an APK. Luncher 0.4.0 is the unmodified upstream signed APK; its versioned source URL is in the asset manifest.

## Release workflow

The GitHub workflow runs tests and packaging on pull requests, main pushes, version tags and manual dispatch. Actions are pinned to immutable commits. Normal main/PR/manual builds upload CI artifacts; only a `v*` tag schedules the release job. The job needs both native OS builds to succeed. Artifact retention is 14 days, separate from permanent published release assets.

For a **new application release** within the authorized maintainer task:

1. Set consistent version metadata: Python package, `__version__`, Android version/manifest generation if applicable, README archive names and changelog. Rebuild/re-sign Android only when required, preserving the signing identity.
2. Run relevant checks and review the source/private-data diff. Commit the intended source and push it to `main`.
3. Create a new annotated version tag matching that source; never reuse/move a public tag. For example, **only after updating the source to 0.1.1**:

```bash
git tag -a v0.1.1 -m 'Firemod 0.1.1'
git push origin v0.1.1
```

4. Monitor the native Ubuntu 22.04 and Windows Server 2022 jobs: locked install, lint, tests, source GUI, packaging and packaged-GUI checks. Do not publish a Wine-only build as native Windows validation.
5. The tag workflow creates a **draft release** containing Linux/Windows archives, `firemod-home.apk`, `firemod-bridge.jar`, and `SHA256SUMS`. Download the completed files and check hashes before publishing. Write release notes with compatibility, Home reboot limitation and any unverified hardware scope.
6. Publish the reviewed draft when publication is within the task's existing authorization. GitHub generates source-code archives for the tag, including Android source/build scripts. Secrets used to authenticate GitHub or sign Android stay outside the distributed source.

For CLI maintenance, `gh run list --repo Macer94/Firemod`, `gh run view RUN_ID --repo Macer94/Firemod` and `gh release view TAG --repo Macer94/Firemod` inspect status. Replace `RUN_ID`/`TAG` deliberately; run `gh auth login` only when authentication is actually absent. Never put a token in documentation or a PR body.

## Documentation-only updates

Update `main` and validate links, instructions and packaging as appropriate. Do not move `v0.1.0` or silently replace the existing release executables: their sources and checksums must continue to match the original tag.

The standalone `Firemod-0.1.0-documentation.zip` release attachment contains the expanded README, human/agent guides and notices with its own SHA-256 file. It is a documentation update, not a new executable version; the original 0.1.0 binaries may contain the shorter initial README. Future builds from `main` include the complete guide directory. To read the standalone manual, extract the ZIP and open `Firemod-documentation/README.md` in a Markdown viewer, or use the linked GitHub pages. Windows/Linux do not necessarily associate `.md` with a rich viewer.

To create that archive from the prepared source environment:

```text
python scripts/build_docs.py
```

The script packages public root guides, `docs/*.md`, the demo screenshot/benchmark and license texts, under a `Firemod-documentation/` prefix. It writes the documentation ZIP and a separate `.sha256` under `artifacts/`; it does not rebuild or modify the executable archives or their existing `SHA256SUMS`. After checking the contents/hash, upload these two documentation files to the intended release when this is part of the authorized task. Include a documentation revision link in the release notes; the application tag remains unchanged.
