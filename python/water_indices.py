"""Band indices for detecting sulphurous discharge / AMD precipitate on land.

Source: Galaszkiewicz, Delaney & Steelman (2024), "Identifying sulphurous
water discharge from legacy oil and gas wells using spectral band analysis of
aerial and satellite imagery", Geomatica 76, 100024 (paper2.pdf, open access).
Their finding: sulphurous water/precipitate has HIGH reflectance in green and
HIGH absorbance in NIR, so a high green:NIR ratio discriminates it; they built
a custom green-NIR-NIR false-colour composite and also tracked NDVI as a
vegetation-stress proxy around known leak sites.

*** CRITICAL SCOPING, verified before any code was written against it ***
`Green/NIR` is DEGENERATE on open water: water absorbs NIR almost totally, so
EVERY water pixel scores high on this ratio - applied to a lake or river it is
a water detector, not a sulfur detector, and would manufacture a spurious
"detection" at 100% of the water surface. Galaszkiewicz's actual imagery
showed sulphurous water and sulphide precipitate FLOWING OVER LAND
("light blue texture ... on the ground surface"), not standing water.

So every function here is intended for LAND-SURFACE pixels only - seeps,
shoreline, streambed exposed at low flow, mine adit outflows before they
reach open water. Never apply green_nir_ratio() to pixels the tool's own
water mask (createUnifiedWaterMask / MNDWI>0.3 in gee_classify.classify)
already calls water; do that filtering BEFORE calling into this module, not
after. This is the B1 (water column) / B2 (precipitate) split in the Water
Phase 2 plan - keep the two hypotheses separate in any report.

Band mapping (matches gee_classify.py / amd_detection_v2.4.0.js):
  Landsat 8:  green=SR_B3, red=SR_B4, NIR=SR_B5
  Sentinel-2: green=B3,    red=B4,    NIR=B8A (S2_MAP in match_scenes.py)

    from water_indices import green_nir_ratio, green_nir_norm, GREEN_NIR_COMPOSITE_BANDS
"""

EPS = 1e-4


def green_nir_ratio(green, nir):
    """Green/NIR. Higher = more paper2-consistent with sulphurous discharge
    on a LAND pixel. On water this is uninformative (near-uniformly high) -
    see module docstring; only meaningful after excluding water pixels."""
    return green / (nir + EPS)


def green_nir_norm(green, nir):
    """Normalised-difference form: (Green-NIR)/(Green+NIR), i.e. an
    'inverse NDVI' shape. Bounded [-1,1] like NDVI/NDWI, which makes it easier
    to compare across scenes than the raw ratio above. Same land-only scoping
    applies."""
    return (green - nir) / (green + nir + EPS)


# For an RGB false-colour product reproducing paper2's fig. 8: green band into
# the RED channel, NIR into GREEN and BLUE. Sulphurous discharge (high green,
# low NIR in truth) then renders reddish/magenta rather than the dark red a
# true-colour or standard CIR composite would show, and normal vegetation
# (low green reflectance, high NIR) renders cyan/blue instead of green -
# maximising the visual contrast paper2 reports. Order matches (R, G, B).
GREEN_NIR_COMPOSITE_BANDS = ("green", "nir", "nir")


def green_nir_ee(ee_image, green_band, nir_band):
    """Earth Engine version: adds GreenNIR and GreenNIRNorm bands to an image
    that already carries `green_band`/`nir_band`. Caller must have already
    excluded water pixels (see module docstring) - this function does not
    apply any water mask itself, so it can be reused for whatever land subset
    a caller defines (shoreline buffer, streambed at low flow, adit outflow
    polygon, ...).
    """
    green = ee_image.select(green_band)
    nir = ee_image.select(nir_band)
    ratio = green.divide(nir.add(EPS)).rename("GreenNIR")
    norm = (green.subtract(nir)).divide(green.add(nir).add(EPS)).rename("GreenNIRNorm")
    return ee_image.addBands([ratio, norm])


def ndvi_stress_ee(ee_image, nir_band, red_band):
    """Standard NDVI, kept here (not in gee_classify.py's NDVI) so Arm C's
    vegetation-stress analysis has one clearly-labelled entry point tied back
    to paper2 sec. 3.2.1 rather than reusing the land-classifier's NDVI band
    for a different purpose without a name change."""
    nir, red = ee_image.select(nir_band), ee_image.select(red_band)
    return nir.subtract(red).divide(nir.add(red).add(EPS)).rename("NDVI_stress")
