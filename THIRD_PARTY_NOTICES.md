# Third-party notices

Original Firemod code and original integration changes are AGPL-3.0-or-later. Components below retain their licenses. Shared Qt libraries remain separate and replaceable in directory bundles.

## Firehome-derived companion

- Upstream: https://github.com/whyashthakker/debloat-fire-stick-claude-code
- Source reference: `2d006a3984ffabd432de6eaf199d4eea2dd0f8c5`, directory `firehome/`.
- MIT license and original copyright notice: `resources/licenses/Firehome-MIT.txt`.
- Modified source: `android/helper` and `android/bridge`. Changes include offline Luncher targeting, early connectivity startup, startup-only profile handling, a boot-scoped fixed-action bridge, fallback behavior, namespace and branding.
- The upstream license mentions an Outfit font used elsewhere in that project; Firemod does not distribute that font.

## Luncher 0.4.0

- Source: https://github.com/CVasilakis/luncher/tree/v0.4.0
- Release: https://github.com/CVasilakis/luncher/releases/tag/v0.4.0
- Unmodified upstream APK, checksum in `resources/android/manifest.json`.
- MIT: `resources/licenses/Luncher-MIT.txt`.
- Upstream artwork derives from Android Open Source Project artwork under Apache-2.0; see https://github.com/CVasilakis/luncher/blob/v0.4.0/app/README.md .
- Luncher is a separate Android application and retains its upstream signing identity.

## Qt / PySide6 Essentials / Shiboken6

- Source/notices: https://code.qt.io/cgit/pyside/pyside-setup.git/ and https://code.qt.io/cgit/qt/ .
- Versions are pinned in `requirements-build.txt`.
- Distribution option used here: LGPL-3.0-only for these components; upstream also offers GPL alternatives and commercial licenses.
- License texts are in `resources/licenses`. Qt shared libraries in `_internal` can be replaced by compatible builds. The repository provides Firemod source and build instructions.

## Python

Included under the Python Software Foundation License. Source/license: https://www.python.org/downloads/source/ and https://docs.python.org/3/license.html . Desktop bundles include the Python license and record the interpreter version in `BUILD-INFO.json`.

## PyInstaller

Source: https://github.com/pyinstaller/pyinstaller . GPL with the PyInstaller bootloader distribution exception; see `resources/licenses/PyInstaller-COPYING.txt`. The exception permits distributing bundled applications under their own licenses.

## Android Debug Bridge

Google Platform-Tools are not redistributed inside Firemod release archives. Firemod uses user-provided ADB or downloads official tools from `dl.google.com` after an explicit user action showing the SDK terms. Google's SDK terms and the archive's notices apply. ADB source: https://android.googlesource.com/platform/packages/modules/adb/ .

## Build tools

pytest, Ruff, Hatchling and dependencies are pinned build/test tools, not application features. Their own licenses apply. Runtime support dependencies retain their upstream notices.
