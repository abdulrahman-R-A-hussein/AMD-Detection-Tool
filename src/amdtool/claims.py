"""What the numbers license - as data, so every report prints the same words.

Source of truth: validation/STATE.md, validation/DECISION_LOG.md ("Claims: what
may and may not be said") and docs/OPERATOR_GUIDE.md section 6. If those change,
change this file in the same commit.
"""

SULFATE_CAVEAT = (
    "Sulfate has no VNIR absorption. No optical sulfate detection is claimed at "
    "any concentration. Any association is with iron precipitate, turbidity, "
    "vegetation or colour that co-varies with sulfate."
)

EXPLORATORY_NOTICE = (
    "EXPLORATORY - not pre-registered. This run chose its area, grouping and "
    "settings interactively, so its p-values describe this run only. A result "
    "becomes evidence only when the test is written down and committed before "
    "the data are extracted."
)

REFERENCE_STANDARD_NOTICE = (
    "Only measured field chemistry is ground truth here. Agreement with "
    "Rockwell & Gnesda's published map is replica fidelity, not accuracy."
)

# SpectraLab-specific: finding W2 in validation/README.md.
STEPWISE_NOTICE = (
    "SpectraLab stepwise material identifications (for example 'jarosite') are "
    "NOT evidence of mine drainage. Run on reference loadings, stepwise "
    "identification returned Jarosite R-squared 0.96 at the Indian River "
    "Lagoon, a Florida site with no mining (finding W2). Five-band material "
    "identification is a hypothesis generator, not a discriminative test."
)

MAY_CLAIM = (
    "A faithful reimplementation of USGS SIM 3466 at the index level.",
    "The project's three departures from SIM 3466 were regressions; fixing them "
    "improved worst-case cross-site Youden J 4.1x (0.107 to 0.440) against the "
    "published map.",
    "Continuous FerricIron1 separates AMD-affected from chemically verified "
    "clean water at monitored locations, out-of-region across four Colorado "
    "districts, with a score monotone in measured contamination.",
    "FerricIron1 ranks severity within a mineral district: rho +0.568 pooled "
    "against dissolved iron (n=75, Landsat 8); +0.64 to +0.68 in Central City, "
    "Ouray and Silverton, but +0.004 in Leadville (n=23), so not in every district.",
    "In coal watersheds a vegetation index tracks measured sulfate and "
    "conductance negatively, replicating across two independent basins, at a "
    "basin-specific scale.",
)

MAY_NOT_CLAIM = (
    "Detection of mine drainage against clean ground - a measured null at n=86 "
    "confirmed source points (best worst-case J 0.234 against a bar of 0.25).",
    "Prediction of concentration across districts - leave-one-region-out R2 is "
    "negative for every index and analyte.",
    "Finding unknown sources in scene-wide search, unless a pre-registered "
    "blind-search test has measured it.",
    "Optical sulfate detection, at any concentration.",
    "That spatial resolution is the constraint - refuted for 10-100 m.",
    "That the coal-drainage signal is near-channel or seep-scale, or "
    "landscape-scale in general.",
    "That agreement with Rockwell's map means accuracy.",
    "Any cost-saving percentage - none has ever been measured.",
)

VERDICT_TEXT = {
    "SUCCESS": "At least one index is sign-consistent across groups, "
               "BH-corrected q < 0.05, and |rho| >= 0.3.",
    "PARTIAL": "Significant after BH correction, but signs disagree between "
               "groups or |rho| < 0.3 - not a result on its own.",
    "NULL": "No index is significant after BH correction. Reported as "
            "prominently as a success would be.",
    "UNINTERPRETABLE": "Median buffer NDVI is above the canopy limit: the "
                       "buffers are mostly canopy, so a null here is a "
                       "measurement limitation, not evidence.",
    "NO_TESTABLE_PAIRS": "Too few stations with both an index value and "
                         "chemistry to test anything.",
}


def boundaries_markdown(include_stepwise=False):
    """The MAY / MAY NOT block, ready to embed in a report."""
    lines = ["### What this may support", ""]
    lines += ["- %s" % c for c in MAY_CLAIM]
    lines += ["", "### What this may NOT support", ""]
    lines += ["- %s" % c for c in MAY_NOT_CLAIM]
    lines += ["", "> %s" % SULFATE_CAVEAT, "", "> %s" % REFERENCE_STANDARD_NOTICE]
    if include_stepwise:
        lines += ["", "> %s" % STEPWISE_NOTICE]
    return "\n".join(lines)
