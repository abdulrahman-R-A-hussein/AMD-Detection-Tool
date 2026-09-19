"""The station counts the field registrations cite come from python/field_power.py.

validation/FIELD_CAMPAIGN_PREREGISTRATION_2026-09-19.md fixes its inflow-station
target from these numbers; if the formula changed, the registration would be
citing a number the code no longer produces.
"""
import field_power as fp


def test_closed_form_counts_cited_by_the_registrations():
    assert fp.n_spearman(0.30) == 89
    assert fp.n_spearman(0.40) == 51
    assert fp.n_spearman(0.50) == 33
    assert fp.n_spearman(0.438) == 42      # Ohio NDVI_stress vs sulfate, 1000 m
    assert fp.n_spearman(0.246) == 132     # Ohio partial rho after mining extent


def test_ohio_anchors_are_the_cmd2_values():
    assert set(fp.OHIO_ANCHORS) == {0.438, 0.246}


def test_all_groups_same_sign_is_the_product():
    assert fp.p_all(0.954, 2) == 0.954 ** 2
    assert fp.p_all(0.9, 1) == 0.9
