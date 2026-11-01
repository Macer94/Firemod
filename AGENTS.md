# Instructions for coding agents

These instructions apply to this repository. Respect the user's task and existing authorization; do not introduce a new approval round for work already authorized. Consult [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md) when operating a Fire TV and [docs/USER_GUIDE.it.md](docs/USER_GUIDE.it.md) for the actual GUI workflow.

## Project and scope

Firemod is an AGPL-3.0-or-later Python/PySide6 desktop app for Android-based Amazon Fire TV devices. Current version: 0.1.0. Official desktop packages target x86_64 Linux and Windows. CI uses Python 3.12, Ubuntu 22.04 and Windows Server 2022. The GUI and primary user documentation are Italian; preserve actual UI labels when documenting actions.

Home integration and acceleration are restricted to API 22. Newer Fire OS app/settings support is best effort and firmware-dependent. Do not broaden compatibility claims based only on desktop tests or a demo screenshot. Vega OS is unsupported.

## Repository map

| Path | Responsibility |
| --- | --- |
| `src/firemod/adb.py` | ADB discovery, explicit target, argument validation, device shell quoting, state read-back |
| `src/firemod/engine.py` | Device validation, plans, journals, app/settings operations, Home install/bridge, restore |
| `src/firemod/catalog.py` | Labels, small optional-system list, protected packages |
| `src/firemod/gui.py` | UI, plan review, worker tasks and result presentation |
| `src/firemod/models.py` | `DeviceInfo`, `Package`, `Plan`, `Outcome` |
| `src/firemod/app.py` | Real CLI: GUI, `--demo`, `--screenshot`, read-only `--diagnose` |
| `src/firemod/paths.py`, `downloads.py` | Resources/private data and explicit official ADB download |
| `android/helper`, `android/bridge` | API-22 companion source and fixed-action shell bridge |
| `resources/android` | Versioned APK/JAR assets and checksum/source manifest |
| `resources/licenses`, `THIRD_PARTY_NOTICES.md` | Upstream notices and license texts |
| `tests` | Offline behavior, refusal/undo, assets, input/download and GUI-thread checks |
| `scripts`, `.github/workflows/build.yml` | Android/desktop builds and native CI/release packaging |

Generated `build/`, `dist/`, `artifacts/` and local virtualenvs are ignored. Never treat their contents as user-authored source or publish private logs found there. Check `git status` before changing files; preserve unrelated user work.

## Setup and checks

Use the explicit virtualenv commands in [README.md](README.md#dal-sorgente); install locked requirements, then install the project editable with `--no-build-isolation --no-deps`. Do not casually regenerate the lock file or upgrade Qt for an unrelated change.

From that environment:

```text
python -m pytest -q
python -m ruff check src tests scripts
python -m firemod.app --help
```

For a headless GUI screenshot on Linux:

```bash
QT_QPA_PLATFORM=offscreen python -m firemod.app --screenshot build/preview.png
```

Use the PowerShell variant in the agent guide on Windows. At the first release the suite contains 33 tests; do not hard-code this as a permanent test count. Tests use simulated devices and demo data; passing them is not hardware certification.

Run checks appropriate to the change. Add meaningful regression tests for device targeting, parsing, mutation verification, restore, downloads or asynchronous GUI behavior. Do not add implementation-mirroring tests for minor prose or presentation changes. For docs, verify local links, commands, CLI options and consistency with code. After changes pass, do not repeat unrelated checks without a new reason.

## Device operations

- Work from the user's requested scope and a verified device identity. Do not mutate a connected Fire TV merely to test a documentation or UI change. Authorized hardware tests should state what changed and preserve an undo path.
- A target-specific ADB command must select the serial explicitly. Keep host subprocesses as argument arrays without `shell=True`; Android shell arguments still need quoting because `adb shell` reparses them.
- Validate package identifiers and IP literals. The Android framework identifier `android` is intentionally valid and always protected. Do not add arbitrary hostnames, command strings or network listeners to the bridge.
- `Engine.require_fire_tv()` guards writes by manufacturer/model and API. Do not bypass it, the protected catalog or the API-22 Home restriction to make an operation appear successful.
- Preserve `ALWAYS_KEEP` and protect unknown system packages. Expanding `OPTIONAL_SYSTEM` requires model/firmware evidence, functional consequences and a tested restoration path.
- No automatic flashing, factory resets, bulk uninstall, root escalation, disabling essential components or uploading device data is part of the existing feature set.

## Mutation and restoration invariants

- Record the previous value/state in the journal **before** a registered mutation. Keep JSON replacement atomic and private. Do not claim this is a full image backup or a filesystem power-loss guarantee.
- Verify settings and package state after a command; stdout containing a positive word is insufficient. Preserve the distinction between completed, skipped/refused and failed operations.
- Plans can partially succeed. Preserve interrupted/pending records and report failures; do not silently delete history or claim all-or-nothing rollback.
- Restore absent settings by deleting their keys, preserve app data, and retain original APK backups before companion upgrades. Refuse unsafe split-APK replacement.
- Only remove the known companion/Luncher packages when undoing an installation recorded as new. Keep already-present Luncher. Do not alter serial checks to force a restore across device identities.
- Data directories are keyed by the ADB serial, which can be `IP:port`. USB/network/IP changes can separate histories. Do not describe physical-device migration as implemented.
- Qt widgets must be updated on the GUI thread. Preserve busy-state controls and prevent a different device selection from reusing the previous engine.

## Android and Home integration

The companion is `org.firemod.home`; Luncher is `com.luncher.launcher`; the recognized legacy helper is `it.massi.firehome`. Amazon Home stays installed. Home redirection does not change Fire OS's native launcher priority.

The bridge performs one fixed Luncher launch, accepts only numeric request identifiers, has no arbitrary command parser or network socket, and uses a boot-ID marker with acknowledgement/fallback. Preserve the static FileObserver reference, boot checks, normal launch fallback and startup-only automatic-profile handling. The companion has no Internet permission.

The shell accelerator survives PC disconnection but not reboot, power loss or process termination. Do not claim persistent shell privileges or 0.1-second Android boots. Benchmark statements must identify prototype/device/method and distinguish PC/ADB overhead from remote-control latency.

If Android source changes, follow [docs/BUILDING.md](docs/BUILDING.md): rebuild APK/JAR and update `resources/android/manifest.json` using the script. Tests check asset hashes and the source digest. Desktop CI does not rebuild Android. Keep signing keys outside the repository, preserve the release signing identity and upstream license notices. Do not regenerate a release key to get past a signature mismatch.

## Documentation, privacy and delivery

Keep README, user/agent guides and compatibility claims consistent with the implementation. There is no CLI apply/restore command or JSON plan importer in 0.1.0; Python engine methods are internal APIs. Retain links to official Amazon/Android instructions when relevant.

Do not commit device serials, personal IPs, boot IDs, full dumps, snapshots, backup APKs, ADB keys, keystores, passwords or GitHub tokens. Review the diff before committing. Demo screenshots and synthetic identifiers are suitable for documentation. The hashed history directory does not anonymize the serial inside the JSON.

Preserve AGPL and third-party notices and replaceable Qt libraries. New guides belong in `docs/`; include the root agent instructions in source distributions and bundle user documentation through the desktop build script when changing packaging.

For release work, follow the build guide. Native tests and packaged-GUI checks on both operating systems precede publishing the draft. Never move a published tag or silently replace existing release binaries for a documentation-only update. Publish/push when the user has authorized that scope; an existing authorization does not need to be requested again.

In the final report state the concrete result, relevant checks, any unverified hardware scope and the files/repository/release involved. Avoid credentials and private device identifiers in the report.
