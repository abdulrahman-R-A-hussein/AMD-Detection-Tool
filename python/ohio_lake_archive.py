"""Archival chemistry for the Ohio field lakes, as seen before the field registration.

validation/FIELD_CAMPAIGN_PREREGISTRATION_2026-09-19.md discloses what the
author had seen before fixing the campaign: this script prints it, so the
disclosure can be regenerated rather than trusted.

Sources (all Water Quality Portal, fetched with python/fetch_wqp.py):
  Piedmont Lake (lake stations)  data/chemistry/piedmont_lake_results.csv
  Piedmont Lake catchment        data/chemistry/piedmont_lake_catchment_oh/
      --region "Piedmont Lake catchment, OH" --bbox "40.06,-81.32,40.225,-81.10"
  Clendening Lake + catchment    data/chemistry/clendening_lake_oh/
      --region "Clendening Lake, OH" --bbox "40.225,-81.30,40.32,-81.10"
  Atwood Lake (lake stations)    data/chemistry/atwood_lake_results.csv

Rules, from the water arm's findings:
  * Iron fractions are never pooled (finding W4): Dissolved, Total and Total
    Recoverable are printed separately.
  * Lake and stream stations are printed separately: the lake water column is
    a measured null (Water Phase 2, B1); the inflow streams are what the
    campaign samples.

Usage:
    python python/ohio_lake_archive.py
"""
import argparse
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEM = os.path.join(ROOT, "data", "chemistry")

SOURCES = (
    ("Piedmont Lake", os.path.join(CHEM, "piedmont_lake_results.csv")),
    ("Piedmont Lake catchment", os.path.join(CHEM, "piedmont_lake_catchment_oh", "consolidated.csv")),
    ("Clendening Lake + catchment", os.path.join(CHEM, "clendening_lake_oh", "consolidated.csv")),
    ("Atwood Lake", os.path.join(CHEM, "atwood_lake_results.csv")),
)

# WQP MonitoringLocationTypeName values, grouped. Lake-mode fetches carry no
# site_type column; every station in them is an in-lake station.
LAKE_TYPES = {"Lake", "Lake, Reservoir, Impoundment"}
STREAM_TYPES = {"River/Stream", "Stream", "Stream: Ditch"}

ANALYTES = (
    ("Sulfate", None),
    ("Specific conductance", None),
    ("pH", None),
    ("Iron", "Dissolved"),
    ("Iron", "Total"),
    ("Iron", "Total Recoverable"),
    ("Manganese", "Dissolved"),
    ("Turbidity", None),
)


def site_class(site_type):
    if pd.isna(site_type):
        return "lake"
    if site_type in LAKE_TYPES:
        return "lake"
    if site_type in STREAM_TYPES:
        return "stream"
    return "other"


def summarise(label, path, say):
    d = pd.read_csv(path, low_memory=False)
    d = d[d["ActivityMediaName"].astype(str).str.lower().eq("water")].copy()
    d["value"] = pd.to_numeric(d["ResultMeasureValue"], errors="coerce")
    d["date"] = pd.to_datetime(d["ActivityStartDate"], errors="coerce")
    types = d["site_type"] if "site_type" in d else pd.Series(pd.NA, index=d.index)
    d["cls"] = types.map(site_class)
    say("=" * 78)
    say("%s   stations with water results: %d   years %s-%s"
        % (label, d["MonitoringLocationIdentifier"].nunique(),
           d["date"].dt.year.min(), d["date"].dt.year.max()))
    for cls in ("lake", "stream", "other"):
        g = d[d["cls"].eq(cls)]
        if g.empty:
            continue
        say("  %s stations: %d" % (cls, g["MonitoringLocationIdentifier"].nunique()))
        for name, frac in ANALYTES:
            m = g["CharacteristicName"].eq(name)
            if frac:
                m &= g["ResultSampleFractionText"].astype(str).eq(frac)
            x = g.loc[m, "value"].dropna()
            if x.empty:
                continue
            units = sorted(g.loc[m, "ResultMeasure/MeasureUnitCode"].dropna().astype(str).str.lower().unique())
            say("    %-21s %-18s n=%-4d median=%-9.4g min=%-8.4g max=%-9.4g stations=%-3d %s"
                % (name, frac or "", len(x), x.median(), x.min(), x.max(),
                   g.loc[m & g["value"].notna(), "MonitoringLocationIdentifier"].nunique(),
                   "/".join(units)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="also write the report to this file")
    a = ap.parse_args(argv)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("OHIO FIELD LAKES - ARCHIVAL CHEMISTRY (Water Quality Portal), water samples only")
    say("Iron fractions are never pooled. Units as reported; iron and manganese in ug/L.")
    for label, path in SOURCES:
        if not os.path.isfile(path):
            say("=" * 78)
            say("%s: MISSING %s - run the fetch command in this script's docstring"
                % (label, os.path.relpath(path, ROOT)))
            continue
        summarise(label, path, say)
    if a.out:
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
