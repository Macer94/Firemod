# Firemod

**A lighter Fire TV, with a way back.**

Firemod is an open-source Linux/Windows desktop application. Connect an Android-based Amazon Fire TV over ADB, choose which optional apps to keep active, apply responsiveness and privacy settings, and restore the original values from a local per-device journal.

![Firemod interface with demo data](docs/firemod-preview.png)

[Downloads](https://github.com/Macer94/Firemod/releases/latest) · [Italian README](README.md) · [User manual (Italian)](docs/USER_GUIDE.it.md) · [Agent operations guide (Italian)](docs/AGENT_GUIDE.md) · [Coding agent instructions](AGENTS.md) · [Compatibility](docs/COMPATIBILITY.md) · [Build instructions](docs/BUILDING.md)

This documentation describes 0.1.0. Clarifications on `main` can be newer than the release binaries; the exact release source remains at [tag v0.1.0](https://github.com/Macer94/Firemod/tree/v0.1.0). The first release passed 33 tests and source/packaged GUI smoke checks on native Ubuntu 22.04 and Windows Server 2022. These are desktop checks, not certification of every Fire TV firmware.

## Features

- Deactivate/reactivate optional apps while keeping their data and logins; no bulk uninstaller.
- Reduce or remove animations, limit supported usage metrics/ad tracking, optionally disable the photographic screensaver.
- On **Fire OS 5 / API 22**, install offline Luncher plus Firemod Home.
- Start a fixed-action Home accelerator for the current device boot.
- Write the undo record before changing anything and verify the actual state afterward.

Amazon Home and essential components are kept. Firmware refusals are reported, not counted as success. This does not root/flash/reset devices, remove advertisements inside streaming apps, or free the APK storage of hidden apps.

## Download and connect

Use the Linux `.tar.gz` or Windows `.zip` package from Releases. Extract the entire folder; keep the executable and `_internal` directory together. Run `Firemod/Firemod` on Linux or `Firemod/Firemod.exe` on Windows. Python is not required. Packages are unsigned; the UI is currently Italian. Linux CI builds use Ubuntu 22.04; local builds inherit their build-machine compatibility limits.

Official packages are x86_64; there are no ARM, macOS or Vega OS packages. Download `SHA256SUMS` from the same release and compare the archive's complete SHA-256 hash using `sha256sum FILE` on Linux or `Get-FileHash FILE -Algorithm SHA256` in PowerShell. A checksum is not a digital signature. The APK/JAR assets are already inside the desktop packages; manual installation is normally unnecessary.

`Firemod-0.1.0-documentation.zip` and its separate `.sha256` file contain the expanded guides. Extract and open `Firemod-documentation/README.md` with a Markdown viewer, or read them on GitHub. The original 0.1.0 binaries retain their initial README; this attachment updates documentation only. Future builds from `main` include the complete `docs/` directory next to the executable.

1. Enable ADB debugging in Fire TV Developer Options and authorize your PC on the TV. If Developer Options is hidden, press the device name seven times in About.
2. Connect by a supported USB data cable, or enter the Fire TV IP on the same network (normally port 5555).
3. Firemod finds `adb` in PATH/Android SDK, lets you choose it, or downloads official Google Platform-Tools after displaying a reference to Google's SDK terms and receiving confirmation.
4. Click **Rileva**, select the device, then **Apri dispositivo**.
5. Choose apps and options; **Prepara il profilo consigliato** only prepares a selection. **Rivedi le modifiche** shows the concrete plan before applying it.

The app checkbox means **perform an action**, not keep this app: selecting an active app proposes deactivation; selecting an inactive app proposes reactivation. Search filters can hide selected rows. The recommended profile sets animations to `0`, privacy and, on API 22, Home/acceleration; it preserves any existing app and screensaver selections. Review the complete plan. Options can stay checked after an operation.

Plans can partially succeed. Read `[OK]`, `[INVARIATO]` (unchanged/skipped/refused) and `[ERRORE]` (error) in the log. A failure does not automatically roll back earlier successful steps. Use the restore point if needed. Wi-Fi input accepts an IP literal, optionally with a port (IPv6 requires `[address]:port`), not a hostname or URL. Firemod does not implement `adb pair`.

References: [Amazon ADB guide](https://developer.amazon.com/docs/fire-tv/connecting-adb-to-device.html), [official Platform-Tools](https://developer.android.com/tools/releases/platform-tools).

## Home acceleration

The original single-device AFTT / Fire OS 5.2.9.5 prototype measured approximately **6–7 seconds to 1.3–1.6 seconds** for Home transitions. Those PC-triggered measurements include ADB input overhead and are not frame-accurate remote-control or cold-boot benchmarks. See [benchmark data](docs/benchmark.json).

The accelerator starts as an ADB shell process, accepts a numeric request in the companion's external app directory, and performs one fixed action: bring Luncher forward through the system activity service. It has no arbitrary command parser or network listener. The companion has no Internet permission.

**The accelerator survives closing Firemod and disconnecting the PC, but not a full reboot or power loss.** Reconnect and select only the accelerator option to re-enable it. The normal Home companion starts automatically and remains the fallback. Sleep is not a reboot; firmware and remote behavior may affect wake-up. This does not make Android boot in 0.1 seconds.

## Restore and privacy

Use **Ripristino** to restore a point for the selected device. Previous values and package states are restored; absent settings keys are removed. Only companions newly installed by that operation are uninstalled. Existing Luncher installations are kept; original companion APKs are backed up before upgrades. Split APK replacement is refused.

History lives in `${XDG_DATA_HOME:-~/.local/share}/Firemod` on Linux or `%LOCALAPPDATA%/Firemod` on Windows. Keep it for restoration. It contains device identifiers and original settings, stays outside the repository, and is never uploaded by Firemod. Do not attach it to public bug reports. Restoration is not a full disk-image backup.

History is keyed by the **ADB serial**; for network connections this is normally `IP:port`. Changing IP/port or switching USB/Wi-Fi can show a separate history for the same physical TV. Automatic history migration is not implemented. Use the original identifier and retain the complete data directory, including APK backups. Restore multiple operations from newest point to oldest; restoring an old value may overwrite later changes to that value. The on-screen log is session text, while journals retain operation summaries. The directory hash does not anonymize the serial inside `snapshot.json`.

## Source

Use Python 3.12 to reproduce CI (the declared minimum is 3.12). Clone this repository and run from its root. The complete Linux and PowerShell setup commands are in the [Italian README](README.md#dal-sorgente); explicit virtualenv interpreter paths avoid shell activation requirements.

```bash
python -m venv .venv
# Activate .venv for your operating system.
python -m pip install -r requirements-build.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m firemod.app
```

Read-only preview: `python -m firemod.app --demo`.

Checks: `python -m pytest -q` and `ruff check src tests scripts`.

The real CLI supports GUI startup, `--demo`, `--screenshot PATH`, `--diagnose ADB_SERIAL` and `--help`. There is no apply/restore CLI or JSON plan importer. Diagnostic JSON includes private identifiers; do not post it unredacted. On Windows, use the Python source command for reliable console output because the packaged GUI executable is windowed.

For contributions, read [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md). Report issues with tool version, desktop OS, model/Fire OS, reproduction steps and sanitized error messages. Do not upload device dumps, history, APK backups, credentials or keys.

## License

Original Firemod code: **AGPL-3.0-or-later**, see [LICENSE](LICENSE). Third-party components keep their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Firemod is independent of Amazon and Google.
