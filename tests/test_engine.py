import json
from pathlib import Path

import pytest

from firemod.adb import AdbError
from firemod.engine import ANIMATIONS, LAUNCHER, Engine, Journal
from firemod.models import DeviceInfo, Outcome, Package, Plan


def info(serial="TEST", sdk=22):
    return DeviceInfo(serial, "AFTT", "Amazon", "Fire OS 5.2.9.5", "5.1.1", sdk,
                      150, 874, "2G", 0, "boot")


class FakeAdb:
    serial = "TEST"

    def __init__(self):
        self.settings = {}
        self.states = {}
        self.calls = []
        self.refuse = False
        self.before_write = lambda: None

    def setting(self, namespace, key):
        return self.settings.get((namespace, key))

    def put_setting(self, namespace, key, value):
        self.before_write()
        self.settings[namespace, key] = value

    def package_state(self, name):
        return dict(self.states.get(name, {"installed": False, "hidden": False, "enabled": 0,
                                          "stopped": False}))

    def shell(self, *args, **kwargs):
        self.calls.append(args)
        if args[0] == "pm" and args[1] in ("hide", "unhide", "disable-user", "enable"):
            name = args[-1]
            if not self.refuse:
                if args[1] in ("hide", "unhide"):
                    self.states[name]["hidden"] = args[1] == "hide"
                else:
                    self.states[name]["enabled"] = 3 if args[1] == "disable-user" else 1
            return "new hidden state: false" if self.refuse else "ok"
        return ""


@pytest.fixture
def session(tmp_path, monkeypatch):
    adb = FakeAdb()
    engine = Engine(adb, storage=tmp_path)
    monkeypatch.setattr(engine, "require_fire_tv", lambda: info())
    monkeypatch.setattr(engine, "packages", lambda: [
        Package("com.test.player", "Player", False, False, False, False),
        Package("com.amazon.tv.launcher", "Amazon Home", True, False, False, True)])
    adb.states["com.test.player"] = {"installed": True, "hidden": False, "enabled": 0, "stopped": False}
    return engine, adb


def test_journal_is_durable_before_first_change_and_settings_restore_exactly(session):
    engine, adb = session
    adb.settings["global", ANIMATIONS[0]] = "0.5"

    def before():
        saved = json.loads(engine.snapshots()[0].read_text())
        assert any(op["status"] == "pending" for op in saved["operations"])

    adb.before_write = before
    outcome = engine.apply(Plan(animations="0"))
    assert len(outcome.done) == 3
    adb.before_write = lambda: None
    restored = engine.restore(Path(outcome.snapshot))
    assert not restored.errors
    assert adb.setting("global", ANIMATIONS[0]) == "0.5"
    assert adb.setting("global", ANIMATIONS[1]) is None
    assert adb.setting("global", ANIMATIONS[2]) is None


def test_package_hiding_preserves_data_and_restores_visibility(session):
    engine, adb = session
    outcome = engine.apply(Plan(packages=["com.test.player"]))
    assert adb.states["com.test.player"]["hidden"]
    assert all("uninstall" not in call for call in adb.calls)
    restored = engine.restore(Path(outcome.snapshot))
    assert not restored.errors
    assert not adb.states["com.test.player"]["hidden"]


def test_firmware_refusal_is_never_reported_as_success(session):
    engine, adb = session
    adb.refuse = True
    outcome = engine.apply(Plan(packages=["com.test.player"]))
    assert not outcome.done
    assert outcome.skipped
    saved = json.loads(Path(outcome.snapshot).read_text())
    assert saved["operations"][0]["status"] == "refused"


def test_core_packages_are_rejected_before_any_change_or_snapshot(session):
    engine, adb = session
    with pytest.raises(AdbError):
        engine.apply(Plan(animations="0", packages=["com.amazon.tv.launcher"]))
    assert not engine.snapshots()
    assert not adb.calls


def test_restore_cannot_cross_device_boundaries(session, tmp_path):
    engine, _ = session
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"schema": 1, "device": {"serial": "OTHER"}, "operations": []}))
    with pytest.raises(AdbError):
        engine.restore(other)


def test_restore_checks_serial_even_inside_history_directory(session):
    engine, _ = session
    result = engine.apply(Plan(animations="0"))
    path = Path(result.snapshot)
    document = json.loads(path.read_text())
    document["device"]["serial"] = "OTHER"
    path.write_text(json.dumps(document))
    with pytest.raises(AdbError):
        engine.restore(path)


def test_second_apply_is_idempotent_for_settings(session):
    engine, _ = session
    engine.apply(Plan(animations="0"))
    second = engine.apply(Plan(animations="0"))
    assert not second.done
    assert not json.loads(Path(second.snapshot).read_text())["operations"]


def test_invalid_animation_scale_is_rejected(session):
    engine, _ = session
    with pytest.raises(AdbError):
        engine.apply(Plan(animations="-1"))


def test_reactivation_has_an_undo_record(session):
    engine, adb = session
    adb.states["com.test.player"]["hidden"] = True
    result = engine.apply(Plan(enable_packages=["com.test.player"]))
    assert not adb.states["com.test.player"]["hidden"]
    assert not result.errors
    restored = engine.restore(Path(result.snapshot))
    assert not restored.errors
    assert adb.states["com.test.player"]["hidden"]


def test_conflicting_app_plan_is_rejected_before_journaling(session):
    engine, _ = session
    with pytest.raises(AdbError):
        engine.apply(Plan(packages=["com.test.player"], enable_packages=["com.test.player"]))
    assert not engine.snapshots()


def test_interrupted_apply_keeps_pending_undo_record(session):
    engine, adb = session
    count = 0

    def interrupt():
        nonlocal count
        count += 1
        if count == 2:
            raise RuntimeError("simulated process interruption")

    adb.before_write = interrupt
    with pytest.raises(RuntimeError):
        engine.apply(Plan(animations="0"))
    path = engine.snapshots()[0]
    document = json.loads(path.read_text())
    assert not document["finished"]
    assert document["operations"][1]["status"] == "pending"
    adb.before_write = lambda: None
    assert not engine.restore(path).errors
    assert all(adb.setting("global", key) is None for key in ANIMATIONS)


def test_hidden_launcher_failure_keeps_current_home_untouched(session, monkeypatch):
    engine, adb = session
    adb.states[LAUNCHER] = {"installed": True, "hidden": True, "enabled": 0, "stopped": False}
    adb.refuse = True
    installs = []
    monkeypatch.setattr(engine, "_install", lambda *args: installs.append(args))
    journal = Journal(engine.device_dir, info())
    with pytest.raises(AdbError, match="reactivated"):
        engine.install_home(journal, info(), Outcome())
    assert not installs
    assert not any(call[:2] == ("am", "force-stop") for call in adb.calls)


def test_package_scan_handles_reserved_android_framework_package(tmp_path):
    adb = FakeAdb()

    def shell(*args, **kwargs):
        if args[:3] == ("pm", "list", "packages"):
            if "-s" in args:
                return "package:android"
            if "-d" in args:
                return ""
            return "package:android\npackage:com.test.player"
        return ""

    adb.shell = shell
    packages = {p.name: p for p in Engine(adb, tmp_path).packages()}
    assert packages["android"].protected
    assert not packages["com.test.player"].protected


def test_package_scan_reads_hidden_and_uninstalled_user_state(tmp_path):
    adb = FakeAdb()

    def shell(*args, **kwargs):
        if args[:3] == ("pm", "list", "packages"):
            if "-s" in args or "-d" in args:
                return ""
            return "package:com.test.hidden\npackage:com.test.removed\npackage:com.test.active"
        return """Packages:
  Package [com.test.hidden] (1234):
    User 0: installed=true hidden=true stopped=false enabled=0
  Package [com.test.removed] (5678):
    User 0: installed=false hidden=false stopped=true enabled=0
  Package [com.test.active] (9012):
    User 0: installed=true hidden=false stopped=false enabled=0
"""

    adb.shell = shell
    packages = {p.name: p for p in Engine(adb, tmp_path).packages()}
    assert packages["com.test.hidden"].hidden
    assert not packages["com.test.active"].hidden
    assert "com.test.removed" not in packages
