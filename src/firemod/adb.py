from __future__ import annotations

import ipaddress
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .models import Device
from .paths import data_dir, resource_dir

PACKAGE = re.compile(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+\Z")


class AdbError(RuntimeError):
    pass


def valid_package(value: str) -> str:
    # Android's framework package is the reserved single-segment identifier "android".
    if value != "android" and not PACKAGE.fullmatch(value):
        raise AdbError(f"Invalid Android package identifier: {value!r}")
    return value


def find_adb() -> str | None:
    name = "adb.exe" if sys.platform == "win32" else "adb"
    candidates = [os.environ.get("FIREMOD_ADB"), shutil.which(name)]
    for root in (resource_dir() / "platform-tools", data_dir() / "platform-tools"):
        candidates.append(str(root / name))
    for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(key):
            candidates.append(str(Path(os.environ[key]) / "platform-tools" / name))
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def endpoint(value: str) -> str:
    """Allow an IP literal and port only. No shell, hostname, credentials, or URL parsing."""
    host, sep, port = value.strip().rpartition(":")
    if not sep:
        host, port = value.strip(), "5555"
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
        number = int(port)
        if not 1 <= number <= 65535:
            raise ValueError()
    except ValueError as exc:
        raise AdbError("Enter a valid IP address, optionally followed by :5555.") from exc
    return f"[{ip}]:{number}" if ip.version == 6 else f"{ip}:{number}"


class Adb:
    def __init__(self, executable: str, serial: str | None = None):
        self.executable = str(Path(executable).resolve())
        self.serial = serial

    def run(self, *args: str, timeout: float = 30, device: bool = True) -> str:
        command = [self.executable]
        if device:
            if not self.serial:
                raise AdbError("Select a Fire TV first.")
            command.extend(["-s", self.serial])
        command.extend(args)
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
        try:
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                    errors="replace", timeout=timeout, **options)
        except subprocess.TimeoutExpired as exc:
            raise AdbError(f"ADB timed out after {timeout:g} seconds. Check the device connection.") from exc
        except OSError as exc:
            raise AdbError(str(exc)) from exc
        output = result.stdout.replace("\r", "").strip()
        if result.returncode:
            raise AdbError((output + "\n" + result.stderr).strip())
        return output

    def shell(self, *args: str, timeout: float = 30) -> str:
        # adb shell reparses its command on Android; quote each validated argument there too.
        return self.run("shell", " ".join(shlex.quote(str(x)) for x in args), timeout=timeout)

    def devices(self) -> list[Device]:
        output = self.run("devices", "-l", device=False)
        result = []
        for line in output.splitlines()[1:]:
            fields = line.split()
            if len(fields) < 2 or fields[0].startswith("*"):
                continue
            meta = dict(item.split(":", 1) for item in fields[2:] if ":" in item)
            result.append(Device(fields[0], fields[1], meta.get("model", ""), meta.get("transport_id", "")))
        return result

    def connect(self, address: str) -> str:
        output = self.run("connect", endpoint(address), timeout=15, device=False)
        if "connected to" not in output:
            raise AdbError(output)
        return output

    def assert_connected(self):
        if self.run("get-state", timeout=10) != "device":
            raise AdbError("Device is not authorized or connected.")

    def getprop(self, key: str) -> str:
        return self.shell("getprop", key)

    def setting(self, namespace: str, key: str) -> str | None:
        value = self.shell("settings", "get", namespace, key)
        if value.startswith("usage:") or value.startswith("Error:"):
            raise AdbError(value)
        return None if value in ("null", "") else value

    def put_setting(self, namespace: str, key: str, value: str | None):
        if value is None:
            self.shell("settings", "delete", namespace, key)
        else:
            self.shell("settings", "put", namespace, key, value)
        if self.setting(namespace, key) != value:
            raise AdbError(f"Firmware refused setting {namespace}/{key}.")

    def package_state(self, package: str) -> dict:
        output = self.shell("dumpsys", "package", valid_package(package))
        row = next((line for line in output.splitlines() if "User 0:" in line), "")
        if not row:
            return {"installed": False, "hidden": False, "enabled": 0, "stopped": False}
        fields = dict(re.findall(r"(\w+)=(\S+)", row))
        return {"installed": fields.get("installed") == "true", "hidden": fields.get("hidden") == "true",
                "enabled": int(fields.get("enabled", "0")), "stopped": fields.get("stopped") == "true"}
