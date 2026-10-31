#!/usr/bin/env python3
"""Build the API-22 companion and fixed-action bridge without Gradle or downloaded code.

Requires a JDK >=17 and Android SDK build-tools/platform 36 (override through environment).
The release signing key lives OUTSIDE the repository and is never distributed.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command, **kwargs):
    subprocess.run([str(arg) for arg in command], check=True, **kwargs)


def main():
    sdk_value = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if not sdk_value:
        raise SystemExit("Set ANDROID_HOME to your Android SDK directory.")
    sdk = Path(sdk_value)
    tools_version = os.environ.get("FIREMOD_BUILD_TOOLS", "36.0.0")
    api = os.environ.get("FIREMOD_BUILD_API", "36")
    tools = sdk / "build-tools" / tools_version
    android_jar = sdk / "platforms" / ("android-" + api) / "android.jar"
    if not android_jar.is_file() or not (tools / "aapt2").is_file():
        raise SystemExit(f"Install Android SDK platform {api} and build-tools {tools_version} first.")
    java = Path(os.environ["JAVA_HOME"]) / "bin" if os.environ.get("JAVA_HOME") else None

    def jtool(name):
        return java / (name + (".exe" if sys.platform == "win32" else "")) if java else name

    build = ROOT / "android" / "build"
    if build.exists():
        shutil.rmtree(build)
    for part in ("gen", "classes", "dex", "bridge-classes", "bridge-dex"):
        (build / part).mkdir(parents=True)
    helper = ROOT / "android" / "helper"
    run([tools / "aapt2", "compile", "--dir", helper / "res", "-o", build / "res.zip"])
    run([tools / "aapt2", "link", "-o", build / "unsigned.apk", "-I", android_jar,
         "--manifest", helper / "AndroidManifest.xml", "--java", build / "gen",
         "--min-sdk-version", "22", "--target-sdk-version", "22", "--version-code", "1",
         "--version-name", "0.1.0", build / "res.zip"])
    sources = sorted((helper / "src").rglob("*.java")) + sorted((build / "gen").rglob("*.java"))
    run([jtool("javac"), "--release", "8", "-classpath", android_jar, "-d", build / "classes", *sources])
    run([tools / "d8", "--min-api", "22", "--lib", android_jar, "--output", build / "dex",
         *sorted((build / "classes").rglob("*.class"))])
    import zipfile
    with zipfile.ZipFile(build / "unsigned.apk", "a", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(build / "dex" / "classes.dex", "classes.dex")
    run([tools / "zipalign", "-f", "4", build / "unsigned.apk", build / "aligned.apk"])
    key = Path(os.environ.get("FIREMOD_KEYSTORE", Path.home() / ".local/share/firemod-signing/release.keystore"))
    key.parent.mkdir(parents=True, exist_ok=True)
    password = os.environ.get("FIREMOD_KEYSTORE_PASSWORD", "firemod-local-build")
    if not key.exists():
        run([jtool("keytool"), "-genkeypair", "-keystore", key, "-storepass", password,
             "-alias", "firemod", "-keypass", password, "-keyalg", "RSA", "-keysize", "3072",
             "-validity", "10000", "-dname", "CN=Firemod Release,O=Firemod,C=IT"])
        key.chmod(0o600)
    output = ROOT / "resources" / "android"
    output.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "FIREMOD_SIGNING_PASSWORD": password}
    run([tools / "apksigner", "sign", "--ks", key, "--ks-pass", "env:FIREMOD_SIGNING_PASSWORD",
         "--key-pass", "env:FIREMOD_SIGNING_PASSWORD", "--out", output / "firemod-home.apk",
         build / "aligned.apk"], env=env)
    run([tools / "apksigner", "verify", "--verbose", output / "firemod-home.apk"])
    run([jtool("javac"), "--release", "8", "-classpath", android_jar, "-d", build / "bridge-classes",
         ROOT / "android/bridge/FiremodBridge.java"])
    run([tools / "d8", "--min-api", "22", "--lib", android_jar, "--output", build / "bridge-dex",
         *sorted((build / "bridge-classes").glob("*.class"))])
    with zipfile.ZipFile(output / "firemod-bridge.jar", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(build / "bridge-dex/classes.dex", "classes.dex")
    files = {path.name: {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
             for path in sorted(output.iterdir()) if path.suffix in (".apk", ".jar")}
    source_digest = hashlib.sha256()
    for path in sorted((ROOT / "android").rglob("*")):
        if path.is_file() and build not in path.parents:
            source_digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0" + path.read_bytes())
    manifest = {"version": "0.1.0", "min_sdk": 22, "home_supported_sdk": [22],
                "android_source_sha256": source_digest.hexdigest(), "files": files,
                "luncher_source": "https://github.com/CVasilakis/luncher/tree/v0.4.0",
                "helper_upstream": "https://github.com/whyashthakker/debloat-fire-stick-claude-code/commit/2d006a3984ffabd432de6eaf199d4eea2dd0f8c5"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Android assets built. Keep the private signing key outside Git:", key)


if __name__ == "__main__":
    main()
