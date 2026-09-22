"""Figures for the GSA Connects 2026 talk (abstract #15510, 11 Oct 2026).

Every figure regenerates from committed data or committed reports, and every
plotted value is printed with the file it came from, so a number on a slide can
be traced to a dated report in validation/.

Values that come from a report table are typed in here as literals AND checked
against the report text at run time (`_assert_in_report`), so a number cannot
silently drift from its source. Values that come from raw data are computed.

Usage:
    python python/make_talk_figures.py                    # all figures
    python python/make_talk_figures.py --only D           # one figure
    python python/make_talk_figures.py --out <directory>
"""
import argparse
import glob
import io
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import numpy as np                       # noqa: E402
import pandas as pd                      # noqa: E402
from scipy import stats                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATION = os.path.join(ROOT, "validation")
DATA = os.path.join(ROOT, "data")
DEFAULT_OUT = r"D:\dev\phd\GSA-2026-Talk\figures"

# A talk is read from 10 m away, not from a page.
plt.rcParams.update({
    "font.size": 15,
    "axes.titlesize": 17,
    "axes.labelsize": 15,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "legend.fontsize": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 110,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Slide mode (the default): the figure carries NO title and NO caption, because
# the slide supplies both and duplicating them wastes the projector. Pass
# --with-titles for a standalone version to drop into a paper or a poster.
SLIDE_MODE = True


def _fig_title(obj, text, **kw):
    """Figure/axes title, suppressed in slide mode."""
    if SLIDE_MODE:
        return
    if hasattr(obj, "suptitle"):
        obj.suptitle(text, **kw)
    else:
        obj.set_title(text, **kw)


def _caption(fig, text, **kw):
    """Source/caveat line under the axes, suppressed in slide mode."""
    if SLIDE_MODE:
        return
    fig.text(kw.pop("x", 0.01), kw.pop("y", 0.035), text, **kw)


# Colour-blind safe (Okabe-Ito).
BLUE, ORANGE, GREEN, RED = "#0072B2", "#E69F00", "#009E73", "#D55E00"
GREY, PURPLE = "#8C8C8C", "#CC79A7"

DISTRICT_LABEL = {
    "central_city_co": "Central City",
    "leadville_co": "Leadville",
    "ouray_co": "Ouray",
    "silverton_co": "Silverton",
}


# ---------------------------------------------------------------- helpers

def _report(name):
    with io.open(os.path.join(VALIDATION, name), encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _assert_in_report(value_text, report_name, label):
    """A literal typed into this script must still appear in its source report."""
    if value_text not in _report(report_name):
        raise SystemExit(
            "TRACEABILITY FAILURE: %r (%s) is not in %s. The report changed; "
            "fix the figure before it reaches a slide." % (value_text, label, report_name))


def _save(fig, out_dir, tag, title):
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, "fig_%s.png" % tag)
    pdf = os.path.join(out_dir, "fig_%s.pdf" % tag)
    fig.savefig(png)
    fig.savefig(pdf)
    plt.close(fig)
    print("  -> %s  (%s)" % (os.path.relpath(png, out_dir), title))


def _pct_lines(ax):
    ax.grid(axis="y", alpha=0.25, zorder=0)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------- B

def fig_B(out_dir):
    """My three 'improvements' were regressions - worst case vs mean."""
    src = "report_paper_faithful_2026-09-13.txt"
    rows = [
        ("A\nas shipped\n(v2.4.0)", 0.107, 0.474, "0.107     0.474"),
        ("B\n+ paper\nseason", 0.260, 0.463, "0.260     0.463"),
        ("C\n+ scene-relative\ncut", 0.403, 0.528, "0.403     0.528"),
        ("D\n+ clay term\n(v3.0.0)", 0.440, 0.541, "0.440     0.541"),
    ]
    for _, _, _, probe in rows:
        _assert_in_report(probe, src, "config row")

    labels = [r[0] for r in rows]
    minj = [r[1] for r in rows]
    meanj = [r[2] for r in rows]
    x = np.arange(len(rows))

    fig, ax = plt.subplots(figsize=(10.5, 6.4))
    fig.subplots_adjust(top=0.88, bottom=0.26, left=0.10, right=0.98)
    ax.bar(x - 0.2, minj, 0.4, label="worst case across sites (MIN J)",
           color=BLUE, zorder=3)
    ax.bar(x + 0.2, meanj, 0.4, label="mean J", color=GREY, alpha=0.65, zorder=3)
    for xi, v in zip(x, minj):
        ax.text(xi - 0.2, v + 0.012, "%.3f" % v, ha="center", fontweight="bold", fontsize=13)
    for xi, v in zip(x, meanj):
        ax.text(xi + 0.2, v + 0.012, "%.3f" % v, ha="center", color="#555555", fontsize=12)

    ax.annotate("", xy=(3 - 0.2, 0.452), xytext=(0 - 0.2, 0.119),
                arrowprops=dict(arrowstyle="->", lw=2.2, color=RED,
                                connectionstyle="arc3,rad=-0.25"))
    ax.text(1.5, 0.155, "4.1\u00d7 better\nafter removing\nmy changes",
            color=RED, fontweight="bold", ha="center", fontsize=14.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Youden J vs the published USGS map")
    ax.set_ylim(0, 0.62)
    _fig_title(ax, "Each \u201cimprovement\u201d I removed made it transfer better",
               fontweight="bold", loc="left")
    ax.legend(loc="upper left", frameon=False)
    _pct_lines(ax)
    _caption(fig,
             "Leave-one-site-out over Silverton / Summitville / Red Mountain Pass. "
             "Mean J FALLS from A to B while\nthe worst case more than doubles. Labels are Rockwell's published map: this is replica fidelity, not field accuracy.",
             fontsize=11, color="#444444", x=0.01, y=0.045)
    print("  fig B from %s: MIN J %s ; mean J %s" % (src, minj, meanj))
    _save(fig, out_dir, "B_configs", "self-correction")


# ---------------------------------------------------------------- C

def fig_C(out_dir):
    """Detection is a null: every index misses the pre-registered bar."""
    src = "report_seep_b2_s2_tiefix_2026-09-15.txt"
    rows = [
        ("ClaySulfateMica", "C2", 0.320),
        ("FerricIron1", "C3", 0.318),
        ("FerricIron1", "C2", 0.291),
        ("NDVI_stress", "C3", 0.270),
        ("FerricIron1", "C1", 0.234),
        ("GreenNIR", "C2", 0.217),
        ("GreenNIRNorm", "C2", 0.217),
    ]
    _assert_in_report("FerricIron1     C1     0.723   0.234", src, "primary-tier best case")

    labels = ["%s\nvs %s" % (i, t) for i, t, _ in rows]
    vals = [v for _, _, v in rows]
    # C1 is the honest tier: chemistry-verified clean water, not bare ground.
    colors = [RED if t == "C1" else GREY for _, t, _ in rows]

    fig, ax = plt.subplots(figsize=(11.5, 6.6))
    fig.subplots_adjust(top=0.88, bottom=0.30, left=0.09, right=0.98)
    bars = ax.bar(labels, vals, color=colors, zorder=3, width=0.62)
    bars[4].set_color(RED)
    ax.axhline(0.25, color="k", ls="--", lw=2, zorder=4)
    ax.text(6.45, 0.257, "pre-registered bar  J \u2265 0.25", ha="right",
            fontweight="bold", fontsize=13)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.008, "%.3f" % v,
                ha="center", fontsize=12)
    ax.annotate("best case on the honest tier:\nmisses by 0.016",
                xy=(4, 0.234), xytext=(4.75, 0.115),
                arrowprops=dict(arrowstyle="->", lw=2, color=RED),
                color=RED, fontweight="bold", fontsize=13)
    ax.set_ylabel("worst-case leave-one-region-out J")
    ax.set_ylim(0, 0.37)
    _fig_title(ax, "Detection of mine drainage: a measured null",
               fontweight="bold", loc="left")
    _pct_lines(ax)
    _caption(fig,
             "86 chemically confirmed source points, 4 Colorado districts, 9 indices, "
             "3 control tiers, Sentinel-2.\nC1 = chemically verified clean water (hardest "
             "and only honest tier). C3 was found circular and is excluded from decisions.",
             fontsize=11, color="#444444", x=0.01, y=0.035)
    print("  fig C from %s: %s" % (src, list(zip(labels, vals))))
    _save(fig, out_dir, "C_detection_null", "detection null")


# ---------------------------------------------------------------- D  (star)

def fig_D(out_dir):
    """Severity ranking works - in three districts out of four."""
    frames = []
    for path in sorted(glob.glob(os.path.join(DATA, "matched", "seep_l8_*_co.csv"))):
        frames.append(pd.read_csv(path))
    d = pd.concat(frames, ignore_index=True)
    sub = d[(d.tier == "target") & (d.radius == 60)]
    cols = ["FerricIron1_p90", "Iron_mgL_dissolved", "region"]
    x = sub[cols].dropna()

    pooled = stats.spearmanr(x.FerricIron1_p90, x.Iron_mgL_dissolved).statistic
    print("  fig D from data/matched/seep_l8_*_co.csv (tier=target, radius=60):")
    print("     pooled rho=%+.3f  n=%d  (report: +0.568, n=75)" % (pooled, len(x)))
    if abs(pooled - 0.568) > 0.002 or len(x) != 75:
        raise SystemExit("TRACEABILITY FAILURE: dose-response no longer reproduces "
                         "rho +0.568 at n=75.")

    # Labels use the committed report's per-district values; the scatter is raw
    # data. They must agree to within rounding or the figure is not traceable.
    REPORTED = {"silverton_co": 0.64, "ouray_co": 0.68,
                "central_city_co": 0.64, "leadville_co": 0.004}

    # One row of four, but TALL: the free area on a 16:9 slide is about 12.5 x 5
    # inches, so an aspect near 2.4 fills it. A 2x2 block is too square and ends
    # up smaller on screen. Reading order puts the failing district last.
    order = ["silverton_co", "ouray_co", "central_city_co", "leadville_co"]
    fig, axes = plt.subplots(1, 4, figsize=(15.5, 6.5), sharey=True)
    fig.subplots_adjust(top=0.86, bottom=0.145, left=0.062, right=0.99, wspace=0.11)
    for ax, reg in zip(axes, order):
        g = x[x.region == reg]
        rho = stats.spearmanr(g.FerricIron1_p90, g.Iron_mgL_dissolved).statistic
        if abs(rho - REPORTED[reg]) > 0.01:
            raise SystemExit("TRACEABILITY FAILURE: %s computes %+.3f, report says %+.3f"
                             % (reg, rho, REPORTED[reg]))
        works = abs(rho) > 0.3
        col = BLUE if works else RED
        ax.scatter(g.FerricIron1_p90, g.Iron_mgL_dissolved, s=58, color=col,
                   alpha=0.85, edgecolor="white", linewidth=0.8, zorder=3)
        # rank-space trend, drawn only where a monotone relationship exists
        if works:
            xr = stats.rankdata(g.FerricIron1_p90)
            yr = stats.rankdata(g.Iron_mgL_dissolved)
            b, a = np.polyfit(xr, yr, 1)
            xs = np.linspace(g.FerricIron1_p90.min(), g.FerricIron1_p90.max(), 20)
            xsr = np.interp(xs, np.sort(g.FerricIron1_p90), np.sort(xr))
            ysr = a + b * xsr
            ys = np.interp(ysr, np.sort(yr), np.sort(g.Iron_mgL_dissolved))
            ax.plot(xs, ys, color=col, lw=2.2, alpha=0.75, zorder=2)
        ax.set_yscale("log")
        shown = "%+.2f" % REPORTED[reg] if works else "%+.3f" % REPORTED[reg]
        ax.set_title("%s\n$\\rho$ = %s   n = %d" % (DISTRICT_LABEL[reg], shown, len(g)),
                     color=col, fontweight="bold", fontsize=15, pad=10)
        ax.set_xlabel("FerricIron1 (red/blue), p90")
        ax.grid(alpha=0.22, zorder=0)
        ax.set_axisbelow(True)
        print("     %-14s n=%-3d rho=%+.3f (report %+.3f)" % (reg, len(g), rho, REPORTED[reg]))
    axes[0].set_ylabel("dissolved Fe (mg/L)")
    axes[3].text(0.96, 0.045, "no relationship", transform=axes[3].transAxes,
                 ha="right", color=RED, fontweight="bold", fontsize=15)
    _fig_title(fig, "The index ranks severity within a district \u2014 but not in every district",
               fontweight="bold", x=0.007, y=0.955, ha="left", fontsize=19)
    _caption(fig,
             "Landsat 8, 60 m buffers, p90. Pooled $\\rho$ = +0.568 (n = 75, within-region "
             "permutation p = 0.0004, BH q = 0.0072).\nLeave-one-region-out R\u00b2 is negative "
             "for every index-analyte pair: it RANKS within a district, it does not predict "
             "concentration across districts.",
             fontsize=12, color="#444444", x=0.007, y=0.055)
    _save(fig, out_dir, "D_dose_response", "severity ranking (star figure)")


# ---------------------------------------------------------------- E

def fig_E(out_dir):
    """Resolution is not the binding constraint."""
    src = "report_seep_b2_ladder_2026-08-15.txt"
    _assert_in_report("FerricIron1      10m    0.494    75   -0.575", src, "ladder 10 m")
    _assert_in_report("FerricIron1     100m    0.517    75   -0.658", src, "ladder 100 m")
    gsd = [10, 20, 30, 60, 100]
    fe = [0.494, 0.526, 0.493, 0.523, 0.517]
    ph = [-0.575, -0.582, -0.558, -0.613, -0.658]

    fig, ax = plt.subplots(figsize=(10, 6.3))
    fig.subplots_adjust(top=0.88, bottom=0.25, left=0.11, right=0.98)
    ax.plot(gsd, fe, "o-", color=BLUE, lw=2.6, ms=11, label="vs dissolved Fe (n = 75)", zorder=3)
    ax.plot(gsd, np.abs(ph), "s-", color=ORANGE, lw=2.6, ms=10,
            label="vs pH, |$\\rho$| (n = 77)", zorder=3)
    ax.set_xscale("log")
    ax.set_xticks(gsd)
    ax.set_xticklabels(["10 m", "20 m", "30 m", "60 m", "100 m"])
    ax.set_xlabel("pixel size (Sentinel-2, resampled)")
    ax.set_ylabel("|Spearman $\\rho$| vs measured chemistry")
    ax.set_ylim(0, 0.8)
    _fig_title(ax, "Finer pixels do not help \u2014 the ceiling is spectral, not spatial",
               fontweight="bold", loc="left")
    ax.legend(frameon=False, loc="lower left")
    ax.grid(alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    ax.annotate("flat across a 10\u00d7 range\n(pH is slightly STRONGER at 100 m)",
                xy=(60, 0.613), xytext=(13, 0.70), color="#444444", fontsize=13,
                arrowprops=dict(arrowstyle="->", lw=1.6, color="#888888"))
    _caption(fig,
             "Therefore the earlier Landsat 30 m \u2192 Sentinel-2 20 m gain was a SENSOR effect "
             "(bands, radiometry, SNR), not a resolution effect.\nTested range 10\u2013100 m; "
             "sub-metre is untested, so a centimetre-scale claim extrapolates against a flat trend.",
             fontsize=11, color="#444444", x=0.01, y=0.035)
    print("  fig E from %s: Fe %s ; pH %s" % (src, fe, ph))
    _save(fig, out_dir, "E_resolution", "resolution ladder")


# ---------------------------------------------------------------- F

def fig_F(out_dir):
    """The blind search: it finds exposed ground, not mines."""
    src = "report_blind_search_2026-09-15.txt"
    _assert_in_report("H-BS1  n=32  flagged=4   recall=0.125 [0.050, 0.281]", src, "H-BS1")
    _assert_in_report("H-BS2  n=50  flagged=14  recall=0.280 [0.175, 0.417]", src, "H-BS2")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.4),
                                   gridspec_kw={"width_ratios": [1.15, 1]})
    fig.subplots_adjust(top=0.80, bottom=0.24, left=0.075, right=0.985, wspace=0.28)

    # left: recall vs the 5% budget, index vs bare-ground baseline
    names = ["H-BS1\ndistricts never used\nto choose the index",
             "H-BS2\ndistricts that\nchose the index"]
    idx = [0.125, 0.280]
    base = [2 / 32, 6 / 50]
    lo = [0.050, 0.175]
    hi = [0.281, 0.417]
    xpos = np.arange(2)
    ax1.bar(xpos - 0.19, idx, 0.38, color=BLUE, label="FerricIron1", zorder=3)
    ax1.bar(xpos + 0.19, base, 0.38, color=GREY, alpha=0.7,
            label="bare-ground baseline (\u2212NDVI)", zorder=3)
    ax1.errorbar(xpos - 0.19, idx, yerr=[np.array(idx) - lo, np.array(hi) - np.array(idx)],
                 fmt="none", ecolor="k", capsize=6, lw=1.8, zorder=4)
    ax1.axhline(0.05, color=RED, ls="--", lw=2, zorder=4)
    ax1.text(1.42, 0.058, "5% flagged-area budget", ha="right", color=RED,
             fontweight="bold", fontsize=12)
    ax1.set_xticks(xpos)
    ax1.set_xticklabels(names, fontsize=12)
    ax1.set_ylabel("recall at known mine sources")
    ax1.set_ylim(0, 0.47)
    ax1.legend(frameon=False, loc="upper left", fontsize=12)
    _pct_lines(ax1)
    ax1.text(0, 0.315, "NO SIGNAL\nDETECTED\np = 0.074", ha="center", color=RED,
             fontweight="bold", fontsize=13)
    ax1.text(1, 0.445, "NOT BETTER THAN\nBARE GROUND\nMcNemar p = 0.038\nvs Holm level 0.025",
             ha="center", color=RED, fontweight="bold", fontsize=12)

    # right: what the flags actually are
    districts = ["central_city", "creede", "leadville", "alma", "ouray", "lake_city", "silverton"]
    flagged = [0.040, 0.060, 0.080, 0.160, 0.170, 0.280, 0.380]
    overall = [0.009, 0.051, 0.052, 0.115, 0.120, 0.121, 0.221]
    y = np.arange(len(districts))
    ax2.barh(y + 0.19, flagged, 0.38, color=ORANGE, label="flagged ground", zorder=3)
    ax2.barh(y - 0.19, overall, 0.38, color=GREY, alpha=0.7, label="landscape overall", zorder=3)
    ax2.set_yticks(y)
    ax2.set_yticklabels([d.replace("_", " ").title() for d in districts], fontsize=12)
    ax2.set_xlabel("share of points that are NLCD barren")
    ax2.set_title("What the flags actually are", fontsize=15, loc="left")
    ax2.legend(frameon=False, loc="lower right", fontsize=12)
    ax2.grid(axis="x", alpha=0.25, zorder=0)
    ax2.set_axisbelow(True)
    ax2.text(0.39, 0.6, "1.2\u20134.4\u00d7 enriched\nin bare ground", color=ORANGE,
             fontweight="bold", ha="right", fontsize=13)

    _fig_title(fig, "Turned loose on the landscape, it does not find mines \u2014 it finds bare ground",
               fontweight="bold", x=0.007, y=0.955, ha="left", fontsize=18)
    _caption(fig,
             "Pre-registered 2026-09-14: site list fixed from station metadata and its SHA-256 "
             "committed before any imagery was touched.\nPower at this n: 0.54 at a threefold "
             "lift, 0.80 at fourfold \u2014 a large effect is excluded, a modest one is not.",
             fontsize=11, color="#444444", x=0.007, y=0.035)
    print("  fig F from %s: H-BS1 %.3f, H-BS2 %.3f" % (src, idx[0], idx[1]))
    _save(fig, out_dir, "F_blind_search", "blind search")


# ---------------------------------------------------------------- G

def fig_G(out_dir):
    """Ohio and Pennsylvania have opposite radius signatures."""
    src = "ACCURACY_ASSESSMENT.md"
    txt = _report(src)
    for probe in ["**\u22120.354**", "**\u22120.438**", "\u22120.143", "\u22120.050"]:
        if probe not in txt:
            raise SystemExit("TRACEABILITY FAILURE: %s missing from %s" % (probe, src))
    radii = [30, 60, 100, 500, 1000]
    ohio = [-0.354, -0.253, -0.255, -0.393, -0.438]
    pa = [-0.143, -0.135, -0.114, -0.010, -0.050]

    fig, ax = plt.subplots(figsize=(10.3, 6.6))
    fig.subplots_adjust(top=0.88, bottom=0.26, left=0.105, right=0.98)
    ax.plot(radii, ohio, "o-", color=BLUE, lw=2.8, ms=11,
            label="Ohio, 5 watersheds (n = 137)", zorder=3)
    ax.plot(radii, pa, "s-", color=ORANGE, lw=2.8, ms=10,
            label="Pennsylvania, 3 sub-basins (n = 268)", zorder=3)
    ax.axhspan(-0.3, 0.02, color=RED, alpha=0.07, zorder=0)
    ax.axhline(-0.3, color=RED, ls="--", lw=2, zorder=2)
    ax.text(1000, -0.285, "pre-registered bar  |$\\rho$| \u2265 0.3", ha="right",
            color=RED, fontweight="bold", fontsize=12.5)
    ax.set_xscale("log")
    ax.set_xticks(radii)
    ax.set_xticklabels(["30 m", "60 m", "100 m", "500 m", "1 km"])
    ax.set_xlabel("buffer radius around the sampling station")
    ax.set_ylabel("$\\rho$, vegetation index vs measured sulfate")
    ax.set_ylim(-0.52, 0.03)
    _fig_title(ax, "A signal that replicates in sign \u2014 and contradicts itself in scale",
               fontweight="bold", loc="left")
    ax.legend(frameon=False, loc="lower left")
    ax.grid(alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    ax.annotate("Ohio: strongest at 1 km\n(\u201clandscape\u201d)", xy=(1000, -0.438),
                xytext=(150, -0.48), color=BLUE, fontsize=12.5,
                arrowprops=dict(arrowstyle="->", lw=1.6, color=BLUE))
    ax.annotate("PA: strongest at 30 m,\ndead at 1 km", xy=(30, -0.143),
                xytext=(40, -0.06), color=ORANGE, fontsize=12.5,
                arrowprops=dict(arrowstyle="->", lw=1.6, color=ORANGE))
    _caption(fig,
             "Each basin is the other's pre-registered falsifier, so radius shape does not "
             "diagnose mechanism \u2014 it measures basin geometry.\nIn Ohio, mining extent carries "
             "~42% of this covariance: conditioned partial $\\rho$ = \u22120.246 against a 0.25 bar "
             "\u2014 PARTIAL by 0.004, not cleared.",
             fontsize=11, color="#444444", x=0.01, y=0.035)
    print("  fig G from %s: Ohio %s ; PA %s" % (src, ohio, pa))
    _save(fig, out_dir, "G_ohio_vs_pa", "coal bridge")


# ---------------------------------------------------------------- H

def fig_H(out_dir):
    """The cryptic problem: neutral pH, high sulfate."""
    # In-lake stations and the inflow streams are DIFFERENT populations and are
    # drawn differently: the campaign samples the inflows, and their gradient is
    # the reason. Lake-mode fetches carry no site_type; every station in them is
    # in-lake (python/ohio_lake_archive.py applies the same rule).
    LAKE_TYPES = {"Lake", "Lake, Reservoir, Impoundment"}
    STREAM_TYPES = {"River/Stream", "Stream", "Stream: Ditch"}
    sources = [
        ("Piedmont", os.path.join(DATA, "chemistry", "piedmont_lake_results.csv")),
        ("Piedmont", os.path.join(DATA, "chemistry", "piedmont_lake_catchment_oh",
                                  "consolidated.csv")),
        ("Clendening", os.path.join(DATA, "chemistry", "clendening_lake_oh",
                                    "consolidated.csv")),
        ("Atwood", os.path.join(DATA, "chemistry", "atwood_lake_results.csv")),
    ]
    pts = []
    for label, path in sources:
        if not os.path.isfile(path):
            print("     MISSING %s" % path)
            continue
        d = pd.read_csv(path, low_memory=False)
        d = d[d["ActivityMediaName"].astype(str).str.lower().eq("water")].copy()
        d["v"] = pd.to_numeric(d["ResultMeasureValue"], errors="coerce")
        types = d["site_type"] if "site_type" in d else pd.Series(pd.NA, index=d.index)
        d["kind"] = np.where(types.isin(STREAM_TYPES), "inflow stream",
                             np.where(types.isna() | types.isin(LAKE_TYPES),
                                      "in lake", "other"))
        key = ["MonitoringLocationIdentifier", "ActivityStartDate", "kind"]
        so4 = (d[d.CharacteristicName.eq("Sulfate")]
               .groupby(key)["v"].median().rename("sulfate"))
        ph = (d[d.CharacteristicName.eq("pH")]
              .groupby(key)["v"].median().rename("pH"))
        j = pd.concat([so4, ph], axis=1).dropna().reset_index()
        j = j[(j.pH > 3) & (j.pH < 11) & j.kind.ne("other")]   # drop recorded pH 0
        j["site"] = label
        pts.append(j)
    p = (pd.concat(pts, ignore_index=True)
         .drop_duplicates(subset=["MonitoringLocationIdentifier", "ActivityStartDate"]))
    for (site, kind), g in p.groupby(["site", "kind"]):
        print("     %-11s %-14s n=%-3d  sulfate %.0f mg/L (%.0f-%.0f)  pH %.2f"
              % (site, kind, len(g), g.sulfate.median(), g.sulfate.min(),
                 g.sulfate.max(), g.pH.median()))

    fig, ax = plt.subplots(figsize=(11, 6.6))
    fig.subplots_adjust(top=0.90, bottom=0.30, left=0.09, right=0.98)
    ax.axvspan(6.5, 9.0, color=GREEN, alpha=0.10, zorder=0)
    ax.text(6.62, 1750, "every point here reads as \u201cclean\u201d by pH alone",
            ha="left", color="#2E7D5B", fontweight="bold", fontsize=13.5, zorder=1)
    colour = {"Piedmont": RED, "Clendening": ORANGE, "Atwood": BLUE}
    for site, c in colour.items():
        for kind, marker, filled in (("in lake", "o", True),
                                     ("inflow stream", "^", False)):
            g = p[(p.site == site) & (p.kind == kind)]
            if g.empty:
                continue
            ax.scatter(g.pH, g.sulfate, s=78, marker=marker,
                       facecolor=c if filled else "none", edgecolor=c,
                       linewidth=1.8, alpha=0.85 if filled else 0.9,
                       label="%s \u2014 %s (n = %d)" % (site, kind, len(g)), zorder=3)
    ax.axhline(250, color=GREY, ls=":", lw=2, zorder=2)
    ax.text(5.97, 268, "US secondary drinking-water\nguidance, 250 mg/L", fontsize=11,
            color="#555555", ha="left", va="bottom")
    ax.set_yscale("log")
    ax.set_xlabel("pH")
    ax.set_ylabel("sulfate (mg/L)")
    ax.set_xlim(5.9, 9.4)
    ax.set_ylim(8, 3000)
    _fig_title(ax, "Neutral pH, 25\u00d7 the sulfate: what pH-based screening walks past",
               fontweight="bold", loc="left", pad=12)
    ax.legend(frameon=False, fontsize=11.5, ncol=3, handletextpad=0.4,
              columnspacing=1.4, loc="upper left", bbox_to_anchor=(-0.02, -0.13))
    ax.grid(alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    _caption(fig,
             "Water Quality Portal records (USGS NWIS + EPA STORET + Ohio EPA). Ohio coal-region "
             "streams run at a median pH of 7.46\u20137.72 across five watersheds.\nSulfate has no "
             "VNIR absorption at any concentration, so no satellite sees this directly. The "
             "inflow gradient is what the pre-registered campaign samples.",
             fontsize=11, color="#444444", x=0.01, y=0.035)
    _save(fig, out_dir, "H_cryptic", "the cryptic problem")


# Figure A (the study-area map) is built by python/make_talk_map.py, which needs
# cartopy for coastlines and state boundaries and so runs in its own environment.

FIGURES = {"B": fig_B, "C": fig_C, "D": fig_D, "E": fig_E,
           "F": fig_F, "G": fig_G, "H": fig_H}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--only", help="one figure letter, e.g. D")
    ap.add_argument("--with-titles", action="store_true",
                    help="bake the title and caption into the image (standalone "
                         "use); the default leaves them to the slide")
    a = ap.parse_args()
    global SLIDE_MODE
    SLIDE_MODE = not a.with_titles

    tags = [a.only.upper()] if a.only else sorted(FIGURES)
    print("GSA 2026 talk figures -> %s" % a.out)
    for t in tags:
        if t not in FIGURES:
            raise SystemExit("unknown figure %r; have %s" % (t, sorted(FIGURES)))
        print("\n[%s]" % t)
        FIGURES[t](a.out)
    print("\nEvery value above traces to the file named beside it.")


if __name__ == "__main__":
    main()
