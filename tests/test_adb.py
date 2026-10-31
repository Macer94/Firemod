import subprocess

import pytest

from firemod.adb import Adb, AdbError, endpoint, valid_package


@pytest.mark.parametrize("value", ["android", "com.netflix.ninja", "it.rainet.androidtv", "org.firemod.home"])
def test_package_ids(value):
    assert valid_package(value) == value


@pytest.mark.parametrize("value", ["x; reboot", "com.app && id", "com.app\nreboot", "../app", "-x"])
def test_rejects_shell_injection_in_packages(value):
    with pytest.raises(AdbError):
        valid_package(value)


def test_endpoint_parses_only_ip_literals():
    assert endpoint("192.168.1.5") == "192.168.1.5:5555"
    assert endpoint("192.168.1.5:1234") == "192.168.1.5:1234"
    assert endpoint("[::1]:5555") == "[::1]:5555"
    for bad in ("host;reboot", "https://192.168.1.2", "192.168.1.2:0", "user@192.168.1.2"):
        with pytest.raises(AdbError):
            endpoint(bad)


def test_adb_never_uses_a_host_shell_and_always_targets_device(monkeypatch, tmp_path):
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "ok\r\n", "")

    monkeypatch.setattr(subprocess, "run", run)
    adb = Adb(str(tmp_path / "adb"), "serial with spaces")
    assert adb.shell("settings", "put", "secure", "key", "value; id") == "ok"
    command, options = calls[0]
    assert command[1:3] == ["-s", "serial with spaces"]
    assert command[-1].endswith("'value; id'")
    assert "shell" not in options


def test_device_parser_keeps_unauthorized_devices_visible(monkeypatch, tmp_path):
    adb = Adb(str(tmp_path / "adb"))
    monkeypatch.setattr(adb, "run", lambda *a, **kw:
                        "List of devices attached\nA device model:AFTT transport_id:2\nB unauthorized\n")
    assert [(d.serial, d.state) for d in adb.devices()] == [("A", "device"), ("B", "unauthorized")]
