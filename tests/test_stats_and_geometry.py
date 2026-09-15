"""Unit tests for amdtool.stats helpers, amdtool.geometry and amdtool.claims.

Pure, offline, fast. The numeric anchors for the binomial helpers come from the
blind-search registration's committed power table, so a regression in the
helpers would also contradict the registration.
"""
import math
import random

import pytest

from amdtool import claims, stats
from amdtool.geometry import BBox


# ------------------------------------------------------------ binomial

def test_binomial_sf_edges():
    assert stats.binomial_sf_ge(0, 10, 0.3) == 1.0
    assert stats.binomial_sf_ge(11, 10, 0.3) == 0.0
    assert stats.binomial_sf_ge(10, 10, 0.5) == pytest.approx(0.5 ** 10)


def test_binomial_critical_values_match_the_registration():
    # report_blind_search_sites_2026-09-14.txt, 5% budget:
    # H-BS1 n=32 "reject if >=5" at both alpha 0.025 and 0.05.
    assert stats.binomial_test_greater(5, 32, 0.05) <= 0.025
    assert stats.binomial_test_greater(4, 32, 0.05) > 0.05
    # H-BS2 n=50: ">=7" at alpha 0.025, ">=6" at alpha 0.05.
    assert stats.binomial_test_greater(7, 50, 0.05) <= 0.025
    assert stats.binomial_test_greater(6, 50, 0.05) > 0.025
    assert stats.binomial_test_greater(6, 50, 0.05) <= 0.05
    assert stats.binomial_test_greater(5, 50, 0.05) > 0.05


def test_binomial_test_empty_is_nan():
    assert math.isnan(stats.binomial_test_greater(0, 0, 0.05))


# ------------------------------------------------------------ McNemar

def test_mcnemar_no_discordant_pairs_is_uninformative():
    assert stats.mcnemar_exact_greater(0, 0) == 1.0


def test_mcnemar_all_discordance_one_way():
    assert stats.mcnemar_exact_greater(5, 0) == pytest.approx(0.5 ** 5)


def test_mcnemar_is_one_sided():
    assert stats.mcnemar_exact_greater(0, 5) == pytest.approx(1.0)
    assert stats.mcnemar_exact_greater(5, 5) > 0.5


# ------------------------------------------------------------ Wilson

def test_wilson_bounds_stay_inside_zero_one():
    lo, hi = stats.wilson_interval(0, 10)
    assert lo == 0.0 and 0 < hi < 0.35
    lo, hi = stats.wilson_interval(10, 10)
    # 0.9999999999999999 is one float step below 1; the bound is 1.
    assert hi == pytest.approx(1.0, abs=1e-12) and 0.65 < lo < 1


def test_wilson_known_value():
    lo, hi = stats.wilson_interval(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-4)
    assert hi == pytest.approx(0.7634, abs=1e-4)


# ------------------------------------------------------------ Holm

def test_holm_both_rejected():
    reject, adj = stats.holm([0.01, 0.04])
    assert reject == [True, True]
    assert adj == pytest.approx([0.02, 0.04])


def test_holm_stops_at_first_failure():
    reject, _ = stats.holm([0.03, 0.04])
    assert reject == [False, False]


def test_holm_preserves_input_order():
    reject, _ = stats.holm([0.2, 0.02])
    assert reject == [False, True]


def test_holm_second_not_rejected_when_first_fails_even_if_small():
    reject, _ = stats.holm([0.026, 0.04])
    assert reject == [False, False]


# ------------------------------------------------------------ existing stats

def test_spearman_monotone_and_small_n():
    assert stats.spearman([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])[0] == pytest.approx(1.0)
    assert stats.spearman([1, 2, 3, 4, 5], [5, 4, 3, 2, 1])[0] == pytest.approx(-1.0)
    rho, n = stats.spearman([1, 2, 3], [1, 2, 3])
    assert math.isnan(rho) and n == 3


def test_spearman_drops_nan_pairs():
    nan = float("nan")
    rho, n = stats.spearman([1, 2, nan, 4, 5, 6], [1, 2, 3, nan, 5, 6])
    assert n == 4 and rho == pytest.approx(1.0)


def test_auc_perfect_and_ties():
    assert stats.auc([3, 4], [1, 2]) == 1.0
    assert stats.auc([1, 2], [3, 4]) == 0.0
    assert stats.auc([1, 1], [1, 1]) == 0.5


def test_benjamini_hochberg_known_example():
    adj = stats.benjamini_hochberg([0.01, 0.04, 0.03, 0.005])
    assert adj == pytest.approx([0.02, 0.04, 0.04, 0.02])


# ------------------------------------------------------------ partial Spearman

def test_partial_spearman_is_nan_when_z_explains_x_exactly():
    # Audit item 7: ranks of x identical to ranks of z leave residuals at float
    # noise. The verbatim original returned 11.97 here - not a correlation.
    z = list(range(50))
    x = [v + 0.1 for v in z]
    y = [(i * 7) % 50 for i in range(50)]
    assert math.isnan(stats.partial_spearman(x, y, z))


def test_partial_spearman_removes_a_shared_driver():
    rng = random.Random(20260914)
    z = [rng.random() for _ in range(400)]
    x = [zi + 0.3 * rng.random() for zi in z]
    y = [zi + 0.3 * rng.random() for zi in z]
    assert stats.spearman(x, y)[0] > 0.7
    part = stats.partial_spearman(x, y, z)
    assert -1.0 <= part <= 1.0
    assert abs(part) < 0.2


def test_partial_spearman_always_a_correlation_on_random_data():
    rng = random.Random(7)
    for _ in range(200):
        n = rng.randint(5, 40)
        x = [rng.random() for _ in range(n)]
        y = [rng.random() for _ in range(n)]
        z = [rng.random() for _ in range(n)]
        v = stats.partial_spearman(x, y, z)
        assert math.isnan(v) or -1.0 - 1e-12 <= v <= 1.0 + 1e-12


# ------------------------------------------------------------ geometry

def test_bbox_rejects_swapped_order():
    with pytest.raises(ValueError):
        BBox(40.0, -80.0, 39.0, -79.0)       # lat_lo > lat_hi
    with pytest.raises(ValueError):
        BBox(39.0, -79.0, 40.0, -80.0)       # lon_lo > lon_hi


def test_bbox_conversions_round_trip():
    b = BBox.from_wqp((37.70, -107.85, 37.95, -107.50, None, "note"))
    assert b.to_wqp() == (37.70, -107.85, 37.95, -107.50)
    assert BBox.from_lonlat(-107.85, 37.70, -107.50, 37.95) == b


def test_bbox_from_geojson_polygon_and_feature():
    poly = {"type": "Polygon", "coordinates": [[[-107.8, 37.7], [-107.5, 37.7],
                                                [-107.5, 37.9], [-107.8, 37.9],
                                                [-107.8, 37.7]]]}
    b = BBox.from_geojson({"type": "Feature", "geometry": poly})
    assert (b.lat_lo, b.lon_lo, b.lat_hi, b.lon_hi) == (37.7, -107.8, 37.9, -107.5)


def test_bbox_from_geojson_rejects_a_point():
    with pytest.raises(ValueError):
        BBox.from_geojson({"type": "Point", "coordinates": [-107.6, 37.8]})


def test_grid_tiles_partition_the_box():
    b = BBox(0.0, 0.0, 2.0, 2.0)
    tiles = b.grid(2)
    assert sorted(tiles) == ["r0c0", "r0c1", "r1c0", "r1c1"]
    assert b.tile_of(0.5, 0.5, 2) == "r0c0"
    assert b.tile_of(1.5, 0.5, 2) == "r1c0"
    assert b.tile_of(2.0, 2.0, 2) == "r1c1"        # NE corner stays inside
    assert b.tile_of(3.0, 0.5, 2) is None


def test_area_is_plausible():
    # Silverton box is roughly 856 km2 (validation scoping estimate)
    b = BBox(37.70, -107.85, 37.95, -107.50)
    assert 800 < b.area_km2() < 900


# ------------------------------------------------------------ claims

def test_boundaries_carry_the_non_negotiable_caveats():
    text = claims.boundaries_markdown()
    assert "no VNIR absorption" in text
    assert "replica fidelity, not accuracy" in text
    assert "jarosite" not in text.lower()


def test_stepwise_notice_is_opt_in():
    assert "Jarosite" in claims.boundaries_markdown(include_stepwise=True)
