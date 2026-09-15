"""Score-raster downloads, without Earth Engine.

The first live SpectraLab run (2026-09-15) exposed two defects: the PNG preview
hit Earth Engine's memory limit at 1024 px, and the failed download still left a
0-byte file on disk. These tests pin both fixes with fakes.
"""
import pytest

from amdtool import raster

MEMORY_ERROR = ("Earth Engine download failed: 400 b'{\"error\": {\"code\": 400, "
                "\"message\": \"User memory limit exceeded.\"}}'")


class FakeImage:
    def __init__(self):
        self.thumb_dims = []

    def select(self, bands):
        return self

    def getThumbURL(self, params):
        self.thumb_dims.append(params["dimensions"])
        return "thumb%d" % params["dimensions"]

    def getDownloadURL(self, params):
        return "tif"


class FakeBBox:
    lat_lo, lon_lo, lat_hi, lon_hi = 37.75, -107.75, 37.95, -107.55

    def to_ee(self, ee):
        return None


@pytest.fixture(autouse=True)
def fixed_range(monkeypatch):
    monkeypatch.setattr(raster, "display_range", lambda *a, **k: (1.0, 2.0))


def test_png_halves_on_a_memory_error(tmp_path, monkeypatch):
    def fake_get(url, timeout):
        if url == "thumb1024":
            raise RuntimeError(MEMORY_ERROR)
        return b"PNGDATA"

    monkeypatch.setattr(raster, "_get", fake_get)
    img, out = FakeImage(), tmp_path / "p.png"
    got = raster.export_png(None, img, "FerricIron1", FakeBBox(), str(out), 30)
    assert img.thumb_dims == [1024, 512]
    assert got["dimensions"] == 512
    assert out.read_bytes() == b"PNGDATA"


def test_png_other_errors_raise_and_leave_no_file(tmp_path, monkeypatch):
    def fake_get(url, timeout):
        raise RuntimeError("Earth Engine download failed: 403 forbidden")

    monkeypatch.setattr(raster, "_get", fake_get)
    img, out = FakeImage(), tmp_path / "p.png"
    with pytest.raises(RuntimeError, match="403"):
        raster.export_png(None, img, "FerricIron1", FakeBBox(), str(out), 30)
    assert img.thumb_dims == [1024]
    assert not out.exists()


def test_png_gives_up_at_the_floor(tmp_path, monkeypatch):
    def fake_get(url, timeout):
        raise RuntimeError(MEMORY_ERROR)

    monkeypatch.setattr(raster, "_get", fake_get)
    img, out = FakeImage(), tmp_path / "p.png"
    with pytest.raises(RuntimeError, match="memory"):
        raster.export_png(None, img, "FerricIron1", FakeBBox(), str(out), 30)
    assert img.thumb_dims == [1024, 512, 256]
    assert not out.exists()


def test_an_empty_download_is_an_error_not_a_file(tmp_path, monkeypatch):
    monkeypatch.setattr(raster, "_get", lambda url, timeout: b"")
    out = tmp_path / "p.png"
    with pytest.raises(RuntimeError, match="empty"):
        raster.export_png(None, FakeImage(), "FerricIron1", FakeBBox(), str(out), 30)
    assert not out.exists()


def test_a_failed_geotiff_leaves_no_file(tmp_path, monkeypatch):
    def fake_get(url, timeout):
        raise RuntimeError("Earth Engine download failed: 400 too large")

    monkeypatch.setattr(raster, "_get", fake_get)
    out = tmp_path / "s.tif"
    with pytest.raises(RuntimeError):
        raster.export_geotiff(None, FakeImage(), "FerricIron1", FakeBBox(), str(out), 30)
    assert not out.exists()


def test_no_usable_range_means_no_preview(tmp_path, monkeypatch):
    monkeypatch.setattr(raster, "display_range", lambda *a, **k: None)
    out = tmp_path / "p.png"
    assert raster.export_png(None, FakeImage(), "FerricIron1", FakeBBox(), str(out), 30) is None
    assert not out.exists()
