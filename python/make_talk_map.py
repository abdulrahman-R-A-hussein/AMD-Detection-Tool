"""Figure A for the GSA 2026 talk: where every number in the talk comes from.

Two panels, because the talk has two terrains and they behave differently:

  left   Colorado mineral districts - open alpine terrain, where detection was
         tested (4 districts, 86 source points) and where the blind search added
         three districts the index had never seen.
  right  Appalachian coal - Ohio and Pennsylvania basins where the method does
         NOT transfer, plus the three Ohio lakes the pre-registered campaign
         will sample.

Boundaries come from cartopy's Natural Earth data if cartopy is importable, and
are simply omitted if it is not: the boxes and points are the content, and a
missing coastline must never silently move a study area.

Usage:
    uv run --with cartopy --with matplotlib --with numpy python python/make_talk_map.py
    python python/make_talk_map.py            # runs without boundaries
"""
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.patches import Rectangle              # noqa: E402
from matplotlib.lines import Line2D                   # noqa: E402
import matplotlib.patheffects as pe                   # noqa: E402


def _halo(lw=3.2):
    """White outline so a label stays readable over a boundary or a box."""
    return [pe.withStroke(linewidth=lw, foreground="white")]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from amdtool.regions import REGIONS                   # noqa: E402

DEFAULT_OUT = r"D:\dev\phd\GSA-2026-Talk\figures"

BLUE, ORANGE, GREEN, RED = "#0072B2", "#E69F00", "#009E73", "#D55E00"
GREY = "#8C8C8C"

plt.rcParams.update({
    "font.size": 14, "axes.labelsize": 14, "xtick.labelsize": 12,
    "ytick.labelsize": 12, "savefig.dpi": 300, "savefig.bbox": "tight",
})

# Districts carrying the validated result vs districts added only by the
# blind search (they had never been used to choose the index).
VALIDATED_CO = ["Silverton, CO", "Ouray, CO", "Leadville, CO", "Central City, CO"]
BLIND_ONLY_CO = ["Alma, CO", "Creede, CO", "Lake City, CO"]
COAL_OH = ["Huff Run, OH", "Leading Creek, OH", "Monday Creek, OH",
           "Raccoon Creek, OH", "Sunday Creek, OH"]
# PA tiles live in the data/regions.json overlay; hard-coded here so the figure
# does not depend on a gitignored file.
COAL_PA = {
    "Chest Creek, PA": (40.55, -78.85, 40.95, -78.63),
    "Clearfield Creek, PA": (40.50, -78.62, 41.05, -78.32),
    "Moshannon Creek, PA": (40.78, -78.32, 41.18, -77.95),
}
# The campaign lakes (python/fetch_wqp.py LAKES; Clendening from its overlay bbox).
LAKES = {
    "Piedmont": (40.1540, -81.2220),
    "Clendening": (40.2686, -81.2767),
    "Atwood": (40.5496, -81.2462),
}
# Silverton/Ouray and Leadville/Alma are adjacent, so their labels are pushed
# apart by hand: (dx, dy) in points, with the alignment that goes with them.
LABEL_OFFSET = {
    "Silverton, CO": ((0, -20), "center", "top"),
    "Ouray, CO": ((-10, 6), "right", "center"),
    "Leadville, CO": ((-10, 2), "right", "center"),
    "Central City, CO": ((0, 14), "center", "bottom"),
    "Alma, CO": ((10, 2), "left", "center"),
    "Creede, CO": ((0, -16), "center", "top"),
    "Lake City, CO": ((0, 13), "center", "bottom"),
}


def _box(ax, bbox, color, lw=2.2, fill=False, alpha=0.18, ls="-", zorder=5):
    lat_lo, lon_lo, lat_hi, lon_hi = bbox[:4]
    if fill:
        ax.add_patch(Rectangle((lon_lo, lat_lo), lon_hi - lon_lo, lat_hi - lat_lo,
                               facecolor=color, alpha=alpha, edgecolor="none", zorder=zorder - 1))
    ax.add_patch(Rectangle((lon_lo, lat_lo), lon_hi - lon_lo, lat_hi - lat_lo,
                           facecolor="none", edgecolor=color, lw=lw, ls=ls, zorder=zorder))
    return (lon_lo + lon_hi) / 2, (lat_lo + lat_hi) / 2


def _boundaries(ax, extent):
    """State and coastline boundaries, if cartopy is available. Never required."""
    try:
        import cartopy.feature as cfeature
        from cartopy.mpl.geoaxes import GeoAxes
    except Exception:
        return False
    if not isinstance(ax, GeoAxes):
        return False
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor="#9AA5B1", lw=1.0, zorder=1)
    ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#F6F4F1", zorder=0)
    ax.add_feature(cfeature.LAKES.with_scale("50m"), facecolor="#D8E8F2", zorder=1)
    ax.add_feature(cfeature.RIVERS.with_scale("50m"), edgecolor="#BBD4E6", lw=0.8, zorder=1)
    return True


def build(out_dir, use_cartopy=True):
    proj = None
    if use_cartopy:
        try:
            import cartopy.crs as ccrs
            proj = ccrs.PlateCarree()
        except Exception as exc:
            print("  cartopy unavailable (%s) - drawing without boundaries" % exc)

    kw = {"subplot_kw": {"projection": proj}} if proj is not None else {}
    fig, (axc, axe) = plt.subplots(1, 2, figsize=(15, 6.6), **kw)
    fig.subplots_adjust(top=0.88, bottom=0.14, left=0.05, right=0.98, wspace=0.14)

    # ---------------------------------------------------------- Colorado
    axc.set_extent([-108.3, -105.1, 37.5, 40.1]) if proj is not None else None
    axc.set_xlim(-108.3, -105.1)
    axc.set_ylim(37.5, 40.1)
    _boundaries(axc, None)
    for name in VALIDATED_CO:
        cx, cy = _box(axc, REGIONS[name], BLUE, fill=True)
        off, ha, va = LABEL_OFFSET[name]
        axc.annotate(name.split(",")[0], (cx, cy), xytext=off,
                     textcoords="offset points", ha=ha, va=va, fontsize=13.5,
                     fontweight="bold", color=BLUE, zorder=7, path_effects=_halo())
    for name in BLIND_ONLY_CO:
        cx, cy = _box(axc, REGIONS[name], GREY, lw=1.8, ls=(0, (4, 2)))
        off, ha, va = LABEL_OFFSET[name]
        axc.annotate(name.split(",")[0], (cx, cy), xytext=off,
                     textcoords="offset points", ha=ha, va=va, fontsize=12,
                     color="#5F5F5F", zorder=7, path_effects=_halo())
    axc.text(-105.35, 37.62, "COLORADO", ha="right", fontsize=12.5,
             color="#7A828A", fontweight="bold", zorder=6)
    axc.set_title("Colorado — open alpine terrain\nwhere the method works",
                  fontsize=16, fontweight="bold", color=BLUE, loc="left", pad=10)

    # ---------------------------------------------------------- Appalachia
    axe.set_extent([-83.0, -77.6, 38.6, 41.4]) if proj is not None else None
    axe.set_xlim(-83.0, -77.6)
    axe.set_ylim(38.6, 41.4)
    _boundaries(axe, None)
    for name in COAL_OH:
        cx, cy = _box(axe, REGIONS[name], ORANGE, fill=True, lw=2.0)
    for name, bbox in COAL_PA.items():
        cx, cy = _box(axe, bbox, ORANGE, fill=True, lw=2.0)
    for abbr, lon, lat in (("OHIO", -82.55, 40.75), ("W. VA.", -80.35, 39.05)):
        axe.text(lon, lat, abbr, ha="center", fontsize=12.5, color="#7A828A",
                 fontweight="bold", zorder=6)
    axe.annotate("Ohio coal basins\n(5 watersheds)", (-81.76, 38.82), xytext=(0, 0),
                 textcoords="offset points", ha="left", va="center", fontsize=13,
                 fontweight="bold", color="#B07800", zorder=7, path_effects=_halo())
    axe.annotate("Pennsylvania\n(3 sub-basins)", (-78.45, 41.15), xytext=(0, 8),
                 textcoords="offset points", ha="center", va="bottom", fontsize=13,
                 fontweight="bold", color="#B07800", zorder=7, path_effects=_halo())
    for label, (lat, lon) in LAKES.items():
        axe.plot(lon, lat, marker="*", ms=23, color=RED, mec="white", mew=1.5, zorder=8)
    axe.annotate("Piedmont · Clendening · Atwood\nthe pre-registered campaign",
                 (-81.20, 40.27), xytext=(-82.93, 39.72), textcoords="data",
                 ha="left", va="center", fontsize=13, fontweight="bold", color=RED,
                 zorder=9, path_effects=_halo(),
                 arrowprops=dict(arrowstyle="->", lw=2.0, color=RED,
                                 connectionstyle="arc3,rad=-0.2"))
    axe.set_title("Appalachian coal — forested, neutral pH\nwhere it does not transfer",
                  fontsize=16, fontweight="bold", color="#B07800", loc="left", pad=10)

    for ax in (axc, axe):
        if proj is not None:
            gl = ax.gridlines(draw_labels=True, lw=0.6, color="#C9CDD2",
                              alpha=0.7, linestyle=":")
            gl.top_labels = gl.right_labels = False
            gl.xlabel_style = gl.ylabel_style = {"size": 11, "color": "#5F5F5F"}
        else:
            ax.grid(alpha=0.22, zorder=0)
            ax.set_axisbelow(True)
            ax.set_xlabel("longitude")
            ax.set_ylabel("latitude")

    handles = [
        Rectangle((0, 0), 1, 1, facecolor=BLUE, alpha=0.3, edgecolor=BLUE, lw=2,
                  label="districts carrying the validated result (86 source points)"),
        Rectangle((0, 0), 1, 1, facecolor="none", edgecolor=GREY, lw=1.8, ls=(0, (4, 2)),
                  label="districts the index had never seen (blind search)"),
        Rectangle((0, 0), 1, 1, facecolor=ORANGE, alpha=0.3, edgecolor=ORANGE, lw=2,
                  label="coal basins: signal replicates in sign, not in scale"),
        Line2D([0], [0], marker="*", ms=17, color=RED, ls="none", mec="white",
               label="Ohio lakes: the next campaign"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               fontsize=12.5, bbox_to_anchor=(0.5, -0.01))
    # No figure-level title: the slide supplies it (see make_talk_figures.py,
    # SLIDE_MODE). The two panel titles stay - they are panel labels, not a title.

    os.makedirs(out_dir, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(out_dir, "fig_A_study_areas.%s" % ext))
    plt.close(fig)
    print("  -> fig_A_study_areas.png  (study areas; cartopy=%s)" % (proj is not None))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--no-cartopy", action="store_true")
    a = ap.parse_args()
    build(a.out, use_cartopy=not a.no_cartopy)


if __name__ == "__main__":
    main()
