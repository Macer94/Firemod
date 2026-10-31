from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .adb import Adb, AdbError, valid_package
from .catalog import LABELS, OPTIONAL_SYSTEM, protected
from .models import DeviceInfo, Outcome, Package, Plan
from .paths import data_dir, resource_dir

HELPER = "org.firemod.home"
LAUNCHER = "com.luncher.launcher"
LEGACY_HELPER = "it.massi.firehome"
REMOTE = "/data/local/tmp/firemod"
MARKER = f"/sdcard/Android/data/{HELPER}/files/home-bridge-ready"
ANIMATIONS = ("window_animation_scale", "transition_animation_scale", "animator_duration_scale")
# These were read back and checked in the native settings during the original AFTT work.
PRIVACY = {"USAGE_METRICS_UPLOAD_ENABLED": "0", "usage_metrics_marketing_enabled": "0",
           "limit_ad_tracking": "1", "settingsApp:deviceUsageData:value": "0",
           "settingsApp:appUsageData:value": "0"}


def atomic_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


class Journal:
    def __init__(self, directory: Path, info: DeviceInfo):
        identifier = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        self.path = directory / identifier / "snapshot.json"
        self.value = {"schema": 1, "firemod": __version__, "created": datetime.now(UTC).isoformat(),
                      "device": {"serial": info.serial, "model": info.model, "fire_os": info.fire_os},
                      "operations": [], "finished": False}
        self.save()

    def save(self):
        atomic_json(self.path, self.value)

    def before(self, operation: dict) -> int:
        operation = {**operation, "status": "pending"}
        self.value["operations"].append(operation)
        self.save()  # The undo record must exist before touching the device.
        return len(self.value["operations"]) - 1

    def finish(self, index: int, status: str = "applied", **extra):
        self.value["operations"][index].update(status=status, **extra)
        self.save()


class Engine:
    def __init__(self, adb: Adb, storage: Path | None = None, log: Callable[[str], None] | None = None):
        if not adb.serial:
            raise AdbError("Select a device before creating a session.")
        self.adb = adb
        self.storage = storage or data_dir()
        self.log = log or (lambda _: None)
        self.device_dir = self.storage / "devices" / hashlib.sha256(adb.serial.encode()).hexdigest()[:20]

    def inspect(self) -> DeviceInfo:
        self.adb.assert_connected()
        props = self.adb.shell("getprop")
        values = dict(re.findall(r"\[([^]]+)\]: \[([^]]*)\]", props))
        model = values.get("ro.product.model", "Unknown")
        manufacturer = values.get("ro.product.manufacturer", "")
        memory = self.adb.shell("cat", "/proc/meminfo")
        mem = dict((k, int(v)) for k, v in re.findall(r"(MemTotal|MemAvailable|MemFree):\s+(\d+)", memory))
        disk = self.adb.shell("df", "/data")
        row = next((line.split() for line in disk.splitlines() if line.startswith("/")), [])
        disabled = self.adb.shell("pm", "list", "packages", "-d")
        boot = self.adb.shell("cat", "/proc/sys/kernel/random/boot_id").strip()
        return DeviceInfo(self.adb.serial, model, manufacturer, values.get("ro.build.version.name", ""),
                          values.get("ro.build.version.release", ""),
                          int(values.get("ro.build.version.sdk", "0") or 0),
                          mem.get("MemAvailable", mem.get("MemFree", 0)) // 1024,
                          mem.get("MemTotal", 0) // 1024, row[3] if len(row) > 3 else "?",
                          disabled.count("package:"), boot)

    def require_fire_tv(self) -> DeviceInfo:
        info = self.inspect()
        if not info.is_fire_tv:
            raise AdbError("This device was not identified as an Android-based Amazon Fire TV. No changes made.")
        if info.sdk < 22:
            raise AdbError("Firemod requires Android API 22 / Fire OS 5 or newer.")
        return info

    def packages(self) -> list[Package]:
        def names(*args):
            return {line.split(":", 1)[1] for line in self.adb.shell("pm", "list", "packages", *args).splitlines()
                    if line.startswith("package:") and valid_package(line.split(":", 1)[1])}
        all_names = names("-u")
        system = names("-s", "-u")
        disabled = names("-d")
        dump = self.adb.shell("dumpsys", "package", timeout=60)
        hidden, uninstalled = set(), set()
        for block in re.finditer(r"(?ms)^  Package \[([^]]+)\](.*?)(?=^  Package \[|\Z)", dump):
            package, body = block.groups()
            state = next((line for line in body.splitlines() if "User 0:" in line), "")
            if "hidden=true" in state:
                hidden.add(package)
            if "installed=false" in state:
                uninstalled.add(package)
        return sorted((Package(name, LABELS.get(name, name), name in system, name in disabled,
                               name in hidden, protected(name, name in system), OPTIONAL_SYSTEM.get(name, ""))
                       for name in all_names - uninstalled), key=lambda p: (p.protected, p.label.casefold()))

    def snapshots(self) -> list[Path]:
        return sorted(self.device_dir.glob("*/snapshot.json"), reverse=True)

    def _setting(self, journal: Journal, namespace: str, key: str, value: str, out: Outcome):
        previous = self.adb.setting(namespace, key)
        if previous == value:
            return
        index = journal.before({"kind": "setting", "namespace": namespace, "key": key,
                                "before": previous, "after": value})
        try:
            self.adb.put_setting(namespace, key, value)
            journal.finish(index)
            out.done.append(f"{key} = {value}")
        except AdbError as exc:
            journal.finish(index, "failed", error=str(exc))
            out.errors.append(f"{key}: {exc}")

    def _disable(self, journal: Journal, name: str, sdk: int, system: bool, out: Outcome):
        valid_package(name)
        if protected(name, system):
            out.skipped.append(f"{name}: essential or unknown system component; kept.")
            return
        previous = self.adb.package_state(name)
        if not previous["installed"] or previous["hidden"] or previous["enabled"] in (2, 3, 4):
            out.skipped.append(f"{name}: already inactive.")
            return
        index = journal.before({"kind": "package", "package": name, "before": previous})
        failures = []
        # Fire OS 5 rejects disable-user; hide works for ordinary third-party apps.
        commands = [("disable-user", "--user", "0", name), ("hide", "--user", "0", name)]
        if sdk == 22:
            commands = commands[1:]
        for args in commands:
            try:
                response = self.adb.shell("pm", *args)
                after = self.adb.package_state(name)
                if after["hidden"] or after["enabled"] in (2, 3, 4):
                    journal.finish(index, after=after)
                    out.done.append(f"{name}: inactive, app data kept.")
                    return
                failures.append(response or "state unchanged")
            except AdbError as exc:
                failures.append(str(exc))
        journal.finish(index, "refused", error="; ".join(failures))
        out.skipped.append(f"{name}: protected by this firmware; unchanged.")

    def _asset(self, filename: str) -> Path:
        root = resource_dir() / "android"
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        item = manifest["files"].get(filename)
        path = root / filename
        if not item or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise AdbError(f"Bundled asset is missing or does not match its checksum: {filename}")
        return path

    def _enable(self, journal: Journal, name: str, out: Outcome):
        previous = self.adb.package_state(valid_package(name))
        if not previous["installed"]:
            raise AdbError(f"Package is no longer installed: {name}")
        index = journal.before({"kind": "package", "package": name, "before": previous})
        try:
            if previous["hidden"]:
                self.adb.shell("pm", "unhide", "--user", "0", name)
            if previous["enabled"] in (2, 3, 4):
                self.adb.shell("pm", "enable", "--user", "0", name)
            after = self.adb.package_state(name)
            if after["hidden"] or after["enabled"] in (2, 3, 4):
                raise AdbError("Firmware refused to reactivate the app.")
            journal.finish(index, after=after)
            out.done.append(f"{name}: active again.")
        except AdbError as exc:
            journal.finish(index, "failed", error=str(exc))
            out.errors.append(f"{name}: {exc}")

    def _install(self, journal: Journal, name: str, asset: str, out: Outcome):
        previous = self.adb.package_state(name)
        operation = {"kind": "install", "package": name, "before": previous}
        # Preserve an existing APK before attempting an upgrade. Split APKs are intentionally not replaced.
        if previous["installed"]:
            paths = [line.removeprefix("package:") for line in self.adb.shell("pm", "path", name).splitlines()
                     if line.startswith("package:")]
            if len(paths) != 1:
                raise AdbError(f"Cannot safely back up split APK package {name}; left unchanged.")
            backup = journal.path.parent / (name + ".apk")
            self.adb.run("pull", paths[0], str(backup), timeout=60)
            operation["backup"] = backup.name
        index = journal.before(operation)
        try:
            output = self.adb.run("install", "-r", str(self._asset(asset)), timeout=90)
            if "Success" not in output or not self.adb.package_state(name)["installed"]:
                raise AdbError(output)
            journal.finish(index)
            out.done.append(f"Installed {name}.")
        except AdbError as exc:
            journal.finish(index, "failed", error=str(exc))
            raise

    def install_home(self, journal: Journal, info: DeviceInfo, out: Outcome):
        if info.sdk != 22:
            out.skipped.append("Home integration currently supports Fire OS 5 / API 22; other options remain available.")
            return
        launcher_state = self.adb.package_state(LAUNCHER)
        if not launcher_state["installed"]:
            self._install(journal, LAUNCHER, "luncher-0.4.0.apk", out)
        elif launcher_state["hidden"] or launcher_state["enabled"] in (2, 3, 4):
            self._enable(journal, LAUNCHER, out)
            restored = self.adb.package_state(LAUNCHER)
            if restored["hidden"] or restored["enabled"] in (2, 3, 4):
                raise AdbError("Existing Luncher could not be reactivated; the current Home was left unchanged.")
        self._install(journal, HELPER, "firemod-home.apk", out)
        granted_before = self.adb.shell("dumpsys", "package", HELPER).partition("grantedPermissions:")[2]
        permission_index = None
        if "android.permission.READ_LOGS" not in granted_before:
            permission_index = journal.before({"kind": "permission", "package": HELPER,
                                               "permission": "android.permission.READ_LOGS", "before": False})
        output = self.adb.shell("pm", "grant", HELPER, "android.permission.READ_LOGS")
        if "Exception" in output or "Error" in output:
            raise AdbError("Firmware refused READ_LOGS: " + output)
        granted = self.adb.shell("dumpsys", "package", HELPER).partition("grantedPermissions:")[2]
        if "android.permission.READ_LOGS" not in granted:
            raise AdbError("READ_LOGS was not granted. Restore this installation from History if needed.")
        if permission_index is not None:
            journal.finish(permission_index)
        self.adb.shell("am", "start", "-n", HELPER + "/.HomeActivity")
        for _ in range(12):
            if "HomeWatcher" in self.adb.shell("dumpsys", "activity", "services", HELPER):
                break
            time.sleep(0.25)
        else:
            raise AdbError("The home service did not start; the previous helper was left active.")
        legacy = self.adb.package_state(LEGACY_HELPER)
        if legacy["installed"] and not legacy["stopped"]:
            index = journal.before({"kind": "legacy_helper", "package": LEGACY_HELPER, "before": legacy})
            self.adb.shell("am", "force-stop", LEGACY_HELPER)
            journal.finish(index)
        out.done.append("Lightweight home enabled. Amazon Home and account data were kept.")

    def bridge_status(self) -> bool:
        try:
            boot = self.adb.shell("cat", "/proc/sys/kernel/random/boot_id")
            marker = self.adb.shell("cat", MARKER)
            pid = self.adb.shell("cat", REMOTE + "/bridge.pid").strip()
            return (marker == boot and pid.isdigit()
                    and "FiremodBridge" in self.adb.shell("cat", f"/proc/{pid}/cmdline"))
        except AdbError:
            return False

    def stop_bridge(self):
        # Remove the marker first so clients immediately use the standard fallback.
        self.adb.shell("rm", "-f", MARKER)
        try:
            pid = self.adb.shell("cat", REMOTE + "/bridge.pid").strip()
            if pid.isdigit() and "FiremodBridge" in self.adb.shell("cat", f"/proc/{pid}/cmdline"):
                self.adb.shell("kill", pid)
        except AdbError:
            pass

    def enable_bridge(self, journal: Journal, info: DeviceInfo, out: Outcome):
        if info.sdk != 22:
            out.skipped.append("Home accelerator currently supports Fire OS 5 / API 22.")
            return
        if not self.adb.package_state(HELPER)["installed"]:
            raise AdbError("Install Firemod Home before enabling its accelerator.")
        if self.bridge_status():
            out.skipped.append("Home accelerator is already active for this boot.")
            return
        index = journal.before({"kind": "bridge", "before": False})
        try:
            self.stop_bridge()
            self.adb.shell("mkdir", "-p", REMOTE)
            self.adb.run("push", str(self._asset("firemod-bridge.jar")), REMOTE + "/bridge.jar")
            # Fixed program and fixed paths. The device-side bridge only opens Luncher; it is not a shell API.
            command = ("trap '' HUP; CLASSPATH=" + REMOTE + "/bridge.jar "
                       "app_process /system/bin FiremodBridge </dev/null >" + REMOTE + "/bridge.log 2>&1 "
                       "& echo $! >" + REMOTE + "/bridge.pid")
            self.adb.run("shell", command)
            for _ in range(25):
                if self.bridge_status():
                    journal.finish(index)
                    out.done.append("Home accelerator active until the next Fire TV reboot; PC can be disconnected.")
                    return
                time.sleep(0.2)
            raise AdbError("Accelerator did not become ready. Standard home remains available.")
        except AdbError as exc:
            self.stop_bridge()
            journal.finish(index, "failed", error=str(exc))
            raise

    def apply(self, plan: Plan) -> Outcome:
        if plan.empty:
            raise AdbError("Select at least one change.")
        info = self.require_fire_tv()
        selected = plan.packages + plan.enable_packages
        packages = {p.name: p for p in self.packages()} if selected else {}
        if set(plan.packages) & set(plan.enable_packages):
            raise AdbError("An app cannot be enabled and disabled in the same plan.")
        for name in selected:
            valid_package(name)
            if name not in packages or packages[name].protected:
                raise AdbError(f"Package cannot be changed by this plan: {name}")
        if plan.animations not in (None, "0", "0.5", "1"):
            raise AdbError("Invalid animation scale.")
        journal = Journal(self.device_dir, info)
        out = Outcome(snapshot=str(journal.path))
        self.log(f"Restore point saved: {journal.path.name} / {journal.path.parent.name}")
        if plan.animations is not None:
            self.log("Updating animation scales…")
            for key in ANIMATIONS:
                self._setting(journal, "global", key, plan.animations, out)
        if plan.privacy:
            self.log("Updating privacy settings…")
            for key, value in PRIVACY.items():
                self._setting(journal, "secure", key, value, out)
        if plan.screensaver:
            for key in ("screensaver_enabled", "screensaver_activate_on_sleep", "screensaver_activate_on_dock"):
                self._setting(journal, "secure", key, "0", out)
        for name in plan.packages:
            self.log(f"Disabling {name}…")
            self._disable(journal, name, info.sdk, packages[name].system, out)
        for name in plan.enable_packages:
            self.log(f"Reactivating {name}…")
            self._enable(journal, name, out)
        if plan.launcher:
            self.log("Installing the lightweight home…")
            try:
                self.install_home(journal, info, out)
            except AdbError as exc:
                out.errors.append(str(exc))
        if plan.accelerator:
            self.log("Starting the home accelerator…")
            try:
                self.enable_bridge(journal, info, out)
            except AdbError as exc:
                out.errors.append(str(exc))
        journal.value["finished"] = True
        journal.value["summary"] = {"done": out.done, "skipped": out.skipped, "errors": out.errors}
        journal.save()
        self.log("Finished. Every attempted change has an undo record.")
        return out

    def restore(self, path: Path) -> Outcome:
        info = self.require_fire_tv()
        path = path.resolve()
        if not path.is_relative_to(self.device_dir.resolve()):
            raise AdbError("Restore points must belong to the selected device's local history.")
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema") != 1 or value.get("device", {}).get("serial") != info.serial:
            raise AdbError("Restore point belongs to a different device or unsupported format.")
        out = Outcome(snapshot=str(path))
        operations = value.get("operations", [])
        for operation in reversed(operations):
            if operation.get("status") in ("restored", "refused"):
                continue
            try:
                kind = operation["kind"]
                if kind == "setting":
                    self.adb.put_setting(operation["namespace"], operation["key"], operation["before"])
                elif kind == "package":
                    name = valid_package(operation["package"])
                    before = operation["before"]
                    current = self.adb.package_state(name)
                    if current["hidden"] != before["hidden"]:
                        self.adb.shell("pm", "hide" if before["hidden"] else "unhide", "--user", "0", name)
                    if current["enabled"] != before["enabled"]:
                        command = {0: "default-state", 1: "enable", 2: "disable", 3: "disable-user",
                                   4: "disable-until-used"}[before["enabled"]]
                        # Lollipop lacks default-state: enable is equivalent to the original enabled behavior.
                        if command == "default-state" and info.sdk == 22:
                            command = "enable"
                        self.adb.shell("pm", command, "--user", "0", name)
                        if command == "default-state" and self.adb.package_state(name)["enabled"] in (2, 3, 4):
                            self.adb.shell("pm", "enable", "--user", "0", name)
                    after = self.adb.package_state(name)
                    if after["hidden"] != before["hidden"] or ((after["enabled"] in (2, 3, 4))
                                                               != (before["enabled"] in (2, 3, 4))):
                        raise AdbError(f"Firmware refused to restore {name}.")
                elif kind == "bridge":
                    self.stop_bridge()
                elif kind == "permission":
                    if operation["package"] != HELPER or operation["permission"] != "android.permission.READ_LOGS":
                        raise AdbError("Unknown permission operation.")
                    if self.adb.package_state(HELPER)["installed"]:
                        command = "grant" if operation["before"] else "revoke"
                        self.adb.shell("pm", command, HELPER, operation["permission"])
                        granted = self.adb.shell("dumpsys", "package", HELPER).partition("grantedPermissions:")[2]
                        if (operation["permission"] in granted) != operation["before"]:
                            raise AdbError("Firmware refused the original permission state.")
                elif kind == "legacy_helper":
                    if not operation["before"]["stopped"]:
                        self.adb.shell("am", "start", "-n", LEGACY_HELPER + "/.HomeActivity")
                elif kind == "install":
                    name = valid_package(operation["package"])
                    if name not in (HELPER, LAUNCHER):
                        raise AdbError("Unknown install operation.")
                    if name == HELPER:
                        self.stop_bridge()
                        self.adb.shell("am", "force-stop", HELPER)
                    if operation["before"]["installed"]:
                        backup = (path.parent / operation["backup"]).resolve()
                        if backup.parent != path.parent or not backup.is_file():
                            raise AdbError("Original APK backup is missing.")
                        response = self.adb.run("install", "-r", "-d", str(backup), timeout=90)
                    else:
                        response = (self.adb.run("uninstall", name, timeout=60)
                                    if self.adb.package_state(name)["installed"] else "Success")
                    if "Success" not in response:
                        raise AdbError(response)
                else:
                    raise AdbError(f"Unknown operation: {kind}")
                operation["status"] = "restored"
                out.done.append(f"Restored {kind}: {operation.get('key', operation.get('package', 'accelerator'))}")
                atomic_json(path, value)
            except (AdbError, KeyError, OSError) as exc:
                operation["restore_error"] = str(exc)
                out.errors.append(str(exc))
                atomic_json(path, value)
        # Always leave a usable stock home after removing an integration created by this restore point.
        if any(op.get("kind") == "install" and op.get("package") == HELPER
               and op.get("status") == "restored" for op in operations):
            self.adb.shell("am", "start", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
        return out

    def open_settings(self) -> str:
        return self.adb.shell("am", "start", "-a", "android.settings.SETTINGS")
