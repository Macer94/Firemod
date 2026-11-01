# Compatibility and limits

[README](../README.md) · [User manual](USER_GUIDE.it.md) · [Agent guide](AGENT_GUIDE.md)

Scope: 0.1.0. Device mutation checks require manufacturer Amazon, model prefix `AFT` and Android API >= 22. Operations address Android user 0; the desktop tool has no Android multiuser selector. Native desktop CI success verifies the desktop program, not each firmware below.

| Software | App management / settings | Home companion / accelerator |
| --- | --- | --- |
| Fire OS 5 / Android 5.1 / API 22 | Original work verified on AFTT/tank, 5.2.9.5 | Supported; original algorithm tested on that device |
| Fire OS 6 / Android 7.1 | Standard ADB operations implemented; hardware validation pending | Not enabled in 0.1.0 |
| Fire OS 7 / Android 9 | Standard ADB operations implemented; firmware may refuse | Not enabled in 0.1.0 |
| Fire OS 8 / Android 11 | Standard ADB operations implemented; firmware may refuse | Not enabled in 0.1.0 |
| Newer Android Fire TV | Best-effort inspection/settings, no compatibility guarantee | Not enabled in 0.1.0 |
| Vega OS / non-Android | Unsupported | Unsupported |
| Phones, tablets, other Android TV brands | May appear in ADB; mutations rejected by manufacturer/model check | Unsupported |

## Home

Amazon Home stays installed and remains Fire OS's native Home target. The companion reads activity-start logs and redirects to Luncher. Native Settings navigation issued by Amazon Home is left alone. Automatic profile pickers are redirected only during the first two minutes after boot; later manual profile changes remain available.

The accelerator is a separate shell process using FileObserver and the companion's external directory. It accepts a numeric request and performs only `startActivityAsUser` for `com.luncher.launcher/.home.HomeActivity`. It opens no network socket and parses no arbitrary shell commands. Another app with directory access could request the same Home action, not arbitrary commands.

The ready marker contains the kernel boot ID: markers from earlier boots never activate the fast path. A failed acknowledgement removes the marker and falls back to ordinary launching. The process survives ADB session disconnection, but not reboot, power loss, or an OS process kill. Re-enable it if it stops.

## Privacy

A settings read-back verifies the saved value, not that every firmware/service honors the key. Values were checked in the native UI during the original AFTT work. Firemod is not a VPN, DNS filter, firewall, or streaming ad blocker. Video/audio previews can also be disabled manually in native Fire TV Preferences; Firemod does not claim an unsupported settings key disables them.

## Preservation

App management uses `pm disable-user` and/or `pm hide`, never bulk uninstall. Fire OS 5 generally refuses changes to Amazon system apps; real state is verified afterward. Unknown system packages and core components are kept. The optional-system-app list is explicit in `catalog.py` and should only grow with model-specific evidence and a tested restore path.

Restoration recovers captured values, not an entire disk image or external app-data changes. Newly installed companions may be uninstalled during restore. Original APKs are backed up before upgrades; split APK replacement is refused.

Plans can partially succeed without automatic all-or-nothing rollback. A restore point undoes its registered operations, not every later operation on the TV; restore consecutive points from newest to oldest if undoing several plans. Android 5.1 may restore an original default-enabled state as explicitly enabled, preserving behavior rather than the exact enabled-state integer.

History is keyed by the ADB serial, usually `IP:port` over the network. IP/port changes or switching USB/network can make the same physical TV appear under a different history. Automatic physical-device identity migration is not implemented. Snapshots include the original serial in clear text and must stay private.

## Desktop and validation evidence

Official packages are x86_64 Linux and Windows, with separate `_internal` shared libraries. There are no ARM or macOS release packages. Native 0.1.0 CI used Ubuntu 22.04 and Windows Server 2022 and passed 33 tests plus source and packaged GUI smoke checks. The local development process also exercised Wine, but the public release binaries were produced by the native CI jobs.

Physical-device evidence consists of the original AFTT prototype Home algorithm/measurements and read-only inspection/app enumeration with the public desktop code. Do not read the prototype benchmark as an end-to-end certification of every installation/restoration path of the new public companion namespace, or of other Fire OS models. Preserve that distinction in issue reports and support claims.
