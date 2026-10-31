import hashlib
import json
import zipfile

from firemod.paths import resource_dir


def test_android_assets_match_manifest():
    root = resource_dir() / "android"
    manifest = json.loads((root / "manifest.json").read_text())
    assert set(manifest["files"]) == {"firemod-home.apk", "firemod-bridge.jar", "luncher-0.4.0.apk"}
    for filename, spec in manifest["files"].items():
        path = root / filename
        assert hashlib.sha256(path.read_bytes()).hexdigest() == spec["sha256"]
        with zipfile.ZipFile(path) as archive:
            assert "classes.dex" in archive.namelist()


def test_android_companion_has_no_network_permission():
    manifest = resource_dir().parent / "android/helper/AndroidManifest.xml"
    text = manifest.read_text()
    assert "android.permission.INTERNET" not in text
    assert 'package="org.firemod.home"' in text


def test_android_sources_match_bundled_build():
    root = resource_dir().parent
    digest = hashlib.sha256()
    for path in sorted((root / "android").rglob("*")):
        if path.is_file() and root / "android/build" not in path.parents:
            digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
    manifest = json.loads((resource_dir() / "android/manifest.json").read_text())
    assert digest.hexdigest() == manifest["android_source_sha256"]
