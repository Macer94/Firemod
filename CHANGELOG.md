# Changelog

## Unreleased

- Expanded Italian/English README and a step-by-step Italian user manual.
- Added root `AGENTS.md` and an operational agent guide documenting real CLI/API behavior, device targeting, settings, journals and restore limits.
- Clarified app-selection semantics, partial outcomes, boot-scoped Home acceleration and ADB-serial-based history.
- Included full guides in future desktop bundles and source distributions; added a standalone documentation ZIP builder. Existing 0.1.0 binaries/tags remain unchanged.

## 0.1.0

- First Linux/Windows desktop interface in Italian, with an English user guide.
- USB/Wi-Fi ADB connection and read-only device diagnostics.
- Explicit optional-app deactivation/reactivation with data preservation.
- Animation, privacy and screensaver settings with state verification.
- Offline Luncher integration and a fixed-action Home accelerator for Fire OS 5 / API 22.
- Per-device, write-ahead restore journals and original companion APK backups.
- Bundled Android source, checksums, AGPL licensing and third-party notices.
- Separate native Linux/Windows CI packaging and packaged-GUI smoke tests.

Known limits: Home acceleration must be reactivated after a complete Fire TV reboot. Newer Fire OS versions expose only standard app/settings management until their Home integration is validated. No blanket removal of protected Amazon apps or in-app advertisements.
