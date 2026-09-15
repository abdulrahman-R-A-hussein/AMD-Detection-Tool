"""amdtool.chemistry against the legacy python/fetch_wqp.py it was moved from.

The consolidation parity test needs a real chemistry folder under data/
(gitignored) and skips without one. The download test never touches the
network: it replaces the HTTP layer.
"""
import csv
import glob
import os
import shutil

import pytest

from amdtool import chemistry
from amdtool.errors import AmdToolError, InsufficientDataError
from amdtool.geometry import BBox

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEM = os.path.join(ROOT, "data", "chemistry")


def _copy_inputs(src, dst):
    os.makedirs(dst)
    for p in glob.glob(os.path.join(src, "*_results.csv")) + [os.path.join(src, "stations.csv")]:
        shutil.copy(p, dst)


@pytest.mark.parametrize("folder", ["huff_run_oh", "silverton_co"])
def test_consolidate_is_byte_identical_to_legacy(folder, tmp_path, legacy):
    src = os.path.join(CHEM, folder)
    if not os.path.isfile(os.path.join(src, "stations.csv")):
        pytest.skip("data/chemistry/%s not present" % folder)
    fetch_wqp = legacy("fetch_wqp")
    a, b = str(tmp_path / "new"), str(tmp_path / "old")
    _copy_inputs(src, a)
    _copy_inputs(src, b)
    assert chemistry.consolidate(a) == fetch_wqp.consolidate(b)
    for name in ("consolidated.csv", "consolidated_sediment.csv"):
        pa, pb = os.path.join(a, name), os.path.join(b, name)
        assert os.path.isfile(pa) == os.path.isfile(pb)
        if os.path.isfile(pa):
            assert open(pa, "rb").read() == open(pb, "rb").read(), name


def test_moved_constants_match_legacy(legacy):
    fetch_wqp = legacy("fetch_wqp")
    assert chemistry.CHARACTERISTICS == fetch_wqp.CHARACTERISTICS
    assert chemistry.START_DATE == fetch_wqp.START_DATE
    assert chemistry.EXCLUDE_SITE_TYPES == fetch_wqp.EXCLUDE_SITE_TYPES
    assert chemistry.SOURCE_POINT_TYPES == fetch_wqp.SOURCE_POINT_TYPES
    for v, u in [("5", "mg/L"), ("500", "ug/l"), ("12", "mg/kg"), ("x", "mg/L"), ("3", "furlongs")]:
        assert chemistry.normalize_iron_value(v, u) == fetch_wqp.normalize_iron_value(v, u)
    for name, t in [("SOMERSET RESERVOIR, L-1", "Lake"), ("ANIMAS RIVER AT SILVERTON, CO.", "Stream")]:
        assert chemistry._site_key(name, t) == fetch_wqp._site_key(name, t)


STATIONS_CSV = (
    "OrganizationFormalName,MonitoringLocationIdentifier,MonitoringLocationName,"
    "MonitoringLocationTypeName,LatitudeMeasure,LongitudeMeasure\n"
    "USGS,USGS-1,CEMENT CREEK AT SILVERTON,Stream,37.81,-107.66\n"
    "USGS,USGS-2,RED AND BONITA ADIT,Mine/Mine Discharge Adit (Mine Entrance),37.89,-107.64\n"
    "USGS,USGS-3,SNOW SITE,Land,37.85,-107.60\n"
)
RESULTS_CSV = (
    "MonitoringLocationIdentifier,ActivityStartDate,CharacteristicName,"
    "ResultMeasureValue,ResultMeasure/MeasureUnitCode,ResultSampleFractionText,"
    "ActivityDepthHeightMeasure/MeasureValue\n"
    "USGS-1,2015-06-01,Iron,800,ug/L,Dissolved,\n"
    "USGS-1,2015-06-01,Iron,800,ug/L,Dissolved,\n"
    "USGS-2,2016-07-01,Iron,25,mg/L,Dissolved,\n"
    "USGS-2,2016-07-01,Iron,4000,mg/kg,Total,\n"
    "USGS-2,2016-07-01,pH,3.1,,,\n"
    "USGS-3,2016-02-01,Sulfate,1,mg/L,,\n"
)


def test_fetch_wqp_writes_the_folder_every_loader_reads(tmp_path, monkeypatch):
    calls = []

    def fake_get(endpoint, params, retries=3):
        calls.append((endpoint, params))
        return RESULTS_CSV if endpoint == "Result" else STATIONS_CSV

    monkeypatch.setattr(chemistry, "_get", fake_get)
    bbox = BBox(37.75, -107.75, 37.95, -107.55)
    out = str(tmp_path / "chem")
    n_water, n_sed = chemistry.fetch_wqp(bbox, out)

    # the request the legacy region fetch made
    assert [c[0] for c in calls] == ["Result", "Station"]
    assert calls[0][1]["bBox"] == "-107.7500,37.7500,-107.5500,37.9500"
    assert calls[0][1]["characteristicName"] == chemistry.CHARACTERISTICS
    assert calls[0][1]["startDateLo"] == "01-01-2013"
    assert "siteType" not in calls[1][1]

    # duplicate dropped, snow site excluded, mg/kg split to sediment:
    # water = USGS-1 iron, USGS-2 iron, USGS-2 pH
    assert (n_water, n_sed) == (3, 1)
    with open(os.path.join(out, "stations.csv"), encoding="utf-8") as fh:
        assert list(csv.DictReader(fh))[0].keys() == set(chemistry.STATION_FIELDS)
    st = chemistry.stations_in_bbox(out, bbox, "sources")
    assert [s["pid"] for s in st] == ["USGS-2"]
    assert st[0]["Iron_mgL_dissolved"] == 25.0 and st[0]["pH"] == 3.1
    inst = chemistry.stations_in_bbox(out, bbox, "instream")
    assert inst[0]["Iron_mgL_dissolved"] == pytest.approx(0.8)


def test_fetch_wqp_outside_the_us_is_insufficient_data_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(chemistry, "_get", lambda e, p, retries=3:
                        STATIONS_CSV.splitlines()[0] + "\n")
    with pytest.raises(InsufficientDataError):
        chemistry.fetch_wqp(BBox(36.20, 44.93, 36.22, 44.95), str(tmp_path / "x"))


def test_request_failure_is_both_an_amdtool_error_and_a_runtime_error(monkeypatch):
    def boom(*a, **k):
        raise OSError("offline")

    monkeypatch.setattr(chemistry.urllib.request, "urlopen", boom)
    monkeypatch.setattr(chemistry.time, "sleep", lambda s: None)
    with pytest.raises(AmdToolError) as ei:
        chemistry._get("Station", {"bBox": "0,0,1,1"})
    assert isinstance(ei.value, RuntimeError)
