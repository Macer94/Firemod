# Contributing

Run the README checks. Device commands, filtering, journaling, restore and download changes need meaningful tests. Keep undo records durable before mutations. Treat package names, device IDs, addresses and archive paths as untrusted; never use a host shell for ADB.

Report firmware refusals accurately. A setting read-back verifies storage, not every service's behavior. Do not add automatic flashing, resets, arbitrary shell execution or data uploads. Expanding device support or the optional-system-app list requires model/firmware evidence and a tested restoration path.

Do not upload restore histories, full package dumps, credentials, ADB keys, signing keys, or account identifiers. Use sanitized reports/demo screenshots. Contributions to original Firemod code are AGPL-3.0-or-later; preserve upstream notices.
