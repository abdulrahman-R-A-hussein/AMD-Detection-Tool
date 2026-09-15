"""The severity report, end to end, without Earth Engine.

Runs on the packaged fixture (src/amdtool/_fixtures/cmd_huff_run_oh_30m.csv).
A number computed from one fixture watershed is a test input, not a finding.
"""
import math
import os

import pytest

from amdtool import raster, severity
from amdtool.dose_response import (VERDICT_NO_PAIRS, VERDICT_NULL, VERDICT_PARTIAL,
                                   VERDICT_SUCCESS, VERDICT_UNINTERPRETABLE)
from amdtool.geometry import BBox
from amdtool.io import load_extracted

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "src", "amdtool", "_fixtures", "cmd_huff_run_oh_30m.csv")
HUFF_RUN = BBox(40.45, -81.30, 40.72, -81.00)
VERDICTS = {VERDICT_SUCCESS, VERDICT_PARTIAL, VERDICT_NULL,
            VERDICT_UNINTERPRETABLE, VERDICT_NO_PAIRS}


@pytest.fixture
def rows():
    return load_extracted([FIXTURE])


def test_coal_preset_writes_three_files_with_the_claim_boundaries(rows, tmp_path):
    preset = severity.get_preset("coal")
    out_rows, res = severity.analyse_rows(rows, preset, HUFF_RUN, grid=2, n_perm=200)
    outputs = severity.write_outputs(str(tmp_path), out_rows, res, preset, HUFF_RUN,
                                     sensor="L8", grid=2)
    assert [o["kind"] for o in outputs] == ["csv", "csv", "txt"]
    assert all(os.path.isfile(o["path"]) for o in outputs)
    report = open(outputs[2]["path"], encoding="utf-8").read()
    assert "EXPLORATORY" in report
    assert "no VNIR absorption" in report
    assert "Jarosite" in report                       # SpectraLab W2 notice
    assert res.verdict in VERDICTS


def test_only_the_presets_validated_index_is_tested(rows):
    # No fishing across the panel: the fixture carries all 8 indices.
    for key in severity.PRESETS:
        preset = severity.get_preset(key)
        _, res = severity.analyse_rows(rows, preset, HUFF_RUN, n_perm=50)
        assert {p.index for p in res.pairs} <= {preset.index}
        assert {p.analyte for p in res.pairs} <= set(preset.analytes)


def test_tiles_come_from_coordinates_alone(rows):
    out_rows, _ = severity.analyse_rows(rows, severity.get_preset("coal"),
                                        HUFF_RUN, grid=3, n_perm=10)
    for r in out_rows:
        assert r["group"] == (HUFF_RUN.tile_of(r["lat"], r["lon"], 3) or "outside")


def test_same_seed_same_p_values(rows):
    preset = severity.get_preset("coal")
    _, a = severity.analyse_rows(rows, preset, HUFF_RUN, n_perm=300, seed=11)
    _, b = severity.analyse_rows(rows, preset, HUFF_RUN, n_perm=300, seed=11)
    assert [p.p for p in a.pairs] == [p.p for p in b.pairs]


def test_canopy_gate_is_reported_for_coal_and_absent_for_metal(rows):
    _, coal = severity.analyse_rows(rows, severity.get_preset("coal"), HUFF_RUN, n_perm=10)
    _, metal = severity.analyse_rows(rows, severity.get_preset("metal_mine"), HUFF_RUN, n_perm=10)
    assert not math.isnan(coal.canopy_median_ndvi)
    assert metal.canopy_limit is None and not metal.canopy_limited


def test_none_and_blank_become_nan():
    out = severity.normalise_rows([{"lat": "40.5", "lon": "-81.1", "Sulfate_mgL": None,
                                    "NDVI_stress_p90": "", "pid": "x"}])[0]
    assert out["lat"] == 40.5
    assert math.isnan(out["Sulfate_mgL"]) and math.isnan(out["NDVI_stress_p90"])
    assert out["pid"] == "x"


def test_unknown_preset_is_rejected():
    with pytest.raises(ValueError):
        severity.get_preset("gold")


def test_sentinel2_is_refused_for_leaf_off_before_touching_earth_engine():
    with pytest.raises(ValueError):
        severity.composite(None, None, severity.get_preset("coal"), "S2")


def test_download_scale_coarsens_only_when_needed():
    small = BBox(40.50, -81.20, 40.55, -81.15)       # ~5 km
    assert raster.download_scale(small, 30) == 30.0
    big = BBox(39.0, -83.0, 41.0, -80.0)             # ~250 km
    s = raster.download_scale(big, 30)
    assert s > 30
    width_m = 3.0 * 111320.0 * math.cos(math.radians(40.0))
    assert width_m / s <= raster.MAX_PIXELS_PER_SIDE


def test_stations_loader_matches_the_legacy_cmd_loader():
    chem_dir = os.path.join(ROOT, "data", "chemistry", "huff_run_oh")
    if not os.path.isdir(chem_dir):
        pytest.skip("data/chemistry/huff_run_oh not present")
    from amdtool.chemistry import stations_in_bbox
    from cmd_detect import load_cmd_stations
    new = stations_in_bbox(chem_dir, None, "all",
                           require_any=("Sulfate_mgL", "SpecificConductance"))
    old = load_cmd_stations("huff_run_oh")
    assert [s["pid"] for s in new] == [s["pid"] for s in old]
    assert [s["Sulfate_mgL"] for s in new] == [s["Sulfate_mgL"] for s in old]
