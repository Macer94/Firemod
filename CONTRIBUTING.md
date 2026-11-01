# Contributing

Thanks for contributing. Start with the [README](README.md), [coding agent instructions](AGENTS.md), [operational guide](docs/AGENT_GUIDE.md) and [build guide](docs/BUILDING.md). Original Firemod contributions are AGPL-3.0-or-later; preserve upstream licenses and notices.

## Reproduce and change

1. Clone the repository, use Python 3.12 and install the locked dependencies plus the editable project as documented in the README.
2. Reproduce the issue with demo/simulated data where possible. Use a branch and preserve unrelated local work.
3. Keep changes focused; update the user/agent documentation when behavior or compatibility changes.
4. Run relevant tests and lint. Do not use a user's working Fire TV as an automatic side effect of tests.
5. Submit a pull request describing the concrete before/after behavior, validation, firmware scope and any remaining limitation.

```text
python -m pytest -q
python -m ruff check src tests scripts
```

For a Linux headless GUI check:

```bash
QT_QPA_PLATFORM=offscreen python -m firemod.app --screenshot build/preview.png
```

The test suite is offline and uses simulated device behavior. New ADB commands, parsing, targeting, journaling, restoration and download behavior need meaningful regression coverage. Small documentation changes need link/command validation rather than tests that mirror prose. Android source changes also require rebuilding and checking the versioned APK/JAR manifest; desktop CI uses those checked-in assets.

## Preserve device behavior

Keep undo records before registered mutations. Treat package names, device IDs, addresses and archive paths as untrusted; use subprocess argument arrays, an explicit serial and device-side argument quoting. Do not bypass protected packages or call internal mutation helpers to avoid journaling.

Report firmware refusals accurately. A settings read-back verifies storage, not every service's behavior. Plans can partially succeed and restoration must preserve pending/error records. Do not add automatic flashing, resets, arbitrary shell execution or data uploads. Expanding Home support beyond API 22 or the optional-system-app list requires model/firmware evidence, functional impact and a tested restoration path.

## Issues and private data

Report Firemod version/commit, desktop OS and architecture, Fire TV model/Fire OS/API, expected/actual result, minimal reproduction and a sanitized error. Identify whether validation was demo, simulated tests, native desktop CI or physical hardware. A benchmark on one device does not establish compatibility with another.

Do not upload restore histories, full package dumps, APK backups, credentials, ADB keys, signing keys, personal IPs or device/account identifiers. Use demo screenshots and synthetic identifiers. Before sharing diagnostics remove serials and boot IDs as well as IP addresses; hashing a directory name is insufficient.

## Distribution and releases

Follow [BUILDING.md](docs/BUILDING.md). Preserve AGPL and third-party notices and separate, replaceable Qt libraries. Do not move a published release tag or silently rebuild its existing binaries for a documentation-only change. Release/publishing actions must be within the maintainer's or user's authorized task; routine authorized work does not need a repeated confirmation.
