"""convolve_splib07 used np.trapz, removed in NumPy 2.x (audit 2026-09-14 item 4).

Nothing called it, so it crashed silently the first time anyone would have used
it. These tests pin the corrected behaviour: integral(refl*RSR)/integral(RSR).
"""
import numpy as np
import pytest


def _convolve():
    import vpca_validation
    return vpca_validation.convolve_splib07


def test_flat_spectrum_convolves_to_its_own_value():
    wl = np.linspace(0.40, 2.50, 2101)
    refl = np.full_like(wl, 0.37)
    rsr = {
        "blue": (np.linspace(0.45, 0.51, 61), np.ones(61)),
        "swir": (np.linspace(1.55, 1.65, 101), np.hanning(101) + 0.01),
    }
    out = _convolve()(wl, refl, rsr)
    assert out["blue"] == pytest.approx(0.37, abs=1e-12)
    assert out["swir"] == pytest.approx(0.37, abs=1e-12)


def test_linear_spectrum_under_a_symmetric_response_gives_the_band_centre():
    wl = np.linspace(0.40, 2.50, 2101)
    refl = wl.copy()                                    # reflectance = wavelength
    band = np.linspace(0.60, 0.70, 101)
    tri = 1.0 - np.abs(np.linspace(-1.0, 1.0, 101))     # symmetric about 0.65
    out = _convolve()(wl, refl, {"red": (band, tri)})
    assert out["red"] == pytest.approx(0.65, abs=1e-6)


def test_band_outside_the_spectrum_is_nan():
    wl = np.linspace(0.40, 1.00, 601)
    refl = np.full_like(wl, 0.5)
    out = _convolve()(wl, refl, {"swir": (np.linspace(2.1, 2.3, 21), np.ones(21))})
    assert np.isnan(out["swir"])
