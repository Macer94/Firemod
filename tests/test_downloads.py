import io
import zipfile

import pytest

from firemod import downloads


class Response(io.BytesIO):
    url = "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"


def test_download_extracts_only_known_members(monkeypatch, tmp_path):
    content = io.BytesIO()
    with zipfile.ZipFile(content, "w") as archive:
        archive.writestr("platform-tools/adb", b"fake executable")
        archive.writestr("../../escape", b"must not be extracted")
    monkeypatch.setattr(downloads.sys, "platform", "linux")
    monkeypatch.setattr(downloads, "data_dir", lambda: tmp_path)
    monkeypatch.setattr(downloads.urllib.request, "urlopen", lambda *a, **kw: Response(content.getvalue()))
    path = downloads.download_adb()
    assert path == str(tmp_path / "platform-tools" / "adb")
    assert not (tmp_path.parent / "escape").exists()


def test_download_rejects_an_unexpected_redirect(monkeypatch):
    response = Response(b"not a zip")
    response.url = "http://example.com/adb.zip"
    monkeypatch.setattr(downloads.sys, "platform", "linux")
    monkeypatch.setattr(downloads.urllib.request, "urlopen", lambda *a, **kw: response)
    with pytest.raises(RuntimeError, match="origin"):
        downloads.download_adb()
